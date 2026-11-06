# Design decisions

Decisions Josef has made about Trove's look and feel. Newest first.

## 2026-11-06: identities, pick a craft idea before the layout

- **Josef:** C (circulation desk) has a real identity but feels too simple. Decide the material, pattern and
  craft idea first, then the layout. Explore printed media across eras and art styles (text, cartography,
  literature) as small mood boards.
- **New canvas page "Identities"**, six boards (`Ident1`..`Ident6`), each with a plate, what we borrow,
  palette, type and a shelf fragment with white books: 01 four-colour pulp (comic halftone), 02 survey
  chart (nautical cartography), 03 banded paperback (1930s-60s Penguin-style grid), 04 wood-type
  broadside (letterpress), 05 riso zine (two-ink overprint), 06 engraved plate (natural history).

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
