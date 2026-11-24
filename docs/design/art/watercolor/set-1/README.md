# Watercolor art, set 1: ready to implement

Approved by Josef on 2026-11-23 for the app: the ten watercolour books that have a book screen on the design canvas
("Covers: Watercolor" page), each a cover and the matching title-page art for the opened book. Covers without a book
screen (the round 1 lighthouse, the harbor, the prairie storm) are not in the set.

`contact-sheet.png` shows all twenty at a glance (covers on top, pages below).

## Two categories: strata and watercolor

Josef, 2026-11-23: these live in their **own category**, `watercolor`, beside strata set 1 (`docs/design/art/strata/set-1`,
category `strata`).

- **Assigning art to a book:** a book's chances are the same for every art in every category. Pool all twenty
  (ten strata, ten watercolor) and pick one deterministically from the book's id, as set 1 does, so its cover and its
  opened page always share one art. Draw from the pooled list, not a category first and then an art, so every art
  stays equally likely as more sets are added.
- **Choosing your own design:** Josef is designing that screen now. There the arts are grouped by category, so every
  art carries its category (`strata` or `watercolor`). Keep the category on the art's data, not in the file path
  alone, so the chooser can group by it.

## Files

| What | Files | Size | Use |
|---|---|---|---|
| Cover art | `covers/<key>.webp` | 472 x 688 (the 236 x 344 cover at 2x) | Every book size: the 176 x 257 shelf book and the 236 x 344 large book |
| Page art | `pages/<key>.webp` | 1140 x 1368 (the 570 x 684 title page at 2x) | The opened book's left page, behind the title, byline, blurb and button |

`manifest.json` lists the ten: `key`, a human `name`, `coverInk`, `pageInk`, `coverInkContrast` and the two paths.
Keys: `mesa`, `hills`, `lake`, `winter`, `city`, `blossom`, `autumn`, `beach`, `lighthouse-day`, `lighthouse-dusk`.
Keys can repeat strata's (`lake`, `winter`, `city`), so key an art by category and key together (`watercolor/lake`).

## How watercolour covers differ from strata covers

- **Painted edge to edge.** Strata covers have a plain white top; watercolour skies run to the top under the title.
- **Two inks per art.** `coverInk` is the colour of the title and the full name on the cover. It is chosen from the
  paint behind the title: cream `#f6efe0` on a dark sky, the book's own dark ink on a light one, whichever reads
  better (each is at least 4.5:1; the measured ratio is `coverInkContrast`). `pageInk` is the dark ink for the opened
  book's title page, whose text always sits on paper.
- **No knockout behind the name.** Strata put the name on a white knockout; on a watercolour cover the name sits on
  the paint like the title (Josef's choice on the canvas boards), in `coverInk`.

Everything else is strata set 1's spec: the same book object, the 176 x 257 shelf size, the narrow hinge (1.5px at
8px), the padding, Barlow Condensed 800 caps 29px for the title and 700 caps 13px +0.16em for the name, 10px gap,
`alt=""` on the art and `aria-label="<Title>, by <Full name>"` on the book. See `docs/design/art/strata/set-1/README.md`.

None of the inks is the UI red. They are art data and belong with the art, not in the design tokens.

## The opened book (title page)

As strata: the page art fills the left page of the opened book (570 x 684 at desktop), behind the text, anchored to
the bottom with `object-fit: cover; object-position: bottom`. Its upper left (about x 0 to 470, y 0 to 350) is kept
as paper for the text; the sky bleeds into it. The canvas boards `WCBook*.dc.html` in docs/design/shelf/project show
the layout.

## Animations (approved 2026-11-23)

Every watercolour cover paints itself in: the cover's own glazes laid back down in the order they were painted, each
spreading from where the brush lands. Files in `anim/` (472 x 688, muted; MP4 and WebM), listed per art in
`manifest.json` under `anim`:

| Version | Where | Timing |
|---|---|---|
| `<key>-loop` | **The sign-in page only** (the blank book on Join, invite, confirm email, sign in), one cover after another | Paints in (all glazes by ~12.3 s), rests from 13.5 s, washes back to paper 18.5–23.5 s, 1.5 s of clean paper. 25 s, seamless. Pick the next cover at random each cycle. |
| `<key>-reveal` | **The book reveal** and **your picks** (when a new book's design options appear) | The same painting at the same timing, played once, ending on the finished cover at 13.5 s. Keep this timing (Josef). |
| `<key>-quick` | **The design studio**, when you choose a design | The same painting at 0.3 of the time, about 4 s, ending on the finished cover. Quicker so nobody waits to see the design (Josef). |
| `<key>-poster` | Reduced motion, and before a video loads | The finished cover. |

- The last frame of `reveal` and `quick` is the cover image, so when the video ends, swap to the still (or leave
  the last frame) with no visible jump.
- `prefers-reduced-motion`: show the poster, play nothing.
- Play `muted`, `playsinline`, no controls; the video sits under the title and name exactly as the cover art does.
- Strata covers will animate in the picks and the studio too (not on the sign-in page), on the same clock; their
  animation is still being designed and is not in this set.
- The screens these play on (the sign-in blank book, the reveal, the picks, the studio) may not be approved
  designs yet. Build the playback when each screen is.

## Source

Rendered by the scripts in `docs/design/art/watercolor/` (animations: `paint_anim.py` and `encode_anim.sh`; `covers.py`, `lighthouse_boats.py`, `abstract.py`,
`abstract2.py`, `pages.py`, `pages2.py`, all seeded) and packaged by `package_set1.py`. The record of every change is
in docs/design/decisions.md.
