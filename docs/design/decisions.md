# Design decisions

Decisions Josef has made about Trove's look and feel. Newest first.

## 2026-11-19: strata, finished (canvas page "Final designs"), waiting for Josef

- **Josef:** strata has potential but the execution felt unpolished, game-like, and the arrangement not thoughtful.
  An engraved-line evolution was tried and rejected ("much closer to the original blocky strata").
- **Done** (`docs/design/art/strata/final.py`): the same slabs, finished. No bevel; a hairline paper seam between
  courses; little colour jitter. One muted family of inks, the sun the only warm note. Composed: one hero peak on the
  right third with shoulders, the sun set against its flank, sage framing the left, stone and haze stepping back,
  mist between planes, a calm lake with a glint path under the sun, firs built from courses in a varied cluster.
  Boards `FinalCover` and `FinalBook` (book screen B with the art).
- **Round 2 (Josef: sloppy, pyramids, prefers round 3's colours; then: keep the style, improve only the scene).**
  A masonry rewrite of the blocks was tried and rejected. Kept the round 1 finish; round 3's inks are back; the
  massif is a broad summit with a rounded shoulder and a second summit, the sun in the notch, a coral peak in the
  middle distance; firs laid without ragged ends.
- **Round 3, the cover first (Josef: members pick a cover; the inside scenery follows it, so the cover must be loved).**
  The cover is now composed for its own shape: one big centred massif with a notched summit and a stone cap, a large
  sun behind it like a halo, haze low on both sides, a still lake mirroring the peak, two small firs. Drawn at 2x.
  The book's inside pages are to follow from the cover (not yet redone to match).
- **Josef's rule: blocks touch by default.** No paper seam between courses and no holes where two forms meet (they
  share one boundary in the renderer, `render(touch=True)`). Spacing is allowed only as a design choice: the sparse
  river or lake, mist between ridges, an edge against open sky.
- **Then: slabs stay slightly 3D, with small uniform joints.** Each slab has a faint lit top edge, a soft underside
  and a faint end shade, and a uniform hairline joint (1px at 2x, half a CSS px) under every course and at the end of
  every slab, so each reads as its own piece. Holes and uneven gaps stay out; the joint is the same everywhere.
  Then (Josef: too much white) the joint is no longer bare paper but the slab's own ink lightened 45% toward paper.
- **Round 4 (Josef: preferred the Fresh directions strata).** The finish experiments (touching blocks, joints, tinted
  seams, muted inks) are set aside for this art: `final.py` now draws with round 3's renderer settings, inks and
  elements exactly (bevelled slabs, jitter, ragged ends, groves, `render(touch=False)`), and only the scenes are
  new: the cover's single clean summit with the sun beside it, and the title page's massif, coral peak, sage slope
  and groves. The renderer options added along the way stay available but off for this art.
- **Round 5, laid clean (Josef: messy, weird shapes; plan it properly).** Same look and inks; a `clean` mode in the
  renderer: no slab shorter than a slab and a half, touching forms share one boundary (no holes, no slivers of the
  form behind), tiny leftovers merge into a neighbour and lone specks are dropped, ragged steps only against open
  sky. Skylines from smooth noise (`Ridge(smooth=True)`), calmer tone flicker, the snow cap a snowline under the
  summit, no stripe on the small peaks, clean feet (the cover's art ends on a straight line, the page's runs off
  the page). Checked by zoom on the summit, sun edge, middle peak and foot before publishing.
- **Cover typography (Josef):** the title set left, the full name right under it at the top (class `cov-final`), so
  the art fills the rest of the cover and runs off its foot. The art is recomposed for the taller space. Fixed-tier
  flag as before: the system sets the name at the foot; this moves it under the title.

## 2026-11-19: the book screen is B, the book opens (approved)

- **Josef approved book screen B** (`FreshReaderOpen`) and asked for it to go to implementation **without art**: the art
  inside the book and on the covers is still to be decided. The build spec is in `docs/design/system.md`,
  "Handoff: the open book (book screen B)".
- **Josef: opening is 3D.** Clicking a book on the shelf zooms in on it and opens it up in 3D. He wants a demo before
  anything is pushed, and will likely workshop it with the implementation session.

## 2026-11-19: three ways to show one book (the book screen)

- **Josef:** not yet sure how the book focus screen should work. Besides the full book page, two more UI approaches,
  one of them the current app's mechanic (the book opens to its pages) optimised and polished.
- **Canvas page "Fresh directions",** to the right of the strata row, under the note "Book screen":
  - **A, the book page** (`FreshBookStrata`): a page of its own with the book's landscape, the cover as a window
    onto it, the chapters below. Linkable and shareable.
  - **B, the book opens** (`FreshReaderOpen`): the current `BookReader` mechanic rebuilt. Title page with the art
    on the left, contents with one-line summaries on the right; choosing a chapter turns the page and moves the
    contents to the left page. Chapter tabs in the top bar, arrow keys, a lifted page corner. Ask to check out sits
    under the book, the same on every page. Round 2: the open book sits over the shelf shaded in dots, as in C,
    instead of the dark backdrop; the top bar and the button strip are paper.
    Round 3: the page keeps the library's header, and everything for the book is inside the book: Close and the page
    tabs as running heads, page turns at the feet, Ask to check out on the title page and under the contents.
  - **Josef removed "I have one like this" (sparks)** from the book screens (B and C). `docs/trove.md` still plans
    sparks (I5); that product change is the orchestrator's to make in the plan.
  - **Round 4, B built as a book** to be animated as paper: cover boards in the book's own ink, a spine at head and
    foot, stacked page edges, top pages bowing into the gutter (shaded in dots). No page feet (the tabs at the head do
    that job), no redundant page labels, and the shelf behind at 60% opacity.
  - **Josef's rule, from now on:** no explanatory sentences in the UI (such as "A thirty-minute video call, if the
    author says yes."). Good UI should not need a sentence for each interaction. Removed from B and C.
  - **Ask to check out is never under a chapter** (Josef: it reads as checking out that one chapter). In B it sits on
    the title page and under the contents on the left page, so it always belongs to the whole book.
  - **Josef removed C** (pulled from the shelf). The choice is now between A and B.
  - **Round 5, B made minimal for 3D:** each page is one flat plane carrying its own content, so a turn rotates the
    plane about the spine and the content moves with it. Under the pages, one board in the book's ink, the spine at
    head and foot, one sheet of page edge. The round 4 curves and stacked edges are gone.
  - **Round 6, strata art drawn for B** (`docs/design/art/strata/book_b.py`): composed for the title page, not cut from
    A's panorama. The page's text holds the upper left; the teal peak and sun climb the right edge, ranges step back
    to a hazy distance, a lake with reflections and an islet crosses the foot, groves frame both shores. The
    contents spread shows the same place from further back under the list and the button.
  - **C, pulled from the shelf** (`FreshReaderPanel`): a side panel over the shelf, which stays in place shaded in
    dots with the book's slot left open. Previous and Next step along the shelf; chapters open in place; a link to
    the full page (A).
- Generated by `docs/design/shelf/reader_boards.py`. Not decided: which one (or which mix) the app uses.

## 2026-11-19: typography for each cover direction, waiting for Josef

- **Josef:** adapt the typography on each cover so it looks polished and well rounded.
- **Done on the canvas page "Fresh directions"** (boards `Fresh`, `FreshLand`, `FreshNew`), in CSS on the live
  title and name, still only the three house faces. Each cover has its own setting:
  marbled paper, one bookbinder's label holding the centred title and the name under a short rule; letterpress, the
  name now tracked rule to rule under a heavy and a hairline rule (`press2.py`), so it reads on the shelf;
  block print, title and name centred on the block; gouache, the title in Barlow Condensed caps in the poster's navy
  and the name reversed out of a navy strip; coloured pencil, a lighter Newsreader in graphite with the name under the
  title; watercolour, Newsreader italic in the indigo of the washes, centred, name under it; cut paper, centred navy
  title and the name in cream on the dark paper at the foot; stipple, the title in spaced caps and three gold dots
  above the name. Titles use balanced line breaks.
- **Fixed-tier flag:** the book title is fixed as Newsreader 600 in ink, top left, and the name as Plex caps at the
  foot. These covers change face, weight, case, colour, alignment and the name's place. Needs Josef's yes before any
  of it goes into the app. The cover inks are art colours taken from each picture; none is the UI red.

## 2026-11-19: two more directions (cut paper, stipple) and three touch-ups, waiting for Josef

- **Josef:** the watercolour is too realistic, like a photograph, so it reads cheap; the coloured pencil is too
  simple; the gouache poster is too childish and its shapes too simple. Two new polished directions, and touch up
  those three.
- **Touch-ups, board `FreshLand`:** gouache round 2 (`gouache2.py`: an alpine lake drawn like a travel poster, with
  shaded peaks, streak clouds and framing pines); pencil round 3 (`pencil3.py`: deeper tones, a cabin and jetty, a
  far shore of firs, reeds, two more pencils); watercolour round 2 (`wash2.py`: the scene as single brushstrokes
  with bare paper between them, not a rendered view).
- **New, board `FreshNew`:** 7. **Layered cut paper** (`papercut.py`): the white cover is the top sheet of a stack,
  cut away to show the layers; moon, stars and window are holes to a glow. 8. **Stippled ink** (`stipple.py`): dots
  only, in two inks, the site's dot shading taken all the way.
- **Flag:** the cut-paper cover uses soft shadows between sheets. The system rule is dot tone for shade, never
  blur; that rule is about the UI, but Josef should decide whether cover art may break it.

## 2026-11-19: two landscape covers that clear to white (gouache, coloured pencil), waiting for Josef

- **Josef:** two more directions with environment art in different styles, edge to edge, that fade or cut to white
  so the title sits on white uninterrupted.
- **Canvas page "Fresh directions"**, board `FreshLand`, at 472 and 122 px wide:
  4. **Gouache poster** (`gouache.py`): dawn over a river town; the sky's top band ends in a hard cloud line (the cut).
  5. **Coloured pencil** (`pencil.py`): a farm road to a lit house; strokes thin out to bare paper (the fade).
- **Pencil, round 2 (`pencil2.py`):** Josef found round 1 interesting but childlike. Redrawn with four muted
  pencils, one hatching direction, tone from line density, crisp ridgelines that dissolve into paper, and one warm
  mark (a lamp and its reflection). The scene is now a lake at dusk. Round 1 (`pencil.py`) is kept for reference.
- **6. Loose watercolour (`wash.py`), added at Josef's request:** one wet-in-wet dusk sky over still water, its top
  edge drying ragged on bare paper. Unlike direction G (sun, three ridges, SVG filters) the sky is the subject and
  the paint is modelled as pigment on paper (pooled edges, granulation, backruns, dry-brush sparkle).
- **Title and name:** the title is the standard Newsreader title on plain white. The name at the foot sits on a
  white knockout over the art, as on the Strata covers.
- **Fixed-tier flag, waiting for Josef:** art on the white book object, as with every cover direction so far.

## 2026-11-19: three fresh cover directions (marbled paper, letterpress, block print), waiting for Josef

- **Josef:** pause the voxel covers. Three other directions tied to paper, books, drawing or painting, one cover
  each, each going somewhere different, thinking about what the site should feel like and what the visuals are for.
- **What the covers are for (my reading, for Josef to correct):** make what a person knows feel like a made object
  worth picking up; tell books apart on a shelf at 122 px; let a member express themselves by choice, never by
  status; stay calm beside the white UI and its one red action.
- **Canvas page "Fresh directions"**, board `Fresh`, each at 472 and 122 px wide on "The Night Shift Knows":
  1. **Marbled paper** (`marble.py`): a full sheet with the title and name on pasted labels. No two sheets match.
  2. **Letterpress** (`press.py`): the title in wood type is the picture, in two inks. Art comes only from the
     author's own words, which fits the grounding rule.
  3. **Block print** (`block.py`): a carved night scene in black and one second colour.
- **Fixed-tier flags, waiting for Josef:** all three put art on the white book object. Marbled paper covers the
  whole cover and moves the title onto a label. Letterpress replaces the Newsreader title with printed display
  type (the live title stays for screen readers). No cover ink is the UI red.
- **Open product question:** who picks what (palette, inks, scene), unchanged from direction H.

## 2026-11-18: cover direction H, round 3: back to Strata, solid and detailed, waiting for Josef

- **Josef:** the 3D voxel look doesn't work well. Go back to the Strata slabs and refine them with more detail and a
  more solid feel. The voxel page stays on the canvas for reference only.
- **Now (`docs/design/art/strata/`):** courses sit tight with no paper between them; each slab has a lit top edge, a
  shaded underside and occasional seams, so it reads as laid stone. Courses are finer (2px on the shelf, 1.5px on
  small books). New detail: strata bands on a peak, a pale far ridge for depth, water that mirrors the peaks above it,
  and groves standing on trunks. Mist pales slabs toward paper before any go missing.
- **Shown:** canvas page "Strata covers", board `StrataCover2`: design 1 ("the lake", `cover_lake.py`) at four sizes,
  and the seven other designs redrawn with the same renderer.
- **Still open:** the Fixed-tier yes for art on the book object, and who picks a design.

## 2026-11-18: cover direction H, round 2: voxel scenes (replaces the 2D Strata look), waiting for Josef

- **Josef on round 1:** too rough and basic. These are book covers, not page art: eventually dozens of designs
  members pick from, each leaving room for the title. Make it much closer to the reference, a 3D scene of small
  cubes, polish it, present a book design, and iterate until it is as good as the original.
- **Now:** the art is a real voxel scene rendered in Blender (`docs/design/art/voxel/`): about 96,000 slab cubes,
  a raking sun from the left, white sky, rendered on white. Design 1, "the valley", is on the canvas page "Voxel
  covers", board `VoxelValley`, at 472, 236, 122 and 92 px wide and on a shelf beside white books.
- **Cover layout:** the top third is empty sky for the title, the art sits in the middle, and the foot is white for
  the full name. Title and name keep white knockouts for long text at small sizes.
- **Still open:** everything listed under round 1 (the Fixed-tier yes for art on the book object, who picks a
  design). The Strata page stays on the canvas for reference.

## 2026-11-18: cover direction H, Strata (stacked-slab landscapes), waiting for Josef

- **Josef:** experiment with the stacked-slab landscape art from his references (mountains, water and trees built
  from horizontal bars), refined, on the cover and inside the book too, so the white UI lets the art be the hero.
- **Canvas page "Strata covers"**, boards `StrataBook` (one book opened: the cover is a window onto its landscape,
  which runs across the top of the book page), `StrataShelf` (nine covers on a shelf, one book at three sizes, how
  the art is made) and `StrataPlaces` (phone book page, the interview reveal, the checkout once the author says yes,
  the meeting waiting room). Source: `docs/design/art/strata/`.
- **Refined from the reference:** one course height per size (4px book page, 2px shelf) instead of mixed noise; seven
  ink families; light from the left with a clean shadow face; mist made by leaving bricks out, never blur.
- **Needs Josef's yes (Fixed tier):** the book object is "white, outlined, a dot shadow, title and full name only".
  Strata keeps all of that and adds art on the cover, so it changes a Fixed rule. Title and name sit on white
  knockouts where they meet the art.
- **Product questions for Josef, not decided:** who picks a book's landscape (the member, Trove, or the member from
  a short set); whether the reveal's three titles share one landscape or each gets its own; whether the art appears
  beyond the book page (checkout, meeting) at all.
- **Cover art is not UI:** coral (`#E87457` family) is the warm note and is not the UI red.

Pending Josef's feedback.

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
