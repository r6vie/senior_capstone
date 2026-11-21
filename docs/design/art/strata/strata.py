"""Strata: landscapes built from horizontal slabs, for Trove covers.

Every shape is cut into courses (rows) of one height; each course is laid in bricks of
random length with a little colour drift. Edges step instead of curving, mist is made by
leaving bricks out and paling them toward paper (never a blur or gradient).

A scene lives in world pixels (CSS px of its panorama). render() draws any viewport of it
at any output size, with the course height chosen for that size, so the shelf cover and
the book-page hero are the same place drawn for the size they show at.
"""

import math
import random

import numpy as np
from PIL import Image, ImageDraw

PAPER = (250, 250, 247)


def hexrgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))


def mix(a, b, t):
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(3))


def shade(c, k):
    """k<0 darker, k>0 lighter."""
    return mix(c, (0, 0, 0), -k) if k < 0 else mix(c, (255, 255, 255), k)


def _h(ix, iy, seed):
    n = (ix * 374761393 + iy * 668265263 + seed * 2147483647) & 0xFFFFFFFF
    n = ((n ^ (n >> 13)) * 1274126177) & 0xFFFFFFFF
    return ((n ^ (n >> 16)) & 0xFFFF) / 65535.0


def vnoise(x, y, scale, seed=0):
    """Smooth value noise in 0..1: coherent patches instead of speckle."""
    gx, gy = x / scale, y / scale
    ix, iy = math.floor(gx), math.floor(gy)
    fx, fy = gx - ix, gy - iy
    fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    a, b = _h(ix, iy, seed), _h(ix + 1, iy, seed)
    c, d = _h(ix, iy + 1, seed), _h(ix + 1, iy + 1, seed)
    return (a + (b - a) * fx) * (1 - fy) + (c + (d - c) * fx) * fy


# ---------- layers. Each answers: for a row at world y, which world x are covered, and what colour. ----------


class Ridge:
    """A mountain range: peaks composed by max. Light comes from the left: each peak's shadow face starts
    on a line leaning down-right from its summit, and the course ends on the shadow edge are inked darkest."""

    brick = (1.3, 5.0)

    def __init__(self, peaks, base, lit, dark, rough=6, seed=1, lean=0.32, bands=None, ribs=0.0, mist=None,
                 smooth=False, cap=None, flicker=0.12, round=False):
        # peak: (x, top_y, left_half_width, right_half_width, power)
        self.peaks = [p if len(p) == 5 else (p[0], p[1], p[2], p[2], p[3]) for p in peaks]
        self.base = base
        self.lit = [hexrgb(c) for c in lit]
        self.dark = [hexrgb(c) for c in dark]
        self.seed = seed
        self.lean = lean
        # ribs > 0: spurs and gullies running down from each summit break the faces up (round 3)
        self.ribs = ribs
        # mist: (y_from, y_to) where the foot of the range pales toward the lake haze
        self.mist = mist
        # bands: (y_top, y_bottom, lit palette, dark palette) — exposed strata of another colour
        self.bands = [(a, b, [hexrgb(c) for c in l], [hexrgb(c) for c in d]) for a, b, l, d in (bands or [])]
        rng = np.random.default_rng(seed)
        self.noise_x = np.linspace(-400, 2400, 900)
        ny = np.cumsum(rng.normal(0, 1, 900))
        self.noise_y = (ny - np.convolve(ny, np.ones(31) / 31, "same")) * rough / 3
        if smooth:
            # a calm skyline: only broad ledges and dips, nothing narrower than a few slabs
            w = rng.normal(0, 1, 900)
            a = np.convolve(w, np.ones(19) / 19, "same")
            b = np.convolve(w[::-1], np.ones(7) / 7, "same")
            self.noise_y = (a / (a.std() + 1e-9) * 0.75 + b / (b.std() + 1e-9) * 0.25) * rough / 2
        self.flicker = flicker
        self.round = round   # a dome: an elliptical crest instead of a peak
        # cap: (depth, lit, dark): a snowline `depth` below the highest summit, wavering gently; above it every slab
        # is laid in the cap's inks (lit or shaded as the face is)
        self.cap = (cap[0], [hexrgb(c) for c in cap[1]], [hexrgb(c) for c in cap[2]]) if cap else None

    def _cands(self, x):
        out = []
        for px, ty, lw, rw, pw in self.peaks:
            hw = np.where(x < px, lw, rw)
            t = np.abs(x - px) / hw
            if getattr(self, "round", False):
                h = (self.base - ty) * np.sqrt(np.clip(1 - t ** 2, 0, None)) ** pw
            else:
                h = (self.base - ty) * np.clip(1 - t, 0, None) ** pw
            out.append(np.where(t < 1, self.base - h, np.inf))
        return np.array(out)

    def top(self, x):
        y = self._cands(x).min(axis=0)
        return y + np.interp(x, self.noise_x, self.noise_y) * np.isfinite(y)

    def cover(self, x, y):
        return (y >= self.top(x)) & (y <= self.base)

    def colour(self, x, y, rng):
        xa = np.array([x])
        k = int(self._cands(xa)[:, 0].argmin())
        px, ty = self.peaks[k][0], self.peaks[k][1]
        top = self.top(xa)[0]
        depth = min(1, max(0, (y - top) / max(1, self.base - top)))
        n = vnoise(x, y, 46, self.seed)
        if self.ribs:
            # the terminator wanders: spurs reach into the light and the light reaches into gullies
            wob = (vnoise(y, x * 0.2, 22, self.seed + 9) - 0.5) * self.ribs * 22 * min(1, (y - ty) / 60)
            in_shadow = x > px + (y - ty) * self.lean + wob
        else:
            in_shadow = x > px + (y - ty) * self.lean
        lit, dark = self.lit, self.dark
        for a, b, bl, bd in self.bands:
            wob = (vnoise(x, 0, 30, self.seed + 3) - 0.5) * 10
            if a + wob <= y <= b + wob:
                lit, dark = bl, bd
        if self.cap and not hasattr(self, "_summit"):
            px0 = min(self.peaks, key=lambda p: p[1])[0]
            self._summit = float(self.top(np.linspace(px0 - 60, px0 + 60, 241)).min())
        if self.cap and y - self._summit < self.cap[0] + (vnoise(x, 0, 22, self.seed + 8) - 0.5) * 5:
            lit, dark = self.cap[1], self.cap[2]
        pal = dark if in_shadow else lit
        i = (0.62 * depth + 0.38 * n) * len(pal)
        if rng.random() < getattr(self, "flicker", 0.12):
            i += rng.choice((-1, 1))
        if self.ribs:
            ang = math.atan2(x - px, max(4.0, y - ty))
            rib = vnoise(ang * 14, (y - ty) / 60, 1, self.seed + 7)
            if rib > 0.64:      # a spur: catches light, even on the shadow face
                if in_shadow and rib > 0.72 and rng.random() < 0.75 * self.ribs:
                    pal = lit
                    i = len(pal) - 1 - rng.random()
                else:
                    i -= 1.4 * self.ribs
            elif rib < 0.34:    # a gully: deeper ink
                i += 1.3 * self.ribs
        if self.mist:
            a, b = self.mist
            m = min(1, max(0, (y - a) / (b - a)))
            if m > 0 and rng.random() < m * 0.8:
                return mix(pal[int(min(len(pal) - 1, max(0, i)))], (233, 236, 236), 0.35 + 0.35 * m)
        # the stepped edge on the shadow side reads as ink
        if in_shadow and self.top(np.array([x + 14]))[0] > y:
            i = len(pal) - 1
        if not in_shadow and self.top(np.array([x - 14]))[0] > y and rng.random() < 0.6:
            i = 0
        return pal[int(min(len(pal) - 1, max(0, i)))]


class Blob:
    """Clouds, tree crowns, a sun: a union of ellipses. Rows near the top of each blob are lighter."""

    brick = (2.0, 9.0)

    def __init__(self, ellipses, colours, top_light=True, short=False):
        self.e = ellipses  # (cx, cy, rx, ry)
        self.c = [hexrgb(c) for c in colours]
        self.top_light = top_light
        self.short = short

    def cover(self, x, y):
        m = np.zeros_like(x, dtype=bool)
        for cx, cy, rx, ry in self.e:
            m |= ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1
        return m

    def colour(self, x, y, rng):
        # position within the nearest ellipse, 0 top .. 1 bottom
        best = None
        for cx, cy, rx, ry in self.e:
            dd = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
            if best is None or dd < best[0]:
                best = (dd, (y - (cy - ry)) / (2 * ry), (x - cx) / rx)
        _, v, u = best
        k = v * 0.75 + max(0, u) * 0.35 if self.top_light else rng.random()
        k = min(0.999, max(0, k + rng.uniform(-0.18, 0.18)))
        return self.c[int(k * len(self.c))]


class Water:
    """A band of water: long ragged runs with paper gaps; glints gather in calm patches."""

    brick = (2.5, 9.0)

    def __init__(self, y0, y1, x0, x1, colours, glint, seed=3, taper=0.0, mirror=None, gaps=(0, 2), squash=0.35):
        self.y0, self.y1, self.x0, self.x1 = y0, y1, x0, x1
        self.c = [hexrgb(c) for c in colours]
        self.g = [hexrgb(c) for c in glint]
        self.rng = random.Random(seed)
        self.rows = {}
        self.taper = taper
        self.mirror = mirror or []  # layers reflected about y0
        self.gaps = gaps
        self.squash = squash

    def cover(self, x, y):
        if not (self.y0 <= y <= self.y1):
            return np.zeros_like(x, dtype=bool)
        key = round(y)
        if key not in self.rows:
            r = random.Random(key * 7919 + 13)
            t = (y - self.y0) / max(1, self.y1 - self.y0)
            a = self.x0 + r.uniform(-60, 60) + self.taper * t * 400
            b = self.x1 + r.uniform(-90, 40) - self.taper * t * 260
            ngaps = r.randint(*self.gaps) + (1 if t < 0.08 else 0)
            gaps = [(r.uniform(a, b), r.uniform(20, 110)) for _ in range(ngaps)]
            self.rows[key] = (a, b, gaps)
        a, b, gaps = self.rows[key]
        m = (x >= a) & (x <= b)
        for gx, gw in gaps:
            m &= ~((x >= gx) & (x <= gx + gw))
        return m

    def colour(self, x, y, rng):
        my = 2 * self.y0 - y + (y - self.y0) * self.squash  # reflections are a little shorter than the thing
        for layer in reversed(self.mirror):
            if layer.cover(np.array([x]), my)[0] and rng.random() < 0.8 - (y - self.y0) / max(1, self.y1 - self.y0) * 0.5:
                return mix(layer.colour(x, my, rng), self.c[2], 0.45)
        n = vnoise(x, y * 3, 90, 77)
        path = getattr(self, "path", None)
        if path and abs(x - path[0]) < path[1] * (0.5 + (y - self.y0) / max(1, self.y1 - self.y0)) and rng.random() < 0.6:
            return self.g[int(rng.random() * len(self.g))]
        if n > 0.72 and rng.random() < 0.55:
            return self.g[int(rng.random() * len(self.g))]
        t = (y - self.y0) / max(1, self.y1 - self.y0)
        k = min(0.999, max(0, 0.05 + 0.6 * vnoise(x, y * 2, 70, 5) + t * 0.2 + rng.uniform(-0.12, 0.12)))
        return self.c[int(k * len(self.c))]


class Band:
    """A flat ground (island shore, terrace): a ragged lens between two y's."""

    brick = (2.0, 10.0)

    def __init__(self, x0, x1, ytop, ybot, colours, seed=5, lens=0.6):
        self.x0, self.x1, self.yt, self.yb = x0, x1, ytop, ybot
        self.c = [hexrgb(c) for c in colours]
        self.seed = seed
        self.lens = lens

    def cover(self, x, y):
        if not (self.yt <= y <= self.yb):
            return np.zeros_like(x, dtype=bool)
        r = random.Random(round(y) * 31 + self.seed)
        t = (y - self.yt) / max(1, self.yb - self.yt)
        w = (self.x1 - self.x0) / 2
        cx = (self.x0 + self.x1) / 2
        half = w * (1 - self.lens * (1 - t) ** 2) + r.uniform(-30, 30)
        return (x >= cx - half) & (x <= cx + half)

    def colour(self, x, y, rng):
        return self.c[int(rng.random() * len(self.c))]


class Grove(Blob):
    """Tree crowns: lit on the upper left, inked underneath, short bricks so they read as leaves."""

    brick = (0.9, 3.2)

    def colour(self, x, y, rng):
        best = None
        for cx, cy, rx, ry in self.e:
            dd = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
            if best is None or dd < best[0]:
                best = (dd, (y - cy) / ry, (x - cx) / rx)
        _, v, u = best
        k = 0.45 + 0.4 * v + 0.25 * u + rng.uniform(-0.2, 0.2)
        k = min(0.999, max(0, k))
        return self.c[int(k * len(self.c))]


class Trunks:
    """Thin dark trunks under a grove; drawn as narrow slabs so the canopy reads as standing on them."""

    brick = (0.3, 0.6)
    ragged = 0

    def __init__(self, posts, colour):
        self.posts = posts  # (x, top, bottom, half_width)
        self.c = hexrgb(colour)

    def cover(self, x, y):
        m = np.zeros_like(x, dtype=bool)
        for px, t, b, hw in self.posts:
            if t <= y <= b:
                m |= np.abs(x - px) <= hw
        return m

    def colour(self, x, y, rng):
        return shade(self.c, rng.uniform(-0.1, 0.1))


class Mesa:
    """A mesa or butte: a flat top, cliff faces that step out in ledges as they fall, and the rock laid in horizontal
    beds of alternating tone. Lit on the left face, shaded on the right; the top course is the lightest.
    cx, top: centre and top of the flat; tw, bw: half widths at the top and at the base."""

    brick = (1.3, 5.0)

    def __init__(self, cx, top, tw, bw, base, lit, dark, ledges=3, bed=8, seed=1, mist=None, flicker=0.04,
                 talus=False, top_tint=None, shadow_slope=0.0, wall_ledge=None, wobble=6, speckle=0.8,
                 shadow_steps=None, ragged=1, lean=0.0, flare=0.0, bedding=None):
        self.cx, self.top_y, self.tw, self.bw, self.base = cx, top, tw, bw, base
        self.lit = [hexrgb(c) for c in lit]
        self.dark = [hexrgb(c) for c in dark]
        self.ledges, self.bed, self.seed, self.mist, self.flicker = ledges, bed, seed, mist, flicker
        # talus: sheer walls for the top two thirds, then a skirt of scree stepping out to the base
        self.talus = talus
        self.top_tint = [hexrgb(c) for c in top_tint] if top_tint else None
        self.shadow_slope = shadow_slope
        # wall_ledge: sheer walls with one ledge of this width two thirds down; shadow_steps: the shade edge in this
        # many clean steps; wobble and speckle: how much the walls and the lit face vary course to course
        self.wall_ledge, self.wobble, self.speckle, self.shadow_steps = wall_ledge, wobble, speckle, shadow_steps
        self.ragged = ragged
        self.lean = lean      # the centre slides this much per unit of depth: the butte tilts
        self.flare = flare    # the walls step out by this much (world px) from cap to the top of the skirt
        # bedding: (list of world y, colour): darker beds across the lit face
        self.bedding = (bedding[0], hexrgb(bedding[1])) if bedding else None

    def _half(self, y):
        t = np.clip((y - self.top_y) / max(1, self.base - self.top_y), 0, 1)
        if self.wall_ledge is not None:
            return self.tw + np.where(t > 0.66, self.wall_ledge, 0.0)
        if self.talus:
            wall = 0.66
            skirt = np.clip((t - wall) / (1 - wall), 0, 1)
            L = max(1, self.ledges)
            steps = np.floor(skirt * L) / L + (skirt * L % 1) ** 2 / L
            body = self.flare * np.minimum(t / wall, 1)
            return self.tw + body + (self.bw - self.tw - self.flare) * steps
        L = self.ledges
        # a staircase: each tier a steep cliff, then a short shelf
        f = np.floor(t * L) / L + ((t * L) % 1) ** 3 / L
        return self.tw + (self.bw - self.tw) * f

    def cover(self, x, y):
        if not (self.top_y <= y <= self.base):
            return np.zeros_like(x, dtype=bool)
        hw = self._half(y)
        wob = (np.array([vnoise(v, y, 26, self.seed) for v in np.atleast_1d(x)]) - 0.5) * self.wobble
        return np.abs(x - self._cx(y)) <= hw + wob

    def _cx(self, y):
        return self.cx + self.lean * (y - self.top_y)

    def colour(self, x, y, rng):
        hw = float(self._half(y))
        cx0 = self.cx
        self.cx = self._cx(y)
        try:
            return self._colour(x, y, rng, hw)
        finally:
            self.cx = cx0

    def _colour(self, x, y, rng, hw):
        # the shadow edge: a stepped diagonal falling to the right, one step per bed
        steps = (y - self.top_y) // self.bed
        if self.shadow_steps:
            t = min(0.999, max(0, (y - self.top_y) / max(1, self.base - self.top_y)))
            k = int(t * self.shadow_steps)
            shadow = x > self.cx + hw * (0.42 - 0.2 * k / max(1, self.shadow_steps - 1))
        else:
            shadow = x > self.cx + hw * 0.18 + self.shadow_slope * steps * self.bed
        pal = self.dark if shadow else self.lit
        if self.top_tint and not shadow and y - self.top_y < 2 * self.bed:
            pal = self.top_tint            # dusk light on the top courses
        if self.bedding and not shadow and any(abs(y - b) < 2.5 for b in self.bedding[0]):
            return self.bedding[1]         # a darker bed of rock across the lit face
        bed = int((y - self.top_y) // self.bed)
        i = (bed % 2) * 1.0 + self.speckle * vnoise(x, y, 40, self.seed + 1)
        if y - self.top_y < self.bed * 0.6:
            i = 0 if not shadow else 0.5      # the flat top catches the light
        if not shadow and abs(x - (self.cx - hw)) < 6:
            i = 0                            # the lit cliff edge
        if rng.random() < self.flicker:
            i += rng.choice((-1, 1))
        if self.mist:
            a, b = self.mist
            m = min(1, max(0, (y - a) / (b - a)))
            if m > 0 and rng.random() < m * 0.8:
                return mix(pal[int(min(len(pal) - 1, max(0, i)))], (240, 238, 234), 0.35 + 0.35 * m)
        return pal[int(min(len(pal) - 1, max(0, i)))]


class Terraces(Ridge):
    """A hill cut into terraces: a Ridge whose face is laid in level beds of two alternating inks, each bed's edge
    lit, so the hill reads as steps."""

    def __init__(self, peaks, base, ink_a, ink_b, bed=10, beds=None, lip=None, **kw):
        super().__init__(peaks, base, ink_a, ink_b, **kw)
        self.a = [hexrgb(c) for c in ink_a]
        self.b = [hexrgb(c) for c in ink_b]
        self.bed = bed
        # beds: one palette per terrace from the top down (each terrace one solid colour); lip: the pale course on
        # each terrace's edge
        self.beds = [[hexrgb(c) for c in p] for p in beds] if beds else None
        self.lip = [hexrgb(c) for c in lip] if lip else None

    def _crest_y(self):
        return min(p[1] for p in self.peaks)

    def top(self, x):
        # the skyline steps down bed by bed, like the terraces themselves
        t = super().top(x)
        return np.where(np.isfinite(t), np.ceil(t / self.bed) * self.bed, t)

    def colour(self, x, y, rng):
        xa = np.array([x])
        top = self.top(xa)[0]
        k = int(self._cands(xa)[:, 0].argmin())
        px = self.peaks[k][0]
        n = int((y - top) // self.bed)
        if self.beds:
            # terraces counted from the hill's own top, so each terrace is one colour band across the slope
            n = int((y - self._crest_y()) // self.bed)
            pal = self.beds[min(len(self.beds) - 1, max(0, n))]
            if self.lip and (y - top) % self.bed < 4.5:
                return self.lip[int(rng.random() * len(self.lip))]
            return pal[int(min(len(pal) - 1, max(0, 0.6 * vnoise(x, y, 80, self.seed) * len(pal))))]
        pal = self.a if n % 2 == 0 else self.b
        lit = x < px
        i = (0 if lit else 1) + 0.4 * vnoise(x, y, 70, self.seed)
        if (y - top) % self.bed < 4:
            i -= 1                            # the lip of each terrace catches the light
        if rng.random() < getattr(self, "flicker", 0.05):
            i += rng.choice((-1, 1))
        if self.mist:
            a, b = self.mist
            m = min(1, max(0, (y - a) / (b - a)))
            if m > 0 and rng.random() < m * 0.8:
                return mix(pal[int(min(len(pal) - 1, max(0, i)))], (236, 236, 230), 0.35 + 0.35 * m)
        return pal[int(min(len(pal) - 1, max(0, i)))]


class River:
    """A river winding toward the viewer: narrow where it leaves the far hills, wide at the foot, its line swinging
    side to side. Calm long runs, a few glints."""

    brick = (2.5, 9.0)

    def __init__(self, y0, y1, cx, amp, w0, w1, colours, glint, swings=1.2, phase=0.0, seed=5):
        self.y0, self.y1, self.cx, self.amp, self.w0, self.w1 = y0, y1, cx, amp, w0, w1
        self.c = [hexrgb(c) for c in colours]
        self.g = [hexrgb(c) for c in glint]
        self.swings, self.phase, self.seed = swings, phase, seed

    def _line(self, y):
        t = min(1, max(0, (y - self.y0) / max(1, self.y1 - self.y0)))
        c = self.cx + self.amp * math.sin(t * math.pi * self.swings + self.phase) * (0.3 + 0.7 * t)
        w = self.w0 + (self.w1 - self.w0) * t ** 1.4
        return c, w, t

    def cover(self, x, y):
        if not (self.y0 <= y <= self.y1):
            return np.zeros_like(x, dtype=bool)
        c, w, _ = self._line(y)
        return np.abs(x - c) <= w / 2

    def colour(self, x, y, rng):
        c, w, t = self._line(y)
        if vnoise(x, y * 3, 40, self.seed) > 0.74 and rng.random() < 0.6:
            return self.g[int(rng.random() * len(self.g))]
        k = min(0.999, max(0, 0.15 + 0.5 * t + 0.25 * abs(x - c) / max(1, w / 2) + rng.uniform(-0.1, 0.1)))
        return self.c[int(k * len(self.c))]


class Firs:
    """Conifers built from courses: each tier steps out and back, lit on the left of the trunk line, inked on the right.
    trees: (x, base_y, height, half_width)."""

    brick = (1.4, 4.0)
    ragged = 0
    min_run = 0.5     # a tree tapers to its tip; its top courses may be narrow

    def __init__(self, trees, lit, dark, tiers=6):
        self.t = trees
        self.lit = [hexrgb(c) for c in lit]
        self.dark = [hexrgb(c) for c in dark]
        self.tiers = tiers

    def _half(self, tree, y):
        x, base, h, w = tree
        up = base - y
        if up < 0 or up > h:
            return -1
        f = up / h
        saw = 1 - ((f * self.tiers) % 1)
        return max(0.7, w * (1 - f) ** 0.9 * (0.4 + 0.6 * saw ** 0.8))

    def cover(self, x, y):
        m = np.zeros_like(x, dtype=bool)
        for tr in self.t:
            hw = self._half(tr, y)
            if hw > 0:
                m |= np.abs(x - tr[0]) <= hw
        return m

    def colour(self, x, y, rng):
        best = min(self.t, key=lambda tr: abs(x - tr[0]) if self._half(tr, y) > 0 else 1e9)
        pal = self.lit if x < best[0] - 0.3 else self.dark
        return pal[int(rng.random() * len(pal))]


def trees(cx_list, ground_y, size, colours, seed=9, spread=1.0):
    """A grove: overlapping crowns standing on the ground line, back ones higher."""
    r = random.Random(seed)
    e = []
    for cx in cx_list:
        for j in range(4):
            s = size * r.uniform(0.55, 1.1)
            x = cx + r.uniform(-size, size) * spread
            y = ground_y - s * (1.9 - j * 0.35) - r.uniform(0, size * 0.4)
            e.append((x, y, s * 1.15, s * 0.8))
    return Grove(e, colours)


def grove(cx_list, ground_y, size, colours, trunk="#5B3B2A", seed=9, spread=1.0, trunk_h=1.0):
    """Trees with trunks: crowns held up on visible trunks, the reference's bonsai-like groves."""
    r = random.Random(seed + 1)
    posts, e = [], []
    for cx in cx_list:
        h = size * r.uniform(1.1, 1.8) * trunk_h
        top = ground_y - h
        posts.append((cx + r.uniform(-2, 2), top, ground_y, max(0.9, size * 0.09)))
        for j in range(4):
            s = size * r.uniform(0.55, 1.0)
            e.append((cx + r.uniform(-size, size) * spread, top - s * (0.45 + j * 0.15) + r.uniform(-2, 2), s * 1.2, s * 0.72))
    return [Trunks(posts, trunk), Grove(e, colours)]


# ---------- rendering ----------


def render(scene, viewport, size, course, seed=7, gap=None, slab_shade=True, fade=None, brick=(1.6, 7.5), paper=PAPER,
           jitter=0.05, touch=True, slab=(0.10, 0.22, 0.10), joint=0, seam=1.0, clean=False, flush=False):
    """Draw the viewport (wx0, wy0, wx1, wy1) of the scene at size (W, H) with course height in output px.

    fade: list of (edge, start, end) in output px; bricks thin out and pale toward paper across it.
    """
    W, H = size
    wx0, wy0, wx1, wy1 = viewport
    sx = (wx1 - wx0) / W
    sy = (wy1 - wy0) / H
    img = Image.new("RGB", (W, H), paper)
    dr = ImageDraw.Draw(img)
    gap = gap if gap is not None else 0
    rng = random.Random(seed)
    xs_out = np.arange(W) + 0.5
    xs_world = wx0 + xs_out * sx

    def fade_amount(px, py):
        """A fade is (axis, from, to) in output px, 0 at from and 1 at to, or a function (px, py) -> 0..1."""
        a = 0.0
        for f in fade or []:
            if callable(f):
                a = max(a, f(px, py))
                continue
            axis, s, e = f
            v = py if axis == "y" else px
            a = max(a, min(1, max(0, (v - s) / (e - s))))
        return a

    for row_top in range(0, H, course):
        yc = wy0 + (row_top + course / 2) * sy
        # who owns each pixel of this course: the nearest layer that covers it
        owner = np.full(W, -1)
        for k in range(len(scene) - 1, -1, -1):
            m = scene[k].cover(xs_world, yc) & (owner < 0)
            owner[m] = k
        minrun = int(1.5 * course) if clean else 2
        if clean:
            # no slivers or specks: a piece shorter than a slab and a half goes to the nearer form it touches, or
            # away if it touches none
            for _ in range(3):
                e = np.flatnonzero(np.diff(np.concatenate([[-2], owner, [-2]])))
                changed = False
                for i in range(len(e) - 1):
                    a0, b0 = e[i], e[i + 1]
                    k = owner[a0]
                    # a layer may allow narrower pieces (a tree tapering to its tip)
                    if k < 0 or b0 - a0 >= int(getattr(scene[k], "min_run", 1.5) * course):
                        continue
                    left = owner[a0 - 1] if a0 > 0 else -1
                    right = owner[b0] if b0 < W else -1
                    owner[a0:b0] = max(left, right)
                    changed = True
                if not changed:
                    break
        edges = np.flatnonzero(np.diff(np.concatenate([[-2], owner, [-2]])))
        segs = [(edges[i], edges[i + 1], owner[edges[i]]) for i in range(len(edges) - 1) if owner[edges[i]] >= 0]
        # blocks touch by default: where two forms meet they share one boundary, and if it steps, both sides step
        # with it, so no hole opens between them. Only an edge against open paper steps on its own (that is the
        # silhouette). Spacing is a design choice a layer makes (water breaks, mist), never a by-product.
        bounds = {}
        for i, (a0, b0, k) in enumerate(segs):
            if i + 1 < len(segs) and segs[i + 1][0] == b0 and touch:
                nb = segs[i + 1]
                step = min(getattr(scene[k], "ragged", 1), getattr(scene[nb[2]], "ragged", 1))
                d = rng.randint(-step, step) * course // 2
                d = max(-(b0 - a0 - minrun), min(nb[1] - nb[0] - minrun, d))
                d = d if (b0 - a0 > minrun and nb[1] - nb[0] > minrun) else 0
                bounds[b0] = b0 + d
        runs = []
        edges_fill = []     # flush: (source column, x0, x1) to fill out to the page edge after the row is laid
        for i, (a0, b0, k) in enumerate(segs):
            layer = scene[k]
            step = getattr(layer, "ragged", 1)
            if a0 in bounds:
                a = bounds[a0]
            else:
                a = max(0, a0 + rng.randint(-step, step) * course // 2)
            if b0 in bounds:
                b = bounds[b0]
            else:
                b = min(W, b0 + rng.randint(-step, step) * course // 2)
            mr = int(getattr(layer, "min_run", 1.5) * course) if clean else 2
            if clean and b - a < mr:
                a, b = (a0, b0) if b0 - a0 >= mr else (a, a)
            if b > a:
                runs.append((layer, a, b))
                if flush and a0 == 0 and a > 0:
                    edges_fill.append((a, 0, a))
                if flush and b0 == W and b < W:
                    edges_fill.append((b - 1, b, W))
        for layer, a, b in runs:
            if True:
                x = a
                while x < b:
                    lm = int(getattr(layer, "min_run", 1.5) * course) if clean else minrun
                    ln = max(lm, int(course * rng.uniform(*getattr(layer, "brick", brick))))
                    x2 = min(b, x + ln)
                    if clean and b - x2 < lm:
                        x2 = b    # a short remainder joins this slab instead of standing alone
                    cxw = wx0 + ((x + x2) / 2) * sx
                    c = layer.colour(cxw, yc, rng)
                    c = shade(c, rng.uniform(-jitter, jitter))
                    f = fade_amount((x + x2) / 2, row_top + course / 2)
                    if f > 0:
                        # mist: slabs pale toward paper first, and only the palest ones go missing
                        if f > 0.55 and _h(x, row_top, 99) < (f - 0.55) * 2.2:
                            x = x2
                            continue
                        c = mix(c, paper, f * 0.8)
                    h = course - gap
                    # joint: a small uniform paper line at the end of every slab, so each reads as its own piece
                    xe = x2 - 1 - joint if x2 - x > joint + 1 else x2 - 1
                    if seam < 1.0 and (joint or gap):
                        # the joint is the slab's own ink lightened toward paper: a fine seam, not a white line
                        dr.rectangle([x, row_top, x2 - 1, row_top + course - 1], fill=mix(c, paper, seam))
                    dr.rectangle([x, row_top, xe, row_top + h - 1], fill=c)
                    if slab_shade and course >= 4:
                        # a laid slab: light catches its top edge, its underside sits in shadow, and the
                        # joint to the next slab is a faint darker seam
                        lw = max(1, course // 6)
                        top_l, under, joint_d = slab
                        dr.rectangle([x, row_top, xe, row_top + lw - 1], fill=shade(c, top_l))
                        dr.rectangle([x, row_top + h - lw, xe, row_top + h - 1], fill=shade(c, -under))
                        if x2 - x > course * 2 and _h(x, row_top, 5) < 0.55:
                            dr.rectangle([xe - lw + 1, row_top + lw, xe, row_top + h - lw - 1], fill=shade(c, -joint_d))
                    x = x2
        # a run that reaches the side of the page stays flush with it (no uneven paper notches): its outermost
        # column is stretched to the edge after the fact, so the random draws and every other slab stay as they were
        for src, x0, x1 in edges_fill:
            col = img.crop((src, row_top, src + 1, min(H, row_top + course)))
            img.paste(col.resize((x1 - x0, col.height)), (x0, row_top))
    return img
