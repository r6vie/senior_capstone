# Review guide: the book and interview build

What was built on `josef/full-build` while Josef was away, what's still unproven, and what needs a person.
Every call we made for him is in [decisions.md](decisions.md).

## How to see it

```bash
python3 scripts/dev.py --scripted-ai
```

That runs the app with a free stand-in for the AI, so walking it costs nothing. Drop `--scripted-ai` to use real Claude, which costs money. Nothing links to the interview or My book yet, so type the addresses: `/interview` and `/my-book`.

- Give a member the question after a reading: `scripts/ask_after_reading.py`
- See real API spending: `python3 scripts/ai_spend.py`

## What's new

- **The interview, finished:** adapts when answers run thin, a quiet Skip, and it no longer loses a member's words on a refresh, a lost connection, a stale screen or a retry.
- **The book review:** rewrite the back cover, go back to the other two titles, undo a chapter rewrite, see the member's own words behind each chapter.
- **My book (`/my-book`):** one page for every stage, from no book yet to on the shelf.
- **Adding to your book (I3):** a short new round of questions, then proposed changes approved one by one. The shelved book doesn't change until the member confirms, nothing goes live unseen, and an approved change can be undone.
- **Sparks (I5) and the question after a reading (I6):** built against stubs.
- **Book writing:** rewritten prompts in the chosen voice, plus tools to measure them: saved transcripts, lints and an editor's rubric (`api/evals/`).

## How good is the writing?

Scores out of 35, one fresh editor per book. All of these interviews used a simulated member.

| Book | Before | After |
|---|---|---|
| Dana (quiet) | 14 | 20 |
| Theo (quiet) | 17 | 20 |
| Mateo | not scored | 25 |
| Ana (never used for tuning) | not scored | 24 |

Part of the rise isn't the prompts: the simulated member changed, and Dana's first score was marked down for a contaminated transcript. Theo's replay of one saved transcript, 17 to 20, is the clean comparison.

Claims traced to what the member said went from 93.4% to 96.8%, with none unsupported. That audit wasn't repeated after the final prompt changes.

- **Books from members with material** are ones a reader would book, in the quality session's judgment.
- **Quiet members' books are honest but thin.** Editors never scored them above 2 of 5 on "would a reader book 30 minutes".
- **Across a shelf, books still sound alike:** one rueful narrator, with a belief corrected and a trailing shrug. A lint catches only part of this.
- **The last prompt changes showed no proven gain.** A blind reader preferred the earlier version for Dana and Theo, and the new one for Ana.

## Not proven

- **No real person has taken the interview.** This is the biggest open question.
- **No real microphone, phone keyboard or screen reader.**
- **Quality's last walk was before the final fixes.** It stopped at round 6 as Josef asked, so round 6's fixes have automated tests and the UI session's own walk, not an independent one. Some have tests only: the lost reply on Shape, the stranded draft, the prefilled "Say it again", a refused reading send, a stale send while adding.
- **Real wait times aren't measured,** so the screens don't say how long titles and the book usually take.
- **Adding and proposed changes ran on the real model once per case on the final prompts,** and no editor judged the output. Skip got little real testing.
- **The 30-day résumé expiry** is tested for its index, not an actual deletion. Older unfinished interviews can keep résumé text on the interview itself until their draft is written.

## Decisions for Josef

1. **Should readers see one line of the author's own words per chapter?** The plan says no. Quality recommends yes, as the cheapest way to raise a quiet member's book. Not built.
2. **Should members be able to edit their book's text directly?** The plan says later. Quality calls its absence the top risk to a member's pride in their book, which appears under their real name. Not built.
3. **What happens when a member takes a whole book off the shelf?** Today they can only remove chapters, down to three. It affects open checkouts, so it needs Ellie. Not built.
4. **Test with real people?** Quality suggests Josef and three teammates take the real interview, for about $2.40.
5. **Remove the old persona from git history?** Until this build, the repo held a test persona based on a real CWRU alum, with invented details. It's gone from the current files but still in the public history. Removing it means rewriting history, which affects everyone's clones.
6. **Author names on the book can take 4 lines instead of 3.** This touches a Fixed design rule (decisions.md).

## Needs teammates

- **Daniel:** navigation, so members can reach `/interview` and `/my-book`. **Until this lands, a real member can't get to any of this without typing an address.** Also a way back to the shelf from My book, sign-out (call `clearAllDrafts`), the per-tab session, the sign-in page shown when the API is down, and account deletion that also removes sparks and reading questions. `auth/service.py` gained a small dev helper, `user_id_by_email`.
- **Alvisa:** the shelf still shows sample books, so a member's own book doesn't appear on it. D1 mounts `SparkButton` on each chapter of someone else's book. `.book-author` now clamps at 4 lines, so check the shelf.
- **Ellie:** C4 calls `interview.service.ask_after_reading` once "Did you meet?" confirms the meeting. Use the module form, `from trove.interview import service`, to avoid an import cycle.

Also changed in shared files: routes in `App.tsx`, the 503 text in `core/errors.py`, and the book name clamp in `styles.css`. CLAUDE.md's Commands table gained two rows.

## Smaller limits we kept

- **Name filter on reading answers** over-catches places and products, and can't catch lowercase names; the prompt covers those. The member is told when a name stood in the way.
- **Résumé-term check** is a heuristic and can miss a name or drop an item over a capitalized word.
- **Undo after adding a chapter** says "I won't suggest them again" even where that doesn't quite fit. The conditional wording needs a signal the API doesn't have.
- **Sample personas stay simulated, and are too obliging,** so voice scores only go so far.
