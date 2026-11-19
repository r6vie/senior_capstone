"""Cells: the reference's paper-model look.

Each layer is a smooth, softly shaded shape (a height field lit from the upper left) that is then sampled onto
its own grid of cells: every cell takes the average tone under it, plus a whisper of jitter. Layers are stacked
back to front like cut paper, and each one pales into white mist toward its base, which is what separates them.
Each material has its own grain: big blocks for snowy mounds, fine lines for coral, small squares for leaves,
long strokes for water.
"""

import numpy as np
from PIL import Image

PAPER = np.array([0.965, 0.969, 0.950])


def rgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i : i + 2], 16) / 255 for i in (0, 2, 4)])


def smooth(t):
    t = np.clip(t, 0, 1)
    return t * t * (3 - 2 * t)


class Canvas:
    def __init__(self, w, h, seed=3):
        self.w, self.h = w, h
        self.img = np.ones((h, w, 3)) * PAPER
        self.Y, self.X = np.mgrid[0:h, 0:w].astype(float)
        self.rng = np.random.default_rng(seed)
        self.bevel = 1.0

    def layer(self, mask, colour, cell, jitter=0.025, row_shade=0.0, ragged=0.0):
        """mask: HxW float 0..1; colour: HxWx3. Sample both onto (cw, ch) cells and paint cells that are mostly in."""
        cw, ch = cell
        H, W = self.h, self.w
        ys, xs = np.nonzero(mask > 0)
        if len(ys) == 0:
            return
        ya, yb = (ys.min() // ch) * ch, min(H, ys.max() + ch)
        xa0, xb0 = max(0, (xs.min() // cw) * cw - cw), min(W, xs.max() + cw)
        for y0 in range(ya, yb, ch):
            y1 = min(H, y0 + ch)
            # rows of the finest grains drift a little sideways, as the reference's strokes do
            off = int(self.rng.integers(0, cw)) if ragged else 0
            for x0 in range(xa0 - off, xb0, cw):
                xa, xb = max(0, x0), min(W, x0 + cw)
                if xb <= xa:
                    continue
                m = mask[y0:y1, xa:xb].mean()
                if m < 0.5 + ragged * (self.rng.random() - 0.5):
                    continue
                c = colour[y0:y1, xa:xb].reshape(-1, 3).mean(0)
                c = c * (1 + self.rng.normal(0, jitter))
                if row_shade and (y0 // ch) % 2:
                    c = c * (1 - row_shade)
                block(self.img, y0, y1, xa, xb, c, self.bevel)

    def save(self, path):
        Image.fromarray((self.img * 255).round().astype(np.uint8)).save(path)


def block(img, y0, y1, x0, x1, c, k=1.0):
    """Paint one cell as a tiny block: lit top face, darker right side and underside."""
    c = np.clip(c, 0, 1)
    img[y0:y1, x0:x1] = c
    h, w = y1 - y0, x1 - x0
    if k <= 0 or h < 3 or w < 3:
        return
    t = max(1, h // 4)
    s = max(1, min(w // 6, 3))
    img[y0:y0 + t, x0:x1] = np.clip(c + (1 - c) * 0.22 * k, 0, 1)
    img[y1 - t:y1, x0:x1] = c * (1 - 0.16 * k)
    img[y0 + t:y1, x1 - s:x1] = c * (1 - 0.10 * k)


def lambert(hfield, X, Y, light=(-0.55, -0.65, 0.52), k=1.0):
    gy, gx = np.gradient(hfield)
    n = np.dstack([-gx * k, -gy * k, np.ones_like(hfield)])
    n /= np.linalg.norm(n, axis=2, keepdims=True)
    L = np.array(light) / np.linalg.norm(light)
    return np.clip((n * L).sum(2), 0, 1)


def ramp(shade, stops):
    """Map 0..1 shade to colour through stops [(t, hex), ...]."""
    ts = np.array([t for t, _ in stops])
    cs = np.array([rgb(c) for _, c in stops])
    out = np.zeros(shade.shape + (3,))
    for i in range(3):
        out[..., i] = np.interp(shade, ts, cs[:, i])
    return out


def mist(colour, Y, y_from, y_to, amount=1.0):
    """Pale toward paper; returns the colour and a keep-mask so nearly-white cells drop out cleanly."""
    t = smooth((Y - y_from) / (y_to - y_from)) * amount
    return colour * (1 - t[..., None]) + PAPER * t[..., None], (t < 0.82).astype(float)


def bars(cv, mask, colour, ch, lmin, lmax, jitter=0.03, smear=0.0, smear_len=(40, 160), alt=0.0, keep=0.5):
    """Horizontal bars of random length on rows of height ch: the reference's strata. Each bar takes the mean tone
    under it. smear: chance that a run's end extends sideways into pale bars, the reference's horizontal mist."""
    H, W = cv.h, cv.w
    r = cv.rng
    for y0 in range(0, H, ch):
        y1 = min(H, y0 + ch)
        row = mask[y0:y1].mean(0)
        on = row > keep
        if not on.any():
            continue
        idx = np.flatnonzero(np.diff(np.concatenate([[0], on.astype(int), [0]])))
        for a, b in zip(idx[::2], idx[1::2]):
            x = a
            while x < b:
                L = int(r.integers(lmin, lmax + 1))
                x2 = min(b, x + L)
                c = colour[y0:y1, x:x2].reshape(-1, 3).mean(0) * (1 + r.normal(0, jitter))
                if alt and (y0 // ch) % 2:
                    c = c * (1 - alt)
                block(cv.img, y0, y1, x, x2, c, cv.bevel)
                x = x2
            for end, sign in ((a, -1), (b, 1)):
                if smear and r.random() < smear:
                    base = colour[y0:y1, max(0, min(W - 1, end - 1 if sign > 0 else end))].mean(0)
                    L = int(r.integers(*smear_len))
                    xs, xe = (end, min(W, end + L)) if sign > 0 else (max(0, end - L), end)
                    steps = max(1, (xe - xs) // max(1, lmin))
                    for k in range(steps):
                        sx0 = xs + k * (xe - xs) // steps
                        sx1 = xs + (k + 1) * (xe - xs) // steps
                        t = (k + 1) / (steps + 1) if sign > 0 else 1 - k / (steps + 1)
                        cc = base * (1 - 0.35 - 0.6 * t) + PAPER * (0.35 + 0.6 * t)
                        cv.img[y0:y1, sx0:sx1] = np.clip(cc * (1 + r.normal(0, 0.015)), 0, 1)
