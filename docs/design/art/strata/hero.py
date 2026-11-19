import sys; sys.path.insert(0,'.')
from strata import render
from scenes import lake, LAKE_COVER
S = 2  # output px per world px
W, H = 1440 * S, 620 * S
edge = [("y", 560 * S, 616 * S), ("x", 60 * S, 0), ("x", 1380 * S, 1440 * S)]
pano = render(lake(), (0, 0, 1440, 620), (W, H), 8, fade=edge)
pano.save('out/lake-pano.png')
x0, y0, x1, y1 = [v * S for v in LAKE_COVER]
def cover_fade(px, py):
    if not (x0 <= px < x1 and y0 <= py < y1):
        return 0
    return min(1, max(0, (py - (y0 + 270 * S)) / (40 * S)))
c = render(lake(), (0, 0, 1440, 620), (W, H), 8, fade=edge + [cover_fade]).crop((x0, y0, x1, y1))
c.save('out/lake-cover-lg.png')
