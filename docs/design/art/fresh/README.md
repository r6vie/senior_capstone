# Three fresh cover directions

Josef paused the voxel work and asked for three different directions tied to paper, books, drawing or painting,
one cover each. Shown on the canvas page "Fresh directions" (board `Fresh`), all on "The Night Shift Knows".

| File | Direction | Run |
|---|---|---|
| `marble.py` | Marbled paper: drops spread on a bath, then combed; each pixel is traced back to its drop | `python3 marble.py out.png [seed]` |
| `press.py` | Letterpress: the title set in wood type to the full width, two inks overprinted | `python3 press.py out.png "Title" "Full Name" [seed]` |
| `block.py` | Block print: a carved night scene, black plus one second colour | `python3 block.py out.png [seed]` |

Each writes a 944 x 1376 image (the 472 x 688 cover at 2x). `press.py` uses fonts that ship with macOS.
