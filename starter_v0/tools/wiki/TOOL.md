---
name: wiki
track: core
kind: live_api
provider: Wikipedia REST API (no key)
requires_env: []
inputs: [title, lang]
outputs: [items]
side_effect: false
---
# wiki

Returns the lead summary of one Wikipedia article (`/api/rest_v1/page/summary/{title}`)
for background/definition questions ("X là gì?", "ai là Y?").

- `lang`: `en` or `vi`; any other value falls back to `en`.
- Empty/non-string `title` -> error dict, no HTTP request.
- Exact title 404 -> full-text search (`/w/rest.php/v1/search/page`), summary of the best hit, result marked
  `resolved_from`, `match: search_fallback`, `alternatives`, `note`. No hit -> `WikiNotFound` error dict suggesting `lookup`.
- HTTP 429 -> one retry after `Retry-After` (capped at 5s).
- Disambiguation pages and other HTTP errors -> error dict, never raises.
- Not for news or recent events (use `lookup`).
