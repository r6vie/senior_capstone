"""Marbled paper, the bookbinder's way, as maths: drops of colour spread on a bath, then combed.
Every pixel is traced backwards through the strokes and drops to find which drop of colour it came from.
python3 marble.py out.png [seed]"""
import sys
import numpy as np
from PIL import Image

W, H = 944, 1376
SS = 2
seed = int(sys.argv[2]) if len(sys.argv) > 2 else 7
r = np.random.default_rng(seed)


def rgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], float)


PAL = [rgb(c) for c in ("#1F2F4F", "#3E5C82", "#8FA9BF", "#EDE6D6", "#C9A24A", "#16181F", "#DCE3E6", "#5E7F8C")]
WEIGHT = [0.22, 0.2, 0.14, 0.2, 0.07, 0.07, 0.06, 0.04]
BASE = rgb("#EDE6D6")

ops = []
# the stone pattern: rounds of drops, later drops push earlier ones into veins
for n, rad in ((90, (50, 110)), (160, (30, 70)), (260, (14, 40))):
    for _ in range(n):
        ops.append(("drop", r.uniform(-80, W + 80), r.uniform(-80, H + 80), r.uniform(*rad),
                    PAL[r.choice(len(PAL), p=WEIGHT)]))
# gel-git: a wide rake pulled up, then down between
for i, x in enumerate(np.arange(-40, W + 80, 78)):
    ops.append(("tine", x + r.normal(0, 3), 0, 0, 1, 150 * (1 if i % 2 else -1), 30))
# nonpareil: a fine comb drawn across
for y in np.arange(-20, H + 40, 26):
    ops.append(("tine", 0, y + r.normal(0, 1.2), 1, 0, 60, 12))
# one slow wave through the whole sheet, the marbler's hand
ops.append(("wave", 34, 520, r.uniform(0, 6)))

Y, X = np.mgrid[0:H * SS, 0:W * SS].astype(float) / SS
px, py = X.ravel().copy(), Y.ravel().copy()
col = np.tile(BASE, (px.size, 1))
live = np.ones(px.size, bool)
for op in reversed(ops):
    if op[0] == "wave":
        _, amp, wl, ph = op
        px -= amp * np.sin(py / wl * 2 * np.pi + ph)
    elif op[0] == "tine":
        _, bx, by, mx, my, z, c = op
        d = np.abs((px - bx) * (-my) + (py - by) * mx)
        s = z * np.exp(-d / c)
        px -= s * mx
        py -= s * my
    else:
        _, cx, cy, rad, colour = op
        dx, dy = px - cx, py - cy
        d2 = dx * dx + dy * dy
        hit = live & (d2 < rad * rad)
        col[hit] = colour
        live &= ~hit
        k = np.sqrt(np.clip(1 - rad * rad / np.maximum(d2, 1e-6), 0, 1))
        px = np.where(live, cx + dx * k, px)
        py = np.where(live, cy + dy * k, py)
img = np.asarray(Image.fromarray(col.reshape(H * SS, W * SS, 3).astype(np.uint8)).resize((W, H), Image.LANCZOS), float)
# pigment sits unevenly on paper: fine grain, and a little soft mottling
grain = r.normal(0, 5.0, (H, W, 1))
mott = np.asarray(Image.fromarray((r.random((H // 24 + 2, W // 24 + 2)) * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC), float)[..., None]
img = img * (0.95 + 0.1 * mott / 255) + grain
Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(sys.argv[1])
