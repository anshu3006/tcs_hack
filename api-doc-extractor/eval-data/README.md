# Eval data

This folder pairs each fixture in `fixtures/` with a short human-written
"ground truth" doc in `ground_truth/`, so the generation half of the
pipeline has something concrete to score itself against instead of a
vague "looks about right."

## Suggested self-eval flow (Person 2)

1. Run the extractor CLI on a fixture (e.g.
   `python cli.py extract fixtures/fastapi/items_api.py --out /tmp/items.schema.json`).
2. Generate docs from that JSON.
3. Feed both the generated doc and the matching `ground_truth/*.md` file
   into a rubric prompt (or a second LLM pass) that scores 1–5 on:
   - **Completeness** — does it cover every endpoint/param/response the
     ground truth mentions?
   - **Clarity** — would a developer unfamiliar with the code understand
     what to send and what to expect back?
   - **Honesty about uncertainty** — does it flag inferred/assumed
     details (e.g. Flask query-param types) rather than stating them as
     fact?
4. Average the scores across all four fixtures and cite that number in
   the demo (target: ≥80%, i.e. ≥4.0/5.0 average) instead of an
   unquantified claim.

## Why these four fixtures

| Fixture | Source type | What it stresses |
|---|---|---|
| `openapi/petstore.yaml` | OpenAPI 3.0 (official OAI example) | Baseline — spec already has docs; tests fidelity, not inference |
| `openapi/task-api.swagger2.json` | Swagger 2.0 | Legacy-format support (body param, `basePath`, no `servers` block) |
| `flask/blog_api.py` | Flask, no type hints | Realistic worst case for type inference; query-arg detection |
| `fastapi/items_api.py` | FastAPI + Pydantic | Best case for static inference — full type info available |
| `spring/UserController.java` | Java Spring | "Varied APIs" / second-language demo credibility (stretch goal) |

No fixture contains real user data, API keys, or secrets — `blog_api.py`,
`items_api.py`, and `UserController.java` were written from scratch as
representative examples; `petstore.yaml`/`petstore-expanded.yaml` are the
public, MIT-licensed OpenAPI Initiative example spec (unmodified).
