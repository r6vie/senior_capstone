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
| `hero.py` | The lake panorama at 1440 x 620 and its large cover, cut from the same drawing so the cover lines up with it |
| `covers.py` | Every cover place at large, shelf and small size, plus a contact sheet |
| `phone.py` | The panorama and cover at three-quarter size for the phone book page |
| `boards.py` | Writes the three canvas boards (the uploaded image ids are in it) |

Run from this folder with Python 3.13, Pillow and NumPy: `python3 hero.py && python3 covers.py && python3 phone.py`.
Images go to `out/`. Convert them with `cwebp -lossless` before uploading. A cover is 1 to 4 KB and the panorama
is 27 KB.
