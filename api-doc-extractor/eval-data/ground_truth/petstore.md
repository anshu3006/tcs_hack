# Ground truth: Swagger Petstore (`fixtures/openapi/petstore.yaml`)

This fixture is the official OpenAPI 3.0 "Swagger Petstore" example, which
already ships with human-written `summary`/`description` fields inside the
spec itself — so for this one, the spec *is* the ground truth. Use it as a
"does the generator preserve/clarify existing documentation?" check rather
than a "can it invent documentation from nothing?" check.

Reference points to score generated docs against:

- `GET /pets` — "List all pets". Takes an optional `limit` query param
  ("How many items to return at one time (max 100)"). Returns a paged
  array of pets and includes an `x-next` pagination header.
- `POST /pets` — "Create a pet". Takes a `Pet` object in the request body.
  Returns 201 with no body on success.
- `GET /pets/{petId}` — "Info for a specific pet". `petId` is a required
  path parameter ("The id of the pet to retrieve"). Returns a single `Pet`.
- A `Pet` has `id` (int64), `name` (string, required), and an optional
  `tag` (string).
- All operations share an `Error` response shape (`code` + `message`) for
  unexpected errors.

Expected generated-doc quality: high (5/5) — nearly all the source
material a doc generator needs is already present in the spec, so this
fixture mainly tests formatting/presentation quality, not inference.
