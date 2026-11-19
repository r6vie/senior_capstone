# Three fresh cover directions

Josef paused the voxel work and asked for three different directions tied to paper, books, drawing or painting,
one cover each. Shown on the canvas page "Fresh directions" (board `Fresh`), all on "The Night Shift Knows".

| File | Direction | Run |
|---|---|---|
| `marble.py` | Marbled paper: drops spread on a bath, then combed; each pixel is traced back to its drop | `python3 marble.py out.png [seed]` |
| `press.py` | Letterpress: the title set in wood type to the full width, two inks overprinted | `python3 press.py out.png "Title" "Full Name" [seed]` |
| `gouache.py` | Gouache poster landscape: flat shapes, dry-brushed edges, a banded dawn sky that cuts to white | `python3 gouache.py out.png [seed]` |
| `pencil.py` | Coloured pencil landscape: short strokes that thin out to bare white paper | `python3 pencil.py out.png [seed]` |
| `pencil2.py` | Coloured pencil, round 2 (the one on the board): four muted pencils, one hatching direction, a lake at dusk | `python3 pencil2.py out.png [seed]` |
| `block.py` | Block print: a carved night scene, black plus one second colour | `python3 block.py out.png [seed]` |

Each writes a 944 x 1376 image (the 472 x 688 cover at 2x). `press.py` uses fonts that ship with macOS.
