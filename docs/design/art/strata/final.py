"""Strata, final round: the same slabs, finished and composed.

What changed from round 3, and why:
- Finish. No bevel on the slabs (it read as a game sprite); a hairline of paper between courses instead, so the
  land reads as stacked sheets. Much less colour jitter and tone flicker, so faces are calm and the ribs read.
- Palette. One family, muted: a deep teal for the hero, a cool haze for distance, warm stone, sage, and the sun as
  the only warm note. Value does the depth: dark near, pale far.
- Arrangement. One hero peak on the right third, with a shoulder so its mass is asymmetric; the sun set in the notch
  beside it, overlapping the flank, never touching an edge; three planes (sage foreground framing the left,
  stone and haze in the middle distance, mist between them); the lake carries a glint path from the sun toward the
  viewer; firs in a cluster of varied heights on the near right shore and a small pair far left, not a row.
- Trees. Lollipop crowns are gone: firs are built from courses, tier by tier.

python3 final.py -> out/final-title.png (B's title page, 1140 x 1368), out/final-contents.png (B's contents page foot,
1140 x 752), out/final-cover-xl.png (472 x 688), out/final-cover-sm.png (244 x 356)"""
import sys
sys.path.insert(0, ".")
from strata import Ridge, Blob, Water, Band, Firs, render

# round 3's inks (scenes.py), which read better than a muted set
from scenes import CORAL as SUN, HAZE_LIT as HAZE_L, HAZE_DARK as HAZE_D, STONE_LIT as STONE_L, STONE_DARK as STONE_D, \
    TEAL_LIT as TEAL_L, TEAL_DARK as TEAL_D, SAGE_LIT as SAGE_L, SAGE_DARK as SAGE_D, CLOUD, COBALT as WATER, GLINT, \
    SHORE, LEAF, RUST
MIST = CLOUD[:3]
FIR_L = LEAF[3:5]
FIR_D = LEAF[4:6]


def calm(layer, flicker=0.04):
    layer.flicker = flicker
    return layer


def page():
    """B's title page, world 570 x 684. The text holds the upper left (to x 480, down to y 390)."""
    # the massif: a sharp main summit, a rounded shoulder and a ledge stepping down its left flank, a saddle, and a
    # lower second summit to the right, so its outline is a range and not a pyramid
    hero = calm(Ridge([(470, 316, 132, 100, 1.5), (414, 404, 96, 70, 0.75), (558, 380, 72, 90, 1.2)], 590,
                      TEAL_L, TEAL_D, seed=24, rough=4,
                      ribs=0.9, lean=0.2, mist=(556, 590),
                      bands=[(316, 344, STONE_L, STONE_D)]))
    haze = calm(Ridge([(30, 492, 110, 120, 1.05), (150, 474, 100, 110, 0.9), (250, 488, 80, 90, 1.15),
                       (330, 500, 70, 80, 1.0)], 552, HAZE_L, HAZE_D, seed=21, rough=5, ribs=0.5, mist=(520, 552)))
    stone = calm(Ridge([(200, 498, 70, 80, 1.35), (240, 522, 40, 44, 0.85)], 566, SUN, RUST, seed=22, rough=4,
                       ribs=0.8, mist=(540, 566)))
    sage = calm(Ridge([(-20, 468, 150, 170, 1.2), (110, 528, 60, 64, 0.85)], 594, SAGE_L, SAGE_D, seed=23,
                      rough=6, ribs=0.9, lean=0.3, mist=(566, 594)))
    lake = Water(592, 684, -40, 620, WATER, GLINT, seed=26, mirror=[hero], gaps=(1, 3), squash=0.6)
    lake.path = (392, 14)
    return [
        Blob([(392, 414, 26, 26)], SUN, top_light=False),
        haze,
        Blob([(250, 528, 120, 6), (150, 534, 70, 5)], MIST),
        stone,
        hero,
        sage,
        Blob([(330, 560, 140, 6), (450, 566, 80, 5)], MIST),
        lake,
        Band(-60, 120, 640, 668, SHORE, seed=27, lens=0.8),
        Firs([(28, 652, 46, 9), (52, 655, 34, 7)], FIR_L, FIR_D),
        Band(392, 650, 652, 690, SHORE, seed=28, lens=0.7),
        Firs([(470, 672, 96, 17), (502, 676, 150, 23), (532, 674, 116, 19), (560, 678, 80, 14), (440, 676, 58, 12)],
             FIR_L, FIR_D, tiers=7),
    ]


def cover():
    """The cover is the centrepiece, composed for its own portrait shape (world 236 x 344): the title on paper above
    y 118, the name on paper below y 304. One massif, centred and big, its summit just under the title; a large sun
    behind the summit like a halo; haze ranges low on both sides; a still lake that mirrors the peak, with the glint
    path straight down the middle; a low near shore with two small firs at the right. Few things, each large."""
    hero = calm(Ridge([(122, 142, 90, 80, 1.5), (140, 156, 22, 24, 1.0), (78, 184, 50, 38, 0.72), (186, 190, 44, 64, 1.15)], 252, TEAL_L,
                      TEAL_D, seed=44, rough=3, ribs=1.0, lean=0.2, mist=(232, 252),
                      bands=[(142, 158, STONE_L, STONE_D)]))
    left = calm(Ridge([(-6, 200, 60, 70, 1.1), (40, 214, 40, 44, 0.9)], 248, HAZE_L, HAZE_D, seed=41, rough=2,
                      ribs=0.5, mist=(228, 248)))
    right = calm(Ridge([(230, 206, 50, 60, 1.1)], 248, HAZE_L, HAZE_D, seed=42, rough=2, ribs=0.5, mist=(228, 248)))
    sage = calm(Ridge([(-20, 222, 70, 80, 1.0)], 256, SAGE_L, SAGE_D, seed=43, rough=2, ribs=0.8, lean=0.3,
                      mist=(244, 256)))
    lake = Water(254, 302, -20, 260, WATER, GLINT, seed=46, mirror=[hero], gaps=(1, 2), squash=0.55)
    lake.path = (116, 7)
    return [
        Blob([(116, 160, 34, 34)], SUN, top_light=False),
        left,
        right,
        Blob([(60, 230, 50, 3), (196, 234, 40, 3)], MIST),
        hero,
        sage,
        lake,
        Band(160, 280, 288, 304, SHORE, seed=47, lens=0.7),
        Firs([(206, 298, 30, 6), (220, 300, 22, 5)], FIR_L, FIR_D, tiers=5),
    ]


OPTS = dict(slab_shade=False, gap=0, jitter=0.015, brick=(2.2, 9.0))

if __name__ == "__main__":
    S = 2
    render(page(), (0, 0, 570, 684), (1140, 1368), 8, fade=[("y", 1344, 1368)], seed=11, **OPTS).save("out/final-title.png")
    render(page(), (-60, 230, 630, 684), (1140, 752), 8, fade=[("y", 736, 752)], seed=11, **OPTS).save("out/final-contents.png")
    render(cover(), (0, 0, 236, 344), (944, 1376), 8, fade=[("y", 1200, 1216)], seed=5, paper=(255, 255, 255), **OPTS).save("out/final-cover-xl.png")
    render(cover(), (0, 0, 236, 344), (244, 356), 3, fade=[("y", 310, 314)], seed=5, paper=(255, 255, 255),
           **dict(OPTS, gap=0)).save("out/final-cover-sm.png")
