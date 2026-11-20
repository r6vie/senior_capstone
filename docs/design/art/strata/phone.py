import sys; sys.path.insert(0,'.')
from strata import render
from scenes import lake, LAKE_COVER
S = 1.5  # 0.75 css scale at 2x
W, H = round(1440 * S), round(620 * S)
edge = [("y", 560 * S, 616 * S), ("x", 60 * S, 0), ("x", 1380 * S, 1440 * S)]
render(lake(), (0, 0, 1440, 620), (W, H), 6, fade=edge).save('out/lake-pano-phone.png')
x0, y0, x1, y1 = [round(v * S) for v in LAKE_COVER]
def cf(px, py):
    if not (x0 <= px < x1 and y0 <= py < y1): return 0
    return min(1, max(0, (py - (y0 + 270 * S)) / (40 * S)))
render(lake(), (0, 0, 1440, 620), (W, H), 6, fade=edge + [cf]).crop((x0, y0, x1, y1)).save('out/lake-cover-phone.png')
print(W, H, x1 - x0, y1 - y0)
