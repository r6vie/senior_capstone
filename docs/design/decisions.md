# Design decisions

Decisions Josef has made about Trove's look and feel. Newest first.

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
