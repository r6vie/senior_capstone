# The Librarian in the interview: plan

Status: **scope approved by Josef, 2026-11-19.** The backend is on main (L1). The screen is being designed
with the Trove UI Design session and needs Josef's approval there before the frontend is built.

Source: `docs/LIBRARIAN_SPEC.md` (Overdue's Librarian), adapted for Trove. This plan says what we take, what
we change and what we leave out.

## What it is in Trove

While a member types an answer, the Librarian reads over their shoulder. The goal is a WOW moment: answering
should feel like being read by someone sharp, so that filling in the interview is a pleasure and the member
wants to keep going. It works in two places:

1. **Marks on the answer itself,** in the text field:
   - underlines
   - a strike with a better word
   - a loose circle
   - a short handwritten note above a phrase

   As in the spec, every mark is anchored to the member's exact words, and it is erased when those words
   change.
2. **A notebook on the right.** This is mostly commentary, never a copy of the answer. It shows the member's
   book forming and proves the Librarian is really reading. The entry kinds are in the next section.

The interview itself does not change: one question at a time, Sweep → Dig → Shape, 15–25 questions, Opus
writing the questions, and grounding as before. The Librarian is a layer on top.

## The notebook

| `kind` | What it is | Example | Grounding check, in code |
|---|---|---|---|
| `chapter` | a chapter taking shape; struck and retitled as the answer improves | "ch. ? the night the build broke" | names words from the answers |
| `connection` | links this answer to an earlier one | "same instinct as the robotics story." | names words from both answers |
| `saving` | a question it wants to ask later | "ask: what did the PI say?" | names words from the answers |
| `clip` | a short quote, at most 8 words, used sparingly | "nobody reads the README" | verbatim from the answers |
| `note` | a short observation | | none |

`clip` is limited to one per answer, and never more than about one in five entries.

**Behaviour:**

- **Revising:** the Librarian revises entries as the answer improves. A revised entry strikes its old wording
  and writes the new one.
- **Erasing:** when the words an entry was built on are deleted, the entry is rubbed out.
- **The notebook drives the next question.** The question writer sees the open `saving` and `chapter`
  entries and may build the next question on one of them. It returns that entry's id, which is checked in
  code. When the question appears:
  - the source entry gets circled
  - a `saving` entry built on gets ticked off
- **Clips feed the book.** `clip` entries are offered to the book writer as preferred chapter quotes. They
  are the member's own words, so grounding holds. Marks, notes and the rest of the notebook never go into
  the book.

**Lifetime:**

- The notebook is kept for the whole interview. Going back to an answer or resuming shows exactly what was
  there.
- It is hidden after the reveal, but never deleted.
- When the author reopens the interview to add to their book (I3), the notebook comes back. On that open it
  is trimmed to make room for new notes. In order:
  1. drop ticked `saving` entries
  2. drop `note`s
  3. keep `chapter`, `connection` and `clip` entries, newest first, up to a cap

## What makes it fun (Josef, 2026-11-19)

The notes have to matter, not be random commentary that nobody cares about. They matter when they **come
back**. These are approved:

**Payoff loops:**

- **It credits your edits.** When the member sharpens a phrase it teased, it strikes its own note and writes
  "better." or "there it is." This makes editing feel like a conversation.
- **It makes bets, then calls them.** A new notebook kind, `bet`: "betting this ends in a spreadsheet."
  - When a later answer proves it, it ticks the bet: "called it."
  - When a later answer contradicts it, it strikes the bet: "wrong. good."
  - At most 2 open bets at once.
- **One back-cover line per interview.** The member's best sentence gets the big double underline, and the
  notebook gets "this goes on the back cover." This replaces the spec's "big" mark.
- **A running bit.** A concrete thing the member keeps mentioning gets circled with a count, and that pays off
  ("×3. the whiteboard has tenure."). Once per interview.

**Personality:**

- **Witty working chapter titles** ("ch. ? the build that broke everyone"), which it keeps improving.
- **Reader's-eye asides:** "I'd check this one out." / "a junior would pay for this." No counts or scores.
- **It concedes gracefully.** Now and then, when the member deletes marked text or ignores a push, it writes
  "fine. your call." instead of quietly erasing. At most once per interview.

**Frequency: rare and sharp.**

- Usually 1–2 marks and 1–2 notebook entries per answer, and only after a sentence ends.
- A rare generic line is acceptable, so nothing blocks generic lines in code.

**Not chosen:** the sign-off stays a plain dry line, with no callback to the interview.

**Tuning:** the "would you screenshot this?" bar is applied during testing, never at runtime, because the app
runs only Haiku. An Opus judge scores the eval cases, and a session revises the Librarian prompt until it
reads well. Each eval run's cost is stated up front, and the overall API budget is $15.

## The voice: professional, still sassy

Overdue's Librarian roasts 18–22-year-olds. Trove's is **a sharp senior editor**: dry, exact, quick to notice
and on the member's side. It is wry more than mean, and it teases the writing, never the person. It should
still be worth a screenshot.

- **What it goes after:** vagueness, jargon, résumé-speak, hedging and a buried lead. For example:
  - "says who?"
  - "a number would help."
  - "this is the chapter."
  - "résumé voice."
  - "buried the lead."
- **Admiration** is rare and dry: "good. keep that."
- **No Gen Z register:** no slang and no swear jokes.
- **Kept from the spec:**
  - the banned list
  - the silence rules (spec §4, in substance)
  - it never touches the book, apart from clips, as above
- **Format:** lowercase handwriting, no exclamation marks, no emoji, no "we".
  - Notes on the answer: at most about 32 characters.
  - Notebook entries: at most about 60 characters.

## Scope

**In:**

- marks on the answer
- the notebook (the kinds above), with the link to the next question
- silence
- the résumé-speak and paste flag (instant, no AI: highlighted, with "in your own words?")
- the contact-details line ("contact details come after a yes.")
- keyboard mashing ("a classic.")
- **idle lines:**
  - after about 24 s of quiet on an empty answer
  - at most 3 per interview
  - written in the professional voice
  - never on the first question or a silent answer
  - no doodles
- the handwritten **sign-off** under the title at the reveal

**Out:**

- swear strikes
- the self-correcting question
- the short-answer hold (adaptive questions already handle thin answers)
- doodles
- verdicts after Send
- counters
- the curveball sheet
- the hand-and-pen shadow
- an on-device model
- invite-a-friend

**Design rule change, approved:** the Librarian writes in red, the same red as the primary action. It is
recorded in `docs/design/system.md` by the design session.

## Backend (Trove AI)

Everything lives in the `interview` feature, in the `interviews` collection it already owns. There is no new
collection.

**`POST /interview/notes`:** called while the member types.

- **Request:**
  - `question_id`
  - the current answer text
  - the text at the previous call
  - a pasted flag
  - the ids of the marks and entries currently shown
  - The server already holds the earlier turns, so the client doesn't send them.
- **Response:**
  - `silent`
  - `marks`: which to keep, which to add (`{id, move, anchor, occurrence, note}`)
  - `notebook`: which entries to keep, add, revise or erase (`{id, kind, text, anchors, source_turns}`)
- **Ids:** stable hashes, so they survive repeated calls.
- **No-model shortcut:** if the text grew by fewer than 2 words without finishing a sentence, keep
  everything and add nothing.
- **Client-side placement:** the client places a mark only if its anchor still matches the text.

**Saving the notebook:**

- On Send (and on Skip) the final marks are saved with the turn, and the notebook is saved on the interview.
- The interview response returns both, so going back, resuming and the adding round show exactly what was
  there.

**The question writer:**

- It gets the open `saving` and `chapter` entries, and returns an optional `builds_on` entry id, which is
  checked in code.
- That entry is ticked or circled when the question is asked.
- The `book_turns` and draft prompts get `clip` entries as preferred quotes.

**The sign-off:** one line, written with the finished book, at most 24 characters, checked like a note.

**Models:**

- **The Librarian runs on Claude Haiku 5.5** (Josef, 2026-11-19): notes and the sign-off, with thinking on,
  structured output and low effort.
- Opus as now for the questions and the book (`docs/trove.md` §4). `builds_on` rides on the question call.

**Cost controls:**

- prompt caching on the system prompt and on a per-question prefix
- a rate limit of 200 notes calls per member per hour
- a cap of about 8 notes calls per answer
- Scripted AI gets a stand-in, so dev and tests stay free.

**Checks in code on every line**, using the spec's validate-and-retry loop (one retry, then drop the bad
item):

- length
- banned characters and words
- no meta talk ("question", "interview", "so far")
- no sensitive term unless the member used it
- nothing on heritage or language
- the content filter
- the grounding checks in the table above
- the caps:
  - at most 3 marks per answer
  - 1 "big" mark per interview
  - 1 callback circle per interview
  - a limited number of notebook additions per call

**Silence**, in layers, as in the spec:

- a client pattern list
- the same list on the server
- the model can also declare an answer silent
- a silent answer is never sent to the model and is masked in later prompts

On silence, that answer's marks and entries built on it are erased.

**Evals:** `evals/librarian`, about 30 fixed answer cases with an Opus judge.

- **Must pass:**
  - every silent case stays silent
  - no line fails the professional-tone test
  - every notebook entry passes grounding
- **Targets:**
  - sharp or funny at 3/5 or better
  - at least one notebook entry on most non-silent answers
- **Cost:** it costs money, so the cost is stated and approved before the run.

## Frontend (after Josef approves the screen with the UI session)

Josef approved the screen on 2026-11-19 (canvas page "Librarian notebook", v127; branch
`josefbroz/design-elevate`).

His direct notes:

- **The hand is a messy, human notebook.** Entries are slightly off-level, underlines are uneven, and words
  are struck and rewritten above. The unevenness is seeded per entry, so it is stable, never a uniform
  script.
- **The ink is the red marker.**
- **The notebook has no bullets.** Text starts right after the spine.
- **Clips are written in the marker hand,** in quotation marks.
- **Removed:**
  - the notebook footer line
  - "Only you see this"
  - the send-key hint
  - the notebook header tag

Implementation starts as soon as Josef approves the screen. Trove UI Implementation builds the approved screen: the handwriting engine, the marks renderer anchored to
substrings, the notebook, rub-out erasing, the client triggers and gates (spec §14), the client silence list,
the scripted moves and the idle lines.

## Bookkeeping

- `docs/plan.md`: a new row, L1, "The Librarian".
- `docs/trove.md` §4: replace the "on hold" line about margin reactions with these decisions.
