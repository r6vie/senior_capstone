"""Turn a smooth render into the reference's slabs: python3 pixelate.py beauty.png id.png out.png

Each material is redrawn in its own grain of flat slabs (wide, staggered rows), each slab the mean tone of the
render under it. A hairline lighter row top keeps the courses legible. A light softening matches the reference."""

import sys

import numpy as np
from PIL import Image, ImageFilter

beauty_p, id_p, out_p = sys.argv[1:4]
PAPER = np.array([246, 247, 242]) / 255
b = Image.open(beauty_p).convert("RGBA")
bg = Image.new("RGBA", b.size, (246, 247, 242, 255))
bg.alpha_composite(b)
img = np.asarray(bg.convert("RGB")).astype(float) / 255
ida = np.asarray(Image.open(id_p).convert("RGBA")).astype(int)
alpha = ida[..., 3] > 128
code = ((ida[..., 0] > 128) * 4 + (ida[..., 1] > 128) * 2 + (ida[..., 2] > 128) * 1) * alpha
# id colours from smooth.py: blue FF0000=4, cream 00FF00=2, coral 0000FF=1, terrace FFFF00=6, water 00FFFF=3,
# trunk FF00FF=5, leaf FFFFFF=7
H, W = code.shape
out = np.ones_like(img) * PAPER
r = np.random.default_rng(9)

# coral lives inside the cream masses as a colour band: give it its own grain
red = (img[..., 0] - img[..., 2]) > 0.12
code = np.where((code == 2) & red, 1, code)

# (code, cell w, cell h, tone levels); a fixed grid of flat blocks, each with a light top row and darker side/foot
GRAIN = [
    (4, 12, 5, 3),   # blue
    (2, 12, 6, 6),   # cream
    (1, 14, 4, 3),   # coral
    (6, 12, 4, 4),   # terraces
    (3, 18, 5, 5),   # water
    (5, 4, 5, 2),    # trunks
    (7, 6, 5, 5),    # leaves
]
PALE = np.array([0.71, 0.82, 0.87])


def snap(col, levels, lo, hi):
    L = col.mean()
    if hi - lo < 1e-3 or L <= 0:
        return col
    t = np.clip((L - lo) / (hi - lo), 0, 1)
    Lq = lo + np.round(t * (levels - 1)) / (levels - 1) * (hi - lo)
    return np.clip(col * (Lq / L), 0, 1)


import os
ONLY = os.environ.get('ONLY')
if ONLY:
    keep = set(int(v) for v in ONLY.split(','))
    GRAIN = [g for g in GRAIN if g[0] in keep]
    out = img.copy()
for c, cw, ch, levels in GRAIN:
    mask = code == c
    if not mask.any():
        continue
    lum = img[mask].mean(1)
    lo, hi = np.percentile(lum, 2), np.percentile(lum, 98)
    for y0 in range(0, H, ch):
        y1 = min(H, y0 + ch)
        for x0 in range(0, W, cw):
            x1 = min(W, x0 + cw)
            m = mask[y0:y1, x0:x1]
            if m.mean() < 0.5:
                continue
            col = img[y0:y1, x0:x1][m].mean(0)
            if np.abs(col - PAPER).max() < 0.03:
                continue
            col = snap(col, levels, lo, hi)
            if c == 3:  # water pales with distance
                col = col * (1 - np.clip((600 - y0) / 320, 0, 0.55)) + PALE * np.clip((600 - y0) / 320, 0, 0.55)
            col = np.clip(col * (1 + r.normal(0, 0.012)), 0, 1)
            out[y0:y1, x0:x1] = col
            if ch >= 4 and cw >= 6:
                out[y0, x0:x1] = np.clip(col + (1 - col) * 0.14, 0, 1)
                out[y1 - 1, x0:x1] = col * 0.9
                out[y0 + 1:y1 - 1, x1 - 1] = col * 0.94
im = Image.fromarray((np.clip(out, 0, 1) * 255).round().astype(np.uint8))
# the original reads as an upscaled, compressed render: soften the same way
small = im.resize((int(W * 0.6), int(H * 0.6)), Image.LANCZOS)
im = small.resize((W, H), Image.BICUBIC)
import io
buf = io.BytesIO()
im.save(buf, "JPEG", quality=82)
buf.seek(0)
Image.open(buf).convert("RGB").save(out_p)
print("ok")
