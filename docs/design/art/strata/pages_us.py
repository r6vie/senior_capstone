"""Book screen B's title-page art for the covers in covers_us.py (the lakefront city and the fir forest). As in
pages_new.py, the page opens the place up into a much richer scene than its cover, in the cover's inks and at the
cover's slab size. World 570 x 684 = the title page; the text holds the upper left (about x 0-470, y 0-350), so the
art climbs highest on the right.

python3 pages_us.py [city|forest ...] -> out/page-{name}-title.png"""
import math
import random
import sys
sys.path.insert(0, ".")
from strata import Ridge, Blob, Water, Band, River, Grove, Firs, grove, render
from covers_new import Blocks, disc
from covers_us import (tower, DUSK_SUN, TOWER_FAR, WINDOW, LAKE, PIER, LIGHT_W, LIGHT_D, CLOUD_P, Boles, OldFir,
                       Meadow, SUN_F, GLOW, PATH, FERN)

PARK = ["#6C766C", "#667066", "#606A61"]              # lawn along the lakefront, gone slate in the dusk
PARK_TREE = ["#5F6E62", "#566559", "#4C5B50", "#43524A", "#3A4842"]
PROM = ["#C9BCB4", "#C0B3AB"]                         # the promenade, catching the last light
SAIL_L = ["#F4F0EA", "#ECE7E0"]
SAIL_D = ["#C9C3C4", "#BFB9BB"]
HULL = ["#3E4258", "#363A4E"]


def sail(x, water, h, w, flip=False):
    """A small sailboat: a stepped triangle of sail (lit on the left), a dark hull, all level blocks."""
    out = []
    for i in range(int(h / 3)):
        y = water - 4 - (i + 1) * 3
        ww = w * (1 - i / (h / 3))
        out.append((x, y, x + max(1.5, ww), y + 3, SAIL_L if i % 4 else SAIL_D))
    out.append((x - w * 0.3, water - 4, x + w * 1.1, water, HULL))
    return out


T_LIT = ["#C9A79A", "#C2A093"]
T_SHADE = ["#5E6A86", "#57627E"]
T_CAP = ["#D6B8AC", "#CFB0A4"]


WIN_LIT = ["#A6877E", "#9F8178"]         # windows on the lit face: a deeper mauve than the wall
WIN_SHADE = ["#4D5873", "#4A5570"]       # windows on the shaded face: one value darker than the wall
WIN_WARM = ["#E3C48E", "#DDBC86"]
PIER_LIT = ["#A27F75", "#9C796F"]
ROOFTOP = ["#4A4F63", "#43485C"]


def slab_tower(x0, x1, top, base=500, steps=(), style="grid", lights=0, seed=0, roof=()):
    """A tower as clean blocks: lit warm on its left two thirds, slate in shade on its right third, a pale cap course
    on top; steps: setbacks (inset, height) stacked on top, each narrower. Its facade in one of three styles, as a
    detail layer over the faces: "grid" (punched windows), "bands" (ribbon windows every other floor), "piers"
    (vertical fins on the lit face); a few windows lit warm; roof: rooftop boxes and masts (x0, y0, x1, y1)."""
    out = []
    r = random.Random(seed)
    def facade(a, b, t, bt):
        split = a + (b - a) * 0.66
        y0 = int((t + 8) // 4 * 4)
        if style == "grid":
            for y in range(y0, int(bt) - 6, 8):
                x = a + 3
                while x + 3 <= split - 2:
                    out.append(("detail", x, y, x + 3, y + 4, WIN_LIT))
                    x += 6
                x = split + 2
                while x + 3 <= b - 2:
                    out.append(("detail", x, y, x + 3, y + 4, WIN_SHADE))
                    x += 6
        elif style == "bands":
            for i, y in enumerate(range(y0, int(bt) - 14, 8)):
                if i % 4 == 3:
                    continue                      # a blank spandrel every fourth floor breaks the rhythm
                out.extend([("detail", a + 2, y, split, y + 4, WIN_LIT), ("detail", split, y, b - 2, y + 4, WIN_SHADE)])
            out.extend([("detail", a, bt - 8, split, bt, PIER_LIT), ("detail", split, bt - 8, b, bt, WIN_SHADE)])
        elif style == "piers":
            x = a + 4
            while x + 2 <= split - 2:
                out.append(("detail", x, t + 6, x + 2.5, bt - 4, PIER_LIT))
                x += 7
            x = split + 3
            while x + 2 <= b - 2:
                out.append(("detail", x, t + 6, x + 2.5, bt - 4, WIN_SHADE))
                x += 7
    def body(a, b, t, bt):
        split = a + (b - a) * 0.66
        out.extend([(a, t, split, bt, T_LIT), (a, t, split, t + 3, T_CAP), ("shade", split, t, b, bt)])
        facade(a, b, t, bt)
    body(x0, x1, top, base)
    t, a, b = top, x0, x1
    for inset, h in steps:
        a, b = a + inset, b - inset
        body(a, b, t - h, t)
        t -= h
    # a few groups of two or three lit windows side by side, on the lit face, in a muted warm ink
    split = x0 + (x1 - x0) * 0.66
    cols = max(1, int((split - x0 - 5) // 6))
    for _ in range(lights):
        n = min(cols, r.choice((2, 3)))
        c0 = r.randrange(max(1, cols - n + 1))
        y = int((top + 8) // 4 * 4) + 8 * r.randrange(max(1, int((base - top - 14) // 8)))
        for c in range(n):
            x = x0 + 3 + 6 * (c0 + c)
            out.append(("detail", x, y, x + 3, y + 4, WIN_WARM))
    out += [("detail", *bx, ROOFTOP) for bx in roof]
    return out


def city_page():
    """The lakefront at dusk, opened up: a long skyline across the water, its tallest tower with setbacks and a dark
    spire on the right climbing high, the others massed in clusters of uneven width and height, stepping down toward
    the left into a pale far skyline with the sun half set into it; pink dusk clouds; the lake wide with the main
    tower's warm reflection; a breakwater running out from the left to a small lighthouse; three sailboats coming
    home; in front, the lakefront park: a promenade, lamps, and trees on trunks in groups."""
    main = (slab_tower(488, 536, 196, steps=((5, 22), (7, 18)), style="piers", seed=1) +
            [(510, 120, 514, 160, LIGHT_D), (504, 150, 508, 156, LIGHT_D), (516, 150, 520, 156, LIGHT_D),
             # a sky-lobby band partway up and a podium band at the foot give the long shaft some structure
             ("detail", 488, 332, 520, 340, T_CAP), ("detail", 520, 332, 536, 340, WIN_SHADE),
             ("detail", 488, 484, 520, 500, PIER_LIT), ("detail", 520, 484, 536, 500, WIN_SHADE)])
    # the rest in three groups of uneven width with a gap at x 320-346 where the far skyline shows through; only the
    # main tower is tall
    rest = (slab_tower(546, 576, 380, style="bands", seed=2, roof=[(552, 372, 562, 380)]) +
            slab_tower(440, 484, 384, steps=((6, 14), (6, 10)), lights=2, seed=3, roof=[(461, 344, 463, 360)]) +
            slab_tower(414, 440, 432, seed=4) +
            slab_tower(398, 418, 410, style="piers", seed=5, roof=[(402, 404, 410, 410)]) +
            slab_tower(368, 402, 452, seed=6) + slab_tower(346, 368, 470, style="bands", seed=7) +
            slab_tower(282, 320, 418, steps=((7, 16),), style="piers", seed=8,
                       roof=[(300, 386, 302, 402)]) +
            slab_tower(262, 286, 452, seed=9) + slab_tower(236, 264, 440, seed=10,
                                                                  roof=[(240, 434, 250, 440)]) +
            slab_tower(200, 238, 470, lights=1, seed=11) + slab_tower(186, 204, 482, style="piers", seed=12))
    r = random.Random(11)
    far, x = [], -20
    while x < 600:
        w = r.uniform(12, 30)
        far.append((x, r.uniform(446, 476), x + w, 500, ["#D9CCD0", "#D2C4C9"] if r.random() < 0.6 else
                    ["#CFC2C8", "#C8BBC1"]))
        x += w
    pieces = rest + main
    # the shaded faces are their own layer, so the edge between light and shade runs clean and straight
    lit = [p for p in pieces if p[0] not in ("shade", "detail")]
    shade = [(a, t, b, bt, T_SHADE) for _, a, t, b, bt, *_ in (p for p in pieces if p[0] == "shade")]
    detail = [p[1:] for p in pieces if p[0] == "detail"]
    city = Blocks(far), Blocks(lit), Blocks(shade), Blocks(detail)
    shore = Blocks([(x, 496 + (i % 2), x + w, 504, ["#4E5268", "#474B60"]) for i, (x, w) in
                    enumerate([(-60, 150), (90, 70), (160, 140), (300, 90), (390, 260)])])
    lake = Water(500, 620, -120, 720, LAKE, ["#9AA6BE", "#A4AFC6"], seed=130, gaps=(0, 0), squash=0.5)
    lake.brick = (5.0, 14.0)
    boats = Blocks(sail(236, 600, 36, 14) + sail(340, 580, 24, 9) + sail(430, 606, 44, 16))
    pier = Blocks([(-10, 560, 200, 568, PIER[0]), (-10, 568, 204, 572, PIER[1])])
    light = Blocks([(186, 524, 196, 560, LIGHT_W), (192, 524, 196, 560, ["#CFCAC6", "#C6C1BD"]),
                    (186, 536, 196, 542, LIGHT_D), (187, 516, 195, 524, LIGHT_D), (189, 512, 193, 516, LIGHT_D)])
    lamps = Blocks([(x, 594, x + 2, 618, LIGHT_D) for x in (262, 360, 382)] +
                   [(x - 1, 590, x + 3, 594, WINDOW) for x in (262, 360, 382)])
    return [
        disc(118, 470, 26, DUSK_SUN),
        Blob([(196, 398, 40, 4.5), (232, 404, 22, 3.5), (130, 432, 34, 4), (548, 352, 26, 4)], CLOUD_P,
             top_light=False),
        *city,
        shore,
        Band(-60, 640, 500, 620, LAKE[:2], seed=134, lens=0.0),     # behind the lake: no paper anywhere in it
        lake,
        Blob([(508, 516, 12, 3), (512, 534, 8, 3), (510, 552, 5, 2.5)], ["#9C93A6", "#958CA0"],
             top_light=False),                                                       # the main tower, muted in the lake
        Blob([(118, 510, 14, 2.5), (120, 522, 9, 2.2), (117, 534, 5, 2)], ["#D9B49C", "#D2AC94"], top_light=False),
        pier, light, boats,
        # the lakefront park: promenade, lawn, lamps and trees on trunks in two uneven groups
        Band(-60, 640, 614, 622, PROM, seed=132, lens=0.0),
        Band(-60, 640, 620, 700, PARK, seed=133, lens=0.0),
        lamps,
        Blob([(40, 604, 90, 10)], ["#5B6683", "#55607C"], top_light=False),      # the water deepening, lower left
        *grove([6, 50, 110, 166], 664, 20, PARK_TREE, trunk="#3A3836", seed=135, spread=0.8, trunk_h=1.3),
        *grove([486, 546], 666, 18, PARK_TREE, trunk="#3A3836", seed=136, spread=0.8, trunk_h=1.3),
        Blob([(100, 670, 90, 5), (536, 672, 50, 5)], ["#3A4540", "#353F3A"], top_light=False),
        Blob([(300, 684, 130, 7)], ["#3E4943", "#39443E"], top_light=False),   # their shade
    ]


CREEK = ["#9FB6BE", "#93ABB4", "#879FA9"]
ROCK = (["#A9A79E", "#A09E95"], ["#76756F", "#6D6C67"])
PLANK = ["#8C6A4E", "#82614A"]


class Creek:
    """A meadow creek winding across the page: a curved band, narrow far right, wider toward the left."""

    brick = (2.5, 9.0)

    def __init__(self, line, width, colours):
        from strata import hexrgb
        self.line, self.width = line, width
        self.c = [hexrgb(c) for c in colours]

    def cover(self, x, y):
        import numpy as np
        top = np.array([self.line(v) for v in x])
        return (y >= top) & (y <= top + np.array([self.width(v) for v in x]))

    def colour(self, x, y, rng):
        return self.c[int(rng.random() * len(self.c))]


def clumped(x0, x1, base, hs, ws, seed):
    """Firs in groups of three to five with gaps between groups, every one its own height, on a wavy base."""
    r = random.Random(seed)
    out, x = [], x0
    while x < x1:
        for _ in range(r.randint(3, 5)):
            out.append((x, base(x) + r.uniform(-2, 2), r.uniform(*hs), r.uniform(*ws)))
            x += r.uniform(8, 14)
        x += r.uniform(14, 40)
    return out


def forest_page():
    """The forest opened up: a snow-capped peak far off on the right; a far stand blue in the haze; the forest on both
    sides with an opening where the trail goes in and the low sun sits in it; the meadow with the trail winding back
    and a creek crossing it under a plank footbridge; the old fir on the right edge climbing nearly to the top, a
    smaller fir beside it; boulders, ferns and a pair of young firs in the lower left as the near anchor."""
    creek_line = lambda x: 594 - 0.07 * x + 9 * math.sin(x / 55 + 0.8)
    creek_w = lambda x: 4 + max(0, 570 - x) / 95
    big = OldFir((540, 640, 500, 66), ["#5A774B", "#526E44"], ["#26392B", "#22342A"], tiers=14, seed=9,
                 broken=(6, 9), reach={11: (0.6, 1.0), 4: (1.3, 1.1), 1: (1.2, 1.25), 0: (1.25, 1.3)})
    # three groups of different heights, with haze gaps at x 60-110 and x 200-236
    left = [(4, 520, 82, 15), (24, 524, 116, 18), (46, 518, 64, 13),
            (120, 522, 70, 13), (140, 524, 132, 20), (162, 520, 96, 15), (184, 522, 58, 11),
            (240, 518, 44, 10), (254, 521, 62, 12)]
    right = [(344, 520, 70, 13), (362, 523, 110, 17), (384, 520, 62, 12), (408, 524, 128, 19), (432, 520, 84, 15),
             (452, 522, 150, 20)]
    return [
        # the peak far off on the right, its summit right of the text column
        Ridge([(436, 362, 110, 70, 0.85), (515, 395, 50, 60, 0.9), (380, 410, 50, 30, 0.9), (330, 456, 60, 40, 0.9),
               (580, 420, 40, 60, 0.9)], 490, ["#C3CDD3", "#BBC6CC"],
              ["#93A2AD", "#8B9AA5"], seed=210, rough=3, ribs=0.6, smooth=True, flicker=0.03, lean=0.25,
              cap=(30, ["#F0F2F1", "#E8EBEA"], ["#8B9AA5", "#84939E"])),
        disc(296, 460, 18, SUN_F),
        Band(-60, 640, 478, 520, ["#D6D8C2", "#CFD2BB"], seed=211, lens=0.0),
        Firs(clumped(-10, 600, lambda x: 494 + 4 * math.sin(x / 50), (26, 56), (6, 9), 21),
             ["#BAC6C2", "#B3C0BB"], ["#9CADAC", "#95A6A5"], tiers=4),
        Firs([(260 + i * 14, 512, 26 + (i * 11) % 18, 7) for i in range(6)], ["#D2D4BC", "#CBCDB4"],
             ["#B7BBA6", "#AFB39F"], tiers=4),
        Firs([(x, 522 + 9 * math.sin(x / 47 + 1), h, w) for x, _, h, w in left + right], ["#86A06C", "#7D9764"], ["#536E4C", "#4B6545"], tiers=6),
        # the meadow
        Meadow(lambda x: 516 + 4 * math.sin(x / 31 + 0.4) + 2 * math.sin(x / 11), 700,
               ["#DCD39C", "#D5CC93", "#D0C78E"]),
        Band(-60, 640, 600, 700, ["#B9B97C", "#AFB074", "#A5A76C"], seed=212, lens=0.0),
        Band(-60, 640, 640, 700, ["#A5A76C", "#9FA066", "#999A61"], seed=215, lens=0.0),
        Blob([(60, 532, 30, 3), (420, 534, 34, 3), (180, 560, 24, 3), (380, 576, 30, 3.5), (120, 650, 30, 4)],
             ["#A3A266", "#9A9A60"], top_light=False),
        Creek(lambda x: creek_line(x) - 2, lambda x: creek_w(x) + 4, ["#8E9A68", "#868F60"]),   # its banks
        Creek(creek_line, creek_w, CREEK),
        # a copse out in the meadow left of the trail, and its shadow
        Blob([(196, 578, 44, 4)], ["#9A9A60", "#929259"], top_light=False),
        Firs([(150, 576, 66, 14), (172, 580, 92, 17), (198, 578, 54, 12), (218, 581, 40, 10)],
             ["#7A9663", "#728E5C"], ["#4A6444", "#435C3E"], tiers=6),
        River(514, 700, 300, 34, 4, 70, PATH, GLOW, swings=1.1, phase=0.5, seed=213),
        # the plank footbridge where the trail crosses the creek
        Blob([(336, 596, 16, 2.4)], ["#8E955E", "#868D58"], top_light=False),
        Blocks([(296, 580, 344, 584, ["#A8876A", "#A08064"]), (296, 584, 344, 590, PLANK),
                (296, 590, 344, 593, ["#5E4634", "#563F2F"]),
                (296, 570, 300, 593, ["#5E4634", "#563F2F"]), (340, 570, 344, 593, ["#5E4634", "#563F2F"])]),
        # shadows thrown right
        Blob([(560, 646, 60, 6), (500, 628, 50, 5), (480, 600, 30, 4), (90, 676, 40, 5)], ["#8E955E", "#868D58"], top_light=False),
        Firs([(474, 600, 130, 26)], ["#7A9663", "#728E5C"], ["#4A6444", "#435C3E"], tiers=8),
        Boles([(540, 600, 690, 8, 0, (["#7A5240", "#704A3A"], ["#4A3128", "#422B23"]))]),
        big,
        # the near anchor: boulders, young firs and ferns in the lower left
        Firs([(18, 692, 168, 32), (64, 696, 112, 22), (100, 698, 70, 15)], ["#7A9663", "#728E5C"], ["#3E5A3E", "#385238"], tiers=7),
        Grove([(104, 692, 30, 9), (196, 698, 22, 7), (4, 694, 26, 8)], FERN),
        Ridge([(160, 658, 22, 18, 0.7)], 684, ROCK[0], ["#66655F", "#5F5E59"], seed=214, rough=1, smooth=True,
              flicker=0.02),                                                         # one clear boulder
    ]


SCENES = {"city": city_page, "forest": forest_page}

if __name__ == "__main__":
    for name in sys.argv[1:] or list(SCENES):
        img = render(SCENES[name](), (-8, 0, 578, 684), (1172, 1368), 8, clean=True, jitter=0.04)
        img.crop((16, 0, 1156, 1368)).save(f"out/page-{name}-title.png")
