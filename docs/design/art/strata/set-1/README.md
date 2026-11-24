# Strata art, set 1: ready to implement

Approved by Josef on 2026-11-21 as the first set of book art for the app. Ten places, each with a cover and the
matching title-page art for the opened book. These are the exact files published on the design canvas
("Covers: Strata" page), checked against the canvas byte for byte.

`contact-sheet.png` shows all twenty at a glance (covers on top, pages below).

## Files

| What | Files | Size | Use |
|---|---|---|---|
| Cover art | `covers/<key>.webp` | 472 x 688 (the 236 x 344 cover at 2x) | Every book size: the 176 x 257 shelf book and the 236 x 344 large book |
| Page art | `pages/<key>.webp` | 1140 x 1368 (the 570 x 684 title page at 2x) | The opened book's left page, behind the title, byline, blurb and button |

`manifest.json` lists the ten arts: `key`, a human `name`, the cover `ink` (the colour of the title and name on that
cover), and the two file paths. Keys: `lake`, `desert`, `coast`, `valley`, `karst`, `winter`, `fields`, `lagoon`,
`city`, `forest`.

All files are lossless webp and opaque. A cover's top is plain white, where the title sits. A page's background is the
paper colour (#fafaf7), and its upper left (about x 0 to 470, y 0 to 350 of 570 x 684) is kept empty for the text.

## Which book gets which art

Josef: each book gets one of the ten at random, so the sample libraries vary. Pick it **deterministically from the
book's id** (for example a stable hash of the id, modulo 10), so a book keeps the same art across reloads and on
every screen: its cover and its opened page always share one key. Whether the key is later stored on the book in the
API is the orchestrator's call; the mapping alone needs no backend change.

## The cover (fixed tier, approved 2026-11-21; see docs/design/system.md "Book" and the strata type role)

Shelf book `.book`: **176 x 257**, shelf gap **36px**.

- The art fills the whole cover under the outline: absolutely positioned at `left/top: -<outline>`, width and height
  `100% + 2 x <outline>`, `z-index` below the text. `alt=""`; the book's `aria-label` already says
  "<Title>, by <Full name>".
- Narrow hinge: a 1.5px ink line, 8px in from the left edge, drawn above the art.
- Padding 20px top, 13px right, 14px bottom, 18px left.
- Title: Barlow Condensed 800, caps, 29px, line-height 0.92, letter-spacing +0.01em, set left,
  `text-wrap: balance`, in the art's `ink`.
- Full name right under it, 10px gap: Barlow Condensed 700, caps, 13px, letter-spacing +0.16em, in the art's `ink`,
  on a white knockout (padding 0 3px 1px, margin-left -3px) so it stays legible where art rises into it.

Large book `.book-lg` (236 x 344): the same book scaled by 1.34: padding 27 / 17 / 19 / 24px, hinge 2px at 11px,
title 39px, name 17px, gap 13px.

Every cover keeps the art below the name line in its left part, so a title of up to three lines plus a one-line name
fits. Phone and `.book-sm` sizes are not decided yet.

The `ink` values are art data, not UI colours: none of them is the UI red, and they belong with the art (from the
manifest), not in the design tokens.

## The opened book (title page)

The page art fills the left page of the opened book (570 x 684 at desktop), behind the text, anchored to the bottom;
`object-fit: cover; object-position: bottom` keeps the art if the page is a little shorter or taller. The book
screen boards on the canvas (`FinalBook*.dc.html` in docs/design/shelf/project) show the layout.

## Animation (approved 2026-11-23)

Every strata cover builds itself: the renderer's own slabs laid back down in one sweep from the foot of the cover to
the top, racing up at first and slowing as it climbs, each slab appearing a little above its course and drifting
down into place, the top ones settling slowest. One version only, `anim/<key>-quick.{mp4,webm}` (472 x 688, muted,
24 fps, about 4 s), listed per art in `manifest.json` under `anim`.

- **Where:** the book reveal, your picks (when a new book's design options appear) and the design studio (when you
  choose a design). The same fast timing as watercolour's quick version there. **Never on the sign-in intro**:
  that is watercolour only (Josef, 2026-11-23).
- The last frame is the cover image, pixel for pixel, so swap to the still with no visible jump.
- `prefers-reduced-motion`: show the cover, play nothing. Play `muted`, `playsinline`, no controls, under the title
  and name where the cover art sits.
- These screens may not be approved designs yet; wire the playback in as each one is.

## Source

Each image is rendered by the strata scripts in this folder (`final.py`, `covers_more.py`, `pages_more.py`,
`covers_new.py`, `pages_new.py`, `covers_us.py`, `pages_us.py`, `fields.py`); the record of every change is in
docs/design/decisions.md. Re-render only through those scripts, and re-check against the canvas.
