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
