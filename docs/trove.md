# Trove: Product Plan

Status: living document, started November 5, 2026. We add to it as decisions are made. It replaces the earlier story-pivot plan (in git history at the `founderscircle-v1` tag).

Each section separates three things:

- **Decided:** the team has agreed.
- **Leaning:** a recommendation on the table, not yet confirmed.
- **Open:** still to be discussed.

The reasoning behind decisions is collected in §9. Ideas we considered and dropped are listed at the end, with the reason, so we don't relitigate them.

---

## 1. The idea

FoundersCircle is now **Trove**. It is a professional networking web app built on one idea:

> **You are the author of the book you haven't written yet.**

Everyone has a book in them: the one only they could write, about what they know, have figured out, or care about. Trove's AI finds that book, and other people find you through it. Checking out someone's book means a short conversation with its author.

*"The AI helps you find the trove in yourself, and then helps other people find it."*

The concept comes from Overdue, where every person *is* a book about themselves. In Trove you are the book's **author**, not its subject. The book points at what you could tell someone, not at who you are or your status.

## 2. Who it's for and why it's different

### Decided

- **Audience:** students and alumni meeting people who can open opportunities for them. Alumni → students is the main example, but anyone can meet anyone.
- **The main use is meeting new people.** It is not about matching people who have had the same experiences.
- **Trove is not trying to replace LinkedIn.** It is a different place with a different job.
- **The core difference is that Trove is non-performative.** LinkedIn rewards performing: posts, polish, personal brands. Trove is built to resist that ("think Substack"). It creates a level playing field, so a student and a VP sit on the same shelf.
- **Launch community:** CWRU. For now everyone is CWRU, so there are no branches and no affiliation badges.

### Leaning

- **Draft pillars:**
  1. **No audience, no performance.** No feed, no followers, no likes or view counts, no posts.
  2. **Find the trove in yourself, then let others find it.** The AI interviews, organizes and recommends. It never invents anything; every part of a book traces back to the author's own answers.
  3. **Meet first; opportunities follow.** Trove creates weak ties, and doors open between people who were curious about each other.
  4. **Real names, private contact.** Books show the author's full name. Contact details are shared only when the author says yes.
  5. **Generous, not extractive.** Authors control how many copies they lend out.
  6. **Face to face.** Video by default, in person when nearby.

### Open

- **Reasons people might not sign up, to design against early:**
  - Alumni: "I'll get flooded", "what's in it for me", "another profile to maintain", "anonymous requests feel sketchy", "students will no-show", "my employer could see this".
  - Students: "I have nothing interesting to say", "I already have LinkedIn/Handshake", "video calls with strangers are awkward", "networking is fake".
  - Everyone: "it'll be empty", "AI wrote it, so it's fake", "where does my data go".
- **How we verify that someone is part of CWRU.** For students, a case.edu email. Alumni have no clean check yet (see §9.2).
- **How members sign in.** The rebuild starts with the email and password sign-in carried over from FoundersCircle. Whether to switch to one-time email codes (as in Overdue) or add LinkedIn is still open.

## 3. The book

### Decided

- **One book per person, at a time.** It grows over time; there's never a second book alongside it.
- **The cover shows the title.** No genre on the cover.
- **No genres anywhere in the book.** A book's chapters can cover very different things, so no single genre fits a whole book.
- **Chapters:** the inside of the book is a set of chapters. Each one is something the author could talk about, and each is grounded in the author's own words.
- **Names:** books show the author's **full name** (§9.1). Employer, title, links and contact details stay off the book; contact details are revealed only when the author accepts a checkout.
  - There are no pen names.
  - The book stays the focus of the page, not the person's résumé.
- **Adding to the book:** the author can reopen the interview from their book at any time to add detail or chapters (as in Overdue's author interview).
- **What a book holds** (B1):
  - A title, the author's full name, a cover style, an optional blurb, and the chapters in reading order.
  - Each chapter has a title, a short summary and the quotes from the interview it's grounded in. Readers see the title and summary; only the author sees the quotes.
  - Copies default to 3 (1–10). Readers never see the number.
  - A book is a draft or on the shelf. Only books on the shelf are visible to readers, newest first.
  - Covers are plain white for now. Each book stores a cover style so covers can differ later.
  - Every book page and the shelf need sign-in.
- **Sample books** (B1): about 20 invented books, seeded only into a developer's own database. They're marked as samples in the database so the seed can remove them, but readers don't see a "sample" label for now.

### Open

- Whether a book shows a seniority or stage marker ("student", "10+ years in"), and where.
- Cover design.
- What else goes inside the book besides the title and chapters.

## 4. Making the book

### Decided

- **The interview hunts for what the person knows that others don't**, and for whatever will lead to the best connections. It follows the strongest thread and pushes for specifics. Like Overdue, it explores more than one direction at once.
- **The question style we like:**
  - "What do people come to you for?"
  - "What's something about your work outsiders always get wrong?"
  - "What did you figure out the hard way?"
  - "What would you argue about for an hour?"
- **Résumé and file upload** (§9.3):
  - Uploading is optional.
  - The résumé tells the AI where to dig, never what to say. It is used only to personalize the interview, never as book content.
  - The raw file is not stored once the interview questions have been drawn from it.
- **The reveal shows three books you could write.** It shows only their titles and covers, so nobody has to compare three long tables of contents. The author picks one.
- **How the inside is generated** (§9.4):
  - The interview first produces one shared pool of grounded chapters.
  - Each of the three titles draws on that pool from a different angle.
  - The inside is finished to match whichever title is picked. All three can be prepared in the background so the pick feels instant.

- **The interview, first version** (decided 2026-11-06; screens: interview direction A, "The question band", in `docs/design/shelf/project/InterviewA.dc.html`):
  - **Format:** a conversation, one question at a time. The member types or speaks each answer. The Librarian speaks only through its questions: calm, curious and plain.
  - **Asks for moments, not summaries.** Questions ask for a specific time or scene, then climb from what happened, to what you decided, to what you know now, to what you'd tell someone facing it. There are no "tell me about yourself", "what is the importance of", "how do you balance", yes/no or leading questions.
  - **Contrast questions** surface knowledge people take for granted: what people get wrong, what you learned the hard way, what people come to you for.
  - **Three phases:** Sweep (wide and light across school, work, turning points, side pursuits), Dig (the 2–3 strongest threads, in depth), Shape (the last 1–2 questions: when two threads from different parts of their life look like the same move, the Librarian asks the member about the link, then closes). Shape never plays back what the member said and never asks them to confirm it ("Is this you?"). Josef removed that step on 2026-11-23: the member knows what they told the Librarian, so asking them to confirm it adds nothing. Hedges, refusals and credit given to others anywhere in the interview still bind the book. Internally the interviewer keeps a light ranking of threads to decide where to dig. It is not shown.
  - **Reader lens, built into the question generator:** every next question is chosen with "what would a CWRU reader give 30 minutes for?" in mind. There is no separate critic pass.
  - **Length:** about 20–25 minutes, roughly 15–25 questions. The Librarian decides when it has enough. After about 10 answers, the member may also say "I've said enough. Show me my book."
  - **Saved after every answer, silently.** The member can leave and resume at any time ("Last time you were telling me about…").
  - **Voice:** the browser's built-in speech recognition (no new service). An editable transcript before sending. Where it isn't supported, the member types.
  - **Résumé:** optional PDF at the start. Its text is extracted, used only to shape questions, and deleted when the interview ends. The file is never stored.
  - **Grounding, kept light:** each chapter keeps the quotes it came from (B1). Nothing more elaborate for now.
  - **Chapters:** 3–5 per book.
  - **The reveal:** three titles appear one at a time, each with one line on why it's you. Covers stay white until a cover direction is chosen. The member picks one, and the book is finished to match.
  - **Blurb:** 2–4 sentences, first person, written with the draft, shown in review and on the book. Grounded like the chapters: only the member's own answers, never the résumé. Rewritten when a chapter is removed.
  - **Review before the shelf:** the member edits the title, the chapters and the back cover in their own words, can remove a chapter, then "Put it on the shelf". Josef, 2026-11-23: no "Rewrite chapter" or "Rewrite back cover"; the Librarian doesn't rewrite on request, the member edits.
  - **Model:** Opus 5.5 for questions and book writing.
  - **Limits** (T7): one interview per member; a member who already has a book can't start another (adding to your book is I3). A book keeps at least 3 chapters, so removing stops there. A résumé must be a readable PDF up to 5 MB; only the first 20 pages are read. If it can't be read, the member starts without it.
- **The interview adapts when answers run thin** (decided 2026-11-07, revised the same day; I4; §9.9):
  - **One pipeline, no fork.** Nobody is asked "do you already have a story?". When answers are short, vague or have no concrete moments, the interviewer asks better questions, not easier ones.
  - **Better questions means a sharper angle:** anchored in the member's real contexts (a class, a research project, a job, a team, a club, a high school project) and asking for the specific decision, problem or thing they figured out. Never small talk ("What did you do last Saturday?").
  - **The tone stays professional.** Members are treated as people with something worth telling. No reassurance copy ("anything counts", "that's okay"), no praise, no hand-holding.
  - **"Skip"** is always available, quiet. The member can skip a question they'd rather not answer or have nothing to say to, and the interviewer moves on to the next question. A skip is never shown or counted; the interviewer just takes it as a cue to try other ground.
  - The interview changes angle early instead of reaching the question cap with a thin pool.
  - Signals are internal: never shown, never a score. Grounding is unchanged.
- **Built early, waiting on teammates' pieces to run for real** (§9.9; choices in `docs/review/decisions.md`):
  - **Sparks from other books: dropped** (2026-11-19). The book screen no longer has "I have one like this", and sparks are not part of Trove.
  - **Each reading grows the book:** after "Did you meet?", the author answers one quick question, "What did they ask you about that surprised you?". The answer can become a new chapter or improve one, with the author's approval (through I3).
- **The Librarian reads over the member's shoulder** (decided 2026-11-19; L1; `docs/librarian-plan.md`).
  - While the member types, it marks the answer in red handwriting and keeps a notebook beside it. The notebook holds chapters taking shape, connections, questions it's saving, bets, and short clips of the member's own words.
  - The notebook drives the next question.
  - Its voice is a sharp senior editor: dry and wry, teasing the writing, never the person. It goes silent on sensitive topics.
  - Only clips, which are the member's own words, can reach the book.
  - The notebook is hidden after the reveal and comes back, trimmed, when the author adds to the book.
  - It runs on Haiku 5.5.
- **On hold until the interview works:** bursts on strong lines, the card drawer for the sweep, bookmark tabs, the pencil-to-ink spine, the shelf stamp and live cleanup of spoken answers. A practical "how-to" chapter is welcome but not enforced.

### Open

- The Librarian's more playful voice (on hold with the interactive layer).
- Free-text editing of the book by the author.
- Whether an abandoned interview's résumé text should expire (recommended: after 30 days).
- Later ideas, not planned: asking someone who knows you (answers shape questions only; needs a privacy decision), chapters in progress for members early on, a free-talk "ramble" mode, and a private timeline sketch.

## 5. Discovery

### Decided

- **D1 reader (Alvisa, 2026-11-18, updated 2026-11-19):** D1 began with a hardcoded Librarian
  recommendation. Restore the earlier Changing course and Starting over rows using the
  matching seeded sample books; these are preview groupings, not the final category decision.
  Recently added loads every published book from the existing books API. Selecting a book lifts
  it from its shelf position, enlarging it while the front cover opens to the left. Everything
  behind it, including navigation, is very dim. The settled spread has the title and full author
  name on the left and the table of contents on the right. Contents continue onto another page
  when they do not fit; selecting a chapter turns to its summary, with Back to contents available.
  Close or Escape returns to the shelf. The existing checkout form is reached from the reader.
  Reduced-motion users get the same reader without the movement.

- **Shelves will be grouped by categories.** The categories are still to be defined, and they will not be genres.
- **D2 smart search (Alvisa, 2026-11-22):** search the public text already in each available book:
  title, author's full name, blurb, chapter titles and chapter summaries. Do not make another
  Claude call, and never search grounding quotes, interview answers, contacts or checkout data.
  The existing top-bar field stays visible; focusing it opens a paper-colored translucent layer
  over the current page. After two characters, results update 200 ms after typing and show the
  book cover plus one matching public excerpt. Search and Enter run immediately. The underlying
  page remains faintly visible but cannot be used until Search is closed.
- **"The Librarian recommends":** the AI recommends books to you.
- **D3 recommendation (Alvisa, 2026-11-21):** this version stays signed-in. A member without a
  finished book sees the same large book graphic inviting them to create or finish theirs. Once
  their book has been published, only its author-approved public title, blurb and chapter text may
  shape a match. Claude extracts a small, evidence-backed profile of interests, domains, knowledge,
  experiences, explicit goals, current locations and places of origin from that text when the profile is missing or the book has
  changed. It does not choose the match. A deterministic scorer compares exact concepts, related
  concepts (for example, tennis and football through sports), and knowledge that complements an
  explicitly stated goal. The strongest grounded signal supplies the one-sentence reason. Member
  type does not filter or score matches: students, alumni, founders and non-founders may all match
  with one another. The pick stays for seven days unless either book changes or the recommended
  book leaves the shelf. A member's off-shelf book may privately shape their own recommendation,
  but an off-shelf book is never recommended to somebody else.
- **Member context for matching (Alvisa, 2026-11-23):** before the first book interview, a member
  records whether they are a current student, alumni, or both, and separately whether they are a
  founder. Existing members answer once, and the values can be changed later. They are ordinary
  member metadata but are not shown prominently or required on the book. They provide context for
  future matching work; the D3 scorer does not prefer or exclude a pairing because of them.
- **Recommend a book:** you can recommend a book in the app to anyone you've met (your Past meets), or to anyone else by sharing a link (§9.5).
- **No friends or follows.** Meeting someone is the only way to become connected.

### Open

- What the categories are and how the home screen is laid out.

## 6. Checkouts, copies and messaging

### Decided

- **You need a book of your own to check one out.**
- **Checking out is one step** (§9.6): the reader presses "Check out" and writes a short message. The author accepts or declines. On accept, contact details are revealed and the two arrange the reading.
- **A checkout is for the whole book.** It isn't tied to a chapter, because a reader may be interested in several.
- **A checkout ends.** It is one reading; afterwards the book is returned. Nothing stays behind as a permanent connection, only a Past meet.
- **No rule or check blocks asking for a job or a referral.** It isn't the ideal use of Trove, but we won't police it.
- **Copies are private and automatic:** each author sets how many checkouts they'll have open at once (default 3, 1–10).
  - When every copy is out, the book quietly leaves the shelf, and comes back when a copy is returned. There is no queue and no "fully booked" label.
  - Readers never see copy counts or how many checkouts a book has.
- **A checkout the author doesn't answer closes quietly** after 7 days. A declined or expired checkout shows the reader "this book isn't available right now".
- **Checkout limits** (decided 2026-11-07, C1):
  - A reader can have at most **3 open checkouts** at once. Open means waiting for an answer or accepted, and not yet returned.
  - Both kinds of open checkout use one of the author's copies. A copy is taken the moment someone checks the book out, so an author never has more open checkouts than copies.
  - After a checkout is declined or expires, the same reader can check out that book again after **30 days**. Declines and expiries are treated the same, so the reader can't tell which it was.
  - A reader can **cancel** a checkout the author hasn't answered yet, which frees the copy and the reader's slot right away.
  - The checkout message is required, up to 1,000 characters.
  - The author gets an email for each new checkout (unless they turned email off), with the reader's full name and message.
  - The reader's own book must be **on the shelf**; a draft doesn't count.
  - The author sees the reader's full name, their message and their book, to decide.
- **Messaging lives in the app.** The thread is where you check out a book, coordinate the meeting and share the video link. A member can choose to get communications by email instead.
- **"Did you meet?" matters:** answering it returns the copy, which frees it for the next reader.
- **Messaging is a small thread inside each checkout** (§9.8). Messages exist only inside a checkout, so there are no cold DMs.
- **How messages work** (decided 2026-11-18, C3):
  - The thread opens when the author accepts. While a checkout waits, the reader's note is the whole ask, so nobody can nudge an author who hasn't decided. The note is the thread's first message.
  - After the reading ("Did you meet?", C4), the thread stays in Past meets as read-only history.
  - A message is up to 2,000 characters. Each person can send at most 30 messages an hour in a thread.
  - The new-message email says who wrote and links to the thread; no message text is copied into it. At most one every 10 minutes per thread, for each person, and it respects the email switch.
  - The thread has its own page, `/checkouts/<id>/messages`, linked from each accepted checkout.
  - The app can post short notes into a thread (for example a confirmed meeting time) through the messaging feature. Notes look different from people's messages. Each feature decides whether to post them.
  - A private "New message" marker on your Checkouts page shows a thread you haven't read since the last message. The other person never learns whether you've read anything, and it is a label, never a count.

### Open

- _None for now._ (How soon a copy returns if nobody answers "Did you meet?" was decided in C4, §8.)

## 7. The reading

### Decided

- **A video call by default, or in person when both people are nearby.**
- **Contact details are revealed when the author accepts.** Both people see each other's on the Checkouts page, and both get an email that only links to Trove: contact details are never copied into emails (C2).
- **The meeting is arranged in the app, and kept light** (§9.7):
  - Each side shares a few times that work, and the app suggests overlaps.
  - A calendar invite with one click, a field for the video link, a reminder on the day, and "Did you meet?" afterwards.
  - No video built into Trove. People can move to their own channels whenever they want.
- **Both people get some preparation** (a short brief). It must be fully thought through, not a tacked-on AI feature. Details to be decided.

### Open

- The design of the meeting preparation.

## 8. After the reading

### Decided

- **Past meets:** a section listing the books whose authors you've met, with a bookmark on each.
- **Contact details stay available after a meeting**, so people can keep talking through their usual channels.
- **A private "Did you meet?" check** returns the copy. It is also a quiet signal for spotting no-shows.
- **How "Did you meet?" works** (decided 2026-11-18, C4):
  - It's asked once the confirmed meeting time has passed. If no time was confirmed, it's asked 14 days after the author said yes. It shows in the app (on the Checkouts page, and on Past meets for the person who hasn't answered yet); there is no email for now.
  - Each person answers "Yes, we met", "Not yet" or "No". "Not yet" keeps the checkout open to reschedule. The first Yes or No from either person returns the copy, and the book comes back on the shelf if it was fully lent. The other person can still answer afterwards.
  - It's a Past meet when someone said Yes and nobody said No. If the answers disagree, it isn't one. Answers are kept privately as a possible no-show signal; nobody is ever shown them.
  - If nobody answers, the copy returns 14 days after the question is asked, and it isn't a Past meet.
  - Both people get the Past meet: each sees the other's full name and book, their contact details, and a link to the conversation, which is now read-only history.

## 9. Reasoning behind decisions

### 9.1 Full names, contact on a yes (decided 2026-11-07, replacing first names only)

- **Full names build trust.** Talking it through with our advisor: alumni are wary of a checkout from someone they can't place, and a real name makes both the book and the checkout feel like they come from a person.
- **The cost is the lookup.** A full name makes a LinkedIn search one click away, and that's where status sneaks back in. So the book carries the name and nothing else of the résumé: no employer, title or links. A reader picks a book for what's in it.
- **Contact details still wait for a yes.** Nobody can reach an author outside Trove until the author accepts, which keeps "no cold messages" meaningful.
- **Pen names would mostly end up as real names anyway**, so there are none.

### 9.2 Membership and affiliation (revised 2026-11-23)

There are no public affiliation badges. Before a member begins their first book interview, they
record whether they are a current student, alumni, or both, and independently whether they are a
founder. Existing members can supply or change the same context in Settings. It is not shown on the
book and does not restrict or prioritize who may match with whom. The values are member-supplied;
email and invite history never infer them.

Membership verification (decided 2026-11-16, A2, Daniel):

- **Students:** a code sent to their case.edu email. The address must end in exactly `@case.edu`.
- **Alumni:** an invite link from a verified member. Alumni are reached through members we already have, so no outside check is needed for now.
  - Each link works once and expires after 14 days; a member can have 5 open at a time; we record who invited whom.
  - Still open for later: graduation-year review, an alumni-office partnership, and LinkedIn education data (needs partner access we don't have).
- **Sign-in stays email and password.** The emailed code only proves the address belongs to the person.
- Accounts that exist before this ships count as verified. Accounts that aren't verified can't sign in.

### 9.3 Résumé upload (decided)

- **A résumé is the most performative document a person owns.** If its lines end up in the book, the book becomes a résumé.
- **The AI reads it for patterns** (a sudden change of field, a gap, an odd side project) and turns them into specific opening questions. The very first question feels personal, and that is the hook.
- **Book content still comes only from interview answers**, and stays grounded in quotes from them.
- **Uploading is always optional.** Many students have thin résumés, and some people won't want to share one.

### 9.4 Three titles from one pool of chapters (decided)

- **Step 1.** From the interview, the AI writes a pool of candidate chapters, each grounded in a quote, plus three titles and covers. Each title takes a genuinely different angle, not a rewording of the others.
- **Step 2.** Once the author picks a title, the AI writes the blurb and picks and orders chapters from the pool to fit it. The book reads as one coherent thing, and the facts stay the same whichever title is chosen.
- **Speed:** step 2 is small. All three insides can be generated in the background while the covers are on screen, and the two unused ones thrown away. Since it happens once per person, the extra cost is acceptable.

### 9.5 No friends; Past meets are your connections (decided)

- **Friends lists bring back what we're avoiding:** counts, performing for an audience, and finding people you already know.
- **Recommending to "anyone on the platform" doesn't fit.** It would mean searching for people by name, and names are hidden.

### 9.6 One-step checkout, library rules kept (decided 2026-11-07, replacing the queue)

- **The holds queue felt like a game.** The author picking winners from a waiting list is the gamified part, and it was the hardest part to build. A checkout is now a request the author accepts or declines.
- **The identity is in the library rules, not the queue.** What keeps Trove from being a regular networking app:
  - You borrow a book, not a person: readers choose by what someone knows.
  - A checkout ends. It is one reading and then the book is returned; there's no connection count.
  - You need a book of your own to check one out.
- **Copies stay, privately.** They protect popular authors from being flooded ("I'll get flooded"). When every copy is out the book quietly leaves the shelf, so nothing ever shows as fully booked or popular.
- **Popular authors:** the Librarian's recommendations can quietly steer readers toward books that are checked out less.

### 9.7 Arranging the meeting in the app (decided)

- The request thread is where the two people coordinate.
- The app handles the small, annoying parts (finding a time, the calendar invite, the link, the reminder) and nothing more.
- Video calls stay on Zoom, Meet and similar tools.

### 9.8 In-app messaging: build it, but small (decided)

**Why build it:**

- **There's no other channel before the yes.** Contact details are hidden until the author accepts, so the checkout message and early back-and-forth have to go through Trove. The only alternative is relaying emails between people without exposing their addresses. That's more fragile, not less: incoming email has to be parsed, spam filtered, and delivery kept reliable.
- **Scheduling needs a home.** Shared times, the meeting slot, the video link and "Did you meet?" all belong in the same place as the conversation.
- **Most of it already exists.** `backend/connections.py` already has requests, accept/decline, a message thread per request, and email notifications (`backend/notifications.py`). Building messaging mostly means repurposing that code, not starting over.

**What to leave out:**

- No messages outside a request, so there are no cold DMs.
- No group chats, attachments, read receipts, typing indicators or real-time sockets. Checking for new messages periodically is enough.
- No reply-by-email for now. Email notifications link back to the thread.

**After the meeting:** the thread stays in Past meets as history. Contact details are revealed by then, so people naturally move to their own channels.

### 9.9 Helping members who don't know their story (decided 2026-11-07)

- **"I don't have a story" is rarely true.** Members are professionals and students who've done real work: even a freshman can talk about a high school project. When answers run thin, the usual cause is a question that didn't land.
- **So the fix is better questions, not a softer app.** The first draft (situation cards, small everyday questions, a "mirror" playing back what's unusual) was dropped: the mirror read as flattery, and the rest treated members as more lost than they are.
- **A fork at the start would sort people badly**, so the interview adapts by itself, and "Skip" lets the member move past any question.
- **This is a first-class part of the interview**, and it fixes a known weak spot: quiet members reaching the question cap with too little material.
- **Sparks and growing the book come later** because they need the shelf, checkouts and "Did you meet?" to exist first. Together they make building your story continue after the first interview.

## 10. Considered and dropped

| Idea | Why it was dropped |
| --- | --- |
| Matching people on similar past or future experiences | Not the use case; Trove is about meeting new people |
| A "stories" angle as the main difference from LinkedIn | LinkedIn already has too many story posts. Not performing is the difference |
| The map concept (geographic, experience and personal maps) | Explored; the team prefers books |
| Dinner tables, letters, time bank, passport, radio | Explored; none fit |
| Genres, on the cover or as shelves | Chapters vary too much for one genre per book |
| Several books per person | One book at a time keeps people from showing off range |
| Pen names as the default | Most people would pick their real name anyway |
| First names only until a mutual yes | Cost trust with alumni; full names with contact on a yes instead (§9.1) |
| A holds queue where the author picks who gets each copy | Felt like picking winners, and added a step (§9.6) |
| Friends lists and follows | They bring back counts and performing |
| Requests tied to one chapter, written as "margin notes" | Too complicated; a reader may want several chapters |
| Blocking job or referral asks | We won't police how people use requests |
| Showing when a book is fully checked out, or a "watch" list | Makes a popularity score out of scarcity |
| Reader's notes and acknowledgments | People keep talking through their own channels after a yes |
| Readings as events | Not now |
| Branches or affiliation badges, including CWRU | Everyone is CWRU for now |
| The book slowly becoming a real written book over years | Not needed; we're not planning for multi-year use |

## 11. Decision log

- **2026-11-05, first session:**
  - Renamed to Trove and committed to the book pivot.
  - Chose non-performative as the core difference.
  - Set the use case: meeting people who open opportunities.
  - Hidden names; video by default.
  - Chose "you are the author of your unwritten book" as the core concept.
  - Decided the first set of book, discovery, request and reading rules.
- **2026-11-05, second session:**
  - Confirmed:
    - first names on books
    - no CWRU branch or badge
    - the résumé rule
    - one pool of chapters behind three titles
    - no friends or follows
    - keep the queue, hide the scarcity
    - meetings arranged in the app, kept light
  - Approved small, request-scoped messaging in the app (§9.8).
- **2026-11-05, repo setup:**
  - Stay on MongoDB (low traffic expected; Postgres considered and declined).
  - Rebuild Trove from scratch in the same repo. FoundersCircle is tagged `founderscircle-v1`; only sign-in, email and the Claude client were carried over.
- **2026-11-06, the book model (B1):**
  - No pen names; books show the first name only.
  - Settled what a book holds, who sees what, and how sample books work (§3).
- **2026-11-06, the interview (I1, I2):**
  - First version settled (§4): conversation, moments-first questions, three phases, reader lens in the generator, voice, autosave, the reveal and review.
  - Interactive layer (margin notes, bursts and the rest) on hold until the interview works.
  - Screens: interview direction A, "The question band".
- **2026-11-07, names and checkout (after talking with our advisor):**
  - Books show full names; employer, title and links stay off the book; contact details only when the author accepts (§9.1).
  - Checkout is one step: check out with a message, the author accepts or declines, the reading, the return. The holds queue is gone; copies stay private and a fully lent book quietly leaves the shelf (§6, §9.6).
- **2026-11-07, the blurb (T13):**
  - Blurb: 2–4 sentences, first person, written with the draft, shown in review and on the book.
- **2026-11-07, members who don't know their story:**
  - Approved the adaptive interview (§4, §9.9, I4): one pipeline, prompted mode, the mirror and "Help me find it".
  - Revised after seeing the screens: no mirror, no situation cards, no small-talk questions or reassurance copy. Thin answers get sharper, professional questions, and a quiet "Skip" replaces "Help me find it" (an "Ask me another way" button was tried and dropped).
  - Sparks from other books and each reading growing the book are planned for after the whole loop works (I5, I6).
- **2026-11-07, checkout limits (C1, Ellie):**
  - 3 open checkouts per reader; pending and accepted checkouts both use a copy; unanswered checkouts close after 7 days.
  - After a decline or expiry, the same book can be checked out again after 30 days; readers can cancel an unanswered checkout; authors get an email for each new checkout (§6).
  - Your own book must be on the shelf before you check one out; authors see the reader's book when deciding.
- **2026-11-10, account basics (A1, Daniel):**
  - Contact details: the sign-in email is always shared on a yes; a LinkedIn profile link and a phone number are optional, and each is shared only if the member adds it. No separate contact email for now.
  - Checked lightly: LinkedIn must be an `https://linkedin.com/in/...` link, and a phone number has 7 to 15 digits. We never check that a number works.
  - One email switch (checkouts and messages). Account emails, like the welcome message, are sent either way.
  - Deleting an account is permanent and asks the member to type their email. It removes the account, sessions and the member's book. (The first version kept accepted checkouts for the other person as "a former member"; changed on 2026-11-16, below.) Each feature cleans up its own data through `auth.on_account_deleted`.
- **2026-11-16, deleting an account removes everything (Daniel):** when a member deletes their account, everything that belongs to them goes: the account, sessions, book, and every checkout and meeting they were in, for both people. Accepted checkouts and past meets do not stay behind for the other person. This keeps one rule for every feature and frees any copy the member had taken.
- **2026-11-16, arranging the meeting (M1, Daniel):**
  - A meeting belongs to one accepted checkout, and only the two people on it can see it. Before the author says yes there is nothing to arrange.
  - Each person offers up to 5 start times, each 30 minutes. The app shows which ones both offered; either person can confirm any offered time that is still ahead, and can change it later.
  - Times are shown in each person's own time zone. The reminder email shows UTC until we decide how to know a member's zone.
  - The video link must start with `https://`. A place to meet is an optional short note for people who are both nearby.
  - The calendar invite (.ics) is a download for each person. Nobody is emailed when a time is confirmed; that waits on messages (C3).
  - Deleting an account removes the member's meetings, for both people, through `auth.on_account_deleted`.
  - One reminder email per person, sent once the meeting is within 24 hours. It respects the email switch. There is no scheduled job yet, so it goes out when someone opens a meeting page.
- **2026-11-16, the reveal (C2, Ellie):**
  - On accept, both people see each other's contact details on the Checkouts page (the sign-in email, plus LinkedIn and phone if added), read fresh from Settings.
  - Both get an email that only links to Trove; contact details are never copied into emails. It respects each member's email switch.
- **2026-11-18, messages (C3, Ellie):**
  - The thread opens on accept and becomes read-only history after the reading; 2,000 characters a message, 30 an hour per person.
  - The new-message email names the sender and links to the thread, at most one per 10 minutes per thread; it respects the email switch.
  - Its own page, app notes other features can post (such as a confirmed meeting time), and a private "New message" marker (§6).
- **2026-11-18, "Did you meet?" and Past meets (C4, Ellie):**
  - Asked after the confirmed meeting time (or 14 days after the yes); Yes / Not yet / No; the first Yes or No returns the copy; unanswered copies return after 14 days (closing that open question in §6).
  - A Past meet needs a Yes and no No, and both people get it, with name, book, contacts and the read-only conversation. In the app only for now (§8).
