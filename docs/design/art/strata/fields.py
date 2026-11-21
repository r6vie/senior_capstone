"""Long fields (Josef, 2026-11-21: "I am not a fan of the rice terraces actually, can we turn them into long fields
instead?"): the place of "The Patient Field" becomes rolling farmland, long strips of crops running across the land
in perspective and draped over the swells, hedgerow lines between them, the low sun on the left. Replaces the rice
terraces cover (covers_new.rice) and page (pages_new.terraces).

The land is a height field seen from above the near edge: depth t runs 0 at the horizon to 1 at the near edge; a
surface point (x, t) lands on screen at y(x, t) = base(t) - swell(x, t). For each column the nearest surface point
at or above a screen y is what you see there, so a swell hides the strips behind it, as a real hill does. Strips are
bands of t, their edges wavering a little in x; faces that fall away to the right (the screen y rising toward the
right) are in shade, so the light comes from the left.

python3 fields.py [cover|page ...] -> out/fields-cover-{xl,sm}.png, out/page-fields-title.png"""
import math
import random
import sys
import numpy as np
sys.path.insert(0, ".")
from strata import Ridge, Blob, Band, Grove, Trunks, hexrgb, render
from covers_new import disc, Blocks

# crops in pairs of (lit, shade) inks, muted and warm in the low sun; no colour near the UI red
WHEAT = (["#EDD39A", "#E8CA8B"], ["#B8955E", "#AC8A56"])
SAGE = (["#B8C08A", "#AEB77F"], ["#77824F", "#6F7A4A"])
GREEN = (["#93A86C", "#899F63"], ["#627843", "#5A6F3D"])
OCHRE = (["#DDB775", "#D6AD69"], ["#96734A", "#8C6B42"])
PLOW = (["#B98F6E", "#B08566"], ["#86634C", "#7C5B46"])
PALE = (["#E6DDB0", "#E0D6A6"], ["#B8A878", "#AFA070"])
DEEP = (["#6F8752", "#667D4B"], ["#455A35", "#3E5230"])
HEDGE = ["#4E5F3A", "#465634", "#3E4D2E"]


class Land:
    """Long fields over rolling land. swells: (x, t, half width in x, half depth in t, height in world px)."""

    brick = (2.4, 10.0)
    min_run = 1.0

    def __init__(self, horizon, near, x0, x1, swells, strips, seed=1, hedge=HEDGE, power=1.6, cross=(), vx=120, grain=1.0, near_t=0.97):
        self.h, self.n, self.x0, self.x1 = horizon, near, x0, x1
        self.swells, self.power, self.seed = swells, power, seed
        r = random.Random(seed)
        # strip edges in t: narrow far, wide near, each its own width
        self.edges, t = [0.0], 0.0
        for _ in range(200):
            t += r.uniform(0.7, 1.4) * (0.05 + 0.2 * t) * grain
            if t >= 1.2:
                break
            self.edges.append(t)
        self.strips = [([hexrgb(c) for c in a], [hexrgb(c) for c in b]) for a, b in strips]
        self.order = [r.randrange(len(strips)) for _ in self.edges]
        for i in range(1, len(self.order)):                 # no two neighbours alike
            while self.order[i] == self.order[i - 1]:
                self.order[i] = r.randrange(len(strips))
        self.phase = [r.uniform(0, 6.28) for _ in self.edges]
        # a hedgerow on roughly half the strip edges, never two missing in a row: the across-bands stop dominating
        self.hedged = [r.random() < 0.5 or i % 2 == 0 for i in range(len(self.edges))]
        self.hedge = [hexrgb(c) for c in hedge]
        # field boundaries running toward us, converging on a point on the horizon: (x where it meets the near edge,
        # t from, t to); fields change crop across them
        self.cross, self.vx = cross, vx
        self.near_strip = ([hexrgb(c) for c in DEEP[0]], [hexrgb(c) for c in DEEP[1]])
        self.near_t = near_t
        self.xs = np.arange(x0, x1 + 0.5, 0.5)
        self.ts = np.linspace(0, 1.15, 700)
        X, T = np.meshgrid(self.xs, self.ts)
        self.Y = self._y(X, T)                              # rows: t, cols: x
        # for each column, running minimum from the near edge back: what the eye sees above each point
        self.skyline = self.Y.min(axis=0)

    def _y(self, x, t):
        y = self.h + (self.n - self.h) * np.power(np.clip(t, 0, None), self.power)
        for sx, st, wx, wt, hgt in self.swells:
            y = y - hgt * np.exp(-((x - sx) / wx) ** 2 - ((t - st) / wt) ** 2)
        return y

    def _col(self, x):
        return int(np.clip(round((x - self.x0) / 0.5), 0, len(self.xs) - 1))

    def cover(self, x, y):
        cols = np.clip(np.round((np.asarray(x) - self.x0) / 0.5).astype(int), 0, len(self.xs) - 1)
        return y >= self.skyline[cols]

    def t_at(self, x, y):
        c = self.Y[:, self._col(x)]
        ok = np.flatnonzero(c <= y)
        return self.ts[ok.max()] if len(ok) else 0.0

    def colour(self, x, y, rng):
        t = self.t_at(x, y)
        tw = t + 0.012 * (0.3 + t) * math.sin(x / 37.0 + self.seed)        # strip edges waver a little
        i = max(0, int(np.searchsorted(self.edges, tw, side="right")) - 1)
        i = min(i, len(self.order) - 1)
        e0 = self.edges[i]
        e1 = self.edges[i + 1] if i + 1 < len(self.edges) else 9
        # the hedgerow along each strip's near edge, thicker as it comes near
        k = self._col(x)
        ti = int(np.clip(np.searchsorted(self.ts, t), 0, len(self.ts) - 1))
        dy = self.Y[ti, min(k + 4, len(self.xs) - 1)] - self.Y[ti, max(k - 4, 0)]
        if self.hedged[i] and dy <= 0.6 and (e1 - tw) < 0.004 + 0.016 * t and t > 0.03:
            return self.hedge[i % len(self.hedge)]
        seg = 0
        f = (self.h + (self.n - self.h) * t ** self.power - self.h) / (self.n - self.h)
        for xn, t0, t1 in self.cross:
            xl = self.vx + (xn - self.vx) * f
            if t0 <= t <= t1:
                if abs(x - xl) < 0.6 + 3.0 * t:
                    return self.hedge[1]
                if x > xl:
                    seg += 1
        # shade: the surface falls toward the right
        if self.near_strip is not None and t > self.near_t:
            lit, dark = self.near_strip
        else:
            lit, dark = self.strips[(self.order[i] + 2 * seg) % len(self.strips)]
        pal = dark if dy > 0.6 else lit
        return pal[int(rng.random() * len(pal))]


FAR = (["#C9C2D6", "#C2BBCF"], ["#A9A2BE", "#A29BB7"])
SUN = ["#F3CD8C", "#F0C47E", "#EAB972"]
TREE = ["#5E7446", "#536940", "#475C37", "#3B4E2E"]
CROPS = [WHEAT, SAGE, GREEN, OCHRE, PLOW, PALE]


def lone_tree(x, ground, s, seed):
    r = random.Random(seed)
    e = [(x + r.uniform(-s, s) * 0.6, ground - s * 1.25 - r.uniform(0, s * 0.45), s * r.uniform(0.7, 1.0),
          s * r.uniform(0.55, 0.75)) for _ in range(5)]
    trunk = Trunks([(x, ground - s * 1.3, ground, max(1.1, s * 0.15))], "#4A3A2C")
    trunk.min_run = 0.4          # a trunk is narrower than a slab and a half; clean mode must keep it
    return [trunk, Grove(e, TREE)]


def cover():
    """Long fields at harvest, minimal: a low lilac horizon with the sun just above it on the left; the land rises
    into one long swell on the right (the only thing above the name line), the strips of wheat, sage, green, ochre
    and ploughed earth running across it and bending over its shoulder, shaded where it falls away to the right; a
    lone tree on the crest; the strips widen toward us and the near edge is a broad green field."""
    # no ploughed strip on the cover: on the crest it sat like a brown cap
    land = Land(222, 380, -20, 260, [(222, 0.30, 90, 0.26, 52), (30, 0.72, 90, 0.2, 32)],
                [WHEAT, SAGE, GREEN, OCHRE, PALE], seed=7,
                cross=[(-40, 0.10, 1.2), (90, 0.1, 1.2), (170, 0.15, 1.2), (250, 0.2, 1.2)], vx=60, grain=1.5)
    crest_y = float(land.skyline[land._col(214)])
    return [
        disc(58, 204, 13, SUN),
        Ridge([(40, 208, 90, 80, 1.0), (150, 212, 80, 90, 1.0)], 224, *FAR, seed=301, rough=2, smooth=True,
              flicker=0.02),
        land,
        *lone_tree(214, crest_y + 2, 11, 302),
    ]


HOUSE_W = (["#EDE6D8", "#E5DDCC"], ["#BDB3A2", "#B3A998"])
ROOF = ["#7A5A48", "#6C4F40"]
LANE = ["#E9DDBF", "#E2D5B4", "#DACCA8"]


class Lane:
    """A farm lane winding over the land: a band of fixed width on the ground, following a path in (x, t)."""

    brick = (2.0, 8.0)
    min_run = 0.6

    def __init__(self, land, pts, width, colours):
        self.land, self.width = land, width
        self.pts = pts                      # (x, t) from far to near
        self.c = [hexrgb(c) for c in colours]

    def _x(self, t):
        ts = [p[1] for p in self.pts]
        xs = [p[0] for p in self.pts]
        return float(np.interp(t, ts, xs))

    def cover(self, x, y):
        out = np.zeros_like(x, dtype=bool)
        for i, xv in enumerate(np.asarray(x)):
            if not self.land.cover(np.array([xv]), y)[0]:
                continue
            t = self.land.t_at(xv, y)
            if t < self.pts[0][1] or t > self.pts[-1][1]:
                continue
            out[i] = abs(xv - self._x(t)) < self.width * (0.15 + t)
        return out

    def colour(self, x, y, rng):
        t = self.land.t_at(x, y)
        if x - self._x(t) > self.width * (0.15 + t) * 0.55:
            return hexrgb("#CDBF98")
        return self.c[int(rng.random() * len(self.c))]


def hedge_trees(land, xs, t, s, seed):
    """Trees standing along a hedgerow at depth t: their feet on the ground at that depth."""
    r = random.Random(seed)
    out = []
    for x in xs:
        g = float(land._y(np.array([float(x)]), np.array([t]))[0])
        k = s * (0.4 + t) * r.uniform(0.8, 1.2)
        out += lone_tree(x, g + 1, k, r.randrange(999))
    return out


def page():
    """The farmland opened up: a lilac range low on the horizon with the sun just above it on the left; the land
    rolling in three swells, the strips of crops running across them in perspective and bending over each shoulder,
    shaded where they fall away to the right; field boundaries converging on the horizon; a lane winding from the
    near edge over the middle swell to a white farmhouse with a dark roof among trees; trees along the hedgerows; on
    the right the highest swell rises with one big tree on its crest, the only thing above the text's corner."""
    land = Land(452, 760, -20, 600, [(505, 0.30, 140, 0.24, 118), (240, 0.52, 110, 0.18, 46),
                                       (60, 0.80, 140, 0.2, 30)], CROPS, seed=11,
                cross=[(-300, 0.08, 1.2), (-90, 0.12, 1.2), (-10, 0.12, 1.2), (110, 0.1, 1.2), (200, 0.14, 1.2),
                       (330, 0.16, 1.2), (560, 0.2, 1.2), (820, 0.12, 1.2)], vx=280, near_t=0.9)
    crest_x = 515
    crest_y = float(land.skyline[land._col(crest_x)])
    hx, ht = 250, 0.40
    hy = float(land._y(np.array([float(hx)]), np.array([ht]))[0])
    k = 1.6
    house = Blocks([(hx + a * k, hy + b * k, hx + c * k, hy + d * k, ink) for a, b, c, d, ink in
                    [(-14, -12, 4, 0, HOUSE_W[0]), (4, -12, 14, 0, HOUSE_W[1]),
                     # one wide, low gable in brown, about twice as wide as it is tall
                     (-17, -15, 17, -12, ROOF), (-13, -18, 13, -15, ROOF), (-8, -21, 8, -18, ROOF),
                     (-9, -8, -5, -2, ["#5E5650"]), (7, -8, 10, -2, ["#7A7066"])]])
    return [
        disc(120, 440, 20, SUN),
        Ridge([(80, 432, 140, 120, 1.0), (300, 438, 120, 140, 1.0), (470, 426, 90, 100, 1.0)], 456, *FAR,
              seed=401, rough=2, smooth=True, flicker=0.02),
        land,
        Lane(land, [(262, 0.40), (300, 0.5), (230, 0.62), (190, 0.78), (250, 1.0), (300, 1.15)], 14, LANE),
        *hedge_trees(land, [200, 284, 300], 0.40, 11, 402),
        house,
        *hedge_trees(land, [60, 92, 360, 420], 0.56, 11, 403),
        *hedge_trees(land, [20], 0.86, 10, 404),
        *hedge_trees(land, [470, 500, 532], 0.9, 14, 406),
        *lone_tree(crest_x, crest_y + 4, 22, 405),
    ]


if __name__ == "__main__":
    for name in sys.argv[1:] or ["cover", "page"]:
        if name == "page":
            img = render(page(), (-8, 0, 578, 684), (1172, 1368), 8, clean=True, jitter=0.04)
            img.crop((16, 0, 1156, 1368)).save("out/page-fields-title.png")
        if name == "cover":
            render(cover(), (0, 0, 236, 344), (472, 688), 8, paper=(255, 255, 255), clean=True, jitter=0.04).save(
                "out/fields-cover-xl.png")
            render(cover(), (0, 0, 236, 344), (244, 356), 3, paper=(255, 255, 255), clean=True, jitter=0.04).save(
                "out/fields-cover-sm.png")
