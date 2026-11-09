# Decisions for Josef to review

Calls made during the unattended build while Josef was away. Each is built to be easy to change. Newest last.

| # | Question | What we chose | Alternatives | How to change it |
|---|---|---|---|---|
| 1 | Can a book grow past the first version's 5 chapters? | Up to 8, since a book grows after the first interview (trove.md §3) | Stay at 5, with new chapters replacing old ones; no limit | One constant in the interview engine |
| 2 | Does revising a book bump it on the shelf? | No. `published_at` stays put, since the shelf isn't a feed | Show recently revised books first | The shelf sort in `books/service.py` |
| 3 | What of a sparked chapter reaches the interviewer? | Its title only, framed as a cue. Never its summary, author or book title | Title and summary, for better questions, at more risk of the other author's material leaking in | The `interview/adding` prompt and the sparks query |
| 4 | Can sparks feed a member's first interview? | Yes, if they've saved any before starting | Only reopened interviews | Where the interview loads sparks |
| 5 | When is a reader's "I have one like this" available? | On every chapter of someone else's book, with up to 12 unused saved | One per book; no limit | The limit in the sparks service |
| 6 | Is Skip offered on the Shape step ("Is this you?")? | No. That step has confirm or correct, and skipping it would leave the book unconfirmed | Offer it there too | The skip route's phase check |
| 7 | Where does My book live? | `/my-book`, matching Daniel's shell branch | `/book`, as first specified | One route in `App.tsx` |
| 8 | What happens to the blurb when a member approves only some changes? | A new blurb is written for that selection and shown for approval. Nothing goes live unseen | Rewrite it silently; keep the old blurb always | The revision route and the proposed changes screen |
| 9 | Can a member remove a chapter after the book is on the shelf? | Yes, down to three chapters, through the same confirm step. Taking the whole book down is left for the team, since it affects open checkouts | No removal; add taking a book down now | `/my-book` and the books service |
| 10 | What do members see for the interview's phases? | Plain words, such as First look, Deeper and Check, plus a note when it's mostly done, which isn't a count | Keep Sweep, Dig and Shape; show no phases | Phase labels in `InterviewPage.tsx` |
| 11 | What can a member change while reviewing a draft? | Rewrite or remove a chapter, rewrite the back cover, or go back to the other two titles. Free-text editing stays out, per trove.md, but **quality flags it as the top risk to a member's pride in their book, so it's for Josef to decide** | Build free-text editing now | The review screen and interview routes |
| 12 | How much should a chapter summary give away? | The problem, the turn and what was at stake. It names the method without its steps, because the steps are what the call is for | Tell the whole method, as before | The summary rule in the book prompts |
| 13 | How long does an abandoned interview keep résumé text? | 30 days after the last activity, as trove.md §4 recommends | Until the interview ends; 7 days | A constant in the interview service |
| 14 | What happens when an interview doesn't produce enough for a book? | Never a dead end. The Librarian keeps asking on new ground. At the turn limit it says so plainly and offers to keep answering or leave | End with a shorter book; end with a failure message | The interview's finish step |
| 15 | Does the reading question show who the reading was with? | Yes, to the author only, in the screen and never in a prompt or the book | Don't name them | The My book reading question |
| 16 | Can an approved change to a shelved book be taken back? | Yes. The last version is kept, and a quiet undo restores it until the next change is applied | No undo; keep a full history | `previous_version` in the books service |
| 17 | Must a proposed change quote the new answers? | Yes, at least one quote from the new round, or the change is dropped, so a change is always earned by what was just said | Any verbatim quote from the whole interview | `revise_book` in the interview engine |
| 18 | Does a spark come back if it's saved again after being used? | Yes, for the next round | Stays used | `add_spark` in `interview/service.py` |
| 19 | How does code spot a name in a reading answer? | Any capitalized word that isn't a common word or the member's own name counts as one. Its quotes are dropped, and a change or blurb using it isn't proposed. It over-catches (a place, a product), and the cost is a lost quote, never a leak | Trust the prompt rule alone; a proper name-recognition library | `NOT_NAMES` and `_other_people` in the interview engine |
