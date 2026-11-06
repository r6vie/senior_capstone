# Contributing to Trove

This file is written for **AI coding agents** (Claude Code, Codex, Cursor and others) working on
behalf of the people on this team. People should read it too. Several people's agents work in
this repository at the same time, so most of these rules exist to keep their work from
colliding.

Read [CLAUDE.md](CLAUDE.md) first for the stack, commands and code conventions.

## The rules (read these even if you read nothing else)

1. **One plan item per branch, one branch per pull request.** The work is split into items in
   [docs/plan.md](docs/plan.md). Never mix two items in one PR.
2. **Stay inside your item's files.** Each item lists the feature folders it owns. Don't edit
   files outside them except under "Shared files" below.
3. **Never push to `main`.** Every change reaches `main` through a reviewed PR with passing CI.
4. **Run `python3 scripts/check.py` before every commit.** Don't commit if it fails.
5. **Don't make product decisions.** If [docs/trove.md](docs/trove.md) or the plan item doesn't
   answer a question, stop and ask your human. Don't guess and build it. This is the most
   common way agent work goes wrong on this team.
6. **Never refactor, rename or reformat code you weren't asked to change**, especially another
   person's feature. Note it in your PR description instead.
7. **Small PRs.** Aim for under about 400 changed lines, not counting generated files. Split anything bigger.
8. **Leave the repo runnable.** After your PR merges, `python3 scripts/dev.py` must still start and
   every page that worked before must still work.

## Starting a piece of work

1. **Find your item** in `docs/plan.md`. Check that it's assigned to your human and that its
   dependencies are marked done. If they aren't, stop and tell your human.
2. **Update from `main`:**
   ```bash
   git checkout main && git pull
   ```
3. **Create a branch** named `<person>/<item-id>-<short-slug>`, for example
   `josef/b2-request-a-book`.
4. **Read before writing:**
   - the item in `docs/plan.md`
   - the matching section of `docs/trove.md`
   - the `__init__.py` docstring of each feature you'll touch
   - an existing feature that does something similar (`auth` is the reference implementation)
5. **Install and verify the baseline:**
   ```bash
   uv sync --directory api && npm --prefix web install && python3 scripts/check.py
   ```
   If the baseline fails, stop and tell your human. Don't fix unrelated breakage inside your item.
6. **List your assumptions before writing code.** Go through the item and write down every
   product choice it leaves open: the item's "Decide first" questions, plus anything else you
   would otherwise have to guess (wording, limits, edge cases, what happens on failure).
   - Give your human each question with your recommendation, and wait for their answers.
   - Record the answers in `docs/trove.md` as part of your PR.

   Only then start building.

## Where code goes

### Adding to a backend feature (`api/trove/<feature>/`)

| File | What goes in it |
|---|---|
| `__init__.py` | A docstring: what the feature covers, the collections it owns, the doc section. Keep it current. |
| `models.py` | Pydantic request models (subclass `RequestBody`) and response models. |
| `service.py` | All database access and business logic, plus `async def ensure_indexes(database)`. Other features may import from here. |
| `router.py` | `router = APIRouter(prefix="/<feature>", tags=[...])`. Thin: validate, call service, return models. |

Then:

1. Register the feature in `api/trove/main.py`: add the router to `ROUTERS` and `ensure_indexes`
   to `INDEX_SETUPS`.
2. Write tests in `api/tests/test_<feature>.py`.
3. Run `python3 scripts/generate_api_client.py` and commit `api/openapi.json` and
   `web/src/api/schema.ts`.

### Adding to the frontend (`web/src/features/<feature>/`)

- Pages are `<Name>Page.tsx`, components are `<Name>.tsx`, tests sit next to them as `*.test.tsx`.
- Register each page's route in `web/src/app/App.tsx`.
- Call the API only through `api` in `web/src/api/client.ts`, with types from `schema.ts`.
- Reusable building blocks (buttons, fields, layout) go in `web/src/ui/`. Check there before
  creating a new one.
- **Look and feel: follow [docs/design/system.md](docs/design/system.md).** Use the tokens and the component
  recipes; no raw colors, sizes, fonts or radii. The system has three tiers: *fixed* (palette and the red rule,
  type, square corners, dot tone, the book object: change only with a human's yes), *defaults* (the recipes and
  screen pattern: follow, or say why not in the PR) and *free* (screens and parts not designed yet: design them
  from the tokens, and add any new pattern to the Additions section of `system.md`). Say in the PR description
  what, if anything, you added or deviated from.

### Adding a prompt

Follow [api/trove/ai/prompts/README.md](api/trove/ai/prompts/README.md). Prompts are product
decisions in text form. A prompt change needs its evals run, and the output difference
described in the PR.

## Feature boundaries and data ownership

Each feature owns its MongoDB collections, listed in its `__init__.py`. Only that feature's
`service.py` reads or writes them. To use another feature's data, call that feature's service
functions. If the function you need doesn't exist:

- If the other feature is **yours in this item**, add it.
- If not, **don't add it yourself.** Write down in your PR what you need, and tell your human so
  the owner can add it. Work against a small stub in your own code until then.

This is what lets two agents build two features at once without editing the same files.

## Shared files

These files are touched by many items. Change them only when your item needs it, keep the
change minimal, and **say so in the PR description** so reviewers look closely:

- `api/trove/main.py` (registering routers and indexes: add lines, don't reorder)
- `api/trove/core/*`
- `api/tests/conftest.py`, `api/tests/fakes.py`
- `web/src/app/App.tsx` (add routes, don't restructure)
- `web/src/ui/*`, including the design tokens in `styles.css`, and `docs/design/system.md` with
  `docs/design/system/tokens.css` (the design system: changes to Fixed rules need a human's yes)
- `CLAUDE.md`, `CONTRIBUTING.md`, `scripts/*`, `.github/*`

## The API contract

The backend's Pydantic models are the single source of truth for the API. The frontend's types
are generated from them:

```bash
python3 scripts/generate_api_client.py
```

Run it after **any** change to a route, request model or response model, and commit both
generated files in the same commit as the change. CI fails if they are stale.

**Merge conflicts in `api/openapi.json` or `web/src/api/schema.ts`: don't resolve them by hand.**
Resolve the real conflicts in the Python code first, then rerun the generator and commit its output.

## Tests

- Every new route gets an API test: the success case, the main failure case (401, 404, 409 and so
  on), and any product rule it enforces (for example, "names stay hidden before a yes").
- Database tests use a real MongoDB. Take the `client` fixture, or `database` for direct access.
  Each test run gets a throwaway database, emptied between tests.
- **Never call the real Claude API in tests.** Use the `fake_claude` fixture and script its
  responses with `text_message(...)` from `tests/fakes.py`.
- Never send real email. Tests run with SMTP turned off automatically.
- Frontend: test behavior a member would notice, with Testing Library. Don't test implementation details.

## Commits and pull requests

- **Commit messages:** one imperative line saying what the change does for the product, for
  example "Let authors set how many copies they lend". Add detail below it only when it helps.
- **Before opening a PR:**
  ```bash
  git fetch origin && git rebase origin/main && python3 scripts/check.py
  ```
- **Open the PR** with `gh pr create`, and fill in the template (`.github/pull_request_template.md`)
  completely. Link the plan item.
- **PRs are squash-merged** after one approving review from a teammate and green CI.
- **When your PR merges,** mark the item done in `docs/plan.md`. Either include that change in
  the PR, or make it right after in a one-line PR.

## Product questions

`docs/trove.md` separates Decided, Leaning and Open. Build only what is **Decided**. When you
reach a question it doesn't answer:

1. Stop. Don't pick an answer and build it.
2. Ask your human the question, with two or three concrete options and your recommendation.
3. **Who decides:**
   - The owner of the feature decides questions inside that feature (owners are listed in
     `docs/plan.md`).
   - If the question affects another person's feature, it waits for the next team sync. Work
     on something else meanwhile.
4. Once it's decided, record the decision in `docs/trove.md` (in your PR) so the next agent
   doesn't ask again.

## Handing work over

Agents don't remember earlier sessions, and teammates don't see your terminal. When you stop
partway through, the work must be resumable by anyone:

- Commit and push the branch, even if it isn't finished. Open a **draft** PR.
- In the draft PR description, write: what's done, what's left, and any decision you're waiting on.
- Don't leave work only in your local working tree.

## Never

- Commit `.env`, API keys, connection strings or personal data.
- Use `git push --force` on `main` or on someone else's branch.
- Merge or rebase onto a teammate's unmerged branch. Wait until it reaches `main`.
- Disable, skip or weaken a test or check to make it pass. Fix the cause, or ask your human.
- Add a dependency without saying why in the PR. Prefer what's already installed.
- Edit `web/src/api/schema.ts` or `api/openapi.json` by hand.
- Change a prompt without running its evals.
