"""Strata, final: the Fresh directions strata (round 3: scenes.lake3, hero3.py) exactly as it was drawn: the same
renderer settings (bevelled slabs, colour jitter, ragged ends, default brick lengths, no joint or touch changes),
the same inks and the same elements (ribbed ranges with a stone cap and mist at their feet, a coral sun, cloud
bands, groves, a lake that mirrors the land). Only the scenes are new, composed for the cover first and for book
screen B's pages.

Cover (world 236 x 344; title on paper above y 118, name on paper below y 304): one teal massif, centred and big,
a notched summit with a stone cap, the coral sun behind it like a halo, haze ranges low on both sides with a small
coral peak, a still lake mirroring it all, a low shore with a grove at the left.
Title page (world 570 x 684; the text holds the upper left): the same massif on the right third with its shoulder
and second summit, the sun against its flank, a coral peak and haze in the middle distance, a sage slope framing
the left, the lake, groves on both near shores. The contents page shows the same place from further back.

python3 final.py -> out/final-title.png, out/final-contents.png, out/final-cover-xl.png, out/final-cover-sm.png"""
import sys
sys.path.insert(0, ".")
from strata import Ridge, Blob, Water, Band, trees, render
from scenes import TEAL_LIT, TEAL_DARK, CORAL, RUST, STONE_LIT, STONE_DARK, SAGE_LIT, SAGE_DARK, COBALT, GLINT, \
    CLOUD, SHORE, LEAF, HAZE_LIT, HAZE_DARK


CAP = (22, STONE_LIT, STONE_DARK)
CALM = dict(smooth=True, flicker=0.05)


def page():
    teal = Ridge([(470, 316, 136, 100, 1.2), (414, 410, 92, 70, 1.05), (566, 392, 76, 90, 1.2)], 590, TEAL_LIT,
                 TEAL_DARK, seed=13, rough=6, ribs=0.9, cap=(34, STONE_LIT, STONE_DARK), mist=(552, 590), **CALM)
    far = Ridge([(40, 488, 120, 130, 1.1), (200, 472, 120, 120, 1.05), (330, 496, 80, 90, 1.0)], 556,
                HAZE_LIT, HAZE_DARK, seed=17, rough=4, ribs=0.5, mist=(524, 556), **CALM)
    coral = Ridge([(212, 484, 72, 86, 1.3)], 566, CORAL, RUST, seed=12, rough=3, ribs=0.5, mist=(544, 566), **CALM)
    sage = Ridge([(-20, 470, 150, 170, 1.25), (112, 530, 62, 66, 1.1)], 594, SAGE_LIT, SAGE_DARK, seed=14, rough=5,
                 ribs=0.8, mist=(568, 594), **CALM)
    return [
        Blob([(386, 424, 34, 34)], CORAL, top_light=False),
        far,
        coral,
        Blob([(312, 550, 84, 6)], CLOUD),
        teal,
        sage,
        Water(590, 700, -40, 620, COBALT, GLINT, seed=21, mirror=[teal, coral], gaps=(1, 2), squash=0.55),
        Band(-60, 230, 640, 700, SHORE, seed=31, lens=0.5),
        trees([16, 58, 100, 142, 182], 654, 15, LEAF, seed=41),
        Band(390, 640, 652, 700, SHORE, seed=32, lens=0.5),
        trees([430, 478, 526, 568], 668, 16, LEAF, seed=42),
    ]


def cover():
    """Title and name set left at the top (to about y 100); the art fills the rest and runs off the foot."""
    teal = Ridge([(126, 126, 118, 104, 1.15), (64, 220, 62, 50, 1.0), (206, 216, 54, 74, 1.15)], 288, TEAL_LIT,
                 TEAL_DARK, seed=13, rough=3, ribs=0.9, cap=(24, STONE_LIT, STONE_DARK), mist=(266, 288), **CALM)
    far = Ridge([(16, 236, 78, 88, 1.1), (224, 232, 66, 78, 1.1)], 280, HAZE_LIT, HAZE_DARK, seed=17, rough=2,
                ribs=0.5, mist=(258, 280), **CALM)
    sage = Ridge([(-14, 240, 82, 96, 1.25)], 292, SAGE_LIT, SAGE_DARK, seed=14, rough=2, ribs=0.8, mist=(276, 292),
                 **CALM)
    return [
        Blob([(166, 160, 30, 30)], CORAL, top_light=False),
        far,
        Blob([(52, 266, 46, 4)], CLOUD),
        teal,
        sage,
        Water(288, 352, -20, 260, COBALT, GLINT, seed=21, mirror=[teal], gaps=(1, 2), squash=0.55),
        Band(-30, 104, 318, 352, SHORE, seed=31, lens=0.5),
        trees([6, 30, 54, 78], 328, 8, LEAF, seed=41),
    ]


# round 3's look (bevelled slabs, colour jitter, default brick lengths, round 3's inks), laid clean: no slivers,
# no holes between forms, no specks, ragged steps only against open sky
CLEAN = dict(clean=True)

if __name__ == "__main__":
    P = page()
    render(P, (0, 0, 570, 684), (1140, 1368), 8, **CLEAN).save("out/final-title.png")
    render(P, (-50, 260, 620, 684), (1140, 722), 8, **CLEAN).save("out/final-contents.png")
    render(cover(), (0, 0, 236, 344), (472, 688), 8, paper=(255, 255, 255), **CLEAN).save("out/final-cover-xl.png")
    render(cover(), (0, 0, 236, 344), (244, 356), 3, paper=(255, 255, 255), **CLEAN).save("out/final-cover-sm.png")
