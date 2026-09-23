# Ground truth: User API (`fixtures/spring/UserController.java`)

- `GET /api/users` — List all registered users. Optional `page` query
  parameter (integer) for pagination.
- `GET /api/users/{id}` — Fetch a single user by numeric ID.
- `POST /api/users` — Register a new user. Body is a `User` object
  (fields not shown in this controller — see the `User` model class).
- `PUT /api/users/{id}` — Update an existing user's profile. Body is a
  `User` object.
- `DELETE /api/users/{id}` — Deactivate (soft-delete) a user account.
  Returns no body.

Expected generated-doc quality: medium — the regex-based Spring extractor
gets method/path/param names and Javadoc summaries, but doesn't resolve
the `User` model's own fields (that would require parsing a second file).
A good generated doc should flag the request/response body shape as
"see User model" rather than guessing its fields.
