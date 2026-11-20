"""Strata art for book screen B: drawn for the title page itself (one page, 570 x 684 CSS px), not cut from the
panorama. The page's text holds the upper left, so the land climbs the right edge: a tall teal peak with a stone cap
and the sun behind it, ranges stepping down to the left under the button, a lake across the whole foot of the page
with every peak mirrored in it, and groves framing the near shores. It runs to the page's edges.
python3 book_b.py  ->  out/bookb-title.png (1140 x 1368) and out/bookb-chapter.png (the same place from a little
further back, 1140 x 752, for the foot of the contents page)"""
import sys
sys.path.insert(0, ".")
from strata import Ridge, Blob, Water, Band, grove, trees, render
from scenes import CORAL, RUST, CLOUD, STONE_LIT, STONE_DARK, TEAL_LIT, TEAL_DARK, SAGE_LIT, SAGE_DARK, COBALT, GLINT, \
    LEAF, SHORE, HAZE_LIT, HAZE_DARK

W, H = 570, 684


def scene():
    # far to near: haze, then a stone range and a small coral peak in the middle distance, framed by a sage
    # shoulder on the left and the teal peak on the right; an islet in the lake; groves on both near shores
    haze = Ridge([(60, 500, 90, 100, 1.05), (190, 482, 120, 140, 1.1), (340, 474, 110, 120, 1.1)], 540,
                 HAZE_LIT, HAZE_DARK, seed=71, rough=3, ribs=0.6, mist=(512, 540))
    stone = Ridge([(268, 496, 100, 120, 1.15)], 552, STONE_LIT, STONE_DARK, seed=72, rough=3, ribs=0.7,
                  mist=(530, 552))
    coral = Ridge([(158, 506, 86, 104, 1.2)], 558, CORAL, RUST, seed=73, rough=3, ribs=0.9,
                  bands=[(532, 536, STONE_LIT, STONE_DARK)], mist=(540, 558))
    sage = Ridge([(-10, 430, 150, 170, 1.35), (112, 500, 70, 80, 1.15)], 578, SAGE_LIT, SAGE_DARK, seed=75,
                 rough=5, ribs=1.0, mist=(552, 578))
    teal = Ridge([(478, 300, 190, 150, 1.5), (382, 452, 60, 70, 1.15), (604, 400, 80, 100, 1.2)], 580,
                 TEAL_LIT, TEAL_DARK, seed=74, rough=5, ribs=1.0, lean=0.1, bands=[(292, 328, STONE_LIT, STONE_DARK)],
                 mist=(548, 580))
    return [
        Blob([(436, 354, 30, 30)], CORAL, top_light=False),
        Blob([(372, 392, 38, 6), (402, 388, 22, 5)], CLOUD),
        haze,
        Blob([(286, 456, 62, 10), (240, 462, 44, 8), (338, 462, 34, 7)], CLOUD),
        stone, coral,
        Blob([(196, 486, 40, 8), (226, 482, 26, 6)], CLOUD),
        sage, teal,
        Water(578, 684, -40, 620, COBALT, GLINT, seed=76, mirror=[haze, stone, coral, sage, teal], gaps=(1, 3),
              squash=0.6),
        Band(244, 372, 600, 612, SHORE, seed=81, lens=0.8),
        trees([262, 290, 318, 344], 606, 7, LEAF, seed=82),
        Band(-60, 214, 622, 652, SHORE, seed=77, lens=0.8),
        *grove([16, 50, 86, 122, 160], 638, 13, LEAF, seed=78),
        Band(392, 640, 648, 678, SHORE, seed=79, lens=0.7),
        *grove([418, 456, 494, 530, 566], 666, 16, LEAF, seed=80, trunk_h=1.2),
    ]


if __name__ == "__main__":
    S = 2
    foot = ("y", 672 * S, 684 * S)
    render(scene(), (0, 0, W, H), (W * S, H * S), 8, fade=[foot], seed=11).save("out/bookb-title.png")
    # on the contents spread the same land, seen from a little further back, fits under the list and the button
    render(scene(), (-60, 230, 630, 684), (W * S, 376 * S), 8, fade=[("y", 740, 752)], seed=11).save("out/bookb-chapter.png")
