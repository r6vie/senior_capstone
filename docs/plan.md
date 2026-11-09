# Trove: Work Plan

The work, who owns it, and what each piece must do. The product itself is described in
[trove.md](trove.md); this file is how we build it. Agents: read [CONTRIBUTING.md](../CONTRIBUTING.md)
before starting an item.

**Goal:** the whole loop works end to end, then we polish:

1. Sign up.
2. Find your book in the interview and pick one of three titles.
3. Browse and search the shelf.
4. Check out a book, and the author accepts.
5. Names and contacts are revealed, and you arrange the meeting.
6. "Did you meet?"
7. Past meets.

## How we work

- **Vertical ownership.** Each person owns whole features: backend, frontend, prompts and tests.
  Your agent works only inside your features' folders (CONTRIBUTING.md, "Shared files", lists
  the exceptions).
- **This file is the source of truth** for who is doing what. Update an item's status in the
  same PR that changes it.
- **Review:** any teammate approves, CI is green, and the author squash-merges.
- **Product questions:** the feature's owner decides and records the decision in `trove.md`.
  Questions that cross features go to the next sync.
- **Sync twice a week.** Walk this file top to bottom: what merged, what's blocked, and which
  open questions need a decision.
- **One shared Claude API key** in everyone's `.env`. Evals cost real money, so run them when a
  prompt changes, not on every save.

## Owners

| Person | GitHub | Owns | Folders |
|---|---|---|---|
| **Josef** | @BrozJosef | The book and the interview: the AI heart, prompts, evals, sample books | `api/trove/books`, `api/trove/interview`, `api/trove/ai/prompts`, `api/evals`, `web/src/features/{book,interview}` |
| **Alvisa** | @alvisakrasniqi | Discovery: shelves, search, "the Librarian recommends", recommending a book | `api/trove/discovery`, `web/src/features/discovery` |
| **Ellie** | @ecolvin22 | Checkouts and messaging: checkouts, copies, reveal, threads, "Did you meet?", past meets | `api/trove/checkouts`, `api/trove/messaging`, `web/src/features/{checkouts,messaging}` |
| **Daniel** | @r6vie | Accounts, meetings and the app shell: account and contact details, settings, CWRU verification, arranging the meeting, navigation | `api/trove/auth`, `api/trove/meetings`, `web/src/features/{auth,account,meetings}`, `web/src/app`, `web/src/ui` |

Review requests go to the folder's owner automatically (`.github/CODEOWNERS`). `api/trove/notifications` is shared: each owner adds the templates and `notify_*` functions for
their own feature's emails.

## Contracts between features

These are the functions features call on each other. **Each owner builds theirs first**, even
as a minimal version, so the others can build against them. Until a function exists, call a
local stub with the same signature and swap it out when the real one merges.

| Function (in `<feature>/service.py`) | Owner | Returns | Used by |
|---|---|---|---|
| `books.get_public_book(db, book_id)` | Josef | The book as readers see it: title, author's full name, cover, chapters, copies. **Never** the author's contacts, employer or title. `None` if not on the shelf | discovery, checkouts |
| `books.get_book_of(db, user_id)` | Josef | That member's own book, or `None` | checkouts (you need a book to check one out) |
| `books.list_shelf(db, *, limit, after)` | Josef | Public books on the shelf, newest first | discovery |
| `interview.nothing_open(db, user_id)` | Josef | Whether no questions or changes are open on this member's book, so it can be undone | books |
| `interview.ask_after_reading(db, author_id, checkout_id)` | Josef | Nothing. Queues the author's one question after a reading. Safe to call twice. Call it once "Did you meet?" confirms the meeting happened | checkouts (C4) |
| `auth.first_name_of(db, user_id)` | Daniel | First name (for greetings; books show the full name, trove.md §9.1) | everyone |
| `auth.contact_details_of(db, user_id)` | Daniel | The contact details the member chose to share on a yes | checkouts (reveal) |
| `checkouts.get_checkout_for(db, checkout_id, user_id)` | Ellie | The checkout if this user is its reader or author, else `None` | messaging, meetings |
| `checkouts.fully_checked_out(db, books)` | Ellie | The ids of the books (each with `_id` and `copies`) whose copies are all out, so the shelf can hide them. Never shown to readers as a label or count | books, discovery (the shelf) |
| `checkouts.past_meets(db, user_id)` | Ellie | People this member has met: checkout id, other person's full name, book id | discovery (recommend to someone you've met) |

When you change one of these, tell the people in the "Used by" column.

## Items

Status: `todo`, `doing`, `review` (PR open) or `done`. IDs are used in branch names (`josef/b1-book-model`).

**Before writing code,** the agent lists every assumption it would otherwise have to make, and
the owner answers them. Each item's "Decide first" lists the known ones.

### Wave 1: the foundations others build on

**B1 · The book model and sample books** · Josef · `review`
- `books` collection: one book per member, with title, chapters (title + short text + the quotes
  it's grounded in), cover style, copies (default 3), and on-shelf status.
- Ships the `books.*` contract functions above, plus `GET /books/me` and `GET /books/{id}`.
- `scripts/seed.py` adds about 20 sample books (clearly marked as samples) to your own dev
  database, so everyone else can build before real books exist.
- Done when: other features can list and open books from the seed, and the reader view never
  includes last names.
- Decide first: the exact chapter fields; what a "cover" is for now (a style id is enough).

**A1 · Account basics and contact details** · Daniel · `todo`
- Ships `auth.first_name_of` and `auth.contact_details_of`.
- Already done (Josef, 2026-11-07, for full names on books): signup asks for a required last name;
  the account has `last_name` and `full_name` (`auth.full_name`, `auth.full_names_of`); and
  `PATCH /auth/me` sets or changes the first and last name.
- Members choose which contact details are revealed on a yes: email by default, plus optional
  LinkedIn URL and phone.
- Settings page: contact details, email notifications on/off, delete account (which also removes
  the book; coordinate with Josef).
- Done when: contact details are saved, are never visible before a yes, and deleting an account
  removes everything that belongs to it.

**U1 · App shell and navigation** · Daniel · `todo`
- A minimal layout with navigation to Shelf, My book, Checkouts, Past meets and Settings, with
  empty pages that the owners fill in.
- Style it with the design system (`docs/design/system.md`, `docs/design/system/tokens.css`). Use the top bar
  from the Reference screen · The shelf.
- Done when: every owner has a route and an empty page in their own feature folder to work in.

**C1 · Checking out a book** · Ellie · `doing`
- One step (trove.md §6, §9.6): a reader presses "Check out" and writes a short message. They must
  have a book of their own (`books.get_book_of`). The author accepts or declines.
- An unanswered checkout closes quietly after a set time. A declined or expired checkout shows
  "this book isn't available right now".
- Copies are private: when every copy is out, the book leaves the shelf until one is returned.
  No queue. Readers never see copy or checkout counts.
- Ships `checkouts.get_checkout_for`.
- Builds against the seeded books from B1.
- Decide first: open-checkout limit per reader; the exact expiry period; whether a reader can
  check out the same book again after an expiry.

### Wave 2: the core experience

**I1 · The book-finding interview** · Josef · `review`
- Hunts for what the member knows that others don't (trove.md §4), following strong threads
  and exploring several directions.
- Optional résumé upload: used only to shape questions. Nothing from it goes in the book. The
  file is not kept.
- Decide first: the interview format (cards, conversation or both), its length, and how it ends.

**I2 · Three titles, then the book** · Josef · `review`
- The interview produces a pool of grounded chapters plus three titles and covers. The member
  picks one, and the inside is finished to match (trove.md §9.4).
- Evals: 6–10 varied test personas in `api/evals/`, so prompt changes can be compared.
- Done when: a real person goes from signing up to a book on the shelf.

**I4 · The interview adapts** · Josef · `review`
- When answers run thin (trove.md §4, §9.9), the interviewer changes angle: sharper questions
  anchored in the member's real projects, classes and work, in a professional tone. A quiet
  "Skip" is always available and moves to the next question. No mirror, cards or reassurance copy.
- Screens first, approved by Josef, then the engine, API and UI.
- Evals: the quiet personas (e.g. Dana) should reach a full book without hitting the cap.

**D1 · The shelf and opening a book** · Alvisa · `todo`
- The home page shows shelves of books (start with "Recently added" until the categories are
  decided), and a book page opens one.
- Uses only `books.get_public_book` and `books.list_shelf`.
- Has a "Check out" button that leads into C1.

**D2 · Smart search** · Alvisa · `todo`
- Search by topic, never by name.
- Decide first: how to search.
  - **Recommended:** at publish time, Claude writes hidden search terms for each book, and a
    MongoDB text index covers title, chapters and those terms. No new provider needed.
  - Alternative: vector search, which needs an embeddings provider.

**C2 · Accepting and the reveal** · Ellie · `todo`
- When the author accepts, both people see each other's full name and the contact details they
  chose (`auth.contact_details_of`), at the same moment, and both get an email.
- Done when: names and contacts are visible only to those two people, and only after accept.

**C3 · Messages inside a checkout** · Ellie · `todo`
- A plain thread per checkout. No messages outside a checkout (trove.md §9.8).
- Email notification for new messages, at most one every 10 minutes per thread.

**M1 · Arranging the meeting** · Daniel · `todo`
- Each person shares a few times that work, and the app suggests overlaps.
- A field for the video link, a calendar invite (.ics) for both people, and a reminder email on
  the day. In person is optional when both are nearby.
- Uses `checkouts.get_checkout_for`.

### Wave 3: closing the loop

**C4 · "Did you meet?" and past meets** · Ellie · `todo`
- After the meeting time, both people are asked "Did you meet?". The answer returns the copy, and
  the book comes back on the shelf if it was fully lent.
- The answer is also stored as a private no-show signal.
- A "Past meets" page lists books whose authors you've met, with contacts still visible.
- Ships `checkouts.past_meets`.

**I3 · Adding to your book** · Josef · `review`
- Reopen the interview from your book at any time. New material is rewritten into the book
  (not just appended), and the author approves the changes.

**D3 · The Librarian recommends** · Alvisa · `todo`
- One recommended book at a time, each with a one-line reason for why you two should talk.
- Quietly favors books that are checked out less (trove.md §9.6).

**D4 · Recommend a book to someone** · Alvisa · `todo`
- Recommend a book to someone in your Past meets, inside the app (uses `checkouts.past_meets`),
  or to anyone else with a share link.

**A2 · CWRU verification and sign-in** · Daniel · `todo`
- Decide first:
  - how students and alumni are verified (trove.md §9.2)
  - whether to keep password sign-in or switch to one-time email codes

### Wave 4: demo readiness

**Q1 · End-to-end pass** · everyone
- Run the whole loop with two real accounts.
- Fix what breaks, in the owner's feature.
- Write a short demo script in `docs/demo.md`.

### Later: after the whole loop works

Josef asked for these early. Both are built on `josef/full-build` against stubs, and neither runs for real until its teammate's piece lands: I5 needs `SparkButton` mounted on D1's book page, and I6 needs C4 to call `interview.service.ask_after_reading`.

**I5 · Sparks from other books** · Josef · `review`
- On a chapter of someone else's book, "I have one like this" saves a private prompt for the
  reader's own next interview (I3). Never content, never visible to the other author.

**I6 · Each reading grows the book** · Josef · `review`
- After "Did you meet?" (C4), the author answers one question: "What did they ask you about that
  surprised you?". The answer can become or improve a chapter, with the author's approval (I3).

## Open questions waiting on the team

Cross-feature questions to settle at the next sync:

- Shelf categories (trove.md §5).
- Whether books show a seniority or stage marker (trove.md §3).
- The Librarian's tone. (The visual design is decided: `docs/design/system.md`.)
