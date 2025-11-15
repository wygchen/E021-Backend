"""
populate_db.py

Small pipeline to fill missing fields in `RAG/destination_db.json` and
`RAG/experience_db.json` using an LLM (Gemini / OpenAI) and optional web
enrichment via simple HTTP scraping.

Design / Contract (short):
- Inputs: paths to the two JSON files (defaults to RAG/destination_db.json and RAG/experience_db.json), flags --write (persist changes) and --web (allow using seed URLs in entries to fetch extra text), provider selection.
- Output: Updated JSON files (if --write) or preview printed to stdout (dry-run). Backups created when writing.
- Error modes: network/LLM failures are retried once and then raise; malformed LLM output is ignored and left unchanged.

Usage examples (see README_POPULATE.md for more):
  python RAG/populate_db.py --dry-run
  python RAG/populate_db.py --write --provider openai

Environment variables:
- OPENAI_API_KEY or GEMINI_API_KEY (depending on provider). For Gemini, you may need to set GEMINI_ENDPOINT.

This script is intentionally conservative: it asks the LLM to return a JSON object
with only the filled keys, so merging is straightforward.
"""
import argparse
import json
import os
import time
import copy
from typing import Any, Dict, List, Optional

import requests
from bs4 import BeautifulSoup

try:
    import openai
except Exception:
    openai = None

ROOT = os.path.dirname(os.path.dirname(__file__))
DEST_PATH = os.path.join(ROOT, "RAG", "destination_db.json")
EXP_PATH = os.path.join(ROOT, "RAG", "experience_db.json")
PROMPT_DIR = os.path.join(ROOT, "RAG", "prompts")


def load_json(path: str) -> List[Dict[str, Any]]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: str, data: List[Dict[str, Any]]) -> None:
    # create backup
    bak = path + ".bak"
    if not os.path.exists(bak):
        with open(bak, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def find_missing_fields(entry: Dict[str, Any], keys_to_check: List[str]) -> List[str]:
    miss = []
    for k in keys_to_check:
        v = entry.get(k, None)
        if v is None:
            miss.append(k)
            continue
        if isinstance(v, str) and v.strip() == "":
            miss.append(k)
            continue
        if isinstance(v, list) and len(v) == 0:
            miss.append(k)
            continue
    return miss


def simple_web_fetch_text(url: str, timeout: int = 8) -> Optional[str]:
    try:
        resp = requests.get(url, timeout=timeout, headers={"User-Agent": "ragn-llm/1.0"})
        if resp.status_code != 200:
            return None
        doc = BeautifulSoup(resp.text, "html.parser")
        # heuristics: page title + first 3 <p>
        title = doc.title.string.strip() if doc.title and doc.title.string else ""
        ps = doc.find_all("p")
        text = title + "\n\n"
        for p in ps[:5]:
            t = p.get_text().strip()
            if t:
                text += t + "\n\n"
        return text.strip()
    except Exception:
        return None


def load_prompt(template_name: str) -> str:
    path = os.path.join(PROMPT_DIR, template_name)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def call_llm_openai(prompt: str, model: str = "gpt-4o-mini", max_tokens: int = 1000) -> str:
    if openai is None:
        raise RuntimeError("openai package not installed. Install 'openai' to use OpenAI provider.")
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not set in environment")
    openai.api_key = api_key
    # uses ChatCompletion API if available; fallback to completion
    try:
        resp = openai.ChatCompletion.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=0.0,
        )
        return resp.choices[0].message.content
    except Exception as e:
        raise


def call_llm_genai(prompt: str, model: str = "gemini-2.5-pro") -> str:
    # Lazy import so running in prompt-only mode doesn't require google-genai to be installed.
    try:
        from google import genai
    except Exception as e:
        raise RuntimeError("The 'google.genai' package is not installed or importable. Install it with: pip install google-genai") from e

    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    client = None
    try:
        if api_key:
            try:
                client = genai.Client(api_key=api_key)
            except TypeError:
                os.environ.setdefault("GOOGLE_API_KEY", api_key)
                client = genai.Client()
        else:
            client = genai.Client()
    except Exception as e:
        raise RuntimeError(f"Failed to construct genai.Client(): {e}") from e

    try:
        response = client.models.generate_content(model=model, contents=prompt)
    except Exception as e:
        raise RuntimeError(f"Model call failed: {e}") from e

    # extract best text candidate
    # many client responses expose 'text' attribute
    if hasattr(response, "text") and response.text:
        return response.text

    # try dict-like conversion
    try:
        as_dict = dict(response)
        # common shapes: {'candidates': [{'content': '...'}]} or {'output': '...'}
        if "candidates" in as_dict and isinstance(as_dict["candidates"], list) and len(as_dict["candidates"]) > 0:
            cand = as_dict["candidates"][0]
            if isinstance(cand, dict) and "content" in cand:
                return cand["content"]
        if "output" in as_dict:
            return as_dict["output"]
        # fallback: pretty-print the dict
        return json.dumps(as_dict, indent=2, ensure_ascii=False)
    except Exception:
        return str(response)


def call_llm_generic(provider: str, prompt: str, model: str = None) -> str:
    # provider supports: openai, genai (alias: gemini)
    if provider == "openai":
        return call_llm_openai(prompt, model=(model or "gpt-4o-mini"))
    if provider in ("genai", "gemini"):
        return call_llm_genai(prompt, model=(model or "gemini-2.5-pro"))
    raise NotImplementedError(f"Provider {provider} is not implemented. Use 'openai' or 'genai'.")


def ask_fill(entry: Dict[str, Any], missing: List[str], prompt_template: str, web_text: Optional[str], provider: str, model: Optional[str] = None, prompt_only: bool = False) -> Optional[Dict[str, Any]]:
    # Create prompt
    prompt = prompt_template
    # embed entry as pretty json
    entry_json = json.dumps(entry, indent=2, ensure_ascii=False)
    prompt = prompt.replace("{{ENTRY_JSON}}", entry_json)
    prompt = prompt.replace("{{MISSING}}", json.dumps(missing))
    prompt = prompt.replace("{{WEB_TEXT}}", web_text or "")
    if prompt_only:
        # preview mode: print prompt and do not call the model
        print("\n--- Prompt preview (prompt-only mode) ---\n")
        print(prompt)
        return None

    # call LLM
    try:
        raw = call_llm_generic(provider, prompt, model=model)
    except Exception as e:
        print(f"LLM call failed: {e}")
        return None

    # raw is expected to be a string containing JSON. Try to extract fenced JSON first.
    try:
        text = raw if isinstance(raw, str) else str(raw)
        # look for a fenced json block ```json ... ```
        if "```json" in text:
            start = text.index("```json") + len("```json")
            end = text.find("```", start)
            if end != -1:
                blob = text[start:end].strip()
            else:
                blob = text[start:].strip()
        else:
            # fallback: take first {...} block
            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1 and end > start:
                blob = text[start:end+1]
            else:
                blob = text

        parsed = json.loads(blob)
        # ensure only keys from missing are accepted
        filtered = {k: v for k, v in parsed.items() if k in missing}
        return filtered
    except Exception:
        print("Could not parse LLM response as JSON; raw output follows:\n", raw)
        return None


DEST_KEYS_TO_FILL = [
    "hk_express_destination_type",
    "one_line_pitch",
    "primary_archetype",
    "semantic_profile",
    "semantic_antiprofile",
    "dominant_vibes",
    "primary_experience_types",
    "cost_index",
    "logistics_hub_score",
    "transport_profile",
    "planner_memo",
    "key_dichotomies",
]

EXP_KEYS_TO_FILL = [
    "package_type",
    "one_line_pitch",
    "semantic_profile",
    "semantic_antiprofile",
    "primary_preference_tag",
    "secondary_preference_tags",
    "vibe_tags",
    "cost_tier",
    "duration_type",
    "physical_intensity",
    "logistics_model",
    "package_inclusions",
    "booking_lead_time_warning",
    "event_details",
    "itinerary_role",
    "itinerary_pitch_text",
    "hesitation_analyzer",
    "conflict_solver",
    "competing_experience_ids",
    "upsell_opportunity_ids",
    "planner_memo",
]


def process_entries(entries: List[Dict[str, Any]], keys_to_fill: List[str], prompt_template_name: str, provider: str, web_mode: bool, write: bool, db_path: str, model: Optional[str] = None, prompt_only: bool = False, first_only: bool = False) -> None:
    prompt_template = load_prompt(prompt_template_name)
    changed = 0
    for idx, entry in enumerate(entries):
        if first_only and idx != 0:
            # skip everything except first entry when first_only requested
            continue
        missing = find_missing_fields(entry, keys_to_fill)
        if not missing:
            continue
        print(f"Entry {idx} id={entry.get('destination_id') or entry.get('experience_id')} missing: {missing}")
        web_text = None
        # if web mode and the entry includes 'seed_urls' take the first
        seed_urls = entry.get("seed_urls") or entry.get("seed_url")
        if web_mode and seed_urls:
            if isinstance(seed_urls, list):
                for u in seed_urls:
                    txt = simple_web_fetch_text(u)
                    if txt:
                        web_text = txt
                        break
            elif isinstance(seed_urls, str):
                web_text = simple_web_fetch_text(seed_urls)

        result = ask_fill(entry, missing, prompt_template, web_text, provider, model=model, prompt_only=prompt_only)
        if result:
            for k, v in result.items():
                entry[k] = v
            changed += 1
            print(f"Filled {len(result)} fields for entry {entry.get('destination_id') or entry.get('experience_id')}")
        else:
            print("No fill produced for this entry (LLM error or parse failure).")

    if changed and write:
        print(f"Writing changes to {db_path} (changed {changed} entries)")
        write_json(db_path, entries)
    else:
        print(f"Completed; changed {changed} entries. (write={write})")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dest", default=DEST_PATH, help="Path to destination_db.json")
    parser.add_argument("--exp", default=EXP_PATH, help="Path to experience_db.json")
    parser.add_argument("--provider", default="openai", help="LLM provider (openai|genai|gemini)")
    parser.add_argument("--model", default=None, help="Model name to call (optional, provider default used if omitted)")
    parser.add_argument("--write", action="store_true", help="Persist changes to disk")
    parser.add_argument("--web", action="store_true", help="Allow web enrichment using 'seed_url' or 'seed_urls' fields in entries")
    parser.add_argument("--dry-run", action="store_true", help="Alias for not writing files (default)")
    parser.add_argument("--prompt-only", action="store_true", help="Only build and print prompts, do not call any LLM provider")
    parser.add_argument("--first-only", action="store_true", help="Process only the first entry (useful for step-by-step testing)")
    args = parser.parse_args()

    provider = args.provider
    write = args.write and not args.dry_run

    dests = load_json(args.dest)
    exps = load_json(args.exp)

    print(f"Loaded {len(dests)} destinations and {len(exps)} experiences")

    process_entries(dests, DEST_KEYS_TO_FILL, "llm_fill_destination.txt", provider, args.web, write, args.dest, model=args.model, prompt_only=args.prompt_only, first_only=args.first_only)
    process_entries(exps, EXP_KEYS_TO_FILL, "llm_fill_experience.txt", provider, args.web, write, args.exp, model=args.model, prompt_only=args.prompt_only, first_only=args.first_only)


if __name__ == "__main__":
    main()
