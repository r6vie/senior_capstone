# Trove design system

The look is **Manga screentone**: black ink on white paper, screentone dots for shade, one burst of
lines for emphasis, and one red for the one thing to do next. This file is the rulebook. The picture
of it is the **Design system** page of the design canvas (`docs/design/shelf/`, published at
https://claude.ai/artifact/33uQU8UKZ4gtxcv4ZNof1D). The code of it is
[`docs/design/system/tokens.css`](system/tokens.css).

Read this before you build or change any UI. Everything here sits beside the product rules in
`CLAUDE.md` and `docs/trove.md`, which come first.

## The one-minute version

- Ink (`--ink`) on paper (`--paper`). White (`--white`) is for things you can pick up: books, fields,
  bubbles, panels.
- **Red is the primary action, and the Librarian's hand.** One red button per screen. Errors, success and
  selection are never red. The one exception (2026-11-19, Josef): the Librarian's handwriting and marks in the
  interview are red, as thin line-work only, never a filled shape, button, tag or state. See Additions, "The
  Librarian's notebook".
- Three faces: **Barlow Condensed** (short caps labels), **Newsreader** (book titles, page titles, the
  Librarian's voice), **IBM Plex Sans** (everything you read to do a task).
- A small 5px corner radius (approved 2026-11-19, Folio); the search field and avatar are square; a rounded bubble only for speech.
- Shade is made of dots (tone) for cast shadows and diagonal cross-hatching on spines and under ledges (approved 2026-11-19, Folio), never a blur, a gradient or a glow.
- One focal point and one primary action per screen. Left-aligned.
- Every state is designed: rest, hover, pressed, focus, disabled, busy, error, empty.

## How strictly to follow it: fixed, default, free

A system is a set of decisions, not a cage. Each rule below belongs to one of three tiers.

**Fixed. Change only with a human's yes.** The identity. If these move, the product stops looking like itself.
Fixed isn't frozen: when one of these turns out to be a real limit, raise it with the human and record the change here.

- The palette and the red rule.
- The three faces and their jobs; caps only on short display-face labels.
- 5px corner radius; the search field and avatar are square; the bubble exception as above (Folio, approved 2026-11-19).
- Dot tone for shade; no blur, gradient or glow.
- The book object: white, outlined, a dot shadow, title and full name only.
- Every product rule in `CLAUDE.md` (names, no counts or ratings, no cold messages, no performance features).

**Defaults. Follow them, or say why not in the PR.** Good answers we already found.

- The component recipes in `tokens.css` and on the canvas, with all their states.
- The screen pattern: top bar, then the Librarian's band, then shelves; 44px gutters.
- The spacing scale and the 48px (`--control`) and 44px (`--tap`) sizes.
- One focal point, one primary action.
- Specific copy: buttons say what they do; anything invented is marked as a placeholder.

**Free. Design it, then add it back.** Screens and parts we have not drawn yet: the interview, checkouts,
the meeting, settings, anything new.

1. Compose from the tokens and the existing recipes first.
2. If no recipe fits the task, design a new pattern. Keep to the tokens, the line language (2px / 3px
   ink) and one focal point.
3. Record it under **Additions** below, with the task it solves and a small snippet, so the next
   person reuses it rather than reinventing it.
4. A new idea earns its place by solving a real task, not by adding flavor.

If you are unsure whether something is fixed, ask the human (see "Product questions" in CONTRIBUTING.md).
Don't decide the identity in code.

## Tokens

Defined in `tokens.css`. In feature code use the variables, never raw values.

| Group | Tokens | Rule |
|---|---|---|
| Color | `--paper` `#FAFAF7`, `--paper-sunk` `#F0F0EB`, `--white`, `--ink` `#111`, `--ink-2` `#55554F`, `--ink-3` `#8C8C89`, `--rule` `#C9C9C6`, `--red` `#D42A27` (`--red-hover`, `--red-press`) | `--ink-3` is for disabled borders only, never text. `--rule` is text only on ink. |
| Context | `--fg`, `--bg`; wrap a dark region in `.dark` and every component follows | Dark regions are for the Librarian's band and the sign-in panel, not whole pages. |
| Type | `--font-display`, `--font-serif`, `--font-sans` | See the type roles below. No monospace in product UI. |
| Space | `--s-1`…`--s-8` = 4, 8, 12, 16, 24, 32, 44, 64px | Page gutter is `--s-7`. A value off the scale is a layout smell. |
| Line | `--line` 2px (controls, book outline), `--line-heavy` 3px (panels, bubbles, dialogs) | |
| Radius | `0` default; `--radius-pill`; `--radius-bubble` | See above. |
| Size | `--control` 48px, `--tap` 44px | Nothing you can press is smaller than `--tap`. |

Allowed text/ground pairs (WCAG AA): ink on paper 18:1; ink-2 on paper 7.2:1; white on red 5.0:1; paper on
ink 18:1; rule on ink 11.4:1.

### Type roles

| Role | Face | Size / line | Case |
|---|---|---|---|
| Page title | Newsreader 600, −0.015em | 48–54 / 1.02 | Sentence |
| Shelf name | Barlow Condensed 800, +0.04em | 30 / 1 | CAPS |
| Nav, buttons | Barlow Condensed 600–700, +0.10–0.14em | 17 / 1 | CAPS |
| Caption chip | Barlow Condensed 600, +0.14em | 14 | CAPS |
| Book title | Newsreader 600 | 13.5 shelf, 27 feature | Sentence |
| Book title on a strata cover (Josef, 2026-11-20; sizes 2026-11-21) | Barlow Condensed 800, +0.01em, line-height 0.92, set left | 29 on the 176 shelf book (78 on the 472 board cover, the same book scaled) | CAPS, no knockout; the full name right under it (10px gap), Barlow Condensed 700 13px caps +0.16em in the cover's ink, on a white knockout where the art rises into it |
| Book author (full name) | Plex Sans 600, +0.12em, line-height 1.3 | 9.5 | CAPS, wraps to 4 lines |
| The Librarian's voice | Newsreader italic | 19–22 / 1.3 | Sentence |
| Body, labels | Plex Sans 400/600 | 15–16 / 1.5 | Sentence |
| Hint, secondary | Plex Sans 400, `--ink-2` | 14 | Sentence |

A sentence is never set in caps.

## Tone and texture

- `.tone-fine`, `.tone-mid`, `.tone-dense`: dot grounds. `.tone-fade` dissolves one. Tone is a ground and a
  shadow, **never behind running text**.
- `.burst`: fanned lines. **Once per screen, behind the Librarian's pick only**, inside `.dark`. With `.halo` behind the feature book.
- The book's shadow is offset dots. The shelf board is `.ledge`. There are no blur shadows anywhere.

## Components

All in `tokens.css`; see the canvas for every state. Markup is in the boards' source files.

- **Buttons:** `.button` + `.button-primary` (red), `.button-secondary` (ink outline), `.button-quiet`
  (text). Add `aria-busy="true"` while sending and `disabled` when unavailable. `React`: `web/src/ui/Button.tsx`
  keeps `variant="primary" | "secondary"` and gains `"quiet"`.
- **Fields:** `.field` with a `<label>`, an input / textarea / select, and an optional `.hint`. Error is
  `data-invalid="true"` on the field: a heavier border and a plain sentence with a "!" block. `.choice` for checkboxes and radios.
- **Navigation:** `.wordmark`, `.nav` (the four items Shelf, My book, Checkouts, Past meets; current page has
  `aria-current="page"`), `.search`, `.avatar`.
- **Content:** `.book` (+ `.book-lg`, `.book-sm`), `.shelf-head` + `.shelf-books` + `.ledge`, `.band` (the Librarian's
  feature), `.caption`, `.bubble`, `.contents` (dotted leaders), `.panel`.
- **Feedback:** `.message`, `.message-error`, `.empty`, `.dialog` on `.scrim`, `.skeleton`.

## Rules that are easy to break

- Buttons say what happens ("Ask to check out", "Save contact details"), never "Submit" or "Continue".
- A book shows its title and the author's full name. Never a headline, employer, genre, count, rating, badge or "popular" mark.
  A student's book and a VP's book are identical.
- Search is small and secondary. It is never the hero.
- Empty states are left-aligned with a dotted frame and one next step. No illustrations.
- A dialog only when the task cannot happen in place.
- Motion answers something the person did: hover, press, a page turn. Nothing animates on load or loops.
  120ms, no bounce. `prefers-reduced-motion` turns transitions off.
- Focus is a 3px ink ring (white on dark), always visible for keyboard use.
- Check new UI against [ai-tells.md](ai-tells.md): did a person choose this, or did a default?

## Before you call a screen done

1. Tokens only: no raw color, size, font or radius in feature code.
2. One focal point and one primary action.
3. Every state designed (rest, hover, pressed, focus, disabled, busy, error, empty).
4. 44px targets, allowed contrast pairs, visible focus, a text label on every control.
5. Product rules hold (names, no counts, no cold messages, no feed).
6. Copy is specific; invented copy is marked as placeholder.
7. Run it past `ai-tells.md`.
8. A new pattern? Add it to Additions below.

## Reference screens

On the canvas: **Reference screen · The shelf** (top bar, Librarian's band, shelves) and **Reference
screen · Sign in** (form screen). Copy their structure for new screens.

## Porting to the app

`tokens.css` is the source until it is merged into `web/src/ui/styles.css`. The `--color-*` and `--space-*`
variables the app already uses are aliased in it, so porting is a drop-in. Load the three fonts from Google
Fonts (Barlow Condensed 500–800, Newsreader 400–700 + italic, IBM Plex Sans 400–600). When `styles.css` carries
the tokens, this file stays the rulebook and `styles.css` the implementation.

## Handoff: build the shelf page (static, first screen)

**Build this:** Reference screen · The shelf, i.e. manga B2. Source of truth for pixels:
`docs/design/shelf/project/SysShelf.dc.html` (identical to `MangaB2.dc.html`); live at the canvas link above, page
"Design system", board "Reference screen · The shelf". Static for now: no click behavior, "Ask to check out" is
shown but inert (`aria-disabled` is not needed; just don't wire it). Books are white (cover art is undecided).
Seed 18+ sample books (title + full name only; titles are in the board) and let the shelves scroll.

**Setup.** Copy `docs/design/system/tokens.css` into `web/src/ui/styles.css` (the old `--color-*`/`--space-*` names are
aliased). Add to `index.html`:
`<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@500;600;700;800&family=Newsreader:ital,opsz,wght@0,6..72,400..700;1,6..72,400..500&family=IBM+Plex+Sans:wght@400;500;600&display=swap">`
(self-hosting the same three families is fine). Use the classes in `tokens.css` as written.

### Desktop (1440 reference; fluid down to 960)

Page ground `--paper`. Four stacked parts:

1. **Top bar**, 16px from top, 48px high, 36px side padding, `display:flex; align-items:center; gap:36px`:
   `.wordmark` ("Trove"), `.nav` (Shelf, My book, Checkouts, Past meets; Shelf has `aria-current="page"`),
   then right-aligned `.search` (placeholder "Search by topic", 230px) and `.avatar` (initial).
2. **Librarian's band** (`.band.dark`), starts 80px from top, 384px high, full width, slanted bottom edge. A 3px ink
   rule runs parallel 12px below the slant (`transform-origin:0 0; rotate(-atan(28/width))`). Inside:
   `.burst` (`--fx:82%; --fy:46%`, opacity .55) and `.halo` (476×476, left = bookLeft−120, top −40) behind the
   book; a left-to-right fade (`linear-gradient(90deg,#111 0,#111 44%,transparent 70%)`) over them so no line crosses
   the text; text column at left 44px: `.caption` "The Librarian recommends" (top 34px), page title 48px Newsreader
   (2 lines, 18px below caption), "by Hana" (Plex 600 13px, caps, `--rule`), the reason as `.voice` 22px with a
   4px white left rule and 18px padding (max 640px), then at bottom 48px a row with the primary button
   (`.button.button-primary`, label "Ask to check out", white 2px frame on dark) and the note "A thirty-minute
   video call" (display face 14px caps, `--rule`). The feature book (`.book.book-lg`, 236×344, rotated 3deg) sits at
   left = width−374px, top 18px.
3. **Shelf rows**: first row top 500px, second 780px (i.e. 36px under the band's rule, then 28px between rows); left/right
   gutter `--s-7` (44px). Each row: `.shelf-head` (`.shelf-name` + rule + "See all"), `.shelf-books` (flex, gap 28px),
   then `.ledge` that runs full-bleed to the page edge (margin `0 -44px 0 -8px`). Shelf names are placeholders
   ("Changing course", "Starting over").
4. Row of books overflows horizontally with `overflow-x:auto` and scroll-snap when there are more than fit (at 1440
   six to seven 176px books fit per row). Add 36px of space below the last ledge for its dot shadow.

**Book** (`.book` 176×257 on the shelf, `.book-lg` 236×344, `.book-sm` 92×136; the shelf book was 122×178 until
2026-11-21, when Josef chose the larger size so the cover art and its type read better; shelf gap 36px): white cover, 2px ink outline (3px on lg), a narrow hinge:
a 1.5px ink line 8px in from the left edge, with the cover's type starting 18px in (Josef, 2026-11-21: the old
hinge at 12px with type at 21px took too much of the cover), dot shadow offset 8px right and down, title Newsreader 600 13.5px (27px on lg) at top, full name Plex 600
9.5px caps at bottom. A long name wraps (also at a hyphen) and stops at 4 lines with an ellipsis, so a real full name is never cut (it was 3 until 2026-11-15, when long names hit the limit; Josef approved 4); "ALEXANDRA OKONKWO-BRENNAN" takes 3 lines on `.book` and `.book-sm`, 2 on `.book-lg` (measured in the app with the real fonts). Title and full name only; never a headline, employer, genre, count or badge. Make the book an `<a>`
(or `<button>`) with `aria-label="<Title>, by <Full name>"`, a focus ring and the hover lift (`translateY(-4px)`).

**Nav, shelf row and band** have no other states in this slice. Search is a text input styled as `.search`.

### Phone (proposed here; not drawn on the canvas yet)

Breakpoint: below 720px. Same parts, rearranged:

- Gutter 16px (`--s-4`). Top bar 56px: `.wordmark` at 22px, `.search` collapses to a 44px icon button, `.avatar` 36px.
- **Nav moves to a bottom tab bar**: fixed, 64px high, four equal items in the nav style at 14px, paper ground,
  3px ink top rule, the current item has a 3px ink bar on top. Each target at least 44px.
- **Band** stacks: caption, title (34px Newsreader), reason (`.voice` 18px), button full width (min-height 48px), and the
  feature book at `.book-lg` scaled to 168×244 placed below the button, left-aligned, no rotation. Keep the slanted
  edge (20px). Burst and halo stay, centered behind the book, opacity .45.
- **Shelf rows** keep `.shelf-head` (shelf name 24px) and scroll horizontally with scroll-snap; books 104×152 (use
  `.book-sm` proportions), gap 20px, the first book starts at the gutter, the next one peeks in. The ledge spans the full width.
- Page bottom padding 64px so the tab bar never covers the last ledge.

### Tablet (720–1099px)

Desktop layout with 24px gutters, the search shrinks to 180px, band title 40px, the feature book stays on the right
at width−300px, rows scroll horizontally.

## Handoff: the open book (book screen B)

**Approved by Josef, 2026-11-19.** Build this in place of the current `BookReader` look. Source of truth:
`docs/design/shelf/project/FreshReaderOpen.dc.html` (canvas page "Fresh directions", board "Book screen B · the book
opens"). **No art for now:** pages are plain `--paper`; the art inside the book and on the covers is still to be decided,
so leave the art layer out (keep a place for one image under each page's content).

- **Around the book.** The page keeps the shelf's top bar exactly as on the shelf. Below it the shelf stays in place at
  60% opacity under fine ink dots (`.9px` dots on a 5px grid, opacity .4); the opened book's place on the shelf stays
  empty. There is no other toolbar, backdrop or button outside the book.
- **The book.** Centred, 1180 × 724 at 1440 wide. One board in the book's cover colour (use `--ink` until covers are
  decided), radius 4, 8px larger than the pages all round; the spine shows as a 24px tab at head and foot of the
  gutter; one sheet of page edge (white, 1.5px ink) 6px proud of the pages. Two pages, each a flat plane 570 × 684,
  `--paper`, 2px ink outline (1px where they meet at the gutter), and a 36px strip of dot shade down the gutter.
  No curves, blur or stacked layers: each page is one plane that carries all of its own content.
- **Controls live in the book.** Left page head: "✕ Close the book" (Esc too). Right page head: page tabs
  Contents, 1, 2, … (the current one underlined). The lifted corner at the right page's foot turns forward;
  ← → and swipe turn too. No page numbers or turn links at the feet. No helper sentences anywhere.
- **Spread 1:** left, the title page: title (Newsreader 600, 42px), "by" full name (byline), blurb, then
  "Ask to check out" (`.button-primary`). Right, the contents: numbered rows (number, chapter title, one-line summary,
  ›), dotted rules, hover shades the row `--paper-sunk`.
- **Spread 2 (a chapter):** left, the contents again, compact (no summaries), the current chapter reversed in ink,
  and "Ask to check out" under the list. Right, the chapter: a large number (Barlow Condensed 800, 120px), the title
  (Newsreader 600, 38px), the summary (Newsreader 19px). **Never put Ask to check out under a chapter**: it would
  read as checking out that chapter.
- **Motion (Josef, 2026-11-19).** Clicking a book on the shelf is a 3D move: the view zooms in on that book where it
  stands, then the book opens up in 3D, the cover swinging about the spine, into the open spread. A page turn
  rotates a page plane about the spine in 3D (`transform-style: preserve-3d`, the content on the plane turns with
  it). Reduced motion swaps states with a short fade. Built and workshopped with Josef on 2026-11-21: see Additions,
  "The open book in motion", which replaces the zoom with the book itself flying forward.
- **Demo before anything is pushed.** Josef wants to see a working demo of the open and the turns first and will
  likely workshop them with the implementation session. Nothing of this screen goes to main until he has.
- **Removed:** "I have one like this" (sparks) is not on the book screen. `docs/trove.md` still lists sparks; that
  plan change is the orchestrator's.
- **Phone:** not drawn yet. Until it is, show one page at a time at full width with the same head controls.

## Additions

Patterns added after v1. Each entry: name, the task it solves, date, owner, snippet or link.

### Opening a reader's book (D1, 2026-11-18, Alvisa)

- A modal book spread covers the whole app, with an ink backdrop at 94% opacity. This stronger
  dimming and the slower opening are Alvisa's explicit choices for focusing on the selected book.
- The closed cover starts at the selected book's position. Growth and its leftward hinge rotation
  overlap, settling into a two-page spread. This action-triggered opening is an exception to the
  usual 120ms motion; reduced-motion preferences remove the travel and page turns entirely.
- The left page carries the title and full name. The right page starts with Contents; chapter
  titles are measured at the actual page width and paginated to fit, never truncated to fit more.
  Selecting an entry turns to its summary. Back to contents and previous/next page controls are
  quiet; Ask to check out is the one red action. Escape or Back to shelf closes the reader.
- The spread stays two pages on small screens, with smaller gutters, wrapping text and scrollable
  page content when necessary. Native modal focus containment keeps the background inert.
- Implementation: `web/src/features/discovery/BookReader.tsx` and `BookReader.css`. The static
  Librarian example remains; its preview identifies itself as an example and cannot be checked out.

### The open book in motion (D1, 2026-11-21, Trove UI with Josef)

Task: open, read and close a book as one physical object. Built in `web/src/features/discovery/BookReader.{tsx,css}`,
workshopped with Josef frame by frame. Rules it keeps, for any later change:

- **One object, printed.** The book is a 3D object (`preserve-3d`): cover slab with rims on all four sides, page block
  with fore-edge, head, foot and spine faces, a board and a spine strip. Closed, it is the shelf book exactly: its
  type, hinge, padding and line breaks are measured from the very copy clicked and frozen (`printCover`,
  `.br-line`), its art stretched to the cover. Everything on a page is printed on it: the spine's dot shade
  (`.br-left::after` / `.br-right::after`) and the turned-down corners travel with the paper. Nothing fades,
  scales or reflows on its own, and nothing appears mid-flight: a book's contents and art load when it is pointed
  at, and it waits closed in its place (at most 0.6s) until they are in.
- **Opening (850ms).** It lifts from its shelf place, turns about its upright axis only (head and foot never tip),
  lands a touch large (1.2%) and settles; the cover lifts at once and slows into the spread; the spine strip
  unfolds from the spine line on the cover's curve. Only transforms and opacity animate, so it runs on the
  compositor.
- **Closing (560ms).** Its own curve, not the opening reversed: prompt from the first frame, no swell, slowing onto
  the shelf, back to the copy it came from (a book on two shelves leaves only the clicked copy's place empty).
- **Around it.** One full-window layer of paper at 55% and dots at 62% ink over the shelf (the shelf itself is never
  faded, which flashed it); the clicked copy's dot shadow dissolves out as it lifts and back as it returns.
- **Turning.** Each leaf is six hinged strips that curl as it turns (edge leading, then trailing); a jump turns a
  leaf per spread passed (up to four, 110ms apart), each stacking above the last. Both pages carry a corner:
  forward at the right page's foot, back at the left's from the first chapter on.
- **Art inside.** The book's page art lies behind every left page, the title page and each contents page alike,
  anchored to the foot.
- **The Librarian's pick** on desktop is 260 x 379 with 33px / 15px cover type, and the words beside it stop 24px
  before the burst at every width.

### Growing books (T33, 2026-11-08, design session)

Frames: canvas page "Growing books" (boards `GrowingG1`..`G5`), each at desktop and phone width.

- **Toggle pair (Approve / Decline).** Two `.button-secondary.sm` joined with a −2px overlap; the chosen one has
  `aria-pressed="true"` and is filled ink with white text (never red). Declined content is struck through, so the
  state shows without colour. Used for one decision per row with no side effect until a later confirm.
  `.button[aria-pressed="true"]{background:var(--ink);color:var(--white);border-color:var(--ink)}`
- **Change card (`.chg`).** A white panel, 3px ink outline: caption chip (New chapter / Improved chapter), status word
  at the right, the one italic line on what changed directly under the chip, two columns "Now" and "Proposed" (Proposed has a 4px ink left rule; a new
  chapter's Now is a dotted "Not in your book yet.", a removal's Proposed is a dotted "Comes out of your book."), then the toggle pair.
  On a phone only Proposed shows, with a quiet "See what's there now" that opens Now in place. Added words are underlined; a declined card strikes
  only its title. The status word is Approved, Declined or Not decided.
- **Author-only quotes (`.quotes`).** A 4px ink left rule and Newsreader italic under a chapter, behind a quiet "Show what
  you said" button. The chapter list says once that only the author sees them.
- **Quiet inline action (`.spk`).** A private margin note, not a reaction: the plain text link (`.button.tl`) at 14px in `--ink-2`,
  sentence case, underlined, 44px tall, no plus or tick mark, no width of its own, −12px left margin so its text lines up with the
  host's text. After the press it becomes a plain sentence with an Undo link. It makes no assumption about the row it sits in, so a
  page owned by someone else can mount it at the end of a chapter's content. Hover or focus shows a small `.tip` panel (2px
  outline, white) with one sentence. Build it with `aria-label` that includes the chapter title, and read the saved state from the
  member's list so it survives a reload.
- **Small buttons are 44px.** `.button.sm` (Approve, Decline, Rewrite, Remove, Try again, Choose a PDF) keeps `--tap` height; only its
  padding and type size shrink. Toggle buttons carry `aria-label="Approve: <chapter title>"`.
- **The wait (`.empty.waitbox`, `aria-busy`).** A dotted panel with one plain sentence and a quiet way out. No spinner and no
  progress bar, because the length is unknown and a bar would imply a count.
- **Plain text link (`.button.tl`).** For a quiet action that reads as a sentence, such as "That is enough. Write the changes"
  or "Add a PDF so my first questions fit you": Plex Sans 400, 15px, sentence case, underlined, 44px tall. Caps are for
  short display-face labels only, so a sentence is never set in caps.
- **Added words (`ins`).** In a Proposed column, words that were not in the Now text are underlined (2px, offset 3px), so the
  difference shows without colour and without a second column to compare.
- **Remove in place.** The row turns into "Remove this chapter?" with quiet "Remove" and "Keep it", on a dot tone with the text
  on a white chip. No dialog.
- **Interview review.** The book object (`.book`) beside its title, "by" line and back cover, then quiet "Rewrite the back cover"
  and "See the other titles"; chapters in the member's first-person words with "Show what you said" under each; quiet Rewrite
  and Remove per row. The page scrolls; the red button ends it.
- **My book layout.** The book object (`.book-lg`, `.book` on a phone) beside its title and blurb; chapters as a ruled list
  with dotted separators; a narrow aside holding the reading question and the sparks list. One red button: the next step
  for the book's current stage (Start the interview, Review your book, Add to your book, Continue adding, Review the
  proposed changes).

### Editing your own book (spec-editing.md, 2026-11-15, Trove UI)

- **Edit in place (`.ed-form`).** A quiet "Edit" (`.button-quiet.sm`, 44px) under the text it edits; the text becomes
  `.field`s where it stood, labelled ("Title", "Back cover", "Chapter title", "What it's about"), with a secondary
  "Save" and quiet "Cancel" (never red: the screen's red stays its next step). Typing past the limit is allowed and
  says so under the field, and Save waits; nothing is cut. A refusal from the server shows as a `.message` under the
  fields, in its own words, and the fields keep what was typed. The edit is kept as a draft while it's open, so a
  refresh reopens it. Cmd/Ctrl+Enter saves, Escape cancels.
- **Take off the shelf.** A quiet link under the chapters, asking in place (as **Remove in place** and Undo do):
  "Take your book off the shelf? …" with quiet "Take it off" and "Keep it on the shelf", focus on keeping it. An
  off-shelf book's caption is "Off the shelf", a plain note says what that means, and "Put back on the shelf" is
  the page's red action.

- **Checkouts page** (2026-11-15, Ellie; regrouped 2026-11-22, `web/src/features/checkouts/Checkouts.css`, `.co-*`).
  Task: see what needs you, then follow the rest, without a feed. Three groups under display-caps headings with a
  rule: **Waiting on you** (a request for your book, a "Did you meet?" to answer; "Nothing needs you right now." when
  empty), **Under way**, and **Earlier** (closed checkouts as one dotted-ruled line each: title, "<name> · <status>",
  and a Past meets link when there is one). Your book and books you've checked out mix within a group. Live
  checkouts are Folio `.surf` cards, two to a row from 820px: the name or title in Newsreader, one meta line, and a
  status label at the top right (above the name on a phone): outlined while it waits on someone ("Asks for your
  book", "Waiting"), solid ink once "Accepted". The other member's note (`.checkout-note`) shows only while it's
  waiting. **No red on this page**: no single action is the next step for everyone. Declining asks once, in place
  ("Decline …? Decline / Keep it"), not in a dialog. The unread sign is a dot and "New message", never a number.
- **Check out form** (2026-11-15, Ellie, `CheckOutPage.tsx`). The book's title, byline and blurb, then one
  textarea and the screen's one red button, "Ask to check out", with the note "A thirty-minute video call, if
  the author says yes."
- **Conversation** (2026-11-18, Ellie, `web/src/features/messaging/MessagesPage.css`). Task: read and write a short
  thread inside a checkout. Each message is a `.bubble` (speech is the one rounded shape) in the working face,
  not the Librarian's italic, because these are people's own words to read. Everything stays left-aligned;
  your own messages get a fine dot-tone fill instead of moving to the right. App notes (a confirmed time) are a
  plain line between dotted rules, never a bubble. One red button, "Send". No read receipts, typing dots or
  counts; the only unread sign is the private "New message" caption on the Checkouts page.
- **"Did you meet?"** (2026-11-18, Ellie, `web/src/features/checkouts/DidYouMeet.tsx`). Task: answer privately
  whether the reading happened. A `--paper-sunk` box with the question in Newsreader ("Did you meet <name>?"), one
  muted line ("Only you see your answer. Yes or No returns the copy."), then secondary "Yes, we met" and quiet "Not
  yet" and "No". A chosen "Not
  yet" is filled ink, as the toggle pair. Never red, and no confirm step: the line says what a final answer does
  before the press. Once the copy is back, "Not yet" isn't offered.
- **Past meets** (2026-11-18, Ellie; cards 2026-11-22, `PastMeetsPage.tsx`). Task: find the people you've met again.
  One column of Folio `.surf` cards (at most 760px, newest first, so a list of people reads top to bottom and no
  card leaves a hole beside another), each with a bookmark hanging from its top edge near the right corner (an ink
  ribbon with a notched tail, `.past-meet-bookmark`, 16 by 64px): the other person's name and their book, which book
  was checked out and when it was returned, a "Did you meet?" box if they haven't answered, the contact line, and
  "Your conversation". No counts and no red.
- **Contact line** (2026-11-22, Ellie, `ContactDetails.tsx`). The reveal as one wrapping line: a small display-caps
  "Reach <name>" in `--ink-2`, then the email, LinkedIn profile and phone as links. Used on Checkouts and Past meets.

### Folio: the shelf front page look (2026-11-19, design session; screens: canvas page "Elevate", board `ElevateK3` "Kit 3 · Folio, for build")

Task: a more finished, deeper paper look for the shelf front page, replacing the flat Manga-screentone cards and the filter chips. **Approved by Josef on 2026-11-19** ("I approve all six", relayed by the orchestrator). It changes the fixed tier in six ways, all approved: cross-hatch shade, the 5px corner radius, the square search field and avatar, the notched bookmark, no dot shadow on the Librarian's black-cover book, and shelf arrows that replace "See the whole shelf" and the tabs and chips.

- **Card (`.surf`).** A white face with a 2px ink line and a dot shadow under it (offset 12px down-right, `radial-gradient(circle, var(--ink) 1.3px, transparent 1.7px) 0 0/5px 5px`). Nothing else under it: no stacked page edges. The spine is a cross-hatch on the left,
  `repeating-linear-gradient(45deg, ink 0 1px, transparent 1px 6px), repeating-linear-gradient(-45deg, ...)`, 60px wide, masked to fade to nothing. Shade is hatching on spines and under shelf ledges; dots are for cast shadows.
- **Corners.** `--r: 5px` on cards, buttons, fields, the avatar and books (book cover 3px 5px 5px 3px); 8px on the black cover. This replaces the square-corner rule.
- **Buttons.** A dot shadow `.pbw::before` (inset 5px) that the button presses into on hover and press. A secondary button has a white face and goes ink on hover. No stripes anywhere.
- **Header.** A square search field (icon, "/" key hint) and a square ink avatar tile with white initials and a dot shadow, both on the same 2px line and 44px height as the buttons.
- **The Librarian's cover.** Black; the burst from Kit 2 converges on a point to the right of the book (`repeating-conic-gradient(... at 80% 50%)`, masked with a dark faded centre); the book has no dot shadow.
- **Bookmarked line.** A card with a spine and an ink ribbon bookmark (22 x 64px, notched bottom: `clip-path: polygon(0 0,100% 0,100% 100%,50% 78%,0 100%)`) for the one thing waiting for you, with an eyebrow, a name and one secondary button. A "Your book" block sits beside it. No number.
- **Shelf.** The shelf name, a 2.5px rule and two square arrow buttons (40px, `aria-label` "Earlier books on <shelf>" and "More books on <shelf>"; the start arrow is disabled at the start of the row), then books standing on one ink ledge (14px) with a light diagonal hatch below.
  The next book peeks in at the right edge. Arrows scroll the row in place; there is no "See the whole shelf" and no extra page.
- **Not part of it.** Index tabs and filter chips were dropped from the front page. The interview is the Librarian's notebook (below), not this kit.

### The Librarian's notebook (2026-11-19, design session; screens: canvas page "Librarian notebook", `LibDesktop`, `LibPhone`, `LibParts`, `LibMore`, `LibReopened`)

Task: while a member types an answer in the interview, the Librarian marks it and keeps a notebook. Approved scope is in `docs/librarian-plan.md`.

- **Ink exception.** The Librarian writes in `--red` (white ground 5.0:1). This is an approved exception to "red is the primary action and nothing else": handwriting
  and marks only, thin line-work only, never a filled shape, button, tag or state. The one fill is the paste highlight (red at 20%, multiplied). `--lib: var(--red)`.
- **The hand.** Caveat 600, 23px, tilted -2 degrees, lowercase, ending in a full stop; at most 32 characters on the answer and 60 in the notebook. A fourth face,
  used only for the Librarian's writing (needs Josef's yes). Marks are masks of hand-drawn SVG strokes, so they take the ink colour: `mask: url(wobbly-underline.svg) 0 0/100% 100%`.
- **Marks on the answer (`.mk`).** Anchored to exact words: underline, double underline, strike with a replacement above, loose circle, note only, and the highlight.
  A mark is written (stroke clips in left to right), rests, and is rubbed out (the clip closes from the left), never faded. Only the marked word's line opens (about 30px, 0.35s); the cursor's line, the question and the buttons never move.
- **The notebook (`.nbook`).** A card like the others, with the cross-hatch spine. Text starts just after the spine, with no bullets. Entries: chapter, connection, saving, clip, note.
  Each sits a little off-level (rotation, left offset and size vary per entry) and may carry its own underline or a word rewritten above. A revised entry is struck with a line and rewritten;
  an erased one is rubbed out. A question built on an entry circles it, or ticks a saving.
- **Phone.** The notebook is a sheet that lifts from a one-line peek above the composer; the dot scrim sits behind it.
