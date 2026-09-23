# Doc Writer (Person 2)

Turns Person 1's extractor JSON into enriched API documentation using cloud
LLMs, with prompt-engineering notes and self-eval scores as first-class
deliverables (per the "Doc Writer" role in the team plan).

**Input:** Person 1's JSON only (see `doc_writer/schema.py` for the exact
contract - share that file with Person 1 early).
**Output:** enriched JSON + Markdown docs + `PROMPTS.md` + eval scores.

## What's here

| File | Role |
|---|---|
| `doc_writer/schema.py` | The shared JSON contract (PC1 -> PC2 interface) + a minimal validator |
| `doc_writer/llm_client.py` | `call_llm(prompt, provider)` - Gemini primary, OpenRouter backup, `mock` offline mode |
| `doc_writer/prompts.py` | All prompt templates, versioned via `PROMPT_VERSION` |
| `doc_writer/generator.py` | Per-endpoint generation (description, params, examples, edge cases) |
| `doc_writer/cache.py` | Caches LLM responses by endpoint-content hash so unchanged endpoints skip the API call |
| `doc_writer/evaluator.py` | Second LLM pass that scores each doc 1-5 on clarity/completeness, aggregated against the 80% (4.0/5) target |
| `doc_writer/differ.py` | Plain-English summary of what changed between two runs |
| `doc_writer/output_writer.py` | Writes `enriched.json`, `docs.md`, `eval_report.md` |
| `doc_writer/cli.py` | Standalone CLI so this module runs and demos on its own |
| `fixtures/sample_extracted.json` | A hand-written example in Person 1's format, for testing before real extractor output exists |
| `PROMPTS.md` | Prompt-engineering log - update every time a prompt changes |

## Setup

```bash
cd doc_writer_project
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then fill in GEMINI_API_KEY (and OPENROUTER_API_KEY as backup)
```

## Run it

```bash
# Full run against the sample fixture, real Gemini calls
python -m doc_writer.cli --input fixtures/sample_extracted.json --output out/

# No API keys yet? Test the plumbing end-to-end with the offline mock provider
python -m doc_writer.cli --input fixtures/sample_extracted.json --output out/ --provider mock

# Skip the (slower) self-eval pass while iterating
python -m doc_writer.cli --input fixtures/sample_extracted.json --output out/ --no-eval

# Diff against a previous run once you've regenerated
python -m doc_writer.cli --input fixtures/sample_extracted.json --output out2/ \
    --diff-against out/enriched.json
```

This produces, in `out/`:
- `enriched.json` — the structured output Person 3's UI should render
- `docs.md` — human-readable Markdown version, good for the demo/README
- `eval_report.md` + `eval_raw.json` — self-eval scores (e.g. "avg 4.2/5 across 4 endpoints")
- `diff.json` — only if `--diff-against` was passed

## Integration points for the team

- **Person 1:** your extractor's output must validate against
  `doc_writer.schema.EXTRACTOR_SCHEMA` / pass `validate_minimal()`. Send me a
  sample file early so I can sanity-check against the real shape, not just
  `fixtures/sample_extracted.json`.
- **Person 3:** import `generate_all`, `score_all`, `summarize_changes` from
  `doc_writer` directly in your orchestrator, or shell out to
  `python -m doc_writer.cli`. `enriched.json` is what the doc viewer should
  render; `eval_report.md` numbers are good to show on-camera in the demo.

## Notes

- `provider="mock"` needs no API key at all and returns deterministic
  placeholder JSON - use it to unblock Person 3's UI work and CI-style
  testing before real keys/quota are sorted out.
- Caching is content-based (endpoint JSON + prompt version), so editing an
  endpoint's data - or bumping `PROMPT_VERSION` after a prompt change -
  correctly forces regeneration; unrelated unchanged endpoints stay cached.
