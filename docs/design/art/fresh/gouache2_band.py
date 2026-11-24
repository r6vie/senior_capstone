"""Gouache travel poster, round 2, as a wide band for the book page: the same paint and palette as gouache2.py, laid out
1440 x 620 (painted at 2x). The poster is cut out on bare paper: peaks at both ends, a low valley and lake under the
title, framing pines at the right. python3 gouache2_band.py out.png [seed]"""
import sys
import numpy as np
from PIL import Image

W, H = 2880, 1240
seed = int(sys.argv[2]) if len(sys.argv) > 2 else 2
r = np.random.default_rng(seed)
Y, X = np.mgrid[0:H, 0:W].astype(float)
xs = np.arange(W, dtype=float)


def rgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], float)


def noise(sx, sy, s):
    g = np.random.default_rng(s).random((int(H / sy) + 3, int(W / sx) + 3))
    return np.asarray(Image.fromarray((g * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC), float) / 255


def n1(scale, s, amp):
    return np.interp(xs, np.arange(-scale, W + 2 * scale, scale), np.random.default_rng(s).normal(0, amp, len(np.arange(-scale, W + 2 * scale, scale))))


TOOTH = noise(4, 3, 90)
img = np.ones((H, W, 3)) * np.array([250.0, 250.0, 247.0])


LIMIT = None


def paint(field, colour, edge=1.3, vary=0.045, s=0, alpha=1.0, grade=None):
    """field > 0 is inside. A slightly broken edge and faint brush drag; grade=(colour2, t) blends toward a second
    colour by t (HxW, 0..1) inside the shape, as gouache is blended wet."""
    global img
    if LIMIT is not None:
        field = np.minimum(field, LIMIT - Y)     # nothing behind the lake shows below it
    a = np.clip((field + (TOOTH - 0.5) * edge * 2) / 1.2 + 0.5, 0, 1) * alpha
    col = np.ones((H, W, 3)) * colour
    if grade is not None:
        c2, t = grade
        t = np.clip(t, 0, 1)[..., None]
        col = col * (1 - t) + c2 * t
    drag = 1 + vary * (noise(190, 5, 100 + s) - 0.5) + 0.02 * (TOOTH - 0.5)
    col = np.clip(col * drag[..., None], 0, 255)
    img = img * (1 - a[..., None]) + col * a[..., None]


def lens(cx, cy, rx, ry, p=1.0, skew=0.0):
    u = (X - cx) / rx
    return ry * np.clip(1 - u * u, 0, 1) ** p * (1 + skew * u) - np.abs(Y - cy) - 1e3 * (np.abs(u) >= 1)


LIMIT = 1000
# ---------- sun and streak clouds, only round the two ends ----------
sx, sy = 2270, 700
paint(84 - np.hypot(X - sx, Y - sy), rgb("#FCE6BC"), edge=0.8, vary=0.02, s=20, alpha=0.75)
paint(56 - np.hypot(X - sx, Y - sy), rgb("#FFFAEA"), edge=0.8, vary=0.01, s=21)
rr = np.random.default_rng(seed + 1)
for cx, cy, col in [(260, 420, "#FDE9C6"), (420, 452, "#FAD7A9"), (120, 520, "#F5C29A"), (560, 560, "#ECAE9C"),
                    (2500, 380, "#FDE9C6"), (2700, 410, "#FAD7A9"), (2380, 470, "#F5C29A"), (2760, 520, "#ECAE9C"), (2480, 600, "#D9A2AC")]:
    paint(lens(cx, cy, rr.uniform(150, 300), rr.uniform(6, 12), p=1.4, skew=rr.uniform(-0.3, 0.3)), rgb(col), edge=0.9, s=int(cy))


def alps(peaks, base, lit, shade, snow_lit, snow_shade, snowline, s, jag=7):
    prof = np.stack([cy + (np.abs(xs - cx) / w) ** 0.88 * (base - cy) for cx, cy, w in peaks])
    ridge = np.minimum(prof.min(0), base) + n1(26, s, jag) * (prof.min(0) < base - 8) + n1(9, s + 1, jag * 0.35)
    inside = Y - ridge[None, :]
    paint(inside, lit, s=s, grade=(rgb("#F1D3C0"), (inside - 40) / 260))
    sh = np.zeros((H, W), bool)
    for i, (cx, cy, w) in enumerate(peaks):
        arete = cx + 0.42 * (Y - cy) + 9 * np.sin(Y / 21 + cx) + 5 * np.sin(Y / 7.3 + i)
        if i + 1 < len(peaks):
            nx, ny, nw = peaks[i + 1]
            xv = (cx * nw + nx * w) / (w + nw)
        else:
            xv = W + 300
        yv = cy + (abs(xv - cx) / w) ** 0.88 * (base - cy)
        right = xv + 0.42 * (Y - yv) + 12 * np.sin(Y / 16 + i)
        sh |= (X > arete) & (X < right)
    shf = np.where(sh, inside, -1e3)
    paint(shf, shade, s=s + 2, grade=(rgb("#F1D3C0"), (inside - 70) / 300))
    snow = snowline + 16 * (noise(40, 40, s + 3) - 0.5) + 30 * (noise(9, 14, s + 4) - 0.5)
    sn = np.minimum(inside, snow - Y)
    paint(sn, snow_lit, s=s + 5)
    paint(np.where(sh, sn, -1e3), snow_shade, s=s + 6)
    return ridge



alps([(170, 330, 300), (560, 470, 300), (2420, 330, 330), (2760, 260, 300)], 870, rgb("#E3BDBE"), rgb("#A397C0"),
     rgb("#FFF8EC"), rgb("#CFC6E0"), 520, 30)
alps([(-20, 560, 280), (340, 620, 260), (2180, 640, 260), (2600, 560, 300), (2950, 600, 200)], 910, rgb("#9F92BC"), rgb("#6A6CA5"),
     rgb("#EBDDE6"), rgb("#9D9BC6"), 650, 40, jag=6)
for cy, cx, rx, ry, a in [(905, 500, 700, 14, 0.9), (918, 2300, 700, 12, 0.85), (896, 1400, 500, 8, 0.7)]:
    paint(lens(cx, cy, rx, ry, p=1.3), rgb("#F6DCC8"), edge=0.8, alpha=a, s=int(cy))


def forest(base_fn, colour, s, hmin, hmax, step, grade_to=None):
    edge = base_fn.copy()
    fr = np.random.default_rng(s)
    x = -10.0
    while x < W + 10:
        h = fr.uniform(hmin, hmax)
        wdt = h * fr.uniform(0.2, 0.28)
        b = np.interp(x, xs, base_fn)
        edge = np.minimum(edge, b - h + np.abs(xs - x) * (h / wdt))
        x += fr.uniform(step * 0.7, step * 1.3)
    f = Y - edge[None, :]
    paint(f, colour, s=s, grade=(grade_to, (f - 30) / 140) if grade_to is not None else None)
    return edge


LAKE = 990
BOTTOM = 1160 + 8 * np.sin(xs / 260 + 1) + 4 * np.sin(xs / 71)
h1 = 932 + 12 * np.sin(xs / 210 + 1)
forest(h1, rgb("#4A5E8C"), 50, 12, 26, 9, grade_to=rgb("#7B86AC"))
h2 = 968 - 26 * np.exp(-((xs - 400) / 300) ** 2) - 30 * np.exp(-((xs - 2500) / 380) ** 2) + 8 * np.sin(xs / 150)
e2 = forest(h2, rgb("#2B426F"), 51, 18, 40, 11)

LIMIT = None
# ---------- the lake, ending in a ragged edge of paper ----------
inlake = np.minimum(Y - LAKE, BOTTOM[None, :] - Y)
paint(inlake, rgb("#F2C4A2"), s=60, grade=(rgb("#C9A0B4"), (Y - LAKE) / 180))
mir = 2 * LAKE - Y
refl = np.convolve(np.pad(e2, 30, mode="edge"), np.ones(61) / 61, mode="valid")[None, :] + 6
paint(np.minimum(inlake, mir - refl + 5 * np.sin(X / 23.0) * np.clip((Y - LAKE) / 30, 0, 1)), rgb("#52679A"), edge=1.2, s=61, alpha=0.92)
lr = np.random.default_rng(seed + 7)
for _ in range(90):
    cy = lr.uniform(LAKE + 6, 1215)
    dd = (cy - LAKE) / (1215 - LAKE)
    cx, rx = lr.uniform(-40, W + 40), lr.uniform(50, 190) * (0.6 + dd)
    col = lr.choice(["#FFF1D8", "#F6D0AC", "#7C8BB4", "#52679A", "#E8B4A6"], p=[0.3, 0.25, 0.2, 0.1, 0.15])
    if cy > np.interp(cx, xs, BOTTOM) - 4:
        col = lr.choice(["#7C8BB4", "#52679A", "#E8B4A6"])     # loose streaks below the edge, on bare paper
    paint(lens(cx, cy, rx, lr.uniform(2.2, 4.5) * (0.7 + dd), p=1.3), rgb(col), edge=0.7, s=int(cy))
for k in range(9):
    cy = LAKE + 10 + k * 15 + lr.uniform(-3, 3)
    paint(lens(sx + lr.uniform(-10, 10), cy, lr.uniform(26, 58) * (1 + k * 0.035), 3.4, p=1.2), rgb("#FFF8E4"), edge=0.7, s=k)
paint(np.minimum(1.6 - np.abs(Y - LAKE - 1), BOTTOM[None, :] - Y), rgb("#FFF3DC"), edge=0.5, alpha=0.8)

# a cabin on the far shore, one window lit, under the title
cx0, cy0 = 1500, LAKE - 2
cab = np.minimum(np.minimum(X - cx0, cx0 + 44 - X), np.minimum(Y - (cy0 - 22), cy0 - Y))
roofm = np.minimum((30 - np.abs(X - cx0 - 22)) * 0.62 - ((cy0 - 22) - Y), (cy0 - 21) - Y)
paint(np.maximum(cab, roofm), rgb("#1B2A52"), edge=0.6, s=70)
paint(np.minimum(np.minimum(X - cx0 - 8, cx0 + 17 - X), np.minimum(Y - (cy0 - 15), cy0 - 5 - Y)), rgb("#FFD27A"), edge=0.3, vary=0)
for k in range(6):
    paint(lens(cx0 + 12 + lr.uniform(-2, 2), LAKE + 9 + k * 9, 9 - k * 0.6, 2.2), rgb("#FFD27A"), edge=0.4, vary=0, alpha=0.9 - k * 0.1)

# ---------- a near bank and a framing stand of pines at the right end ----------
bf = np.maximum(lens(2660, 1150, 300, 38, p=0.7), lens(2860, 1140, 160, 44, p=0.7))
pines = np.zeros((H, W)) - 1e3
for tx, top, base, mw in [(2560, 560, 1150, 66), (2660, 420, 1140, 88), (2770, 500, 1130, 74), (2470, 760, 1160, 46),
                          (2860, 640, 1130, 56)]:
    th = base - top
    up = base - Y
    t = np.clip(up / th, 0, 1)
    tier = th / 9.0
    saw = 1 - ((up + 7 * np.sin(tx)) % tier) / tier
    left = (1 - t) * mw * (0.38 + 0.62 * saw ** 0.7) * (1 + 0.16 * np.sin(up / 23 + tx))
    right = (1 - t) * mw * (0.38 + 0.62 * ((saw + 0.35) % 1) ** 0.7) * (1 + 0.16 * np.sin(up / 19 + tx * 2))
    dx = X - tx
    body = np.where(dx < 0, left + dx, right - dx)
    trunk = 3.5 - np.abs(dx)
    pines = np.maximum(pines, np.minimum(np.maximum(body, trunk), np.minimum(up, th - up) + 2))
front = np.maximum(bf, pines)
paint(front, rgb("#131E3F"), edge=0.9, vary=0.03, s=80)
rim = np.minimum(pines, 3.2 - pines)
lit_side = np.minimum(rim, np.where(np.gradient(pines, axis=1) > 0.2, 1.0, -1e3))
paint(np.where(Y < 1120, lit_side, -1e3), rgb("#5B6FA3"), edge=0.5, vary=0, alpha=0.9)

img += r.normal(0, 1.1, (H, W, 1))
Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(sys.argv[1])
