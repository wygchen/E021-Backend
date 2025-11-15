# Populate DB pipeline

This small pipeline helps fill missing fields in the RAG JSON files using an LLM and optional web enrichment.

Quick usage:

1. Dry-run (no writes):

```bash
python RAG/populate_db.py --dry-run --provider openai
```

2. Persist changes (writes to the files, creates .bak first):

```bash
python RAG/populate_db.py --write --provider openai
```

3. Use web enrichment (entries can include `seed_url` or `seed_urls` fields):

```bash
python RAG/populate_db.py --write --web
```

Environment variables:
- `OPENAI_API_KEY` (for OpenAI provider)

Notes and assumptions:
- The script asks the LLM to return a JSON object containing only the missing fields. The script will merge those keys into the original entry.
- Entries may include `seed_url` or `seed_urls` keys that point to pages which the script will scrape for supporting text. The LLM is allowed to use that text as factual context.
- Provider support currently implemented for `openai` (requires `openai` Python package). The code is structured for adding other providers later.

Limitations and next steps:
- LLM output parsing is naive (extract first JSON block). If the model returns explanatory text before/after JSON the parser may fail. Use a low temperature and a parsing-friendly prompt to reduce this.
- Optionally: add a small unit test, or run on a single sample entry first.

````markdown
# Populate DB pipeline

This pipeline helps fill missing fields in the RAG JSON files using an LLM and optional web enrichment. It is designed to be conservative by default (dry-run) and to create backups before writing.

Quick usage:

1. Dry-run (no writes):

```bash
python RAG/populate_db.py --dry-run --provider openai
```

2. Persist changes (writes to the files, creates .bak first):

```bash
python RAG/populate_db.py --write --provider openai
```

3. Use web enrichment (entries can include `seed_url` or `seed_urls` fields):

```bash
python RAG/populate_db.py --write --web
```

Environment variables:
- `OPENAI_API_KEY` (for OpenAI provider)
- if using Gemini/genai: set your Google API key/credentials as required by your deployment (see `RAG/test_gemini_genai.py` and `run_gemini_curl.sh`).

Seeding note:
- The `one_line_pitch` fields in `RAG/experience_db.json` have been seeded from the human-written `RAG/experience_list.md` descriptions as an initial pass. When you run the LLM-based fill pipeline, the LLM will be asked to produce an improved one-line pitch (see the fill rules below) — please review generated pitches manually before publishing.

New content-size rules (enforced by prompts):
- one_line_pitch: 15–30 words (customer-facing, punchy). The pipeline seeds these from `experience_list.md` and the LLM should propose improved versions when asked.
- semantic_profile: exactly 3 paragraphs (each paragraph ~2–4 sentences). Use newline+newline to separate paragraphs inside the JSON string value.
- semantic_antiprofile: exactly 1 paragraph (1–2 sentences) describing who should NOT pick this experience.

Prompting & parsing guidance:
- The prompt templates in `RAG/prompts/` now require the LLM to return a fenced JSON block (```json ... ```). Use the genai client or the minimal `contents`-payload curl form that your deployment supports.
- The pipeline's parser expects a single fenced JSON block. If the model returns other text outside the fence, the parser may fail — keep temperature low and prefer the official client where possible.

Notes and assumptions:
- The script will merge returned keys into the original entry and will create a `.bak` copy before overwriting any file when `--write` is used.
- If a factual field is uncertain, the model should return `null` rather than fabricating a value.

Limitations and next steps:
- Improve the parser to more robustly extract JSON from messy model outputs (fenced + heuristic fallback).
- Add a `genai` provider branch to `RAG/populate_db.py` to use the official Google client for Gemini models.

Requirements:
- pip install openai requests beautifulsoup4

````
