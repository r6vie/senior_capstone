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

    brick = (1.6, 7.0)

    def __init__(self, peaks, base, lit, dark, rough=6, seed=1, lean=0.32):
        # peak: (x, top_y, left_half_width, right_half_width, power)
        self.peaks = [p if len(p) == 5 else (p[0], p[1], p[2], p[2], p[3]) for p in peaks]
        self.base = base
        self.lit = [hexrgb(c) for c in lit]
        self.dark = [hexrgb(c) for c in dark]
        self.seed = seed
        self.lean = lean
        rng = np.random.default_rng(seed)
        self.noise_x = np.linspace(-400, 2400, 900)
        ny = np.cumsum(rng.normal(0, 1, 900))
        self.noise_y = (ny - np.convolve(ny, np.ones(31) / 31, "same")) * rough / 3

    def _cands(self, x):
        out = []
        for px, ty, lw, rw, pw in self.peaks:
            hw = np.where(x < px, lw, rw)
            t = np.abs(x - px) / hw
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
        in_shadow = x > px + (y - ty) * self.lean
        pal = self.dark if in_shadow else self.lit
        i = (0.5 * depth + 0.5 * n) * len(pal)
        if rng.random() < 0.18:
            i += rng.choice((-1, 1))
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

    brick = (3.0, 14.0)

    def __init__(self, y0, y1, x0, x1, colours, glint, seed=3, taper=0.0):
        self.y0, self.y1, self.x0, self.x1 = y0, y1, x0, x1
        self.c = [hexrgb(c) for c in colours]
        self.g = [hexrgb(c) for c in glint]
        self.rng = random.Random(seed)
        self.rows = {}
        self.taper = taper

    def cover(self, x, y):
        if not (self.y0 <= y <= self.y1):
            return np.zeros_like(x, dtype=bool)
        key = round(y)
        if key not in self.rows:
            r = random.Random(key * 7919 + 13)
            t = (y - self.y0) / max(1, self.y1 - self.y0)
            a = self.x0 + r.uniform(-60, 60) + self.taper * t * 400
            b = self.x1 + r.uniform(-90, 40) - self.taper * t * 260
            ngaps = r.randint(0, 2) + (3 if t < 0.12 else 0)
            gaps = [(r.uniform(a, b), r.uniform(30, 160) * (2.5 if t < 0.12 else 1)) for _ in range(ngaps)]
            self.rows[key] = (a, b, gaps)
        a, b, gaps = self.rows[key]
        m = (x >= a) & (x <= b)
        for gx, gw in gaps:
            m &= ~((x >= gx) & (x <= gx + gw))
        return m

    def colour(self, x, y, rng):
        n = vnoise(x, y * 3, 90, 77)
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


# ---------- rendering ----------


def render(scene, viewport, size, course, seed=7, gap=None, slab_shade=True, fade=None, brick=(1.6, 7.5), paper=PAPER):
    """Draw the viewport (wx0, wy0, wx1, wy1) of the scene at size (W, H) with course height in output px.

    fade: list of (edge, start, end) in output px; bricks thin out and pale toward paper across it.
    """
    W, H = size
    wx0, wy0, wx1, wy1 = viewport
    sx = (wx1 - wx0) / W
    sy = (wy1 - wy0) / H
    img = Image.new("RGB", (W, H), paper)
    dr = ImageDraw.Draw(img)
    gap = gap if gap is not None else max(1, round(course / 6))
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
        claimed = np.zeros(W, dtype=bool)
        # front to back so nearer layers win; draw back to front afterwards
        runs_by_layer = []
        for layer in reversed(scene):
            m = layer.cover(xs_world, yc) & ~claimed
            claimed |= m
            runs_by_layer.append((layer, m))
        for layer, m in reversed(runs_by_layer):
            if not m.any():
                continue
            idx = np.flatnonzero(np.diff(np.concatenate([[0], m.astype(int), [0]])))
            for a, b in zip(idx[::2], idx[1::2]):
                # ragged ends: the course steps out or in by part of a brick
                a = max(0, a + rng.randint(-2, 2) * course // 2)
                b = min(W, b + rng.randint(-2, 2) * course // 2)
                x = a
                while x < b:
                    ln = max(2, int(course * rng.uniform(*getattr(layer, "brick", brick))))
                    x2 = min(b, x + ln)
                    cxw = wx0 + ((x + x2) / 2) * sx
                    c = layer.colour(cxw, yc, rng)
                    c = shade(c, rng.uniform(-0.05, 0.05))
                    f = fade_amount((x + x2) / 2, row_top + course / 2)
                    if f > 0:
                        if _h(x, row_top, 99) < f * 0.9:
                            x = x2
                            continue
                        c = mix(c, paper, f * 0.7)
                    h = course - gap
                    dr.rectangle([x, row_top, x2 - 1, row_top + h - 1], fill=c)
                    if slab_shade and course >= 6:
                        # the lower part of each slab sits a little darker: a stacked edge, not a shadow
                        lo = max(1, course // 4)
                        dr.rectangle([x, row_top + h - lo, x2 - 1, row_top + h - 1], fill=shade(c, -0.12))
                    x = x2
    return img
