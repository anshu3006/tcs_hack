# API Doc Generator — Person 3 (UI & Delivery)

## What this is

A working Streamlit app that runs the full pipeline (Extractor → Writer →
Viewer) end-to-end **right now**, using realistic mock data for the parts
Person 1 and Person 2 haven't built yet. This unblocks UI/demo work from
day one instead of waiting on integration.

## Run it

```bash
pip install -r requirements.txt
streamlit run app.py
```

Open the local URL Streamlit prints, paste some code or an OpenAPI spec
(or upload a `.py`/`.json`/`.yaml` file), click **Generate documentation**.

Headless / for the demo video or scripting:

```bash
python cli.py path/to/some_api.py --out result.json
```

## How Person 1 and Person 2 plug in

Drop these two files into the repo root:

- `extractor.py` exporting `extract(source_text: str, source_label: str = ...) -> list[dict]`
  matching `RAW_ENDPOINT_SHAPE` in `interfaces.py`.
- `writer.py` exporting `enrich(raw_endpoints: list[dict], source_label: str = ...) -> list[dict]`
  matching the enriched shape in `interfaces.py` (raw fields + `description`,
  `parameter_explanations`, `examples`, `edge_cases`, `eval_score`).

`orchestrator.py` auto-detects these files. If either is missing, it falls back
to `mock_pipeline.py` — so the app never breaks, it just runs on mock data
until the real module lands. The sidebar shows a banner when it's running on
mocks, so it's always clear which parts are live during the demo.

## Files

| File | Purpose |
|---|---|
| `interfaces.py` | The JSON contract everyone codes against |
| `mock_pipeline.py` | Fake extractor/writer for standalone dev |
| `orchestrator.py` | Chains extractor → writer, caches last run, computes diffs |
| `app.py` | Streamlit UI: upload, sidebar nav, method badges, search, examples, eval scores, diff view |
| `cli.py` | Headless runner for scripting / the demo video |

## Still to do (Person 3 scope)

- Swap in real `extractor.py` / `writer.py` once Person 1/2 land theirs
- `.docx`/PDF export button (stretch — Office prereq)
- Record demo video: run 2-3 of Person 1's real-world fixture APIs through
  this UI live, across at least 2 frameworks/languages
- Top-level project README + packaging once all three slices are merged
