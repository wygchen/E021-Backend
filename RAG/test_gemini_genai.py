"""
Use the official Google genai Python client to call a Gemini model.

This script loads the first experience from `RAG/experience_db.json`, builds a
prompt using the existing `RAG/prompts/llm_fill_experience.txt` template, and
calls the specified Gemini model via the `google-genai` client.

Usage:
  # set API key in env (the client may also accept application default creds)
  export GEMINI_API_KEY="..."

  python RAG/test_gemini_genai.py --model gemini-2.5-pro

Notes:
- This script tries to pass the API key to the client if the constructor accepts it.
- If `google.genai` package is not installed, it prints an instruction to install it.
"""
import os
import json
import argparse
import sys
from typing import Optional

ROOT = os.path.dirname(os.path.dirname(__file__))
EXP_PATH = os.path.join(ROOT, "RAG", "experience_db.json")
PROMPT_PATH = os.path.join(ROOT, "RAG", "prompts", "llm_fill_experience.txt")


def load_json(path: str):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_prompt(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def find_missing_fields(entry, keys_to_check):
    miss = []
    for k in keys_to_check:
        v = entry.get(k, None)
        if v is None or (isinstance(v, str) and v.strip() == "") or (isinstance(v, list) and len(v) == 0):
            miss.append(k)
    return miss


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


def build_prompt(entry, missing, web_text: Optional[str]):
    template = load_prompt(PROMPT_PATH)
    entry_json = json.dumps(entry, indent=2, ensure_ascii=False)
    prompt = template.replace("{{ENTRY_JSON}}", entry_json)
    prompt = prompt.replace("{{MISSING}}", json.dumps(missing))
    prompt = prompt.replace("{{WEB_TEXT}}", web_text or "")
    return prompt


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="gemini-2.5-pro", help="Model name to call (e.g. gemini-2.5-pro)")
    parser.add_argument("--key", help="API key (optional, will use GEMINI_API_KEY env if omitted)")
    parser.add_argument("--dry-run", action="store_true", help="Do not actually call the API; print the prompt")
    args = parser.parse_args()

    api_key = args.key or os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    model = args.model

    exps = load_json(EXP_PATH)
    if not exps:
        print("No experiences found in", EXP_PATH)
        sys.exit(1)

    first = exps[0]
    missing = find_missing_fields(first, EXP_KEYS_TO_FILL)
    prompt = build_prompt(first, missing, web_text=None)

    print("Model:", model)
    print("First experience:", first.get("experience_id"), first.get("experience_name"))
    print("Missing fields:", missing)

    if args.dry_run:
        print("\n--- Prompt preview ---\n")
        print(prompt)
        return

    try:
        from google import genai
    except Exception as e:
        print("The 'google.genai' package is not installed or importable. Install it with:")
        print("  pip install google-genai")
        print("Then re-run this script.")
        raise

    # Create client; some versions accept an api_key parameter, others use env
    client = None
    try:
        if api_key:
            try:
                client = genai.Client(api_key=api_key)
            except TypeError:
                # fallback: set env var and create default client
                os.environ.setdefault("GOOGLE_API_KEY", api_key)
                client = genai.Client()
        else:
            client = genai.Client()
    except Exception as e:
        print("Failed to construct genai.Client():", e)
        raise

    # Call the model. The library's generate_content method may accept either a
    # string or a list for 'contents'; the snippet from AI Studio uses contents="...".
    try:
        response = client.models.generate_content(model=model, contents=prompt)
    except Exception as e:
        print("Model call failed:", e)
        raise

    # Try to print the most useful text result
    printed = False
    # many client responses expose 'text' attribute
    if hasattr(response, "text"):
        print(response.text)
        printed = True

    # try dict-like
    try:
        as_dict = dict(response)
        # print any 'candidates' or 'output' content if present
        if not printed:
            print(json.dumps(as_dict, indent=2, ensure_ascii=False))
            printed = True
    except Exception:
        pass

    if not printed:
        # fallback to str()
        print(str(response))


if __name__ == "__main__":
    main()
