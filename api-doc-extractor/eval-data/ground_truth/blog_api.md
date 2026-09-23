# Ground truth: Blog API (`fixtures/flask/blog_api.py`)

Hand-written reference doc a human maintainer would produce for this
Flask app. Compare generated docs against this for the clarity/completeness
rubric.

- `GET /posts` — List all blog posts. Optional `author` query string
  parameter filters results to that author's posts.
- `POST /posts` — Create a new post. JSON body requires `title`, `body`,
  and `author` (all strings). Returns the created post with a generated
  `id`, HTTP 201.
- `GET /posts/{post_id}` — Fetch a single post by its integer ID. 404 if
  it doesn't exist.
- `PUT /posts/{post_id}` — Partially update a post's `title` and/or
  `body`. 404 if the post doesn't exist.
- `DELETE /posts/{post_id}` — Delete a post by ID. Always returns 204,
  even if the post didn't exist (idempotent delete).
- `GET /authors/{author_name}/posts` — List all posts by a given author.
  Accepts `limit`/`offset` query parameters for pagination (note: in the
  current implementation these are read but not yet applied — flag this
  as a known gap, not a doc-generation error).

Expected generated-doc quality: medium-high. Flask's lack of type hints
means query-parameter *types* have to be assumed (string, since
`request.args.get()` always returns strings) — a good generator should
note this as an assumption rather than asserting a specific type with
false confidence.
