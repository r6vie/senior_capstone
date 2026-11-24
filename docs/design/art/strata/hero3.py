"""Round 3 of the lake: the panorama at 1440 x 620 (2x) and its covers, cut from the same drawing.
python3 hero3.py  ->  out/lake3-pano.png, out/lake3-cover-xl.png (472 x 688), out/lake3-cover-sm.png (244 x 356)"""
import sys; sys.path.insert(0, '.')
from strata import render
from scenes import lake3, LAKE_COVER
S = 2
W, H = 1440 * S, 620 * S
edge = [("y", 560 * S, 616 * S), ("x", 60 * S, 0), ("x", 1380 * S, 1440 * S)]
render(lake3(), (0, 0, 1440, 620), (W, H), 8, fade=edge).save('out/lake3-pano.png')
x0, y0, x1, y1 = [v * S for v in LAKE_COVER]
def cover_fade(px, py):
    if not (x0 <= px < x1 and y0 <= py < y1):
        return 0
    return min(1, max(0, (py - (y0 + 270 * S)) / (40 * S)))
render(lake3(), (0, 0, 1440, 620), (W, H), 8, fade=edge + [cover_fade]).crop((x0, y0, x1, y1)).save('out/lake3-cover-xl.png')
k = 356 / 344
render(lake3(), LAKE_COVER, (244, 356), 3, fade=[("y", 270 * k, 310 * k)], paper=(255, 255, 255)).save('out/lake3-cover-sm.png')
