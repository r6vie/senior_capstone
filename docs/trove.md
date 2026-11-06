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
  4. **Discreet until yes.** First names only. Full identity and contact details are shared only on a mutual yes.
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
- **Names:** books show the author's **first name**. Last name, employer, title and contact details are revealed only on a mutual yes (§9.1).
  - An optional pen name is available for anyone who needs more discretion. The Librarian suggests one, and the author can change it.
  - The book's text stays vague on identifying details, as in Overdue.
- **Adding to the book:** the author can reopen the interview from their book at any time to add detail or chapters (as in Overdue's author interview).

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
- **The interview will be more capable than Overdue's quick cards.** The exact format will be redesigned later.
- **Résumé and file upload** (§9.3):
  - Uploading is optional.
  - The résumé tells the AI where to dig, never what to say. It is used only to personalize the interview, never as book content.
  - The raw file is not stored once the interview questions have been drawn from it.
- **The reveal shows three books you could write.** It shows only their titles and covers, so nobody has to compare three long tables of contents. The author picks one.
- **How the inside is generated** (§9.4):
  - The interview first produces one shared pool of grounded chapters.
  - Each of the three titles draws on that pool from a different angle.
  - The inside is finished to match whichever title is picked. All three can be prepared in the background so the pick feels instant.

### Open

- The interview's format (cards, conversation, voice?), its length, and how the person knows when they're done.
- The Librarian's tone for this audience.
- Whether, and how, the author edits the book by hand after it's made.

## 5. Discovery

### Decided

- **Shelves will be grouped by categories.** The categories are still to be defined, and they will not be genres.
- **Smart search** finds books relevant to what you're looking for. Never search by name.
- **"The Librarian recommends":** the AI recommends books to you.
- **Recommend a book:** you can recommend a book in the app to anyone you've met (your Past meets), or to anyone else by sharing a link (§9.5).
- **No friends or follows.** Meeting someone is the only way to become connected.

### Open

- What the categories are and how the home screen is laid out.

## 6. Requests, copies and messaging

### Decided

- **You need a book of your own to check one out.**
- **A request is for the whole book, with a message.** It isn't tied to a chapter, because a reader may be interested in several.
- **No rule or check blocks asking for a job or a referral.** It isn't the ideal use of Trove, but we won't police it.
- **Copies:** each author sets how many copies of their book can be checked out at once (e.g. 3). When requests come in, the author chooses who gets them.
- **The queue** (§9.6):
  - Requests the author doesn't pick stay in a queue for about 2 weeks instead of being declined right away.
  - The author can still decline manually. A declined or expired request shows the reader "this book isn't available right now".
  - Requests are still accepted when every copy is out; they wait in the same queue.
  - Readers never see how many copies are out or how many requests a book has.
- **Messaging lives in the app.** The thread is where you request a book, coordinate the meeting and share the video link. A member can choose to get communications by email instead.
- **"Did you meet?" matters:** answering it returns the copy, which frees it for the next reader.
- **Messaging is a small thread inside each request** (§9.8). Messages exist only inside a request, so there are no cold DMs.

### Leaning

- **A limit on pending requests per reader** keeps requests deliberate.

### Open

- The exact numbers: copies per author, pending requests per reader, how long a request stays in the queue, and how soon a copy returns if nobody confirms a meeting.

## 7. The reading

### Decided

- **A video call by default, or in person when both people are nearby.**
- **Names and contact details are revealed on a mutual yes.**
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

## 9. Reasoning behind decisions

### 9.1 First names, not full anonymity (decided)

- **Last names are what make someone searchable.** A last name lets you look a person up on LinkedIn or Google, and that lookup is where performance and status sneak back in. A first name alone does neither.
- **Full anonymity costs trust.** Professionals, alumni especially, are wary of requests from someone with no name. A first name makes a book feel like it was written by a person, and makes a request feel like it came from one.
- **Pen names would mostly end up as first names anyway**, so making everyone choose one would add a step without gaining anything. The optional pen name covers people who need discretion.
- **One caution:** in a small community, a first name plus specific details can still identify someone. The book's text should stay vague on identifying details.

### 9.2 Branches and affiliation (decided: none for now)

Everyone at launch is CWRU, so community branches and affiliation badges would carry no information. We can revisit them if Trove expands beyond CWRU.

Membership verification is still open:

- **Students:** a case.edu email.
- **Alumni:** there's no clean check. Options:
  - an invite link shared through alumni channels
  - the person states their graduation year, with manual review while the community is small
  - a partnership with the alumni office
  - LinkedIn education data, which needs partner access we don't have

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

### 9.6 Keep the queue, hide the scarcity (decided)

- **Requests are always open,** even when every copy is out. That's how a library's holds list works, and nothing ever looks shut.
- **A visible "always checked out" turns into a popularity score**, and that's the performative status we're trying to avoid. So readers never see copy counts or request counts.
- **The motivation still works.** When a copy returns, through "Did you meet?", the author is nudged to choose the next reader. That gives everyone a reason to meet and close the loop.
- **Popular authors:** the Librarian's recommendations can quietly steer readers toward books that are getting fewer requests.

### 9.7 Arranging the meeting in the app (decided)

- The request thread is where the two people coordinate.
- The app handles the small, annoying parts (finding a time, the calendar invite, the link, the reminder) and nothing more.
- Video calls stay on Zoom, Meet and similar tools.

### 9.8 In-app messaging: build it, but small (decided)

**Why build it:**

- **There's no other channel before the yes.** Names and contact details are hidden until both people agree, so the request message and early back-and-forth have to go through Trove. The only alternative is relaying emails between people without exposing their addresses. That's more fragile, not less: incoming email has to be parsed, spam filtered, and delivery kept reliable.
- **Scheduling needs a home.** Shared times, the meeting slot, the video link and "Did you meet?" all belong in the same place as the conversation.
- **Most of it already exists.** `backend/connections.py` already has requests, accept/decline, a message thread per request, and email notifications (`backend/notifications.py`). Building messaging mostly means repurposing that code, not starting over.

**What to leave out:**

- No messages outside a request, so there are no cold DMs.
- No group chats, attachments, read receipts, typing indicators or real-time sockets. Checking for new messages periodically is enough.
- No reply-by-email for now. Email notifications link back to the thread.

**After the meeting:** the thread stays in Past meets as history. Contact details are revealed by then, so people naturally move to their own channels.

## 10. Considered and dropped

| Idea | Why it was dropped |
| --- | --- |
| Matching people on similar past or future experiences | Not the use case; Trove is about meeting new people |
| A "stories" angle as the main difference from LinkedIn | LinkedIn already has too many story posts. Not performing is the difference |
| The map concept (geographic, experience and personal maps) | Explored; the team prefers books |
| Dinner tables, letters, time bank, passport, radio | Explored; none fit |
| Genres, on the cover or as shelves | Chapters vary too much for one genre per book |
| Several books per person | One book at a time keeps people from showing off range |
| Pen names as the default | Most people would pick their first name anyway |
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
