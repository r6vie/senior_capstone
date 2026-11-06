# Design decisions

Decisions Josef has made about Trove's look and feel. Newest first.

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
