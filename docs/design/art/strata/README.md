# Strata: cover art laid in slabs

An exploration, not approved. It lives on the design canvas, page "Strata covers"
(https://claude.ai/artifact/33uQU8UKZ4gtxcv4ZNof1D), boards `StrataBook`, `StrataShelf` and `StrataPlaces`.
The decision it waits on is in `docs/design/decisions.md` (2026-11-18).

Every landscape is cut into courses (rows) of one height and laid in bricks of random length. Edges step
instead of curving. Light comes from the left, and each peak has a lit face and a shadow face. Mist is made by
leaving bricks out and paling them toward paper, never by a blur or gradient. A place is defined once in world
pixels and redrawn for each size it shows at, so the courses stay 4px on the book page and 2px on the shelf.

| File | What it does |
|---|---|
| `strata.py` | The renderer: layers (ridge, blob, grove, water, ground) and `render()` |
| `scenes.py` | The ink families and the places: `lake()` (the book-page panorama) and seven cover-only places |
| `cover_lake.py` | Round 2 design 1, "the lake", drawn for the cover at four sizes |
| `shelf.py` | The other seven designs at shelf and small size with the round 2 renderer |
| `board_round2.py` | Writes the round 2 canvas board (`StrataCover2`) |
| `hero.py` | The lake panorama at 1440 x 620 and its large cover, cut from the same drawing so the cover lines up with it |
| `covers.py` | Every cover place at large, shelf and small size, plus a contact sheet |
| `hero3.py` | Round 3 of the lake (`scenes.lake3()`): spurs and gullies down each face (`Ridge(ribs=…)`), a wandering light line, a far haze range, mist at the mountains' feet (`mist=`) and the peaks mirrored in the water. Writes the panorama and the xl and small covers cut from it, used on the Fresh directions page |
| `book_b.py` | Art drawn for book screen B's pages (`FreshReaderOpen`): the title page (570 x 684, full page under the text; the land climbs the right edge, a lake across the foot, groves framing it) and the same place from further back for the foot of the contents page |
| `final.py` | Final round, on the canvas page "Final designs": the same slabs finished (no bevel, a paper seam between courses, calm colour), one muted family of inks, a composed scene (hero peak on the right third, sun set against its flank, planes stepping back into haze, firs in a cluster) for B's title page, its contents page, and the cover |
| `phone.py` | The panorama and cover at three-quarter size for the phone book page |
| `boards.py` | Writes the three canvas boards (the uploaded image ids are in it) |

Run from this folder with Python 3.13, Pillow and NumPy: `python3 hero.py && python3 covers.py && python3 phone.py`.
Images go to `out/`. Convert them with `cwebp -lossless` before uploading. A cover is 1 to 4 KB and the panorama
is 27 KB.
