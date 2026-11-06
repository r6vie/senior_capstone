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
- The book object: white, outlined, a dot shadow, title and first name only.
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
| Book author (first name) | Plex Sans 600, +0.12em | 9.5 | CAPS |
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
- A book shows its title and a first name. Never a last name, genre, count, rating, badge or "popular" mark.
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

## Additions

Patterns added after v1. Each entry: name, the task it solves, date, owner, snippet or link.

_None yet._
