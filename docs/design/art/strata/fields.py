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

    def __init__(self, horizon, near, x0, x1, swells, strips, seed=1, hedge=HEDGE, power=1.6, cross=(), vx=120, grain=1.0, near_t=0.97, hero=None, hero_t0=0.0, row_ink=None, near_ink=None, cross_w=(0.6, 3.0),
                 closed=False):
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
        self.cross_w, self.closed = cross_w, closed
        self.hero_t0 = hero_t0                 # the field ends here, closed by a hedge across it
        self.row_ink = hexrgb(row_ink) if row_ink else None
        if near_ink:
            self.near_strip = ([hexrgb(c) for c in near_ink[0]], [hexrgb(c) for c in near_ink[1]])
        # hero: (left x, right x at the near edge, (lit, shade)): one long field running back to the vanishing point
        self.hero = (hero[0], hero[1], ([hexrgb(c) for c in hero[2][0]], [hexrgb(c) for c in hero[2][1]])) if hero else None
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
        if (self.hedged[i] or (self.closed and e1 > 0.15)) and dy <= 0.6 and (e1 - tw) < 0.004 + 0.016 * t and t > 0.03:
            return self.hedge[i % len(self.hedge)]
        seg = 0
        f = (self.h + (self.n - self.h) * t ** self.power - self.h) / (self.n - self.h)
        for xn, t0, t1 in self.cross:
            xl = self.vx + (xn - self.vx) * f
            if t0 <= t <= t1:
                if abs(x - xl) < self.cross_w[0] + self.cross_w[1] * t:
                    return self.hedge[1]
                if x > xl:
                    seg += 1
        # shade: the surface falls toward the right
        if self.hero and t >= self.hero_t0:
            xl = self.vx + (self.hero[0] - self.vx) * f
            xr = self.vx + (self.hero[1] - self.vx) * f
            if abs(x - xl) < 0.6 + 2.2 * t or abs(x - xr) < 0.6 + 2.2 * t:
                return self.hedge[0]                     # its hedges run all the way back
            if xl < x < xr and t < self.hero_t0 + 0.012:
                return self.hedge[0]                     # and one closes its far end
            if xl < x < xr:
                pal = self.hero[2][1] if dy > 0.6 else self.hero[2][0]
                # crop rows converging with the field, a shade deeper, so it reads as a field and not a path
                u = (x - xl) / (xr - xl) * 9
                if t > 0.25 and abs(u - round(u)) < 0.12 + 0.06 * t and 0 < round(u) < 9:
                    if self.row_ink:
                        return self.row_ink
                    return self.hero[2][1][0] if dy <= 0.6 else self.hedge[2]
                return pal[int(rng.random() * len(pal))]
        if self.near_strip is not None and t > self.near_t:
            lit, dark = self.near_strip
        else:
            lit, dark = self.strips[(self.order[i] + 2 * seg) % len(self.strips)]
        pal = dark if dy > 0.6 else lit
        return pal[int(rng.random() * len(pal))]


FAR = (["#C9C2D6", "#C2BBCF"], ["#A9A2BE", "#A29BB7"])
SUN = ["#F3CD8C", "#F0C47E", "#EAB972"]
TREE = ["#5E7446", "#536940", "#475C37", "#3B4E2E"]
TREE_DARK = ["#3A4D2F", "#2F4026", "#25331E"]
CROPS = [WHEAT, SAGE, GREEN, OCHRE, PLOW, PALE]


def lone_tree(x, ground, s, seed, inks=None):
    r = random.Random(seed)
    e = [(x + r.uniform(-s, s) * 0.6, ground - s * 1.25 - r.uniform(0, s * 0.45), s * r.uniform(0.7, 1.0),
          s * r.uniform(0.55, 0.75)) for _ in range(5)]
    trunk = Trunks([(x, ground - s * 1.3, ground, max(1.1, s * 0.15))], "#4A3A2C")
    trunk.min_run = 0.4          # a trunk is narrower than a slab and a half; clean mode must keep it
    return [trunk, Grove(e, inks or TREE)]


def joins(land, n_edges, seed, skip=()):
    """Bushes where a field boundary running toward us meets a hedged strip edge: one or two at a join, never in a row."""
    r = random.Random(seed)
    out = []
    edges = [e for e in land.edges[1:] if 0.15 < e < 0.85][:n_edges]
    for k, t in enumerate(edges):
        f = (land.h + (land.n - land.h) * t ** land.power - land.h) / (land.n - land.h)
        for xn, t0, t1 in land.cross:
            x = land.vx + (xn - land.vx) * f
            if not (t0 <= t <= t1) or x < 30 or x > 206 or (k, xn) in skip:
                continue
            g = float(land._y(np.array([float(x)]), np.array([t]))[0])
            for _ in range(r.choice((1, 1, 2))):
                xx = x + r.uniform(-6, 6)
                out += lone_tree(xx, g + 1, 7 * (0.6 + t) * r.uniform(0.85, 1.15), r.randrange(999))
    return out


def cover():
    """The book page's farmland, kept to a cover: fields clearly separated, every near field closed by dark hedges on
    all sides, three boundaries converging on the horizon; bushes standing where the hedgerows meet; the land rises in
    one smooth swell on the right with a big tree on its crest (the only thing above the name line); the low sun over
    a lilac range on the left; a deep green near field."""
    land = Land(222, 380, -20, 260, [(212, 0.32, 85, 0.16, 64), (30, 0.74, 90, 0.2, 20)], CROPS, seed=11,
                cross=[(-60, 0.06, 1.2), (70, 0.06, 1.2), (230, 0.06, 1.2)], vx=120, grain=1.15, near_t=0.9,
                cross_w=(1.4, 3.5), closed=True)
    crest_x = 220
    crest_y = float(land.skyline[land._col(crest_x)])
    return [
        disc(58, 206, 13, SUN),
        Ridge([(40, 210, 90, 80, 1.0), (150, 214, 80, 90, 1.0)], 224, *FAR, seed=301, rough=2, smooth=True,
              flicker=0.02),
        land,
        *joins(land, 3, 310),
        *lone_tree(crest_x, crest_y + 2, 12, 302),
    ]


HOUSE_W = (["#F6F2EA", "#F1ECE2"], ["#C2B8A6", "#B8AE9C"])
ROOF = ["#7A5440", "#70503C"]
LANE = ["#E9DDBF", "#E2D5B4", "#DACCA8"]


class Lane:
    """A farm lane winding over the land: a band of fixed width on the ground, following a path in (x, t)."""

    brick = (2.0, 8.0)
    min_run = 0.6

    def __init__(self, land, pts, width, colours):
        self.land, self.width = land, width
        self.pts = pts                      # (x, t) from far to near
        self.c = [hexrgb(c) for c in colours]

    def _half(self, t):
        if isinstance(self.width, tuple):
            t0, t1 = self.pts[0][1], 1.0
            u = min(1.0, max(0.0, (t - t0) / (t1 - t0)))
            return self.width[0] + (self.width[1] - self.width[0]) * u
        return self.width * (0.15 + t)

    def _smooth(self):
        """A Catmull-Rom curve through the control points, sampled densely, so the lane bends without kinks."""
        P = [self.pts[0]] + list(self.pts) + [self.pts[-1]]
        out = []
        for i in range(1, len(P) - 2):
            p0, p1, p2, p3 = (np.array(q, dtype=float) for q in P[i - 1:i + 3])
            for u in np.linspace(0, 1, 40, endpoint=False):
                out.append(0.5 * ((2 * p1) + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u ** 2
                                  + (-p0 + 3 * p1 - 3 * p2 + p3) * u ** 3))
        out.append(np.array(P[-2], dtype=float))
        c = np.array(out)
        order = np.argsort(c[:, 1])
        return c[order, 1], c[order, 0]

    def _x(self, t):
        if not hasattr(self, "_curve"):
            self._curve = self._smooth()
        ts, xs = self._curve
        return float(np.interp(t, ts, xs))

    def cover(self, x, y):
        out = np.zeros_like(x, dtype=bool)
        for i, xv in enumerate(np.asarray(x)):
            if not self.land.cover(np.array([xv]), y)[0]:
                continue
            t = self.land.t_at(xv, y)
            if t < self.pts[0][1] or t > self.pts[-1][1]:
                continue
            out[i] = abs(xv - self._x(t)) < self._half(t)
        return out

    def colour(self, x, y, rng):
        t = self.land.t_at(x, y)
        if x - self._x(t) > self._half(t) * 0.55:
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
    rolling in three swells, fields clearly separated, every near field closed by dark hedges, strips of crops running
    across in perspective and bending over each shoulder, shaded where they fall away to the right; boundaries
    converging on the horizon with bushes standing where hedgerows meet; a lane curving smoothly from the near edge
    over the middle swell to a white farmhouse with a low brown roof among trees; on the right the highest swell with
    two trees on its crest, the only thing above the text's corner; a deep green near field."""
    land = Land(452, 760, -20, 600, [(505, 0.30, 150, 0.2, 118), (240, 0.52, 110, 0.18, 46),
                                       (60, 0.80, 140, 0.2, 30)], CROPS, seed=11,
                cross=[(-60, 0.10, 1.2), (130, 0.1, 1.2), (330, 0.14, 1.2), (560, 0.2, 1.2)], vx=280, near_t=0.9,
                cross_w=(1.4, 3.5), closed=True, grain=1.3)
    hx, ht = 252, 0.43
    hy = float(land._y(np.array([float(hx)]), np.array([ht]))[0])
    k = 1.9
    house = Blocks([(hx + a * k, hy + b * k, hx + c * k, hy + d * k, ink) for a, b, c, d, ink in
                    [(-14, -12, 4, 0, HOUSE_W[0]), (4, -12, 14, 0, HOUSE_W[1]),
                     # one broad, low gable that overhangs both walls; one door on the lit face
                     (-18, -15, 18, -12, ROOF), (-14, -18, 14, -15, ROOF), (-9, -20, 9, -18, ROOF),
                     (-7, -7, -3, 0, ["#5E4436"])]])
    crest = [(496, 13, 405), (534, 9, 407), (470, 6, 408)]
    trees_on_crest = []
    for cx, size, seed in crest:
        cy = float(land.skyline[land._col(cx)])
        trees_on_crest += [Blob([(cx + size * 1.1, cy + 3, size * 1.1, 2.2)], ["#4E5F3A", "#465634"],
                                top_light=False)]
        trees_on_crest += lone_tree(cx, cy + 3, size, seed, TREE_DARK)
    return [
        disc(120, 440, 20, SUN),
        Ridge([(80, 432, 140, 120, 1.0), (300, 438, 120, 140, 1.0), (470, 426, 90, 100, 1.0)], 456, *FAR,
              seed=401, rough=2, smooth=True, flicker=0.02),
        land,
        Lane(land, [(254, 0.43), (276, 0.54), (228, 0.74), (262, 1.12)], (4, 16), LANE),
        *lone_tree(hx + 30, hy + 1, 13, 402, TREE_DARK),        # one dark tree behind the house's shaded side
        house,
        *page_joins(land, 402),
        *trees_on_crest,
    ]


def page_joins(land, seed):
    """The page's bushes: one or two where a converging boundary meets a hedged strip edge, mid distance only."""
    r = random.Random(seed)
    out = []
    edges = [e for e in land.edges[1:] if 0.42 < e < 0.88]
    for k, t in enumerate(edges[:4]):
        f = (land.h + (land.n - land.h) * t ** land.power - land.h) / (land.n - land.h)
        for xn, t0, t1 in land.cross:
            x = land.vx + (xn - land.vx) * f
            if not (t0 <= t <= t1) or x < 24 or x > 450 or r.random() < 0.35 or (abs(x - 250) < 50 and t < 0.56):
                continue
            g = float(land._y(np.array([float(x)]), np.array([t]))[0])
            for _ in range(r.choice((1, 1, 2))):
                xx = x + r.uniform(-8, 8)
                out += lone_tree(xx, g + 1, 9 * (0.5 + t) * r.uniform(0.85, 1.15), r.randrange(999))
    return out


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
