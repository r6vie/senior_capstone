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


def page():
    teal = Ridge([(470, 316, 132, 100, 1.45), (492, 342, 26, 28, 1.0), (414, 404, 90, 70, 1.1), (560, 380, 72, 90, 1.2)],
                 590, TEAL_LIT, TEAL_DARK, seed=13, rough=7, ribs=1.0, bands=[(316, 348, STONE_LIT, STONE_DARK)],
                 mist=(552, 590))
    far = Ridge([(40, 486, 120, 130, 1.1), (200, 470, 120, 120, 1.05), (330, 494, 80, 90, 1.0)], 556,
                HAZE_LIT, HAZE_DARK, seed=17, rough=4, ribs=0.6, mist=(524, 556))
    coral = Ridge([(210, 482, 70, 84, 1.3)], 566, CORAL, RUST, seed=12, ribs=0.9,
                  bands=[(530, 535, STONE_LIT, STONE_DARK)], mist=(544, 566))
    sage = Ridge([(-20, 470, 150, 170, 1.25), (110, 528, 60, 64, 1.1)], 594, SAGE_LIT, SAGE_DARK, seed=14, rough=7,
                 ribs=1.0, mist=(568, 594))
    return [
        Blob([(392, 420, 34, 34)], CORAL, top_light=False),
        far,
        coral,
        Blob([(300, 548, 90, 6), (120, 552, 60, 5)], CLOUD),
        teal,
        sage,
        Water(590, 652, -40, 620, COBALT, GLINT, seed=21, mirror=[far, coral, teal, sage], gaps=(1, 3), squash=0.55),
        Band(-60, 230, 636, 668, SHORE, seed=31, lens=0.8),
        trees([10, 50, 90, 130, 170], 650, 15, LEAF, seed=41),
        Band(380, 640, 648, 690, SHORE, seed=32, lens=0.8),
        trees([420, 470, 520, 560], 666, 17, LEAF, seed=42),
    ]


def cover():
    teal = Ridge([(112, 128, 96, 86, 1.45), (64, 200, 50, 40, 1.0), (190, 198, 40, 62, 1.15)],
                 256, TEAL_LIT, TEAL_DARK, seed=13, rough=2.5, ribs=1.0, bands=[(128, 150, STONE_LIT, STONE_DARK)],
                 mist=(236, 256))
    far = Ridge([(20, 214, 70, 80, 1.1), (216, 210, 60, 70, 1.1)], 250, HAZE_LIT, HAZE_DARK, seed=17, rough=3,
                ribs=0.6, mist=(230, 250))
    coral = Ridge([(198, 204, 36, 46, 1.2)], 252, CORAL, RUST, seed=12, rough=3, ribs=0.9,
                  bands=[(226, 229, STONE_LIT, STONE_DARK)], mist=(238, 252))
    sage = Ridge([(-14, 214, 70, 84, 1.3)], 258, SAGE_LIT, SAGE_DARK, seed=14, rough=4, ribs=1.0, mist=(244, 258))
    return [
        Blob([(146, 158, 26, 26)], CORAL, top_light=False),
        far,
        coral,
        Blob([(60, 234, 40, 5), (200, 238, 34, 4)], CLOUD),
        teal,
        sage,
        Water(256, 302, -20, 260, COBALT, GLINT, seed=21, mirror=[far, coral, teal, sage], gaps=(1, 3), squash=0.55),
        Band(-30, 96, 286, 302, SHORE, seed=31, lens=0.8),
        trees([4, 26, 48, 70], 294, 7, LEAF, seed=41),
    ]


OLD = dict(touch=False)   # round 3's rules exactly: the renderer's defaults, with the old independent ragged ends

if __name__ == "__main__":
    P = page()
    render(P, (0, 0, 570, 684), (1140, 1368), 8, fade=[("y", 1330, 1368)], **OLD).save("out/final-title.png")
    render(P, (-50, 260, 620, 684), (1140, 722), 8, fade=[("y", 690, 722)], **OLD).save("out/final-contents.png")
    k = 2
    render(cover(), (0, 0, 236, 344), (472, 688), 8, fade=[("y", 296 * k, 308 * k)], paper=(255, 255, 255),
           **OLD).save("out/final-cover-xl.png")
    k = 356 / 344
    render(cover(), (0, 0, 236, 344), (244, 356), 3, fade=[("y", 296 * k, 308 * k)], paper=(255, 255, 255),
           **OLD).save("out/final-cover-sm.png")
