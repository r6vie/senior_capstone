# Design decisions

Decisions Josef has made about Trove's look and feel. Newest first.

## 2026-11-23: My book, a calmer page and a design studio (canvas page "My book"; waiting for Josef's approval)

Josef rejected concepts A and B (the notebook does not belong on My book; it felt blocky, old and unbalanced) and asked for a more airy, considered page with the interview as an important block, and a design studio that is
satisfying and adapts to categories (Strata first, then Watercolour and others, about ten designs each). Boards: how it is now, "a calmer page" (one column, the book alone on the left with its design named, the Librarian's black
panel with the one red button as the one important block, hairlines instead of cards), "the design studio" (a page of its own: stage on a ledge, a shelf preview, category tabs, a grid of designs, Shuffle, Use this design), and
every stage in the new look. The notebook is not on My book. New copy: "Change design", "Design", "Use this design", "Continue with the Librarian". Open product questions: whether the design can change at any time and whether it
changes a book already on the shelf; the red button's label.

## 2026-11-23: five logo options (canvas page "Logo"; waiting for Josef's choice)

Five ink-only logo options for the website, chosen from twelve ideas against the mission (a book and a person, not a social network), the feel (printed, calm, literary) and the job (16px favicon, 26px header, avatar, one colour, on paper and black):
A Ribbon (the T is a notched bookmark), B Open V (the V is an open book), C Stacked T (the T is two books), D The book (the product's book object with a T), E Stamp (a library date stamp, "Checked out"). An independent critic
reviewed the first render; its fixes are applied (kerning, drawn wordmarks so none depends on a loaded font, true cut-outs, a small master for the book and the stamp). Its ranking: Ribbon, The book, Stacked T, Stamp, Open V.

## 2026-11-19: Kit 3 "Folio" APPROVED by Josef and sent for implementation, without the interview (the interview is the Librarian's notebook)

Josef asked for the polished Kit 3 direction to be sent for implementation. The Kit 3 board now holds only the parts sheet and the shelf front page; its interview frames are removed, because the interview is the
Librarian's notebook (canvas page "Librarian notebook"). Approved by Josef on 2026-11-19 ("I approve all six", relayed by the orchestrator). The six changes to the fixed tier this look makes: cross-hatch shade on card spines and under shelf ledges (dots stay for cast shadows); a 5px corner radius
(8px on the black cover, 3 to 5px on the book cover) in place of square corners; a square search field and avatar; a notched ribbon bookmark on the one line that needs you; shelf arrows that scroll each
shelf in place instead of "See the whole shelf"; the black cover's book has no dot shadow. The genre tabs and filter chips are gone from the front page. Record: docs/design/system.md, Additions, "Folio".

## 2026-11-19: the Librarian's notebook, round 2 (Interview 4; APPROVED by Josef, 2026-11-19, canvas v127)

Scope answers came from Josef through the orchestrator: red ink (approved as an exception to "red is the primary action and nothing else"), a commentary notebook (chapter, connection, saving,
clip, note), the next question circling or ticking its source, the notebook hidden after the reveal and returning trimmed when the author reopens the interview, and the extras: pasted and
résumé-speak highlight, idle lines, the handwritten sign-off. Out: doodles, swear strikes, the self-correcting question, the short-answer hold.
Josef then asked, directly: red marker, no bullets in the notebook, text starting just after the spine, a messier and more human notebook (things underlined and rewritten above), and no footer line,
"Only you see this" or "Command and Return sends".
- Canvas page "Librarian notebook": `LibDesktop` (five moments), `LibPhone`, `LibParts`, `LibMore` (idle, paste, sign-off), `LibReopened`. The red exception is recorded in `docs/design/system.md`.
- Approved with the screen: red ink for the Librarian (exception to the red rule), the handwriting face Caveat (a fourth typeface, Librarian's hand only), and the notebook, marks and phone sheet as new components. Josef approved the screen as drawn; he did not list these separately.

## 2026-11-19: one interview redesign, as a conversation (replaces the two earlier ones; waiting for Josef's choice)

Josef removed "The thread" and "Question and answer pages" and asked for a third that is more UX friendly and familiar. Board "Interview 3 · The conversation": the Librarian's
question is a message on the left, your answers are messages on the right (each with Edit), the thread scrolls, and a composer is docked at the bottom with the field, Speak and one
red Send. Skip is a quiet "Skip this question" under the question. Phases stay as index tabs.
- Needs Josef's yes: Return sends and Shift and Return starts a new line (the earlier boards had Command and Return send); the current question at 26px with no leading letter;
  earlier messages stay on the page, which hints at progress (decision 26); a square ink "L" tile for the Librarian.

## 2026-11-19: Folio front page: shelves out of the folder, "My book" beside the bookmark (Josef: no large folder)

On Kit 3's example page the two shelves no longer sit in a tabbed folio card. They are Kit 1's shelf: a name, a rule and "See the whole shelf" over a
row of books standing on one ink ledge with a hatch cast, straight on the page. The genre tabs are gone from this page. Under the hero are two equal
blocks: the bookmarked "Review request" and a new "Your book" block (small cover, title, Open), as in Kit 2. Waiting for Josef's choice.

## 2026-11-18: two new complete interview redesigns on Folio v4 (waiting for Josef's choice)

Boards "Interview 1 · The thread" and "Interview 2 · Question and answer pages" on the Elevate page, each with the question, sending, the next
question setting in, and a phone. Also: the ribbon bookmark on the front page now has a notched, two-triangle bottom (needs Josef's yes: a diagonal cut).
- **1, the thread:** earlier questions and answers stack above as plain cards (with Edit); the open question is the one focal folio at the bottom, with the
  phases as its index tabs and Speak, Skip and Send in its footer. Needs Josef's yes: a growing thread hints at progress (decision 26); 60px leading letter.
- **2, question and answer pages:** a two-page card, black page with the Librarian's question in Newsreader italic and "Skip this question", white page with a tall
  answer box, Speak and Send; earlier answers in a row of plain cards below. Needs Josef's yes: a black page inside a card (the system allows black for the
  Librarian's band only); a growing row of answers hints at progress.

## 2026-11-18: Folio v4: new header, plain list rows, interview rebuilt (Josef: rows, header and interview did not look right)

- **Corners (Josef: not so sharp):** Kit 3 now has a small corner radius, 5px on cards, buttons, fields, tabs, the avatar and the search; 8px on the black cover; 3 to 5px on book covers (first tried at 8px, 12px, 4 to 8px; Josef asked for smaller). Needs Josef's yes: the fixed tier says square corners.
- **Header:** the search field and the avatar are square, 44px, 2px ink, like the buttons (the avatar is an ink tile with white initials and a dot
  shadow; the search has an icon and a "/" key hint). Needs Josef's yes: the system allows a pill for both today.
- **List rows:** plain ruled rows (title, one line of the answer), no square markers, no dotted rules; the selected row has a full-height bar at the left edge.
- **Interview question, rebuilt from scratch:** one composed card (the question with a smaller two-line leading letter, an ordinary answer box, a footer
  strip with Speak, Skip, the hint and the one red Send), phases as index tabs, earlier answers in a plain card beside it. Frames: ask, sending,
  next question setting in, and a phone. Needs Josef's yes: the 68px leading letter (type table stops at 22).

## 2026-11-18: Folio v3 (Josef: too busy, no stripes, shade with cross-hatching)

Folio was too busy and its secondary buttons were unreadable. v3: no stripes anywhere (including under buttons); page thickness and the spine are
shaded with diagonal cross-hatching and dots stay only for cast shadow; tabs are low and the open tab is the page's own paper; the cover is plain
black with one book on a ledge and a compact burst; shelves are one ink ledge with a light hatch below; the dashboard tiles became one bookmarked line.
Then Josef: the paper plate under the Librarian's book looked worse and was dropped. Three ways to stand the book are drawn under the interview (A on the black with a clear halo, B stepping out over the bottom edge, C an open two-page cover). Josef then chose A with Kit 2's full burst and no shadow on the book as the decision for Kit 3; options B and C were removed. The shelf page has the book on the black with the burst converging on a point to its right (as in Kit 2, with a dark faded hole and slightly fewer rays), without its dot shadow (needs Josef's yes: the book object without its dot shadow, on the Librarian's black only). Then Josef: a card is only the card and its dot shadow (the hatched page-thickness layers were removed; hatching stays for the spine and under ledges). Secondary buttons now have a white face and invert on hover (also fixed on Kits 1 and 2). Needs Josef's yes: cross-hatching as the shade
(replaces "dots for shade" in the fixed tier), index tabs, the ribbon bookmark, the large letter.

## 2026-11-18: Folio chosen to refine (Josef: "looks promising")

Kit 3 on the Elevate page is now "Folio, refined", with the shelf front page and the interview question built from it. Added: a stitched
spine, a hatched page edge that wraps the corner, a ribbon bookmark on the one request waiting for the author (no number), a library slip for
that request, a bookend at the end of each shelf, the pick standing on its own ledge, and the phases as index tabs on the interview folio.
Still not decided; fixed-tier flags are listed on the board (hatched edge, tabs, stitched spine, ribbon, bookend, printed cover frame, large letter).

## 2026-11-18: three depth kits for C (Josef: flat and boring, rectangles read as placeholders, drop the diagonal)

Boards "Kit 1 · Stacked sheets", "Kit 2 · Relief" and "Kit 3 · Folio" on the Elevate page. Each is a small UI kit (buttons with hover, press and
disabled, fields, filters or tabs, list rows, surfaces, shelf and books) plus the shelf front page built from it. The Librarian's band is a
plain rectangle in all three; the diagonal is gone. Nothing is decided and no app code changed.

- **Kit 1, stacked sheets:** each important surface and button is the top sheet of a stack of outlined sheets with dot tone beneath; the pick's
  book steps out over the band's top edge. Needs Josef's yes: outlined stacked sheets as a depth cue (7px and 14px offsets); a book overlapping a frame.
- **Kit 2, relief:** raised surfaces and keycap buttons with a solid ink edge and a growing dot shadow; shelves and fields are recessed wells.
  Needs Josef's yes: the hard ink edge (5 to 6px) and recessed paper-sunk wells with inner dot shade.
- **Kit 3, folio:** thick folios with a hatched fore-edge, spine shade, index tabs and a hardcover pick with a printed frame. Needs Josef's yes:
  the hatched fore-edge (line art), tabs in place of filter chips, the printed frame inside the black cover.

## 2026-11-17: direction C, Reading Room (Josef: A's details, but a usable, professional layout)

Josef liked A's details (the page shading, the large letter) and found its cards and lined text box confusing, and wanted a UI that is fast
to use and feels like a professional network, not a game. Board "C · Reading Room" on the Elevate page. Nothing is decided and no app code changed.

- **Layout:** every screen is a top bar, a main column and a side column. The answer is an ordinary text box with Speak, Skip and one red Send.
  Earlier answers are a plain list at the side (reread or fix one there). Titles are a radio list beside one large suggested title. The review
  keeps the red Put it on the shelf in the side card so it is always in view. The shelf has a side column (your book, waiting on you), the
  Librarian's band, topic filters and the shelves.
- **Kept from A, used once each:** screentone falling from the header; a binding shade on the one focal card; the large letter on the question
  and the back cover; the red button pressing into its dot shadow; the ink date stamp; the library checkout card for contact details.
- **Dropped from A:** facing pages, index cards, the ruled-paper text box, the page-turn.
- **Needs Josef's yes:** dot shadow under the focal card and the red button; the binding shade; the large letter (76 to 118px, type table stops
  at 22); the 40px caps stamp word; dotted 2px list rules; and the answers list implying progress (decision 26), shown without a number.
- **Placeholder copy:** "Skip any you like", "Reading what you said…", "Waiting on you / Sam Okafor asked to check out your book", the topic filters.

## 2026-11-17: two ways to elevate the Manga screentone look (waiting for Josef's choice)

Boards "A · Bound" and "B · Inked" on the Elevate page. Each draws the interview question (desktop and phone), the wait after Send, the title
reveal, the book review (and the book being written), "on the shelf" (the moment and at rest), the shelf front page, the checkout contact
details, and hover, press and busy states. Nothing here is decided and no app code changed.

- **A · Bound (print craft):** an open book on a desk; question and answer are facing pages, answers are filed on index cards, titles are
  turned like pages, the shelved date is stamped on the back-cover slip. Needs Josef's yes: the book's dot shadow under pages, cards, slips
  and the red button; a black page inside a white spread for the Librarian's pick; hairline ruled lines on the answer sheet.
- **B · Inked (graphic novel):** every screen is a comic page; the question is a black panel, the answer a panel, filed answers small panels,
  titles wipe in along a diagonal, the shelved moment opens the burst. Needs Josef's yes: black panels beyond the band, the band's slant
  reused, a second burst on the shelved moment, display-size Newsreader italic, a 62px caps stamp word.
- **Both need a decision on progress:** a stack of cards (A) or a strip of panels (B) grows with each answer. That shows progress without a
  number, which decision 26 limits to one late sign.

## 2026-11-09: close-out of the quality notes for the frames

- **Closed (R5-12):** the line under Chapters on the review and on My book now reads "“Show what you said” opens your own words behind
  each chapter. Only you see those." on every frame that carries it, matching the build. The old line called the public summaries private.
- **Everything else tagged Design in rounds 1 to 6 was already applied** to the frames (rounds 1, 2 and 4) or fixed in the build (round 5
  re-check); round 6 has no Design items.
- **Copy the build still owes, written here so it is built from one place** (both are UI items, not frame work):
  - R6-03: when words were left out for a name, say which ones: "I left this out because it named someone or somewhere: Geauga,
    County, Fair. Change those and I'll try again." "Say it again" opens the field with the member's words in it. My book uses the
    same sentence above the question panel.
  - R6-08: the undo question is one sentence for both kinds of change: "Undo these changes? Your book goes back to how it was."
    Add "I won't suggest them again" only when the changes were additions.

## 2026-11-08: quality round 4 applied to the frames (T40)

- **Interview A:** Shape now has two frames (field empty: the red Yes alone; correction typed: red "Send my correction" and a quiet "Yes,
  that's me, ignore this"); the exit link has a words-in-the-field frame ("Send this, then show me my book"); "Back to the question"
  replaces Continue / Continue later; "Saved" no longer sits beside an empty field. New board "A · Other states" draws not enough
  material, writing after a return, a failed load, answer saved but next question missing, the review after rewriting (go back to
  the last version; a rewrite that came back too close) and the other two titles. New board "A · Phone" draws start, reveal (title
  clear of the radio) and review (title, then book at small size, then back cover and stacked quiet links).
- **My book and the rest:** sparks list under the red button when no book exists (R4-06); finding titles and writing book states; undo
  copy with the date (R4-05); the reading caption is Plex 14px sentence case (R4-11); the wait and failed panels lose their headings
  (R4-12); a new chapter hides Now on phones (R4-13); "Nothing from these questions changes your book" (R4-08); a removal's back cover
  card says "Rewritten without this chapter" (R4-10); the back cover is always open and never underlined (R4-03); G4 note fixed (R4-15).
- **Samples (R4-18):** the back cover no longer ends "If you're…, I can tell you…", and sample questions ask one thing without "first".
- **CoverDirections:** it never held the old persona; its sample authors now show full names.

## 2026-11-08: quality round 2 applied to the frames (T39)

- **Applied:** R2-01 (a Removing change type; a back cover that fails says so on its own card, the old one stays, they can still
  confirm), R2-03 (a quiet "Undo these changes" on the done screen and on My book after an update; the book stores its previous
  version until the next change), R2-04, R2-05 (no "round" on screen: "For your next questions", "questions in progress"), R2-06 (the
  reading question is hidden on My book while questions or changes are open), R2-07 (the reason sits under the chip; on a phone
  Proposed only, with "See what's there now"), R2-08 (sparks listed in the interview-in-progress state; the start screen's extra
  line only when sparks exist), R2-09 (the spark control is a 14px sentence-case text link, no plus or tick), R2-10, the copy sheet
  (Changed chapter, "That's enough. Write the changes", a frame for words still in the field, shorter bands, the reading-question
  variant of "nothing came of it"), R2-11 to R2-15, R2-18, R2-23. R2-16 and R2-17 are in `system.md` Additions.
- **Not frame work:** R2-19 (slant on the built interview band), R2-20 to R2-22 are UI or API; nothing drawn changes. R2-02 is code.
- **Judgment:** the shelf line sits once in the proposed-changes note rather than twice; the plus mark on the spark control is
  dropped at that weight.

## 2026-11-08: the sample member is fully invented

- The earlier sample member was modelled on a real alum's news story. Replaced everywhere in the frames (`GrowingG1`, `G3`, `G5`,
  `InterviewA`) by Nora Valdez, an invented person with invented material of the same length: first-person chapters, a back cover,
  the three titles. Nothing in the frames comes from a real person.

## 2026-11-08: growing books and interview frames revised after quality round 1 (T37)

- **Applied from `qc/round-1.md`:** R1-04 (the back cover is a change like any other, written before the confirm step, with its own
  failed state), R1-32 (Remove this chapter on My book, confirm step), R1-33 (the note under the reading answer), R1-34 (the
  reading names the reader, to the author only), R1-36 (writing and failed states on My book and in the round), R1-39 (interview in
  progress and titles waiting), R1-40 (real-length text from a finished book, added words underlined), R1-41, R1-42 (Skip only
  while the answer is empty, with its own frame), R1-44, R1-45 (44px targets), R1-59, R1-60, R1-61, R1-62, R1-64.
- **Interview A also:** start screen (R1-18), review screen (R1-19, R1-21, R1-22, with Remove in place per R1-20), phase names
  First look, Deeper, Check (R1-28), done screen (R1-30). The sample member is now Nora Valdez, a fully invented person (pinball restoration, invented text of real length) so every frame uses real text.
  Directions B and C are left as drawn.
- **Design calls:** undecided changes count as not approved and are listed as "Not decided" under "Stays as it is"; "Not now" on the
  question screen goes back, "No thanks" on My book dismisses; one exit per screen; "the shelf has not changed" once in the band and
  once on confirm. Route is `/my-book`.

## 2026-11-08: growing books frames (T33), under the suspended gate

- **I4 frames go to build as they stand** (`InterviewA2`: Skip, sharper angle). Josef suspended frame approval for the
  unattended run, so this is not an approval of the frames. He reviews the built screens afterwards.
- **T33 frames drawn** on the new canvas page "Growing books", five boards, desktop and phone: My book (no book, draft, on the
  shelf, a round open, changes waiting), adding to your book (reopen, a question with Skip, the wait), proposed changes
  (decide, confirm, confirm with nothing approved, done, nothing came of it), "I have one like this" (every state, in three
  unrelated rows), the reading question (ask, the wait, one proposed change). New patterns in `system.md` Additions.
- **Design calls:** Approve/Decline is a toggle pair that fills ink, never red. The confirm step lists titles by group with no
  numbers. The reading question sits beside the book on My book as a quiet panel; Answer is secondary so the one red action
  stays the book's next step. The wait has no spinner or bar. A round that yields nothing says so and returns to My book.

## 2026-11-07: I4, Skip idea approved; frames under review

- **Josef approved the Skip idea only.** The `InterviewA2` frames (Skip, CHEM 223 angle, student-org angle) are drafts under
  his review and are not approved yet.

## 2026-11-07: "Skip" replaces "Ask me another way"

- **Josef (spec b0aa08d):** the button is "Skip". It goes straight to the next question, for one the member would rather not
  answer or has nothing to say to. Quiet, beside Speak, never red. Skips are never shown or counted: no "skipped" state and
  no tally. Frame 1 of `InterviewA2` shows it; the change-of-angle frames stay, with Skip in the action row.

## 2026-11-07: the interview adapts (I4), revised after Josef's review

- **First draft dropped (e46fe34, six frames):** the mirror ("feels like flattery"), the situation cards and "Help me find
  it" with its "last Saturday" question. Josef: don't design for scared people; these are professionals; help them with
  better questions, not easier ones. Spec: trove.md §4 and §9.9 (7289adb).
- **Now three frames on `InterviewA2`:** "Ask me another way" (quiet, beside Speak, on every question; red stays on Send
  answer), and two frames of the change of angle: a sharper question on the band anchored in a real context ("In your CHEM
  223 project, what did you have to figure out that the lab manual didn't tell you?"), then the same pattern in another
  context (a student org). The screen is identical whether the member pressed the button or the answers ran thin, so
  nothing marks them as struggling. No reassurance or praise anywhere.
- **Copy check of direction A:** removed "Take a moment with each" (reveal) and "as you would to a friend" (recording).
  Everything else is plain and direct. Not approved yet.

## 2026-11-07: books show the full name

- **Orchestrator, after Josef talked to the advisor (ce8f005, trove.md §3 and §9.1):** a book shows the author's full name,
  not just the first name. Nothing else from the résumé (no headline, employer, genre or count).
- **Fit:** the name stays Plex 600, 9.5px, caps, +0.12em, now at line-height 1.3. It wraps (also at a hyphen) and stops at
  3 lines with an ellipsis. "ALEXANDRA OKONKWO-BRENNAN" takes 3 lines on the shelf and small books, 2 on the large one
  (measured in the app with real fonts; the first canvas check said 2, 3, 1). The aria-label carries the whole name. Updated in system.md, tokens.css and the design-system boards.

## 2026-11-06: interview screens (T5), three directions

- **Orchestrator T5:** static desktop screens for the interview in the manga system, three directions, nothing on hold
  drawn (no margin notes, bursts, card drawer, bookmark tabs, pencil-to-ink spine, stamp or live filler cleanup).
- **New canvas page "Interview"**, boards `InterviewA`, `InterviewB`, `InterviewC`. Each shows nine frames: start,
  question (typing, recording, transcript, later in the Dig with the exit link), shape moment, reveal (three white-cover
  titles), book review, coming back. A: the question on a black band. B: a literal comic page (see below). C: speech bubble on a screentone ground, phase as a top rail.
- **Rules kept:** first names only, no counts or percentages, phase as a label (Sweep, Dig, Shape), "Saved" tiny and
  silent, one red action per screen (Stop while recording), halo dots never behind running text.

- **Josef: replace B with something more literally comic.** B is now "Comic page": every screen is a page of
  heavy-bordered panels on white gutters, narration caption boxes (The Librarian, You, What I heard, Previously), the
  Librarian's question in a speech balloon on a screentone panel, the member answering from a balloon. Phase is a
  tag in the page header, the reveal is three cover panels, chapters are panels.

**Chosen: direction A (the question band).** B (comic page) and C (speech bubble) stay on the canvas for reference.
Build spec: `docs/design/shelf/project/InterviewA.dc.html`, ten frames at 1280x800.
- **Done frame approved as drawn** ("Your book is on the shelf.", "Go to the shelf", quiet "See my book").
- **Resume frame:** "Start that part again" is removed. It now has "Continue" (red) and a quiet "Continue later", which
  leaves the interview.

## 2026-11-06: cover direction G, watercolor landscapes (from Josef's reference)

- **Josef:** use the reference (red watercolor sun, blue misty ridges, reflection) as the art style for the book
  covers, three covers, and not only Japanese.
- **Board `CoverLandscape`** on the Covers page: `Alpine lake` (vermilion sun, blue ridges, pines), `Headland`
  (amber sun, teal sea, lighthouse, sailboat), `Mesa` (gold moon, terracotta mesas, rain pool, saguaros). No torii,
  bamboo or characters. Same system for all: title on white at the top, a large sun or moon, three layered ridges
  that thin into mist, a rippled reflection, a gradient mask to white under the title, paper grain.
- **Personalization:** the member picks the place and palette, never the topic. The scene set can grow.
- **Cost note:** SVG filters again; render each cover once to a 244x356 WebP.
- **Cover art is not UI:** the lake sun is a vermilion (`#E4442E`) close to, but not, the UI red.

Pending Josef's feedback.

## 2026-11-06: cover direction F, cherry blossom watercolor

- **Josef:** a cherry blossom watercolor cover: paint over the white cover that fades upward with no cut between the
  title area and the picture. Polished and beautiful.
- **Board `CoverWatercolor`** on the Covers page. A pastel two-color wash, a plum branch, layered blossoms and
  drifting petals, masked to white by the title; five palettes (sakura, wisteria, apricot, rain, matcha), mirrored
  branches and a seed per cover. Build steps are shown. Titles take each palette's dark color (AA on white).
- **Cost note:** the art uses SVG filters, so render each cover once to a 244x356 WebP instead of live on the shelf.


## 2026-11-06: cover directions, round 1

- **Josef:** explore the book cover. White ground for contrast, title at the top, titles can carry color, art
  from Japanese art forms, personalized by choice (not by what the book says), designed for the size it shows at.
- **New canvas page "Covers"**, board `CoverDirections`: five directions, each shown at 236x344, 122x178 (five
  variants) and 92x136: A seigaiha waves, B sumi-e bamboo wash, C sashiko stitched cloth (asanoha, shippo, kikko,
  yabane, uroko), D kamon crest, E ukiyo-e Fuji with bokashi sky.
- **Cover rules in the exploration:** title top in Newsreader 600 in the cover color (all cover colors have AA
  contrast on white and avoid the UI red); art in the lower 36%; first name at the foot; vector art so it is sharp
  at 2x (244x356); no Japanese characters. Cover art needs a Fixed-tier decision before joining system.md.

Pending Josef's pick (one, or a mix).

## 2026-11-06: the design system (Manga screentone), and the docs enforce it

- **Chosen:** manga B2 (top navigation, B's banner and shelves, the red framed button) is the reference screen.
  Black ink on white paper, dot tone for shade, one burst, one red for the primary action only.
- **New canvas page "Design system":** the reference shelf and a sign-in screen, then Foundations, Components
  (actions and forms; content and structure) and How to use it. Authoritative rulebook: `docs/design/system.md`.
  Reference CSS: `docs/design/system/tokens.css`.
- **Red changed to `#D42A27`** so white text passes AA (5.0:1).
- **Balance:** rules sit in three tiers: fixed (human's yes), defaults (follow or explain), free (design new
  things, record them under Additions). CLAUDE.md, CONTRIBUTING.md, architecture.md and plan.md now point to it.
- **Not done:** `web/src/ui/styles.css` still has the old placeholder tokens. UI Implementation ports
  `tokens.css` into it (the old `--color-*` and `--space-*` names are aliased, so it is a drop-in).

## 2026-11-06: identities, pick a craft idea before the layout

- **Josef:** C (circulation desk) has a real identity but feels too simple. Decide the material, pattern and
  craft idea first, then the layout. Explore printed media across eras and art styles (text, cartography,
  literature) as small mood boards.
- **New canvas page "Identities"**, six boards (`Ident1`..`Ident6`), each with a plate, what we borrow,
  palette, type and a shelf fragment with white books: 01 four-colour pulp (comic halftone), 02 survey
  chart (nautical cartography), 03 banded paperback (1930s-60s Penguin-style grid), 04 wood-type
  broadside (letterpress), 05 riso zine (two-ink overprint), 06 engraved plate (natural history).

- **Round 2 (Josef: 03 too basic, 04 ugly):** replaced 03 with bookcloth and foil (woven navy cloth, gold
  foil stamping, ribbon marker, marbled endpaper) and 04 with cyanotype blueprint (drawing sheet, dimension
  lines, title block, one amber). Polished 01 (comic panels and gutters), 02 (soundings, shallows, cartouche,
  scale bar), 05 (registration marks, test strip, halftone) and 06 (second row of specimens, scale bar).
  Every board now has a Textures row, a layer to mix and match across identities.

- **Round 3 (Josef: not 03 and 04):** replaced them with other countries' comic textures: 03 manga
  screentone (Japan: dot tones, focus lines, slanted gutters, one red hanko seal) and 04 ligne claire
  (Franco-Belgian: even line, flat colour, brick and roof-tile patterns, flat shadows). Bookcloth and
  cyanotype are dropped.

- **Round 4 (Josef: 04 ligne claire looks like kindergarten):** replaced 04 with Bauhaus primer (1920s German
  design school: circle, square and triangle in vermilion, ochre and Prussian blue, overprint, lowercase
  Jost, one diagonal black bar for the call to action, a visible grid). Textures: overprint, concentric arcs,
  quarter tiles, rule and bar. Ligne claire is dropped.

- **Manga screens (Josef: pick manga screentone, no Japanese letters):** new canvas page "Manga screens",
  three desktop layouts of the shelf page, all Latin type only (Barlow Condensed, Newsreader, Plex), no
  hanko character, one red square used only for the main action: `MangaA` the page (slanted-gutter panels,
  focus lines behind the Librarian pick), `MangaB` the strip (black rail, one dark band, long shelves on
  inked ledges), `MangaC` the spread (open book: pick and contents left, two shelves right, index tabs).

- **Manga B polish and B2 (Josef: polish B, add a version under it with navigation up top like A):** B's banner
  is now a black band with a slanted lower edge and a double rule, a dotted halo and fanned lines behind the
  book, a larger title, a ruled reason line and a "thirty-minute video call" note. `MangaB2` keeps B's banner
  and long shelves but moves the navigation to the top bar, as in A, so the shelves get the full width
  (nine books a row). B's side rail stays on `MangaB` for comparison.

- **"Ask to check out" button (Josef: too decorative, red at rest):** `MangaBtn` shows four flat red buttons with
  rest, hover and pressed on the dark band and on paper: flat red, red with an ink frame, red with a plain
  arrow, and red with Plex sentence-case type. No shadows, tilt or texture. Red stays reserved for this one
  action on any screen.

- **Button chosen:** option 2 (red, thin ink frame; white frame on the dark banner) is now on `MangaB2`.

Pending Josef's pick (one, or a blend).

## 2026-11-06: direction 5, working tool (a clean break from the material looks)

- **Feedback:** the marble, cloth, shadow and daylight directions all read as games or toys. Trove is
  professional software and should feel mature and considered. Start over.
- **Now:** a neutral white and gray interface with one deep blue (#17406B) for the single main action,
  IBM Plex Sans for the interface and Newsreader only for book titles. Left sidebar (Shelf, My book,
  Checkouts, Past meets), a small topic search in the top bar, a quiet Librarian recommendation row,
  shelves as rows of books standing on a thin ledge, and a persistent detail panel on the right
  (chapters, Ask to check out). No decoration, no texture.
- **Books are plain white** (spine hinge, page edge, soft shadow) until Josef settles the cover design.
- New canvas page "Working tool": `ToolShelf` (interactive), `ToolPhone`.
- Josef: "structure and layout are right, but boring and basic." Two static desktop options added to the
  page for character, energy and warmth: `ToolDark` (B, after hours: dark ink room, amber lamplight on
  white books, a 3D-tilted Librarian pick) and `ToolCirc` (C, circulation desk: ink rules, highlighter
  yellow, stamp blue, mono labels, index-card recommendation).

Pending Josef's review.

## 2026-11-06: direction 4, daylight library (from Josef's photo of a Scandinavian library)

- **Reference:** a pale-wood Scandinavian public library: curved ribs overhead, tall arched windows
  with slender slats, low slanted display units with books face out, sun striping the room.
- **Feedback on the first attempt:** it copied nothing of the photo (stepped blocky units, huge empty
  areas), had no real light, and the brown read greenish. Rebuilt.
- **Now:** honey and peach birch (never beige or olive), gold-white daylight, a vault of diagonal
  ribs as the header, two arched windows (the Librarian's pick stands in the first), full-width
  slanted shelf units with six books each, and diagonal stripes of sun across the whole page. Dense
  by default: no staggered empty steps.
- **Search is a small field in the ceiling.**
- Artboards on the Designs page, row 5: `ScandiPage` (interactive), `ScandiPhone`, `ScandiNotes`.

Pending Josef's review.

## 2026-11-05: back to layout, in black and white

- **None of the Carrara, light-and-shadow or cloth-and-oak looks is the one.** They stay on the
  canvas's first page ("Designs") for reference.
- **Start from form only.** New canvas page "Wireframes": four black-and-white layouts of the shell
  homepage, plain shapes, no material or color: `WireA` (feature, then shelves), `WireB` (side
  rail), `WireC` (bookcase), `WireD` (black split).

Pending Josef's pick.

## 2026-11-05: direction 3, the Carrara page

- **Chosen: option A, the polished white Carrara ledge.** B and C stay on the canvas for reference.
- **Keep the marble shiny and thick,** a little thinner than the study (front edge 50px down to
  42px). Thickness is a tweak on the artboard (slim, regular, thick) for Josef to try.
- **Experiment with reflections:** the books mirror into the polished top, and a lifted book's
  reflection drops away from it. Strength is a tweak (off, soft, mirror).
- **Bring in the light and shadow work from direction 2:** one light from the upper left, depth
  with meaning (carved nav and search, raised buttons, the open book held over the wall), and
  window light only on the Librarian's pick.
- **Search lives in the header,** small. The page opens on the Librarian's pick.
- Artboard: `MarblePage.dc.html`, row 4 of the canvas.

Pending Josef's review.

## 2026-11-05: direction 3 (marble)

- **Search is never the main element of the shelf page.** Making the search bar the hero repeated
  FoundersCircle, which the team disliked. Search stays available but secondary.
- **Direction 2 (light and shadow) is not the one** either; it stays on the canvas for reference.
- **New idea: marble is the material of the shelves.** First step: one shelf with a few books, in
  three options, before any full page. Third row of the canvas: `MarbleA` (polished Carrara
  ledge), `MarbleB` (green marble niche), `MarbleC` (honed pink slab with arch and cube bookends).

Pending Josef's pick.

## 2026-11-05: the shelf page, direction 2 (light and shadow)

- **Direction 1 (cloth and oak) is not the one.** It stays on the canvas for reference.
- **Avoid the tells of AI-made design.** The list is in `docs/design/ai-tells.md`. It guides
  choices without banning basic elements.
- **New direction: shadow is the star.** Very minimal, mostly warm whites; light and shadow
  carry the structure. Slightly retro, slightly Bauhaus, sparing with color. Functional, not a
  gimmick: every depth means something (carved, wall, resting, lifted, held, pressed).
- Built as the second row of the same canvas: `ShadowShelf`, `ShadowPhone`, `ShadowSystem`.

Pending Josef's review.

## 2026-11-05: the shelf page

- **Rejected:** the three poster-style directions from T1 (flat SVG-like covers, layouts designed to
  be looked at rather than used). Removed from `docs/design/`; they're in git history at `bc87a6f`.
- **Start from the user and the interface,** then the look. The shelf is a working screen: search a
  topic, browse, open a book to see its chapters, ask to check it out.
- **One direction only,** polished, built as a canvas of screens rather than a single HTML page:
  `docs/design/shelf/` (published at https://claude.ai/artifact/33uQU8UKZ4gtxcv4ZNof1D).
- **Books are objects, between 2D and 3D.** They have depth, light and shadow and must run efficiently in a
  browser. The design fakes the depth in CSS; the 3D build belongs to UI Implementation, using the
  book object artboard as the spec.
- **Feel:** modern, but serif and library-like, in warm colors.

Pending Josef's review of the new canvas.
