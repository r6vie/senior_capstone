"""Strata covers chosen to be relatable for American members (Josef, 2026-11-20/21): a lakefront city at dusk and
an old-growth forest in morning haze (the prairie farm and the bay bridge were dropped). Same style and rules as covers_new.py (see CRITIC.md):
236 x 344 world, title and name on paper at the top, art below y ~180 left of x ~200 (the shelf-size name line),
light from the left, no UI red.

python3 covers_us.py [city|forest ...] -> out/us-{name}-{xl,sm}.png"""
import math
import sys
sys.path.insert(0, ".")
from strata import Ridge, Blob, Water, Band, Mesa, River, Grove, Firs, render
from covers_new import Blocks, disc

# ---- 1 lakefront city at dusk ----
DUSK_SUN = ["#F4C79A", "#F0B988", "#EBAB78"]
TOWER_L = ["#C9A79A", "#BF9C8F", "#B49184"]          # faces catching the last warm light
TOWER_D = ["#5E6A86", "#55607C", "#4C5672"]          # faces in shade, slate blue
TOWER_FAR = (["#D9CCD0", "#D2C4C9"], ["#A9AABD", "#A1A2B6"])
WINDOW = ["#F2D58E", "#EBCB7E"]
LAKE = ["#7C8BA8", "#72809D", "#687592", "#5F6B87"]
LAKE_G = ["#D9B7A6", "#C9AFA8"]
PIER = (["#8C8478", "#80786D"], ["#4E4A46", "#45413E"])
LIGHT_W = ["#F1EEE8", "#E7E3DC"]
LIGHT_D = ["#4A4448", "#403B3F"]
CLOUD_P = ["#F2DCD6", "#EBD2CC", "#E4C8C3"]


def tower(cx, top, hw, base, seed, lit=TOWER_L, dark=TOWER_D):
    return Mesa(cx, top, hw, hw, base, lit, dark, ledges=1, bed=8, seed=seed, wobble=0, speckle=0, ragged=0,
                flicker=0.0)


def city():
    """The skyline across the lake at dusk: one dominant tower with a setback crown on the right (the only thing above
    the name line), five more of uneven height and width with gaps between them; a continuous pale far skyline behind
    with the sun half set into it on the left; faces lit warm on the left, slate in shade on the right, a few lit
    windows clustered on two towers; the lake below with a warm reflection under the main tower; a short breakwater
    stepping out to a small lighthouse, and a dark rocky shore in the lower left as the near anchor."""
    # the main tower wholly right of the name column (its left edge past x 202); the rest broken up unevenly: a
    # stepped block with a shoulder, a stub, a slim one, a low one
    towers = [tower(219, 150, 14, 280, 1), tower(219, 138, 9, 152, 11), tower(219, 126, 2, 140, 12),
              tower(172, 216, 12, 280, 3), tower(190, 232, 6, 280, 8), tower(146, 268, 6, 280, 4),
              tower(124, 226, 7, 280, 6), tower(100, 252, 6, 280, 7)]
    # the far skyline: one continuous pale band of low blocks, no paper between them
    far = [tower(x, t, 13, 280, 20 + i, *TOWER_FAR) for i, (x, t) in
           enumerate([(-6, 256), (20, 250), (46, 258), (72, 248), (98, 254), (124, 246), (150, 252), (176, 244),
                      (202, 250), (228, 246), (254, 252)])]
    windows = Blocks([(x, y, x + 2.5, y + 4, WINDOW) for x, y in
                      [(208, 176), (212, 214)]])
    lake = Water(280, 352, -120, 720, LAKE, ["#9AA6BE", "#A4AFC6"], seed=30, mirror=towers, gaps=(0, 0), squash=0.5)
    lake.brick = (5.0, 14.0)
    return [
        disc(54, 250, 18, DUSK_SUN),
        *far,
        *towers,
        windows,
        Band(-60, 300, 276, 282, ["#4E5268", "#474B60"], seed=31, lens=0.0),       # the shoreline under the city
        lake,
        # the main tower's warm reflection
        Blob([(219, 292, 8, 4), (217, 304, 6, 4), (220, 316, 5, 3.5)], ["#E5BFA4", "#DDB49A"], top_light=False),
        # one solid dark shore wedge in the lower left, the near anchor
        Ridge([(-30, 298, 30, 118, 0.85)], 352, ["#3A4058", "#353B52"], ["#2A3048", "#252A40"], seed=34, rough=3,
              ribs=0.3, smooth=True, flicker=0.02),
    ]


# ---- 2 old-growth forest in morning light ----
GLOW = ["#F7ECCF", "#F3E3BF", "#EFDAB0"]
FAR_T = (["#DDD4CB", "#D6CDC4"], ["#C7BEBB", "#BFB6B3"])          # far trunks, lost in the haze
MID_T = (["#BC9278", "#B3896F"], ["#8A6656", "#805D4F"])
NEAR_T = (["#A06A4E", "#976247"], ["#5E3D31", "#55372C"])          # bark: brown, never the UI red
GIANT_T = (["#9A6448", "#905C42", "#A46E50"], ["#4E3229", "#462D25", "#563830"])
FLOOR_FAR = ["#D3D6B4", "#CACEA9"]
FLOOR = ["#9DAA78", "#93A06E", "#899665", "#7F8C5C"]
MOSS_D = ["#5F6E45", "#56653E", "#4D5B37"]
PATH = ["#EDE0BC", "#E6D7B0", "#DECDA3"]
FERN = ["#6F8A4C", "#637E44", "#56703C", "#47602F", "#3B5128"]


class Boles:
    """Tree trunks rising out of the forest floor into the morning haze: each trunk tapers a little, flares at its
    root, is lit on the left and in shade on the right, and dissolves upward into paper by omitted slabs and paling,
    never a hard cut. trunk: (cx, top, base, half_width, fade_len, (lit, dark))."""

    brick = (1.2, 4.0)
    ragged = 0
    min_run = 0.5

    def __init__(self, trunks):
        from strata import hexrgb
        self.t = [(cx, top, base, hw, fl, [hexrgb(c) for c in lit], [hexrgb(c) for c in dark])
                  for cx, top, base, hw, fl, (lit, dark) in trunks]

    def _hw(self, tr, y):
        cx, top, base, hw, fl, _, _ = tr
        if not (top <= y <= base):
            return -1
        w = hw * (0.85 + 0.15 * (y - top) / max(1, base - top))
        root = max(0, (y - (base - hw * 2.2)) / (hw * 2.2))
        return w + hw * 0.9 * root ** 2

    def _fade(self, tr, y):
        cx, top, base, hw, fl, _, _ = tr
        return 0 if fl <= 0 else max(0.0, min(1.0, (top + fl - y) / fl))

    def cover(self, x, y):
        import numpy as np
        from strata import _h
        m = np.zeros_like(x, dtype=bool)
        for i, tr in enumerate(self.t):
            hw = self._hw(tr, y)
            if hw <= 0:
                continue
            f = self._fade(tr, y)
            if f > 0 and _h(i * 7, round(y * 3), 41) < f ** 1.4:
                continue
            m |= np.abs(x - tr[0]) <= hw
        return m

    def colour(self, x, y, rng):
        from strata import mix
        best = min(self.t, key=lambda tr: abs(x - tr[0]) if self._hw(tr, y) > 0 else 1e9)
        cx, hw = best[0], self._hw(best, y)
        pal = best[5] if x < cx - hw * 0.15 else best[6]
        c = pal[int(rng.random() * len(pal))]
        f = self._fade(best, y)
        return mix(c, (255, 255, 255), f * 0.85) if f > 0 else c


def stand(clumps, base, seed, rise=0.0):
    """A tree line in clumps: firs of very uneven height standing shoulder to shoulder within a clump, with gaps of
    their own width between clumps, so the tips never comb. clump: (x0, x1, height, half_width); rise: the line of
    tips climbs this much per unit x toward the right."""
    import random
    r = random.Random(seed)
    out = []
    for x0, x1, h, hw in clumps:
        x = x0
        while x < x1:
            k = r.uniform(0.45, 1.0)
            out.append((x, base + r.uniform(-2, 2), h * k * (1 + rise * x), hw * (0.75 + 0.35 * k)))
            x += hw * r.uniform(0.9, 1.7)
    return out


class OldFir(Firs):
    """A big fir drawn by hand rather than by formula: each tier's boughs reach a different length on each side, the
    shaded right side has a short broken bough or two, and the leader is a few slabs thick."""

    min_run = 0.7

    def __init__(self, tree, lit, dark, tiers, seed=5, broken=(), reach=None):
        super().__init__([tree], lit, dark, tiers)
        import random
        r = random.Random(seed)
        self.jl = [r.uniform(0.82, 1.18) for _ in range(tiers + 1)]
        self.jr = [r.uniform(0.8, 1.15) * (0.55 if i in broken else 1) for i in range(tiers + 1)]
        for i, (l, rr) in (reach or {}).items():      # a missing or a long bough on one side
            self.jl[i], self.jr[i] = l, rr

    def _sides(self, y):
        x, base, h, w = self.t[0]
        up = base - y
        if up < 0 or up > h:
            return None
        f = up / h
        i = int(f * self.tiers)
        saw = 1 - ((f * self.tiers) % 1)
        hw = max(1.6, w * (1 - f) ** 0.9 * (0.4 + 0.6 * saw ** 0.8))
        return x - hw * self.jl[i], x + hw * self.jr[i]

    def cover(self, x, y):
        import numpy as np
        s = self._sides(y)
        if s is None:
            return np.zeros_like(x, dtype=bool)
        return (x >= s[0]) & (x <= s[1])

    def colour(self, x, y, rng):
        pal = self.lit if x < self.t[0][0] - 0.8 else self.dark
        return pal[int(rng.random() * len(pal))]


class Meadow:
    """Open ground whose edge against the trees undulates instead of running dead level."""

    brick = (2.0, 10.0)

    def __init__(self, top, base, colours):
        from strata import hexrgb
        self.top, self.base = top, base
        self.c = [hexrgb(c) for c in colours]

    def cover(self, x, y):
        import numpy as np
        return (y >= np.array([self.top(v) for v in x])) & (y <= self.base)

    def colour(self, x, y, rng):
        return self.c[int(rng.random() * len(self.c))]


SUN_F = ["#EFD49A", "#EACB8C", "#E4C27F"]


def forest():
    """A fir forest on a bright morning, seen from a trail across a meadow: the trail, an opening in the trees and the
    low sun in it line up as the focal axis; one old fir on the right edge rising high (the only thing above the name
    line), uneven and lived-in, its trunk flaring into the meadow and its shadow thrown right; a mid stand in clumps
    whose tips climb gently toward the right; small warm-hazed firs in the opening; a low fir and ferns in the lower
    left as the near anchor; the meadow edge undulating against the trees."""
    sun = disc(98, 214, 14, SUN_F)
    far = Firs(stand([(-10, 30, 62, 10), (44, 70, 50, 9), (76, 120, 40, 8), (128, 160, 54, 10), (170, 250, 64, 10)],
                     272, 70), ["#D2D4BC", "#CBCDB4"], ["#B7BBA6", "#AFB39F"], tiers=4)
    # the mid stand: two uneven groups on the left with a gap, the opening, then a clump led by one tall fir
    mid = Firs([(x, b, h * 1.35, w * 1.25) for x, b, h, w in
                [(4, 282, 40, 10), (16, 284, 54, 11), (30, 281, 30, 8), (62, 283, 46, 10), (74, 282, 28, 8),
                 (122, 282, 34, 9), (136, 283, 50, 11), (158, 285, 74, 13), (172, 282, 40, 10), (186, 284, 56, 11),
                 (198, 284, 32, 9)]], ["#86A06C", "#7D9764"], ["#536E4C", "#4B6545"], tiers=6)
    side = Firs([(180, 300, 84, 18)], ["#7A9663", "#728E5C"], ["#4A6444", "#435C3E"], tiers=6)
    corner = Firs([(14, 350, 84, 19), (40, 352, 56, 14)], ["#7A9663", "#728E5C"], ["#3E5A3E", "#385238"], tiers=5)
    big = OldFir((222, 316, 226, 40), ["#5A774B", "#526E44"], ["#26392B", "#22342A"], tiers=10, seed=8,
                 broken=(5,), reach={7: (0.55, 1.0), 3: (1.35, 1.1), 1: (1.2, 1.25), 0: (1.25, 1.3)})
    trunk = Boles([(222, 292, 340, 4.6, 0, (["#7A5240", "#704A3A"], ["#4A3128", "#422B23"]))])
    return [
        sun,
        # the haze floor behind the stands, so no paper shows between the planes
        Band(-60, 300, 264, 286, ["#D6D8C2", "#CFD2BB"], seed=60, lens=0.0),
        far,
        mid,
        # the meadow: its edge undulates against the trees; gold in the sun at the back, deepening toward us
        Meadow(lambda x: 278 + 3 * math.sin(x / 21 + 0.6) + 1.8 * math.sin(x / 8.5), 352,
               ["#DCD39C", "#D5CC93", "#D0C78E"]),
        Band(-60, 300, 304, 352, ["#B9B97C", "#AFB074", "#A5A76C"], seed=63, lens=0.0),
        # shade along the foot of the trees, and tussocks breaking up the meadow
        Meadow(lambda x: 278 + 3 * math.sin(x / 21 + 0.6) + 1.8 * math.sin(x / 8.5) if not 84 < x < 118 else 999,
               286, ["#BFB77C", "#B8B076"]),
        Blob([(30, 300, 14, 2.4), (160, 296, 12, 2.0), (66, 318, 16, 2.6), (180, 328, 18, 3), (128, 336, 14, 2.4)],
             ["#A3A266", "#9A9A60"], top_light=False),
        River(276, 352, 100, 20, 4, 44, PATH, GLOW, swings=1.0, phase=0.5, seed=62),
        # shadows thrown right by the firs across the meadow
        Blob([(200, 302, 16, 3.5), (238, 342, 30, 3), (58, 344, 20, 3)], ["#8E955E", "#868D58"], top_light=False),
        side, trunk, big, corner,
        Grove([(4, 348, 22, 7), (60, 352, 14, 5)], FERN),
    ]


SCENES = {"city": city, "forest": forest}

if __name__ == "__main__":
    for name in sys.argv[1:] or SCENES:
        fn = SCENES[name]
        render(fn(), (0, 0, 236, 344), (472, 688), 8, paper=(255, 255, 255), clean=True, jitter=0.04).save(
            f"out/us-{name}-xl.png")
        render(fn(), (0, 0, 236, 344), (244, 356), 3, paper=(255, 255, 255), clean=True, jitter=0.04).save(
            f"out/us-{name}-sm.png")
