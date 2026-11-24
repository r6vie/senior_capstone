# Contributing to Trove

This file is written for **AI coding agents** (Claude Code, Codex, Cursor and others) working on
behalf of the people on this team. People should read it too. Several people's agents work in
this repository at the same time, so most of these rules exist to keep their work from
colliding. They hold whether you work with one assistant or run several agents at once; the extra
rules for the second case are in [Running several agents at once](#running-several-agents-at-once).

Read [CLAUDE.md](CLAUDE.md) first for the stack, commands and code conventions.

## The rules (read these even if you read nothing else)

1. **One plan item per branch, one branch per pull request.** The work is split into items in
   [docs/plan.md](docs/plan.md). Never mix two items in one PR. The one exception: docs-only changes that build
   nothing may share a PR ([When to push, open and merge](#when-to-push-open-and-merge)).
2. **Stay inside your item's files.** Each item lists the feature folders it owns. Don't edit
   files outside them except under "Shared files" below.
3. **Never push to `main`.** Every change reaches `main` through a PR with passing CI. A PR that
   touches another owner's folder, a shared file or a Decided product rule also needs an approval: from
   that folder's owner, any teammate for a shared file, or the decision's owner
   ([Review and merging](#review-and-merging)).
4. **Run `python3 scripts/check.py` before every commit.** Don't commit if it fails.
5. **Don't make product decisions.** If [docs/trove.md](docs/trove.md) or the plan item doesn't
   answer a question, stop and ask your human. Don't guess and build it. This is the most
   common way agent work goes wrong on this team.
6. **Never refactor, rename or reformat code you weren't asked to change**, especially another
   person's feature. Note it in your PR description instead.
7. **Small PRs.** Aim for under about 400 changed lines, not counting generated files. Split anything bigger,
   along the lines in [When to push, open and merge](#when-to-push-open-and-merge).
8. **Leave the repo runnable.** After your PR merges, `python3 scripts/dev.py` must still start and
   every page that worked before must still work.
9. **Ship finished work, not every commit.** Open a PR when a slice is done and checked, and fold
   its follow-ups into it before merging. Every new PR and merge notifies reviewers, and every merge
   is a release ([When to push, open and merge](#when-to-push-open-and-merge)).
10. **An agent merges only when its human says so**, for that PR or as a standing instruction. Merging
    releases to the live site.

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

## AI spending

Real Claude calls in development (evals, real-AI interviews on your own copy) are paid from the team's shared key.
**The development budget is $40** (Josef, 2026-11-23; it was $15).

- To have the app enforce it, set `AI_USAGE_LOG=<a file path>` and `AI_BUDGET_USD=40` in your `.env`. The app then
  refuses calls once that ledger reaches the budget. The ledger counts only your own machine's calls.
- See what you've spent with `python3 scripts/ai_spend.py`.
- Default to free: the scripted AI (`--scripted-ai`) for screens and flows, `FakeClaude` in tests.
- The live site is capped separately, by the key's spend limit in the Anthropic console (docs/deploy.md).

## Tests

- Every new route gets an API test: the success case, the main failure case (401, 404, 409 and so
  on), and any product rule it enforces (for example, "names stay hidden before a yes").
- Database tests use a real MongoDB. Take the `client` fixture, or `database` for direct access.
  Each test run gets a throwaway database, emptied between tests.
- **Run them on a local MongoDB.** Against the shared Atlas cluster the API suite takes 15 minutes to over an
  hour, and every teammate's run competes for the shared cluster's limits. Locally it takes about 2, as in CI. Run
  `docker run -d --name trove-test-mongo -p 27017:27017 --restart unless-stopped mongo:7.0` once, and put
  `TROVE_TEST_MONGODB_URI=mongodb://localhost:27017` in your `.env`.
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
- **Mark the item `done` in `docs/plan.md` in the PR's last commit**, not in a follow-up PR. Setting it to
  `review` while the PR is open is optional.

### When to push, open and merge

Every push to a PR, every new PR and every merge notifies the team, and every merge to `main` is a release
([The live site](#the-live-site)). So ship in finished batches:

- **Commit as often as you like; open the PR once.** Open it when the slice is finished and `check.py` passes.
  A draft PR is for handing work over or asking for early feedback, not for each step.
- **Fold follow-ups in before merging.** If a fix, a review change or more of the same item is already on its
  way, add it to the open PR rather than merging and opening another.
- **Records ride along.** A design decision, a `docs/trove.md` update or a plan status goes in the PR that
  builds it, never in a PR of its own. Docs-only work that builds nothing is batched into one PR per person
  per working day.
- **Split only for review or risk.** Stay under about 400 changed lines (rule 7). Split, or stack PRs, when parts
  need separate review or carry separate risk. Not just because they were written at different times.
- **Merge related PRs one after another,** then check the live site once.
- **Exceptions:** a fix for something broken on the live site, or a change a teammate is blocked on, ships at
  once on its own.

### Review and merging

| What the PR touches | Who must approve | Then |
|---|---|---|
| Your own work: your features' folders, their tests, the regenerated client files, your item's status in `docs/plan.md`, and new decisions for your feature in `docs/trove.md` or `docs/design/decisions.md` | nobody (a review is welcome) | merge on green CI |
| Another owner's folder (`.github/CODEOWNERS` requests them) | that folder's owner | merge after their approval |
| A shared file ([Shared files](#shared-files)) | any teammate | merge after their approval |
| A **Decided** item in `docs/trove.md`, or a Fixed rule in `docs/design/system.md` | the decision's owner: the owner of that feature in `docs/plan.md`. If it spans features or names no feature, it waits for the team sync | merge after their approval |

An approval is a GitHub "Approve" review, or the approver's words quoted in the PR with the date.

- **Always "Squash and merge"**, never "Create a merge commit" or rebase-merge. `main` stays one commit per PR,
  and reverting a PR is one revert.
- **Saying "the owner should review this" in the description is not a review.** If the PR needs one, wait for
  it, or ask your human to get it.
- **GitHub enforces what it can:** squash-only merging, required CI checks and no force-pushes to `main` are
  repository settings. If GitHub refuses a merge, fix the cause. Don't look for a way around it.

### Keeping a branch up to date

- Rebase on `main` (`git fetch origin && git rebase origin/main`), rerun `check.py`, and push your own branch
  with `git push --force-with-lease`. Never force-push `main` or a branch someone else is working on.
- Conflicts in `api/openapi.json` or `web/src/api/schema.ts`: rerun the generator ([The API contract](#the-api-contract)).
- If a squash-merged PR's branch was the base of yours, rebase only your own commits onto `main`:
  `git rebase --onto origin/main <last commit of the merged branch>`.

## The live site

The app runs live on Render ([docs/deploy.md](docs/deploy.md)). Render rebuilds from `main`, so
**merging a PR is releasing it**: it reaches real members in about 10 minutes. (While Render still builds
`daniel/g1-go-live` instead, a merge goes live only once that branch is moved up to `main`. deploy.md, "Which
branch does Render watch?", says how to check and who moves it.)

- **Merge only on green CI that has actually run.** Wait until every check shows passed: not while one is
  pending, and "no checks reported" is not a pass.
- **The live database keeps its data.** There are no migrations. If you change the shape of a stored
  document, the code must still read the old shape, and the PR says how.
- **Never point anything local at the live database** (`trove_prod`). Your `.env` uses
  `trove_dev_<yourname>`; `scripts/dev.py` refuses to start on `trove_prod`.
- **Don't test by writing on the live site.** Sign-ups there send real email and use the real AI. Reproduce
  bugs locally. Make test accounts on the live site only when your human asks.
- **A new setting** (a new value in `.env.example`) also goes into `render.yaml`, and the PR asks the Render
  owner to set it before merging. Otherwise the live site starts without it.
- **After a merge,** open `https://trove-q9uy.onrender.com/api/health` (it must say `"database":true`) and
  the page you changed. If it's broken, say so in the team chat; the Render owner can roll back.
- **Only the Render owner (Daniel)** can read its logs, change settings or keys, redeploy or roll back.

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
5. **Changing something already Decided** (rewriting a "decided" section, reversing a recorded choice) is a
   product decision too, even when your feature needs it. It needs the decision owner's yes before the PR
   merges ([Review and merging](#review-and-merging)).

## From design to code

Screens are designed first (the design canvas, `docs/design/`), then built.

1. **Build only approved designs.** An approval is your human or the design owner saying so, recorded in
   `docs/design/decisions.md` with the date and their words. A board that is merely on the canvas is not
   approved.
2. **Name the source in the PR:** the board, and the decision entry it builds.
3. **When the design changes mid-build,** the newest recorded decision wins. Say in the PR which one you built.
4. **Anything the board leaves open** (an edge case, an error state, phone layout) is a free-tier choice made
   from the tokens ([docs/design/system.md](docs/design/system.md)). Note it in the PR; don't block on it.
5. **Design assets** (art, animation clips, boards) live under `docs/design/`, which is not shipped. The app
   copies what it uses into `web/src/`. Keep each file small: compress images to webp and clips to under 1 MB.

## Running several agents at once

Optional: most work here is one person with one assistant. If you run several agents in parallel, these keep
them from colliding with each other and with teammates.

- **One integrator.** One agent (or you) pushes, opens PRs and merges. The others commit on their own branches
  and report their commit hashes. The integrator pushes those branches at the end of each working day, so
  nothing lives only on one machine. That keeps the cadence in
  [When to push, open and merge](#when-to-push-open-and-merge) in one place.
- **One worktree and one set of files per agent.** Two agents never edit the same files at the same time. When
  two pieces of work must touch the same file, run them one after the other, or stack the second on the first.
- **Separate local copies.** Each running copy of the app gets its own database and ports, for example
  `MONGODB_DATABASE=trove_dev_<name>_qa python3 scripts/dev.py --api-port 8100 --web-port 5273 --scripted-ai`.
- **Tests on the local MongoDB** ([Tests](#tests)). Several suites against the shared dev Atlas cluster slow each
  other down, and slow the live site with them.
- **A checker that didn't write the code.** Before a UI change merges, have a separate agent walk through it
  in the running app at desktop and phone width, judging both bugs and how it feels. The author's own check
  doesn't count.
- **Decisions go to your human, not between agents.** An agent may pass on a decision your human made, quoted.
  It may not make one or approve one.

## Handing work over

Agents don't remember earlier sessions, and teammates don't see your terminal. When you stop
partway through, the work must be resumable by anyone:

- Commit and push the branch, even if it isn't finished. A branch with no PR notifies nobody.
- Open a **draft** PR only when someone else will pick the work up, or you'll be away for a day or more, and
  only one per branch: later, mark that same PR ready. In its description, write what's done, what's left
  and any decision you're waiting on.
- Don't leave work only in your local working tree.

## Never

- Commit `.env`, API keys, connection strings or personal data.
- Use `git push --force` on `main` or on someone else's branch (on your own, use `--force-with-lease`).
- Merge or rebase onto a teammate's unmerged branch. Wait until it reaches `main`.
- Disable, skip or weaken a test or check to make it pass. Fix the cause, or ask your human.
- Add a dependency without saying why in the PR. Prefer what's already installed.
- Edit `web/src/api/schema.ts` or `api/openapi.json` by hand.
- Change a prompt without running its evals.
