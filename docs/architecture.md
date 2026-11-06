# Architecture

How Trove is put together. For what the product is, see [trove.md](trove.md).

## Overview

```
Browser ── web/ (React, Vite) ── /api/* ──► api/ (FastAPI) ──► MongoDB Atlas
                                                  └──────────► Claude (Anthropic API)
                                                  └──────────► SMTP (email)
```

In development, Vite serves the app on `:5173` and forwards `/api/*` to FastAPI on `:8000`,
removing the `/api` prefix. The frontend never talks to MongoDB or Claude directly.

## Backend

- `trove/main.py` builds the app. It lists every feature's router (`ROUTERS`) and index setup
  (`INDEX_SETUPS`).
- `trove/core/database.py` connects to MongoDB in the background when the app starts, retrying
  every 5 seconds. Until it's connected, routes that need the database return 503, and
  `/health` reports `"database": false`.
- `trove/core/config.py` reads settings from the root `.env`; real environment variables win.
- **Sessions:** `POST /auth/login` returns a random bearer token. Only its SHA-256 hash is
  stored, in `sessions`, with a TTL index for expiry. `get_current_user` checks the session and
  the account on every request.
- **Errors:** validation errors never echo submitted values, and database errors become a
  generic 503. Every response is `Cache-Control: no-store` except the API docs.

### Data ownership

| Collection | Owner | Notes |
|---|---|---|
| `users` | auth | Unique on `email` (stored lowercase) |
| `sessions` | auth | Token hash, expiry via TTL index |
| `auth_attempts` | auth | Rate-limit counters, TTL index |
| `notifications` | notifications | One document per email sent, `_id` = dedupe key |

Each new feature adds its rows here in the PR that creates its collections.

## AI

- All Claude calls go through `trove.ai.client.Claude`. It sets the model (`ANTHROPIC_MODEL`,
  default `claude-opus-5-5`) and turns on server-side refusal fallback for models that support
  it. A refusal raises `ClaudeRefused` rather than coming back as a normal response.
- Prompts are Markdown files in `trove/ai/prompts/<feature>/`, loaded with `load_prompt`. Keep the
  prompt prefix stable (no dates or member data in it) so prompt caching works.
- `api/evals/` runs a feature's prompts on fixed test personas against the real API, and saves
  the outputs for people to read and compare.

## Frontend

- `src/app/App.tsx` is the route table. Pages live in `src/features/<feature>/`.
- `src/api/client.ts` is an `openapi-fetch` client typed by the generated `src/api/schema.ts`. A
  middleware adds the bearer token from `sessionStorage`.
- `src/features/auth/AuthProvider.tsx` holds the signed-in member. `RequireAuth` guards pages that
  need a session.
- Design tokens are CSS variables in `src/ui/styles.css`. The visual design is still to be decided.

## Testing

- **API:** pytest with an async HTTP client against the real app.
  - Database tests use a real MongoDB and a throwaway `trove_test_*` database. Locally that's
    the cluster in `.env` (or `TROVE_TEST_MONGODB_URI`); in CI it's a MongoDB service container.
  - Claude is replaced by `FakeClaude`.
- **Web:** Vitest with jsdom and Testing Library.
- **CI** (`.github/workflows/ci.yml`) runs lint, format, tests, the API-client freshness check,
  type-checking and the production build on every PR. `scripts/check.py` runs the same steps
  locally.
