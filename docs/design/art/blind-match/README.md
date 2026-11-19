# Blind match against the reference

Josef asked for the cover art to match his reference (a voxel landscape) and for every iteration to be judged blind:
a fresh judge sees the reference and the attempt side by side in random order, says which is better and which is the
original. Iterate until it can't tell.

| Round | Method | Judge picked the reference? | Confidence |
|---|---|---|---|
| 1-2 | 2D cells (`cells.py`, `refscene.py`) | yes | 92, 92 |
| 3 | Blender cubes, orthographic | yes | 85 |
| 4-8 | Smooth Blender render, pixelated per material (`scene.py` + `pixelate.py`) | yes | 88, 85, 92, 88, 88 |
| 9 | Same scene voxelised with block remeshing | yes | 80 |
| 10-11 | Voxel refinements | yes | 85, 92 |
| 12-13 | Hand-built voxels (`vox.py` + `post.py`): brick-laid hill blocks, coral on right-facing flanks, branching trees, stroked river | yes | 88, 85 |

`answers.txt` records which side the reference was on each round (the judges never saw it).

Run: `blender -b --factory-startup -P scene.py -- beauty.png id.png 64`, then
`ONLY=3 python3 pixelate.py beauty.png id.png out.png` (ONLY limits the pixelation to some materials; 3 is water).
`compare.py` makes the blind side-by-side from `ref.png` (a crop of Josef's reference, not committed).

From round 12: `blender -b --factory-startup -P vox.py -- out.png 64`, then `python3 post.py out.png final.png`.
