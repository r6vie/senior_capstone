# Voxel covers

Book-cover art built as small-cube (voxel) scenes and rendered in Blender, after Josef's references. Round 1 is
one design, "the valley": a blue range, cream mounds with coral strata, cumulus banks, and a wooded island with a
river that dissolves into white. The top of the frame is left empty for the title and the foot for the full name.
On the canvas: page "Voxel covers", board `VoxelValley`. Waiting on Josef (see `docs/design/decisions.md`).

| File | What it does |
|---|---|
| `voxel.py` | Builds the voxel grid with NumPy, turns exposed cells into one mesh of slightly shrunk slab cubes, lights it (raking sun from the left, white sky) and renders in Cycles |
| `comp.py` | Lays the transparent render on white cover paper |
| `board.py` | Writes the canvas board (needs `../strata/boards.py` beside it for the shared page shell) |

Render the cover at twice the large size (944 x 1376), about 12 seconds on this Mac:

    /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P voxel.py -- valley out.png 2 160
    python3 comp.py out.png cover.png

A new design is a new scene function in `voxel.py` (terrain, colours, groves, clouds, camera) registered in `SCENES`.
