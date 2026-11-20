"""Gouache poster landscape: flat, opaque shapes with dry-brushed edges, edge to edge, cut to white under the title.
The end of a night shift: first light over a river town. python3 gouache.py out.png [seed]"""
import sys
import numpy as np
from PIL import Image

W, H = 944, 1376
seed = int(sys.argv[2]) if len(sys.argv) > 2 else 2
r = np.random.default_rng(seed)
Y, X = np.mgrid[0:H, 0:W].astype(float)


def rgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], float)


def noise(scale_x, scale_y, s):
    g = np.random.default_rng(s).random((int(H / scale_y) + 3, int(W / scale_x) + 3))
    return np.asarray(Image.fromarray((g * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC), float) / 255


def ridge(base, waves, s, rough=10):
    """A skyline: a few long swells plus small bumps."""
    x = np.arange(W)
    rr = np.random.default_rng(s)
    y = np.full(W, float(base))
    for amp, wl in waves:
        y += amp * np.sin(x / wl * 2 * np.pi + rr.uniform(0, 6.28))
    bumps = np.interp(x, np.linspace(0, W, 40), rr.normal(0, rough, 40))
    return y + bumps


TOOTH = noise(4.5, 3.2, 90)          # paper tooth: the brush skips it at edges
STREAK = noise(140, 5, 91)           # long horizontal brush drag
img = np.ones((H, W, 3)) * 255.0


def paint(mask_field, colour, edge=2.6, vary=0.07, s=0):
    """mask_field > 0 is inside. Edges break up on the paper tooth; the fill carries faint brush drag."""
    a = np.clip((mask_field + (TOOTH - 0.5) * edge * 2.2) / 1.5 + 0.5, 0, 1)
    drag = 1 + vary * (noise(170, 6, 100 + s) - 0.5) + 0.03 * (TOOTH - 0.5)
    col = np.clip(colour[None, None, :] * drag[..., None], 0, 255)
    global img
    img = img * (1 - a[..., None]) + col * a[..., None]


# sky: bands of colour stepping down from white, each with a soft cloud-shaped upper edge
bands = [(520, "#FBEFD2"), (610, "#F8DDB0"), (700, "#F3C79A"), (790, "#E9B39A"), (860, "#C9A9B4")]
for i, (y0, c) in enumerate(bands):
    edge_line = ridge(y0, [(26, 520), (12, 190), (6, 70)], 10 + i, rough=5)
    paint(Y - edge_line[None, :], rgb(c), edge=3.5, s=i)
# sun, low, half behind the far range
sx, sy, sr = 610, 842, 92
paint(sr - np.hypot(X - sx, Y - sy), rgb("#FFF6DC"), edge=3, vary=0.02, s=20)
# ranges, far to near
far = ridge(880, [(46, 700), (22, 260), (8, 90)], 31, rough=7)
paint(Y - far[None, :], rgb("#8E9CC0"), s=31)
mid = ridge(960, [(40, 560), (26, 230), (9, 80)], 32, rough=8)
paint(Y - mid[None, :], rgb("#5E77A6"), s=32)
# a lighter face on the mid range where the sun catches it
paint(np.minimum(Y - mid[None, :], (mid[None, :] + 26 + 16 * np.sin(X / 37)) - Y) * ((X > 380) & (X < 860)) - 1e3 * ~((X > 380) & (X < 860)),
      rgb("#7C93BC"), edge=4, s=33)
near = ridge(1050, [(34, 620), (16, 200)], 34, rough=6)
paint(Y - near[None, :], rgb("#2F4A78"), s=34)
# the river: a pale band that widens toward the viewer, catching the sky
cx = 500 + 150 * np.sin((Y - 1040) / 120.0) + (Y - 1040) * 0.25
hw = 18 + np.clip(Y - 1050, 0, None) * 0.62
riv = np.where(Y > 1052, hw - np.abs(X - cx), -1e3)
paint(riv, rgb("#F3C79A"), edge=4, vary=0.1, s=40)
dash = (noise(90, 3, 41) > 0.56) & (((Y + 8 * np.sin(X / 50)) % 26) < 7)
paint(np.where(dash, riv - 16, -1e3), rgb("#FDF3DC"), edge=2, vary=0, s=41)
paint(np.where((noise(70, 3, 42) > 0.66) & (((Y + 13) % 26) < 5), riv - 10, -1e3), rgb("#DDA98C"), edge=2, vary=0, s=42)
# the town on the near bank: dark blocks, a spire, lit windows
town = np.full((H, W), -1e3)
rr = np.random.default_rng(seed + 50)
x = -10
blocks = []
while x < W + 10:
    w = rr.integers(34, 78)
    h = rr.integers(40, 120)
    base = near[int(np.clip(x + w / 2, 0, W - 1))] + 26
    if not (cx[int(np.clip(base + 20, 0, H - 1)), 0] - 40 < x + w / 2 < cx[int(np.clip(base + 20, 0, H - 1)), 0] + 60):
        blocks.append((x, base - h, w, h + 400))
        f = np.minimum(np.minimum(X - x, x + w - X), Y - (base - h))
        if rr.random() < 0.35:  # pitched roof
            f = np.maximum(f, np.minimum((w / 2 - np.abs(X - x - w / 2)) * 0.8 - ((base - h) - Y), (base - h) - Y + 1))
        town = np.maximum(town, f)
    x += w + rr.integers(-4, 10)
town = np.where(riv > -6, -1e3, town)
paint(town, rgb("#1B2C52"), edge=2.5, s=50)
front = ridge(1235, [(30, 500), (14, 170)], 60, rough=5)
frontf = np.where(riv > -10, -1e3, Y - front[None, :])
paint(frontf, rgb("#14203F"), s=60)
for bx, by, bw, bh in blocks:
    for wy in np.arange(by + 14, by + 110, 24):
        for wx in np.arange(bx + 9, bx + bw - 12, 17):
            if rr.random() < 0.22 and wy < front[int(np.clip(wx, 0, W - 1))] - 16:
                f = np.minimum(np.minimum(X - wx, wx + 7 - X), np.minimum(Y - wy, wy + 11 - Y))
                paint(np.where(town > 2, f, -1e3), rgb("#FFD98A"), edge=1.2, vary=0, s=70)
# a few reeds of light on the dark front bank keep it from going flat
img += r.normal(0, 1.6, (H, W, 1))
Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(sys.argv[1])
