# Ground truth: Inventory API (`fixtures/fastapi/items_api.py`)

- `GET /items` — List items. Optional `category` (string) query filter
  and `limit` (integer, default 20) for page size. Returns an array of
  `Item`.
- `GET /items/{item_id}` — Fetch one item by integer ID. Returns `Item`.
- `POST /items` — Create an item. Body is an `ItemCreate`: `name`
  (string, required), `description` (string, optional), `price` (number,
  required). Returns the created `Item`, HTTP 201.
- `PUT /items/{item_id}` — Replace an item's details. Same body shape as
  create (`ItemCreate`). Returns the updated `Item`.
- `DELETE /items/{item_id}` — Remove an item. Returns HTTP 204, no body.
- `Item` model: `name` (string), `description` (string, optional),
  `price` (number), `in_stock` (boolean, defaults to true).

Expected generated-doc quality: high (4–5/5) — FastAPI + Pydantic gives
the extractor real type information for both request and response
bodies, so there's little left to infer.
