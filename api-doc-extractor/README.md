# AutoDoc — Extractor & Dataset (Person 1: Data & Extractor)

Turns raw API source — an OpenAPI/Swagger spec, a Flask or FastAPI app, or
a Java Spring controller — into one canonical JSON document. That JSON is
the **only** contract Person 2 (Doc Writer / LLM layer) needs to consume;
they never have to know what the original source looked like.

## Why this shape

The problem statement is "manual API docs are slow and go stale." The
fix this repo targets is the first half of the pipeline: **reliable,
structured extraction**, so the LLM step downstream is writing prose
around solid facts instead of hallucinating parameter types. Everything
here is deterministic static analysis — no LLM calls, no code execution —
so it's fast, free, and safe to run on untrusted source.

## Layout

```
schema/
  api_schema.json      # the shared JSON Schema contract (source of truth)
  models.py             # Python dataclasses mirroring it, + validate()
extractors/
  openapi_parser.py     # OpenAPI 3.x + Swagger 2.0 (JSON or YAML) — the reliable baseline
  flask_fastapi_parser.py  # ast-based static analysis of Flask & FastAPI route decorators
  spring_parser.py      # stretch: regex-based Java Spring (@RestController) parser
fixtures/                # varied real/representative API source, for demo + testing
  openapi/petstore.yaml            # official OAI example (OpenAPI 3.0, MIT)
  openapi/petstore-expanded.yaml   # official OAI example, richer version
  openapi/task-api.swagger2.json   # hand-written Swagger 2.0 fixture (legacy-format coverage)
  flask/blog_api.py                # representative Flask app, no type hints (worst case for inference)
  fastapi/items_api.py             # representative FastAPI + Pydantic app (best case for inference)
  spring/UserController.java       # representative Spring controller (second-language demo)
eval-data/
  ground_truth/*.md     # human-quality reference docs, one per fixture, for Person 2's self-eval
  README.md              # how to use ground_truth for the 80% clarity/completeness target
tests/
  test_extractors.py    # 22 tests: every extractor × every fixture, plus schema validation
cli.py                   # single entry point for extraction (see below)
```

## Quick start

```bash
pip install -r requirements.txt
python -m pytest tests/ -v          # 22 passed
```

## CLI usage

```bash
# One file, auto-detect source type
python cli.py extract fixtures/openapi/petstore.yaml --out out.json

# Force a type (skip auto-detection)
python cli.py extract fixtures/flask/blog_api.py --type flask

# Batch mode — everything under fixtures/ in one go (what the demo video uses)
python cli.py extract-dir fixtures --out-dir /tmp/extracted

# Validate any JSON file against the shared schema
python cli.py validate out.json
```

Every run prints (to stderr) any schema-validation errors and any
extraction *warnings* — e.g. "no type hint, typed as unknown" or "Flask
route uses `request.get_json()`, body shape not inferable." These aren't
failures; they're low-confidence flags Person 2/3 should surface rather
than silently paper over with a guess.

## The schema contract (hand-off to Person 2)

Full definition: `schema/api_schema.json`. Shape, abbreviated:

```jsonc
{
  "api_name": "Swagger Petstore",
  "version": "1.0.0",
  "base_url": "http://petstore.swagger.io/v1",
  "source_type": "openapi",           // openapi | flask | fastapi | spring
  "endpoints": [
    {
      "path": "/pets/{petId}",
      "method": "GET",
      "summary": "Info for a specific pet",
      "description": "...",
      "parameters": [
        { "name": "petId", "in": "path", "required": true, "type": "string", "description": "..." }
      ],
      "request_body": null,           // or { content_type, required, schema, example }
      "responses": [
        { "status_code": "200", "description": "...", "schema": { "fields": { ... } } }
      ]
    }
  ],
  "extraction_metadata": {
    "source_file": "fixtures/openapi/petstore.yaml",
    "extractor_version": "openapi_parser/1.0",
    "extracted_at": "2026-09-23T08:00:00+00:00",
    "warnings": []
  }
}
```

`schema/models.py::validate(doc_dict)` checks any dict against this and
returns a list of human-readable errors (empty = valid) — Person 2/3 can
import and call this directly rather than re-implementing validation.

## What each extractor actually does

- **`openapi_parser`** — parses OpenAPI 3.x and Swagger 2.0, JSON or YAML.
  Resolves local `$ref`s (one level, with cycle protection) into a
  simplified `{fields: {...}}` shape so Person 2 doesn't need a JSON
  Schema resolver of their own.
- **`flask_fastapi_parser`** — walks the file's AST (nothing is imported
  or executed). Detects `Flask()`/`FastAPI()`/`APIRouter()`/`Blueprint()`
  instantiation, then every `@app.route(...)` / `@app.get(...)` etc.
  decorator. For Flask: parses `<int:id>`-style converters for path
  params, and does a best-effort scan of the function body for
  `request.args.get(...)` to catch query params (Flask has no type hints
  to read, so this is inherently approximate — flagged via warnings).
  For FastAPI: reads real type hints for path/query params, and resolves
  `class Foo(BaseModel): ...` definitions in the same file to fill in
  request/response body field shapes.
- **`spring_parser`** *(stretch)* — regex-based (Java has no `ast`
  equivalent available here). Handles the common
  `@GetMapping`/`@PostMapping`/... + `@PathVariable`/`@RequestParam`/
  `@RequestBody` idiom, plus class-level `@RequestMapping` prefixes and
  Javadoc-as-description. Explicitly scoped as "demo credibility for
  varied APIs," not a production Java parser — anything it can't
  confidently parse becomes a warning, not a guess.

## Data considerations (fixtures/eval-data)

- `petstore.yaml` / `petstore-expanded.yaml` are the unmodified, official
  OpenAPI Initiative example spec (MIT-licensed) — used as-is because they
  already carry real human-written descriptions, which makes them a good
  "does generation preserve existing doc quality" check.
- `task-api.swagger2.json`, `blog_api.py`, `items_api.py`, and
  `UserController.java` were written from scratch as representative
  examples of each framework's idiomatic style (not pulled from a
  specific third-party repo), so there's no attribution or licensing
  question and no risk of stray secrets.
- Confirmed via `grep -rniE "api[_-]?key|secret|password|token|..."` across
  `fixtures/` and `eval-data/` — no matches other than this sentence
  itself.
- `eval-data/ground_truth/*.md` gives Person 2 something concrete to
  score generated docs against for the 80% clarity/completeness target
  (see `eval-data/README.md` for the suggested rubric flow).

## Known limitations (by design, not oversight)

- Flask query-param **types** are always guessed as `string` (that's all
  `request.args` ever returns) — flagged, not asserted as fact.
- FastAPI `response_model=list[Item]` (a generic/list-wrapped model) isn't
  unwrapped yet — only bare `response_model=Item` resolves to a field
  shape. List-of-model responses fall back to `schema: null`.
- The Spring extractor doesn't follow `@RequestBody User user` into the
  `User` class to get its fields — it records `model_type: "User"` and
  lets Person 2 note "see User model" rather than fabricating fields.
- No cross-file resolution for OpenAPI (`$ref` to another file) — only
  local (`#/...`) refs are resolved.

These are the honest edges of static analysis without a full type
checker or import graph — better to flag them than to generate
confident-sounding wrong documentation.

## Handing off

```bash
python cli.py extract-dir fixtures --out-dir shared/extracted
```
gives Person 2 a directory of schema-valid JSON to build
`call_llm(...)` prompts against, and gives Person 3 the same JSON to
route through the upload → generate → render UI flow.
