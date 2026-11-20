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

SUN = ["#F0A88A", "#EA9473", "#E2805F"]
HAZE_L = ["#D6DFE4", "#C9D4DB", "#BCCAD2"]
HAZE_D = ["#AEBDC7", "#A0B1BD", "#92A5B3"]
STONE_L = ["#ECE6DB", "#E2DACC", "#D6CCBB"]
STONE_D = ["#B9AE9C", "#A49886", "#8E8271"]
TEAL_L = ["#86A6AC", "#7497A0", "#638892", "#547983"]
TEAL_D = ["#33545B", "#294950", "#203E45", "#18333A"]
SAGE_L = ["#AFBAA9", "#9DAA97", "#8C9A86"]
SAGE_D = ["#617164", "#516155", "#425146"]
MIST = ["#F2F2EE", "#E9EAE6", "#DFE1DD"]
WATER = ["#CEDCE5", "#BBCDDA", "#A7BFCF", "#93AFC4", "#7F9FB8"]
GLINT = ["#F6F5F0", "#ECEEEC", "#E1E7EA"]
SHORE = ["#CDD0B3", "#C0C5A4", "#B2B995"]
FIR_L = ["#4D6858", "#43604F"]
FIR_D = ["#24372E", "#1D2E26"]


def calm(layer, flicker=0.04):
    layer.flicker = flicker
    return layer


def page():
    """B's title page, world 570 x 684. The text holds the upper left (to x 480, down to y 390)."""
    hero = calm(Ridge([(452, 318, 150, 110, 1.5), (386, 414, 64, 56, 1.1), (552, 416, 80, 90, 1.2)], 590, TEAL_L,
                      TEAL_D, seed=24, rough=6, ribs=0.9, lean=0.18, mist=(556, 590)))
    haze = calm(Ridge([(40, 486, 120, 130, 1.1), (190, 470, 130, 120, 1.1), (318, 492, 90, 100, 1.05)], 552,
                      HAZE_L, HAZE_D, seed=21, rough=3, ribs=0.5, mist=(520, 552)))
    stone = calm(Ridge([(236, 500, 96, 110, 1.2)], 566, STONE_L, STONE_D, seed=22, rough=3, ribs=0.7,
                       mist=(536, 566)))
    sage = calm(Ridge([(-30, 452, 190, 210, 1.35), (120, 520, 60, 70, 1.15)], 594, SAGE_L, SAGE_D, seed=23,
                      rough=5, ribs=0.9, lean=0.3, mist=(566, 594)))
    lake = Water(592, 684, -40, 620, WATER, GLINT, seed=26, mirror=[hero], gaps=(1, 3), squash=0.6)
    lake.path = (404, 14)
    return [
        Blob([(404, 400, 26, 26)], SUN, top_light=False),
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
    """The cover, world 236 x 344: title on paper above y 118, the name on paper below y 300."""
    hero = calm(Ridge([(150, 144, 80, 62, 1.5), (118, 196, 34, 30, 1.1), (206, 196, 46, 50, 1.2)], 262, TEAL_L, TEAL_D, seed=34,
                      rough=3, ribs=0.9, lean=0.22, mist=(240, 262)))
    haze = calm(Ridge([(20, 214, 70, 70, 1.1), (96, 206, 70, 66, 1.1)], 246, HAZE_L, HAZE_D, seed=31, rough=2,
                      ribs=0.5, mist=(230, 246)))
    sage = calm(Ridge([(-14, 200, 80, 96, 1.3)], 264, SAGE_L, SAGE_D, seed=33, rough=3, ribs=0.9, lean=0.3,
                      mist=(250, 264)))
    lake = Water(262, 300, -20, 260, WATER, GLINT, seed=36, mirror=[hero], gaps=(1, 3), squash=0.6)
    lake.path = (112, 8)
    return [
        Blob([(112, 186, 15, 15)], SUN, top_light=False),
        haze,
        Blob([(80, 236, 54, 4)], MIST),
        hero,
        sage,
        lake,
        Band(150, 260, 284, 300, SHORE, seed=37, lens=0.7),
        Firs([(184, 292, 38, 8), (200, 294, 56, 10), (216, 293, 42, 8), (230, 295, 28, 6)], FIR_L, FIR_D, tiers=6),
    ]


OPTS = dict(slab_shade=False, gap=1, jitter=0.015, brick=(2.2, 9.0))

if __name__ == "__main__":
    S = 2
    render(page(), (0, 0, 570, 684), (1140, 1368), 8, fade=[("y", 1344, 1368)], seed=11, **OPTS).save("out/final-title.png")
    render(page(), (-60, 230, 630, 684), (1140, 752), 8, fade=[("y", 736, 752)], seed=11, **OPTS).save("out/final-contents.png")
    render(cover(), (0, 0, 236, 344), (472, 688), 6, fade=[("y", 596, 604)], seed=5, paper=(255, 255, 255), **OPTS).save("out/final-cover-xl.png")
    render(cover(), (0, 0, 236, 344), (244, 356), 3, fade=[("y", 308, 312)], seed=5, paper=(255, 255, 255),
           **dict(OPTS, gap=0)).save("out/final-cover-sm.png")
