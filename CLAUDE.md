# Trove

Trove is a professional networking web app for CWRU students and alumni. Every member is the
**author of the book they haven't written yet**: an AI interview finds what they know that
others don't, and turns it into a book (a title and chapters). Other members browse books and
check one out, which means a short video call with its author. The full product plan is
[docs/trove.md](docs/trove.md). Read the relevant section before building anything.

**Before changing code, read [CONTRIBUTING.md](CONTRIBUTING.md).** It covers how several
people's agents work in this repo at once without stepping on each other. Its rules are not
optional.

## Stack

- `api/`: Python 3.13, FastAPI, PyMongo (async) on MongoDB Atlas, Anthropic SDK. Managed with **uv**.
- `web/`: React 19, TypeScript, Vite, React Router, openapi-fetch. Lint and format with **Biome**, tests with **Vitest**.

## Commands

Run from the repository root unless noted.

| Task | Command |
|---|---|
| Install everything | `uv sync --directory api && npm --prefix web install` |
| Run the app | `python3 scripts/dev.py` (web on :5173, API docs on :8000/docs) |
| **All checks (run before every commit)** | `python3 scripts/check.py` (`--fix` formats first) |
| API tests only | `cd api && uv run pytest -q` (one file: `uv run pytest tests/test_auth.py`) |
| Web tests only | `npm --prefix web test` |
| Regenerate the typed API client | `python3 scripts/generate_api_client.py` (after any route or model change) |
| Run a feature's prompt evals | `cd api && uv run python -m evals.run <feature>` (costs money) |

## Layout

```
api/trove/<feature>/     one folder per feature: router.py, models.py, service.py
api/trove/core/          settings, database, shared models, errors (shared; change carefully)
api/trove/ai/            the Claude client; prompts in ai/prompts/<feature>/<name>.md
api/tests/               mirrors trove/; fixtures in conftest.py, fakes in fakes.py
api/evals/               prompt evals on fixed test personas
web/src/features/<feature>/   pages and components for one feature
web/src/ui/              shared components and design tokens (styles.css)
web/src/api/             client.ts, errors.ts, and schema.ts (generated, never edit by hand)
web/src/app/App.tsx      the route table
docs/                    trove.md (product), plan.md (work plan), architecture.md
```

Features: `auth`, `notifications`, `books`, `interview`, `discovery`, `checkouts`, `messaging`, `meetings`.
Each backend feature's `__init__.py` says what it covers and which collections it owns.

## Conventions

- **Feature boundaries.** A feature reads and writes only the MongoDB collections it owns. To use
  another feature's data, call that feature's `service.py` functions. Never query another
  feature's collections, and never import another feature's router.
- **Signed-in user:** `user: dict = Depends(get_current_user)` from `trove.auth.service`.
- **Database:** `database: AsyncDatabase = Depends(get_database)` from `trove.core.database`.
  Indexes live in the owning feature's `ensure_indexes`, listed in `INDEX_SETUPS` in `trove/main.py`.
- **Request bodies** subclass `trove.core.models.RequestBody` (strict, no unknown fields).
- **IDs** are `str(uuid4())` in `_id`. Times are `datetime.now(UTC)`.
- **Claude:** take `claude: Claude = Depends(get_claude)` from `trove.ai.client`, and call
  `await claude.create(...)`. It adds the model, the refusal fallback, and raises `ClaudeRefused`.
  Prompt text goes in `api/trove/ai/prompts/`, never inline. Follow `api/trove/ai/prompts/README.md`.
- **Email:** add a template in `notifications/templates.py` and a `notify_*` function in
  `notifications/service.py`, and call it as a background task.
- **Frontend API calls** go through `api` from `web/src/api/client.ts`. Types come from the generated
  `schema.ts`. Don't write request or response types by hand.
- **Styling:** use the CSS variables in `web/src/ui/styles.css`. No hard-coded colors.
- **Comments** explain *why*, not *what*. Match the density of the surrounding code.

## Product rules that code must respect

- **Names:** only first names appear before a mutual yes. Last names, email and contact details
  are revealed only on an accepted checkout.
- **Grounding:** everything the AI writes into a book must trace back to the member's own interview
  answers. A résumé guides questions only; nothing from it goes into the book.
- **No performance features:** no follower counts, likes, view counts, public request counts,
  "fully booked" badges, or feeds.
- **No cold messages:** messages exist only inside a checkout request.
- **Don't decide product questions in code.** If the plan doesn't say, stop and ask the human
  (see CONTRIBUTING.md, "Product questions").

## Secrets

Secrets live only in `.env` (git-ignored). Never print, log or commit their values. Tests must not
call the real Claude API or send real email: use `FakeClaude` and the default no-SMTP setup.
