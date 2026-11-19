# Three fresh cover directions

Josef paused the voxel work and asked for three different directions tied to paper, books, drawing or painting,
one cover each. Shown on the canvas page "Fresh directions" (board `Fresh`), all on "The Night Shift Knows".

| File | Direction | Run |
|---|---|---|
| `marble.py` | Marbled paper: drops spread on a bath, then combed; each pixel is traced back to its drop | `python3 marble.py out.png [seed]` |
| `press.py` | Letterpress: the title set in wood type to the full width, two inks overprinted | `python3 press.py out.png "Title" "Full Name" [seed]` |
| `press2.py` | Letterpress with the name tracked rule to rule under a heavy and a hairline rule (on the board) | `python3 press2.py out.png "Title" "Full Name" [seed]` |
| `pencil3_band.py` | The coloured-pencil lake as a 1440 x 620 band for the book page, clear under the title | `python3 pencil3_band.py out.png [seed]` |
| `wash2_band.py` | The watercolour brushstrokes as a 1440 x 620 band for the book page | `python3 wash2_band.py out.png [seed]` |
| `stipple_band.py` | The stippled dunes as a 1440 x 620 band for the book page | `python3 stipple_band.py out.png [seed]` |
| `block_band.py` | The block print as a 1440 x 620 band: carved night panels at both ends, one street across | `python3 block_band.py out.png [seed]` |
| `gouache2_band.py` | The gouache alpine lake as a 1440 x 620 band, cut out on bare paper | `python3 gouache2_band.py out.png [seed]` |
| `gouache.py` | Gouache poster landscape: flat shapes, dry-brushed edges, a banded dawn sky that cuts to white | `python3 gouache.py out.png [seed]` |
| `pencil.py` | Coloured pencil landscape: short strokes that thin out to bare white paper | `python3 pencil.py out.png [seed]` |
| `pencil2.py` | Coloured pencil, round 2 (the one on the board): four muted pencils, one hatching direction, a lake at dusk | `python3 pencil2.py out.png [seed]` |
| `wash.py` | Loose watercolour: a wet-in-wet dusk sky over still water; pigment pools at edges, granulates and blooms | `python3 wash.py out.png [seed]` |
| `gouache2.py` | Gouache, round 2 (on the board): an alpine lake drawn like a travel poster | `python3 gouache2.py out.png [seed]` |
| `pencil3.py` | Coloured pencil, round 3 (on the board): deeper tones, cabin, jetty, firs, reeds | `python3 pencil3.py out.png [seed]` |
| `wash2.py` | Watercolour, round 2 (on the board): the scene as a handful of brushstrokes | `python3 wash2.py out.png [seed]` |
| `papercut.py` | Layered cut paper: stacked sheets with shadows; the white cover is the top sheet | `python3 papercut.py out.png [seed]` |
| `stipple.py` | Stippled ink: dots only, two inks, dunes under a moon | `python3 stipple.py out.png [seed]` |
| `block.py` | Block print: a carved night scene, black plus one second colour | `python3 block.py out.png [seed]` |

Each writes a 944 x 1376 image (the 472 x 688 cover at 2x). `press.py` uses fonts that ship with macOS.
