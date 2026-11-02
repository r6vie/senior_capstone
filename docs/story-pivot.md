# The Story Pivot: Design and Plan

Status: proposal for the team, November 2026. Nothing here is final; open questions are collected in section 13.

**In one line:** a career-networking web app where every person is a book. You come to find your own story, or to show the one you already have; you browse other people's stories on library shelves; and you meet the few people whose stories you want to hear in full, by video call or in person.

This replaces the FoundersCircle plan built around four modules (narrative, matching, capital readiness, knowledge graph). Matching, AI onboarding, connections and email carry over as the plumbing underneath. Capital readiness, investor connect and the knowledge graph are dropped.

---

## 1. Why pivot

- **Most networking products feel like scrolling.** Profiles lead with titles and employers, feeds reward volume, and a "connection" usually means a message that goes nowhere.
- **Stories are what people remember.** Starting from someone's story (what shaped them, what they're working through, what they could talk about for an hour) gives two strangers a reason to meet and something to talk about when they do.
- **AI should help people tell their own story, not write a fake one.** The AI interviews, organizes and edits; the words, and on video the face and voice, stay the member's own.
- **Fewer, better connections.** Checking out only one or two books at a time makes each request deliberate, and only a real conversation (video call or in person) completes it.

## 2. Principles

1. **Story first, person second.** A book's cover leads with the story's title. The member's name is shown, but smaller and never first.
2. **Human, not AI slop.** AI may ask, organize, summarize and cut; it never invents experiences. Every AI change is reviewed by the member before it is published.
3. **Intentional, not infinite.** Shelves, not feeds. Limited checkouts. No likes, follower counts or visible scores.
4. **Meet, don't just message.** Messages are for logistics. A checkout is complete only after a video call or an in-person meeting.
5. **Members control what's shown.** Every piece of a book has a visibility level, and anything can be edited or deleted.

## 3. Who it's for

A general career-networking audience: students, early-career people, career changers, founders, mentors and experienced professionals. No school email gate in the first version. A local angle matters ("people near you"), because in-person meetings are encouraged.

## 4. The metaphor

| Real life | In the app |
| --- | --- |
| A person | A book |
| Their story and background | Cover, title, blurb, chapters, story pages, optional video |
| Browsing people | Walking library shelves |
| A quick look | Hovering over a book: its stats card |
| Learning more | Opening the book |
| Asking to meet | Checking the book out |
| The time to meet | The due date |
| Having met | Returning the book |
| People you've met | Your "read before" shelf |

The tone is warm and curious: a good library, not a recruiting app or a dating app.

## 5. The book

Each member has exactly one book. It is their profile and the main visual element of the app.

### 5.1 What's in a book

| Part | What it is | Example | Shown |
| --- | --- | --- | --- |
| **Title** | The story's headline, not the person's job title | "Left Med School to Build Wheelchairs" | Cover, spine |
| **Name** | The member's name, smaller than the title | Maya Rodriguez | Cover |
| **Blurb** | A short third-person teaser (about 280 characters) | "Two years into medical school, Maya realized…" | Hover card, book page |
| **Stats** (hover card) | A glimpse of the person: profession, field, interests, hobbies, city | Product designer · Healthcare · Climbing, film photography · Cleveland | Hover card |
| **Chapters** | The story told in 3–6 short sections, each with a heading | "The lab that changed my mind", "Learning to sell" | Inside the book |
| **"Could talk for an hour about…"** | One specific conversation starter | "Why hospital procurement is broken" | Hover card, book page |
| **Looking for / can offer** | What they'd like from a conversation, and what they can give | Looking for: a co-founder with sales experience | Book page |
| **Video chapters** (optional) | Short clips the member recorded, cut by the AI, one per chapter | 45-second clip on "Learning to sell" | Inside the book |
| **Topics** | Searchable tags | Medical devices · Career change | Search, shelves |
| **Hidden keywords** | Private tags used only for matching; the member can see and remove them | | Never shown to others |
| **Cover style** | Ink colour and cover art chosen by the member | | Everywhere |

### 5.2 Visibility levels

| Level | Who sees it | Typical content |
| --- | --- | --- |
| **Cover** | Everyone browsing | Title, name, cover, topics |
| **Inside** | Anyone who opens the book | Blurb, stats, chapters, video, "could talk for an hour about" |
| **After checkout** | Only the person whose checkout was accepted | Contact details, preferred meeting times, extra context the member chooses |
| **Only me** | Nobody; still used for matching | Hidden keywords, private facts |

This builds directly on the per-fact visibility that onboarding already has (`backend/member_data.py`).

## 6. Making your story

### 6.1 Two ways in

- **"Find my story":** for people who don't have one yet. A guided AI interview draws the story out.
- **"I have a story":** for people who do. They paste or write it, or upload a document or LinkedIn PDF, and the AI interview only fills the gaps and helps structure it into chapters.

Both end in the same place: a draft book the member reviews before it goes on the shelf.

### 6.2 The guided story interview

This is the existing onboarding interview, re-tuned for stories. It keeps everything that already works: one question at a time on a card, suggested answers to tap, a detail box, Skip, a progress bar, an instant first question, and facts saved as you go.

What changes is the question plan. Instead of covering needs, offers and background for matching, it follows a story arc:

1. **Now:** what you do and what you're working on.
2. **Turning points:** a moment or decision that changed your direction.
3. **Struggles:** something hard you worked through, and what you learned.
4. **What you're proud of**, and what you'd do differently.
5. **What's next:** where you're heading and what would help.
6. **Conversation:** what you could talk about for an hour, and who you'd like to meet.

Rules for the interviewer:

- Ask for **specific moments**, not adjectives ("Tell me about the day you decided…", not "Describe yourself").
- Go deeper on the one or two threads with the most story in them, then move on.
- Never invent details. If something isn't clear, ask.
- Avoid sensitive topics unless the member raises them, and default anything personal to "Only me".
- The member decides when to stop. A short interview still produces a book; a longer one produces a richer one.

### 6.3 Binding the book

When the member finishes, the AI drafts the title, blurb, chapters, stats, topics and the "could talk for an hour" line, using only their answers. Then comes a **review screen**, as in Overdue's author interview:

- The draft book, with every generated part editable
- Each chapter can be kept, rewritten or dropped
- **Put it on the shelf**, **Edit first**, or **Save as a draft**

Nothing is published without this review. Later interviews ("Add a chapter") show what would change before anything is saved.

### 6.4 Video chapters (optional)

The member can bring each chapter to life on camera. This is optional everywhere: a text-only book is a complete book.

1. **Prompts:** for each chapter, the app shows a prompt built from what the member already said ("Tell us about the lab that changed your mind. What did you see?") and a short tip (look at the camera, one to two minutes is plenty).
2. **Record** in the browser, one take per prompt, with retakes allowed.
3. **Transcribe** each take with word-level timestamps (a speech-to-text service).
4. **Cut:** the AI reads the transcript, picks the strongest continuous moments, and returns start and end times. A server job cuts the clips (for example with ffmpeg) and adds captions from the transcript.
5. **Review:** the member watches the cut, can choose a different moment or the full take, and approves it before it's shown.

The AI only **selects and trims** the member's own footage. It never generates or alters faces or voices.

## 7. Browsing: the library

### 7.1 Shelves

The library is a set of shelves, not a feed:

| Shelf | What's on it |
| --- | --- |
| **For you** | Best matches for what you're looking for, from the matching engine |
| **Near you** | Books from people in your area, for in-person meetings |
| **Themed shelves** | Built from topics and hidden keywords, for example "Changed careers after 30", "First-time founders", "Engineers who became designers" |
| **New on the shelf** | Recently published books |

Each shelf shows a limited number of books, and you can open a full shelf, but there is no infinite scroll. Search works by topic and story, not by name.

### 7.2 Hover, then open

- **Hover** (or tap-and-hold on touch screens) a book to see its **stats card**: profession, field, interests, hobbies, city, and the "could talk for an hour about" line.
- **Click** the book to open it: the book page with the blurb, chapters, video chapters and what the member is looking for, plus **Check out**.
- Matching explains itself in human words, not scores: "You both left a stable path to start something" or "She's looking for exactly what you can offer".

### 7.3 The book on the web

The visual book should feel like an object, not a card. Two levels, so we can ship early and improve:

1. **First version:** CSS 3D. Books with a spine, cover and thickness on a shelf; hover tilts the book toward you; opening is a page-flip transition.
2. **Later:** a WebGL book (three.js), porting ideas from Overdue's SceneKit book: a hinged cover, curved pages, a ribbon bookmark, and the book flying from the shelf to its page.

## 8. Checking out: intentional connection

### 8.1 The rules

- You can have at most **two active checkouts** at a time (a setting; it could be one). Active means requested, accepted or scheduled, but not yet met.
- While you're at the limit, you **can't request** anyone new. Shelves show "Return a book to check out another".
- A checkout is complete only when **both people confirm they met by video call or in person**. Messaging alone never completes it.
- Each checkout has a **due date** (for example 14 days after it's accepted). If it isn't met by then, it's returned without counting as a meeting, which frees the slot.
- You can **cancel** a request that hasn't been accepted yet, which frees the slot right away.

### 8.2 The lifecycle

```
requested ──accept──▶ accepted ──schedule──▶ scheduled ──both confirm──▶ returned (met)
    │                     │                      │
 decline / cancel     due date passes        due date passes / didn't happen
    ▼                     ▼                      ▼
 closed               returned (not met)    returned (not met)
```

### 8.3 Whose slots count

- **The reader's slots:** every active checkout they started counts toward their limit.
- **The author's side:** accepting someone's request also takes one of the author's slots, so nobody accepts more meetings than they can keep. A member at their limit can still receive requests; they just can't accept until a slot frees. (Open question: should incoming requests wait, or expire after a few days?)

### 8.4 The flow

1. **Request.** On a book page, the reader taps **Check out**. The app helps draft the note (section 9), and the reader picks the meeting type they'd prefer: video call or in person.
2. **Decide.** The author sees the request with the *reader's* book and note, and chooses **Accept** or **Pass**.
3. **Plan the meeting.** Both see each other's contact details and a scheduling panel:
   - meeting type: video call (with a link) or in person (with a suggested public place nearby)
   - a few proposed times, or a link to a calendar booking page
   - optional calendar connection to suggest times that work for both (later)
4. **Meet.** Before the meeting, each side can open a prep sheet (section 9).
5. **Return.** After the time passes, both are asked "Did you meet?": **We met** or **Didn't happen**. When both say "We met", the book moves to each person's **Read before** shelf, and a slot frees.

### 8.5 Why "both confirm" is enough for now

We can't prove a meeting happened, and shouldn't try in the first version. Both people confirming is a reasonable, private honour system. If the answers disagree, the checkout is returned as not met. Nothing about these answers is shown to anyone else.

## 9. Help with outreach and meeting

AI support stays grounded in what both members actually wrote.

- **Request note drafting:** a first draft of the checkout note that points to something specific in the author's story and says why the reader wants to meet. The reader edits it before sending.
- **Meeting prep:** a short brief before the meeting with shared ground, questions to ask and a suggested agenda. This builds on the meeting-prep work already in `backend/meeting_prep.py`.
- **Scheduling help:** suggested times, a video link, or nearby public places for in-person meetings.
- **After the meeting:** a private note for yourself, and an optional thank-you message draft.

## 10. Matching

The existing explainable matching engine (`backend/matching.py`) stays, with new inputs:

- **Inputs:** each book's topics, chapters, hidden keywords, what the member is looking for and can offer, and their city.
- **Story similarity:** shared turning points and struggles (for example both changed careers), not just shared industries. This is where embeddings become worth adding.
- **Complementarity:** one person's "looking for" against another's "can offer".
- **Near you:** location as a filter for the "Near you" shelf, not only a scoring bonus.
- **No visible scores.** Scores rank the shelves; members see plain-language reasons instead.
- **Students and alumni go away.** The general audience doesn't fit fixed roles, so matching uses "looking for" and "can offer" instead.

## 11. Safety, privacy and trust

- **Content filter** on every edited or generated text field: length limits, no contact details or links in public text, and a blocklist (Overdue's rules are a good starting point).
- **Reports** on every book, request and video, sent to a moderator queue.
- **Video:** members approve every cut, captions come from their own transcript, and any video can be removed at any time. Plan for moderation before video is public.
- **Contact details** are shared only after a checkout is accepted.
- **Resting books:** inactive books leave the shelves automatically and come back with one click.
- **Sharing:** a share card (cover, title and a link, without the blurb) to invite people from outside.

## 12. What happens to the existing code

| Area | Today | Plan |
| --- | --- | --- |
| Accounts, sessions, LinkedIn sign-in | `auth.py`, `linkedin_auth.py` | **Keep.** LinkedIn pre-fills the name and photo for the book. |
| Onboarding interview | `onboarding.py`, `interviewer.py` | **Adapt** into the story interview: new question plan and prompt, same one-question card. |
| Facts and visibility | `member_data.py`, `member_models.py` | **Keep** as the raw material for books; add the book's visibility levels. |
| Profiles | `profiles` collection, `models.py` | **Replace** with a `books` collection; drop student/alumni roles. |
| Matching | `matching.py` | **Adapt** to book inputs; add story similarity later. |
| Meeting prep | `meeting_prep.py` | **Adapt** to work for any two books. |
| Connections and messages | `connections.py` | **Replace** with checkouts: the limit, scheduling, both-confirm return. Messages stay for logistics. |
| Email notifications | `notifications.py`, `email_templates.py` | **Keep**; add checkout, scheduling, reminder and "did you meet?" emails. |
| Directory, Find a Match, Requests pages | `frontend/src/pages` | **Replace** with Library, Book page, My shelf and My book. |
| Investor, capital readiness, knowledge graph | Not built | **Dropped.** |

### 12.1 Data model (first draft)

| Collection | One document per | Key fields |
| --- | --- | --- |
| `users` | Account | as today |
| `books` | Member | owner, title, name display, blurb, stats, chapters, hour topic, looking for, can offer, topics, hidden keywords, cover style, status (draft, on shelf, resting), visibility per part |
| `story_sessions` | Story interview | as `interview_sessions` today, plus which mode (find or bring) |
| `facts` | Thing learned | as today |
| `media` | Recorded take or cut clip | owner, chapter, storage key, transcript, chosen segment, status (uploaded, processing, ready, approved) |
| `checkouts` | Request between two members | reader, author, note, preferred meeting type, status, proposed and chosen time, meeting link or place, due date, each side's "did you meet?" answer |
| `messages` | Logistics message | as today, linked to a checkout |
| `reports` | Report | reporter, target, reason, status |

### 12.2 Main screens

| Screen | Route | What it does |
| --- | --- | --- |
| Landing | `/` | Explains "every person is a book" |
| Start your story | `/story/start` | Choose "Find my story" or "I have a story" |
| Story interview | `/story/interview` | The guided one-question interview |
| Review your book | `/story/review` | Edit the draft, then put it on the shelf |
| Record chapters | `/story/video` | Optional video prompts, recording and cut review |
| Library | `/library` | Shelves, hover cards, search |
| Book page | `/books/:id` | Open book, video chapters, Check out |
| My shelf | `/shelf` | Active checkouts, scheduling, requests to you, Read before |
| My book | `/my-book` | Edit, visibility, add a chapter, share card |

### 12.3 Technical choices to make

| Need | Options | Lean |
| --- | --- | --- |
| Video upload, storage and playback | Mux, Cloudflare Stream, or S3 with a CDN | A managed video service, to avoid building playback ourselves |
| Speech to text with timestamps | Deepgram, AssemblyAI, or OpenAI Whisper | Whichever gives word timestamps at the lowest cost for short clips |
| Cutting clips | Done by the video service, or ffmpeg in a background job | Decide after a test |
| Background jobs (cutting, reminders, due dates) | A simple job queue, or scheduled tasks | Start simple |
| 3D book | CSS 3D first, three.js later | CSS 3D for the first version |
| Calendar | Booking links first; Google or Outlook calendar later | Links first |
| Video meeting links | Members paste their own; generate Zoom or Google Meet links later | Paste first |

## 13. Open questions

1. **Name.** Does it stay FoundersCircle? The new direction isn't founder-specific.
2. **Checkout limit:** one or two active checkouts?
3. **Does accepting a request take one of the author's slots?** (Proposed: yes.) And how long can an incoming request wait?
4. **Due date length:** 7, 14 or 21 days after accept?
5. **What if the two "did you meet?" answers disagree?** (Proposed: returned as not met, nothing shown to anyone.)
6. **Is a book required before checking out others?** (Proposed: yes; readers are also authors.)
7. **Who can see video:** anyone who opens the book, or only after a checkout is accepted?
8. **Launch community:** CWRU and Veale contacts first, then open up? A small, local start helps the "Near you" shelf.
9. **Moderation:** who reviews reports, and is video reviewed before it's public?
10. **Mobile:** the web app must work well on phones; is a native app ever in scope?

## 14. Plan

Each phase ends in something that works and can be demoed. Owners are suggestions based on who built what so far; the team should confirm them.

### Phase 0: Decide and design (about 1 week)

- Answer the open questions in section 13.
- Wireframes for the library, hover card, book page, My shelf and the story interview.
- A one-day test of the video pipeline: record, transcribe, have the AI pick a moment, cut it. Measure cost, time and quality before committing.
- **Done when:** decisions are written into this doc and the wireframes are agreed.

### Phase 1: The book and the story interview (2–3 weeks)

- `books` collection, API and visibility levels. (Suggested: Alvisa)
- Story interview: new question plan and prompt, "find" and "bring" modes, then binding the book and the review screen. (Suggested: Josef)
- My book page: edit any part, visibility, put on or take off the shelf.
- Content filter on all book text.
- **Done when:** a new member can sign up, do the interview, review a generated book, edit it and put it on the shelf.

### Phase 2: The library (2 weeks)

- Shelves: For you, Near you, themed and new, with matching re-pointed at books. (Suggested: Alvisa)
- Hover stats card and book page.
- First-version CSS 3D book on shelves. (Suggested: Josef)
- Topic search.
- **Done when:** a member can browse shelves, hover for stats, open a book and understand why it was shown to them.

### Phase 3: Checking out and meeting (2–3 weeks)

- `checkouts` collection with the limit, lifecycle and due dates, replacing connections. (Suggested: Ellie)
- My shelf: active checkouts, requests to you, Read before.
- Request note drafting, and meeting prep adapted to books. (Suggested: Alvisa)
- Scheduling panel: meeting type, proposed times or booking link, video link or nearby place.
- Emails: request, accepted, reminder, due soon, "did you meet?". (Suggested: Ellie)
- **Done when:** two members can go from a book page to a scheduled meeting to a confirmed return, and the limit blocks a third checkout.

### Phase 4: Video chapters (2–3 weeks, after the Phase 0 test)

- Prompts, in-browser recording, upload. (Suggested: Daniel)
- Transcription, AI moment selection, cutting, captions.
- Cut review and approval; playback in the book.
- **Done when:** a member can record a chapter, approve the AI's cut, and readers can watch it in the book.

### Phase 5: Polish and trust (ongoing, then 1–2 weeks)

- Reports and a simple moderator view; resting books.
- Share cards.
- WebGL book with the open-and-fly animation.
- Calendar connection and generated meeting links.
- Seed books for the demo, and usability testing with real people.

## 15. How we'll know it works

- **Story completion:** share of new members who publish a book, and how long it takes.
- **Story quality:** members keep most of the generated book (light edits), and readers open books after hovering.
- **Intentional connection:** share of checkouts that end in a confirmed meeting, and time from request to meeting.
- **Video:** share of books with at least one video chapter, and how often readers watch them.
- **Return visits:** members coming back to add chapters or check out their next book.
