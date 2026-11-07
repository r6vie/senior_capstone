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
- **Red is the primary action and nothing else.** One red button per screen. Errors, success and
  selection are never red.
- Three faces: **Barlow Condensed** (short caps labels), **Newsreader** (book titles, page titles, the
  Librarian's voice), **IBM Plex Sans** (everything you read to do a task).
- Square corners. A pill only for the search field and avatar; a rounded bubble only for speech.
- Shade is made of dots (tone), never a blur, a gradient or a glow.
- One focal point and one primary action per screen. Left-aligned.
- Every state is designed: rest, hover, pressed, focus, disabled, busy, error, empty.

## How strictly to follow it: fixed, default, free

A system is a set of decisions, not a cage. Each rule below belongs to one of three tiers.

**Fixed. Change only with a human's yes.** The identity. If these move, the product stops looking like itself.

- The palette and the red rule.
- The three faces and their jobs; caps only on short display-face labels.
- Square corners; pill and bubble exceptions as above.
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
| Book author (full name) | Plex Sans 600, +0.12em, line-height 1.3 | 9.5 | CAPS, wraps to 3 lines |
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
   nine 122px books fit per row). Add 36px of space below the last ledge for its dot shadow.

**Book** (`.book` 122×178, `.book-lg` 236×344, `.book-sm` 92×136): white cover, 2px ink outline (3px on lg), hinge line at
left 12px, dot shadow offset 8px right and down, title Newsreader 600 13.5px (27px on lg) at top, full name Plex 600
9.5px caps at bottom. A long name wraps (also at a hyphen) and stops at 3 lines with an ellipsis; "ALEXANDRA OKONKWO-BRENNAN" takes 2 lines on `.book`, 3 on `.book-sm`, 1 on `.book-lg`. Title and full name only; never a headline, employer, genre, count or badge. Make the book an `<a>`
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

## Additions

Patterns added after v1. Each entry: name, the task it solves, date, owner, snippet or link.

_None yet._
