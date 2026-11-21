"""A small watercolour engine: transparent pigment glazed onto cold-press paper.

Shapes are drawn in the cover's world units (236 x 344; the title and name sit on bare paper at the top), rendered
at S px per unit. What makes it read as paint, not as a vector drawing with a texture:
  - edges are warped at two scales, so no line is ruled and no curve is geometric;
  - a hard edge (wet paint meeting dry paper) carries a thin dark rim where pigment was carried and dried;
  - inside a wash the pigment settles unevenly in soft blotches, with faint backrun lines where they meet;
  - glazes are Beer-Lambert: each layer filters the light, so overlaps deepen and saturate as real glazes do;
  - granulation is subtle, in the paper's fine tooth; dry brush breaks a stroke on the tooth's peaks;
  - wet-in-wet washes melt into each other and feather out instead of ending.
Bare paper is every white in the picture; nothing is painted white."""
import math
import numpy as np
import cv2
from PIL import Image, ImageDraw

S = 4                      # px per world unit: 236 x 344 -> 944 x 1376 (the 472 x 688 board cover at 2x)
W, H = 236 * S, 344 * S
PAPER = np.array([0.992, 0.987, 0.972])
YY, XX = np.mgrid[0:H, 0:W].astype(np.float32)


def rgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], np.float32) / 255


def _vnoise(sx, sy, seed):
    g = np.random.default_rng(seed).random((int(H / sy) + 3, int(W / sx) + 3)).astype(np.float32)
    return cv2.resize(g, (W, H), interpolation=cv2.INTER_CUBIC)


def fbm(scale, seed, octaves=4, aspect=1.0):
    """Value-noise fbm; scale in px."""
    out, amp, tot = 0.0, 1.0, 0.0
    for o in range(octaves):
        s = max(1.5, scale / 2 ** o)
        out = out + amp * _vnoise(s * aspect, s, seed + o * 31)
        tot += amp
        amp *= 0.5
    return np.clip(out / tot, 0, 1)


def warped(scale, seed, warp=0.6):
    """Domain-warped fbm: the organic, flowing variation of pigment in water."""
    dx = (fbm(scale, seed + 101, 3) - 0.5) * scale * warp * 2
    dy = (fbm(scale, seed + 202, 3) - 0.5) * scale * warp * 2
    base = fbm(scale, seed, 4)
    return cv2.remap(base, XX + dx, YY + dy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


def blur(a, r_px):
    if r_px <= 0:
        return a
    k = int(r_px * 3) * 2 + 1
    return cv2.GaussianBlur(a.astype(np.float32), (k, k), r_px)


def smooth(a, lo, hi):
    t = np.clip((a - lo) / (hi - lo), 0, 1)
    return t * t * (3 - 2 * t)


class Paper:
    def __init__(self, seed=1):
        self.seed = seed
        self.tooth = (0.55 * fbm(2.0, seed, 2) + 0.45 * fbm(5, seed + 5, 2)).astype(np.float32)
        self.img = np.ones((H, W, 3), np.float32) * PAPER
        self._n = 0

    def _seed(self):
        self._n += 1
        return self.seed * 1000 + self._n * 7

    # ---- shapes, in world units ----
    def poly(self, pts):
        im = Image.new("L", (W, H), 0)
        ImageDraw.Draw(im).polygon([(x * S, y * S) for x, y in pts], fill=255)
        return np.asarray(im, np.float32) / 255

    def ellipse(self, cx, cy, rx, ry):
        im = Image.new("L", (W, H), 0)
        ImageDraw.Draw(im).ellipse([(cx - rx) * S, (cy - ry) * S, (cx + rx) * S, (cy + ry) * S], fill=255)
        return np.asarray(im, np.float32) / 255

    def stroke(self, pts, width, taper=True):
        """A brush line along a polyline, swelling in the middle and lifting at the ends."""
        im = Image.new("L", (W, H), 0)
        d = ImageDraw.Draw(im)
        n = len(pts)
        for i in range(n - 1):
            t = (i + 0.5) / max(1, n - 1)
            w = width * ((math.sin(math.pi * t) * 0.7 + 0.3) if taper else 1)
            (x0, y0), (x1, y1) = pts[i], pts[i + 1]
            d.line([(x0 * S, y0 * S), (x1 * S, y1 * S)], fill=255, width=max(1, int(round(w * S))))
            r = w * S / 2
            d.ellipse([x1 * S - r, y1 * S - r, x1 * S + r, y1 * S + r], fill=255)
        return np.asarray(im, np.float32) / 255

    def rough(self, m, amount=1.0, scale=6.0, fine=0.35):
        """Warp a mask's edge at two scales (world units): a wobbly hand edge plus fine brush ragging."""
        s = self._seed()
        dx = (fbm(scale * S, s, 3) - 0.5) * amount * S * 2 + (fbm(1.2 * S, s + 9, 2) - 0.5) * fine * S * 2
        dy = (fbm(scale * S, s + 1, 3) - 0.5) * amount * S * 2 + (fbm(1.2 * S, s + 8, 2) - 0.5) * fine * S * 2
        out = cv2.remap(m.astype(np.float32), (XX + dx).astype(np.float32), (YY + dy).astype(np.float32),
                        cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)   # no paper pulled in at the cover's edge
        return np.clip(blur(out, 0.6), 0, 1)

    def soften(self, m, r):
        """Wet-in-wet: the edge feathers out over r world units, unevenly."""
        s = self._seed()
        b = blur(m, r * S)
        n = (warped(r * S * 2, s) - 0.5) * 0.5
        return np.clip(b + n * b * (1 - b) * 4, 0, 1)

    # ---- painting ----
    def wash(self, mask, colour, density, rim=0.9, rimw=0.9, flow=0.3, blotch=0.12, gran=0.16, dry=0.0,
             vary=None, scale=40):
        """Glaze pigment through a mask (0..1). density ~ 0.2 pale .. 1.5 deep. rim: pooled-edge strength at hard
        edges; flow: uneven settling; blotch: soft patches with faint backrun lines; dry: breakup on the tooth."""
        s = self._seed()
        c = rgb(colour) if isinstance(colour, str) else colour
        m = np.clip(mask, 0, 1).astype(np.float32)
        hard = (m > 0.5).astype(np.uint8)
        dist = cv2.distanceTransform(hard, cv2.DIST_L2, 5) / S if hard.any() else np.zeros_like(m)
        rimf = np.exp(-dist / rimw) * hard * (m > 0.95)
        f = warped(scale * S, s)
        b = warped(scale * 0.7 * S, s + 50)
        patches = smooth(b, 0.42, 0.58)
        backrun = np.exp(-((b - 0.5) / 0.01) ** 2)
        D = density * m * (1 + flow * (f - 0.5) * 2) * (1 + blotch * (patches - 0.5) * 2 + blotch * 0.6 * backrun)
        D = D * (1 + rim * rimf) * (1 + gran * (self.tooth - 0.5) * 2.5)
        if vary is not None:
            D = D * vary
        if dry > 0:
            edge = np.clip(1 - dist / 3.0, 0, 1)
            nz = self.tooth + 0.3 * (fbm(2.5 * S, s + 9, 2) - 0.5)
            broken = nz > (0.75 - 0.4 * dry * (0.4 + 0.6 * edge))
            D = D * np.where(broken, 1 - dry, 1.0)
        D = np.clip(D, 0, 3)[..., None]
        self.img = self.img * np.power(np.clip(c, 0.02, 1), D)

    def loose(self, mask, cols, density=0.8, n=7, rough=0.8, patch=0.45, ground=0.35, seed=None, vary=None):
        """Paint a shape the way the foliage is painted, not as a clean fill: a hand-wobbled outline; a pale ground
        glaze; then n overlapping wet patches of related colours, each pooling at its own edge where it dried, so the
        shape is built from brush marks. patch: patch size as a fraction of the shape's extent."""
        rng = np.random.default_rng(self._seed() if seed is None else seed)
        m = self.rough(mask, rough, 3.0, fine=0.6)
        ys, xs = np.nonzero(m > 0.5)
        if len(xs) == 0:
            return m
        x0, x1, y0, y1 = xs.min() / S, xs.max() / S, ys.min() / S, ys.max() / S
        ex, ey = max(1.0, x1 - x0), max(1.0, y1 - y0)
        self.wash(m, cols[0], density * ground, rim=1.0, flow=0.4, blotch=0.06, vary=vary)
        for i in range(n):
            cx, cy = rng.uniform(x0, x1), rng.uniform(y0, y1)
            rx, ry = ex * patch * rng.uniform(0.5, 1.0), ey * patch * rng.uniform(0.5, 1.0)
            pm = self.rough(self.ellipse(cx, cy, rx, ry), max(0.6, min(rx, ry) * 0.25), max(2.0, min(rx, ry) * 0.6),
                            fine=0.6) * m
            self.wash(pm, cols[i % len(cols)], density * rng.uniform(0.45, 0.85), rim=1.4, flow=0.5, blotch=0.08,
                      vary=vary)
        return m

    def lift(self, mask, amount=0.7, dry=0.0):
        """Lift paint back toward paper with a damp brush or tissue; dry > 0 lifts only on the tooth's peaks, the
        broken white of a dry-brush stroke dragged across."""
        m = np.clip(mask, 0, 1)
        if dry > 0:
            s = self._seed()
            nz = self.tooth + 0.35 * (fbm(2.5 * S, s, 2) - 0.5)
            m = m * np.where(nz > 0.62 - 0.35 * dry, 1.0, 0.15)
        self.img = self.img + (PAPER - self.img) * (m[..., None] * amount)

    def backrun(self, cx, cy, r, colour, strength=0.5):
        """A cauliflower: wet paint crept back into a drying wash, leaving a pale flower with a dark ragged rim."""
        m = self.rough(self.ellipse(cx, cy, r, r * 0.75), r * 0.25, r * 0.35, fine=0.6)
        inner = blur(m, r * S * 0.3)
        self.img = self.img + (PAPER - self.img) * (np.clip(inner * 1.2, 0, 1)[..., None] * strength * 0.6)
        ring = np.clip(m - np.clip(inner * 1.25, 0, 1), 0, 1)
        self.wash(ring, colour, strength, rim=0.0, flow=0.3, blotch=0.02)

    def fade_top(self, y0, y1, seed=77, right=None, keep=None):
        """Nothing above y0, full strength below y1, a ragged drying edge between. right=(x from, x to, y0 there):
        the line rises toward the right edge, where the art may climb above the name line. keep: a mask the fade
        leaves alone (a tower that stands above it)."""
        Yw = YY / S
        lift = 0.0
        if right:
            xa, xb, yr = right
            lift = smooth(XX / S, xa, xb) * (y0 - yr)
        n = (warped(14 * S, seed) - 0.5) * (y1 - y0) * 1.1
        t = smooth(Yw - y0 + lift + n, 0, y1 - y0)
        if keep is not None:
            t = np.maximum(t, np.clip(keep, 0, 1))
        self.img = PAPER + (self.img - PAPER) * t[..., None]

    def finish(self):
        """The paper's own tooth shows faintly everywhere, even where it is bare."""
        self.img = self.img * (1 - 0.018 * (self.tooth[..., None] - 0.5) * 2)

    def save(self, path, size=None):
        a = (np.clip(self.img, 0, 1) * 255).astype(np.uint8)
        im = Image.fromarray(a)
        if size:
            im = im.resize(size, Image.LANCZOS)
        im.save(path)


def ramp_y(y0, y1, a, b):
    t = np.clip((YY / S - y0) / max(1e-6, (y1 - y0)), 0, 1)
    return a + (b - a) * t


def ramp_x(x0, x1, a, b):
    t = np.clip((XX / S - x0) / max(1e-6, (x1 - x0)), 0, 1)
    return a + (b - a) * t
