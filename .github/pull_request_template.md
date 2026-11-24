## What changed

<!-- One or two sentences in product terms: what can a member do now, or what's fixed. -->

## Plan item and source

<!-- The docs/plan.md item this PR delivers, e.g. "B2: Request a book".
     For UI: the design board and the docs/design/decisions.md entry it builds. -->

## Who needs to approve

<!-- "Nobody: own work only", or who: the owner of another folder, any teammate for a shared file, or the
     feature owner for a Decided rule. If someone must approve, wait for them (CONTRIBUTING.md, "Review and merging"). -->

## How it was checked

- [ ] `python3 scripts/check.py` passes
- [ ] Tried it in the running app (describe what you did; desktop and phone for UI)
- [ ] If an API route or model changed: ran `python3 scripts/generate_api_client.py` and committed the result
- [ ] If a prompt changed: ran its evals and summarized the difference below
- [ ] If a product decision was made or changed: updated docs/trove.md
- [ ] If stored documents changed shape: old documents still read correctly (say how)
- [ ] If a new setting was added to `.env.example`: also in `render.yaml`, and the Render owner has set it
- [ ] If a Decided item or a Fixed design rule changed: the owner's approval is here (review or quote)
- [ ] After merging: `/api/health` shows `"database":true` and the changed page works on the live site

## Screenshots

<!-- For anything visible. -->
