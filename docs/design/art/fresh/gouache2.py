"""Gouache travel poster, round 2: an alpine lake at first light. Flat opaque colour, but drawn shapes: peaks with
lit and shadowed planes and snow, streak clouds that thin out to white, pine-edged hills, a framing stand of pines.
python3 gouache2.py out.png [seed]"""
import sys
import numpy as np
from PIL import Image

W, H = 944, 1376
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
img = np.ones((H, W, 3)) * 255.0


def paint(field, colour, edge=1.3, vary=0.045, s=0, alpha=1.0, grade=None):
    """field > 0 is inside. A slightly broken edge and faint brush drag; grade=(colour2, t) blends toward a second
    colour by t (HxW, 0..1) inside the shape, as gouache is blended wet."""
    global img
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


# ---------- sky: flat bands with level, slightly bowed edges; long streak clouds carry it up into the white ----------
bands = [(560, "#FFF6E3"), (640, "#FDE9C6"), (715, "#FAD7A9"), (790, "#F5C29A"), (858, "#ECAE9C"), (915, "#D9A2AC")]
for i, (y0, c) in enumerate(bands):
    line = y0 + 10 * np.sin(xs / 330 + i * 1.7) + n1(120, 10 + i, 3)
    paint(Y - line[None, :], rgb(c), s=i)
rr = np.random.default_rng(seed + 1)
for cy, col in [(470, "#FFF6E3"), (492, "#FFF6E3"), (515, "#FDE9C6"), (538, "#FFF6E3"), (548, "#FDE9C6"), (600, "#FAD7A9"),
                (668, "#FFF6E3"), (700, "#F5C29A"), (742, "#FDE9C6"), (770, "#D9A2AC"), (812, "#FAD7A9"), (836, "#C79FB6")]:
    cx, rx = rr.uniform(60, W - 60), rr.uniform(170, 430)
    paint(lens(cx, cy, rx, rr.uniform(5, 13), p=1.4, skew=rr.uniform(-0.3, 0.3)), rgb(col), edge=0.9, s=int(cy))
# sun with one soft ring
sx, sy = 286, 838
paint(96 - np.hypot(X - sx, Y - sy), rgb("#FCE6BC"), edge=0.8, vary=0.02, s=20, alpha=0.75)
paint(64 - np.hypot(X - sx, Y - sy), rgb("#FFFAEA"), edge=0.8, vary=0.01, s=21)


# ---------- peaks: a drawn skyline, a shadow plane falling from each summit, snow above the snowline ----------
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


alps([(140, 760, 190), (402, 640, 250), (690, 590, 290), (905, 700, 170)], 960, rgb("#E3BDBE"), rgb("#A397C0"),
     rgb("#FFF8EC"), rgb("#CFC6E0"), 745, 30)
alps([(-10, 800, 210), (240, 850, 200), (560, 800, 250), (845, 770, 240)], 1000, rgb("#9F92BC"), rgb("#6A6CA5"),
     rgb("#EBDDE6"), rgb("#9D9BC6"), 832, 40, jag=6)
# mist lying in the valley
for cy, cx, rx, ry, a in [(962, 300, 520, 15, 0.9), (976, 720, 460, 12, 0.85), (948, 620, 300, 8, 0.7)]:
    paint(lens(cx, cy, rx, ry, p=1.3), rgb("#F6DCC8"), edge=0.8, alpha=a, s=int(cy))


# ---------- pine-edged hills ----------
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


LAKE = 1092
h1 = 1010 + 16 * np.sin(xs / 210 + 1) + 22 * np.clip((xs - 500) / 444, 0, 1)
forest(h1, rgb("#4A5E8C"), 50, 14, 30, 9, grade_to=rgb("#7B86AC"))
h2 = 1052 - 30 * np.exp(-((xs - 130) / 210) ** 2) + 10 * np.sin(xs / 150)
e2 = forest(h2, rgb("#2B426F"), 51, 20, 46, 11)

# ---------- the lake: the sky laid flat, the forest upside down, long level streaks ----------
paint(Y - LAKE, rgb("#F2C4A2"), s=60, grade=(rgb("#C9A0B4"), (Y - LAKE) / 300))
mir = 2 * LAKE - Y
refl = np.convolve(np.pad(e2, 30, mode="edge"), np.ones(61) / 61, mode="valid")[None, :] + 6
paint(np.minimum(Y - LAKE, mir - refl + 5 * np.sin(X / 23.0) * np.clip((Y - LAKE) / 30, 0, 1)), rgb("#52679A"), edge=1.2, s=61, alpha=0.92)
lr = np.random.default_rng(seed + 7)
for _ in range(46):
    cy = lr.uniform(LAKE + 6, H)
    d = (cy - LAKE) / (H - LAKE)
    cx, rx = lr.uniform(-40, W + 40), lr.uniform(40, 150) * (0.6 + d)
    col = lr.choice(["#FFF1D8", "#F6D0AC", "#7C8BB4", "#52679A", "#E8B4A6"], p=[0.3, 0.25, 0.2, 0.1, 0.15])
    paint(lens(cx, cy, rx, lr.uniform(2.2, 4.5) * (0.7 + d), p=1.3), rgb(col), edge=0.7, s=int(cy))
for k in range(13):                                  # the sun's path
    cy = LAKE + 10 + k * 15 + lr.uniform(-3, 3)
    paint(lens(sx + lr.uniform(-10, 10), cy, lr.uniform(26, 58) * (1 + k * 0.035), 3.4, p=1.2), rgb("#FFF8E4"), edge=0.7, s=k)
paint(1.6 - np.abs(Y - LAKE - 1), rgb("#FFF3DC"), edge=0.5, alpha=0.8)          # the far waterline

# a cabin on the far shore, one window lit
cx0, cy0 = 150, LAKE - 2
cab = np.minimum(np.minimum(X - cx0, cx0 + 44 - X), np.minimum(Y - (cy0 - 22), cy0 - Y))
roofm = np.minimum((30 - np.abs(X - cx0 - 22)) * 0.62 - ((cy0 - 22) - Y), (cy0 - 21) - Y)
paint(np.maximum(cab, roofm), rgb("#1B2A52"), edge=0.6, s=70)
paint(np.minimum(np.minimum(X - cx0 - 8, cx0 + 17 - X), np.minimum(Y - (cy0 - 15), cy0 - 5 - Y)), rgb("#FFD27A"), edge=0.3, vary=0)
for k in range(6):
    paint(lens(cx0 + 12 + lr.uniform(-2, 2), LAKE + 9 + k * 9, 9 - k * 0.6, 2.2), rgb("#FFD27A"), edge=0.4, vary=0, alpha=0.9 - k * 0.1)

# ---------- the near bank and a framing stand of pines ----------
bank = 1322 + 20 * np.sin(xs / 170 + 2) - 46 * np.clip((xs - 600) / 344, 0, 1) ** 1.4
bf = Y - bank[None, :]
tuft = np.zeros((H, W)) - 1e3
gr = np.random.default_rng(seed + 9)
for _ in range(150):
    gx = gr.uniform(0, W)
    gh, lean = gr.uniform(8, 30), gr.uniform(-0.5, 0.5)
    by = np.interp(gx, xs, bank) + 3
    up = by - Y
    tuft = np.maximum(tuft, np.minimum(np.minimum(up, gh - up), (1.9 * (1 - up / gh) + 0.4) - np.abs(X - gx - lean * up)))
pines = np.zeros((H, W)) - 1e3
for tx, top, base, mw in [(742, 786, 1310, 62), (826, 650, 1296, 84), (905, 735, 1290, 70), (668, 960, 1318, 44),
                          (60, 1050, 1332, 46)]:
    th = base - top
    up = base - Y
    t = np.clip(up / th, 0, 1)
    tier = th / 9.0
    saw = 1 - ((up + 7 * np.sin(tx)) % tier) / tier                 # each tier of boughs widens downward, then cuts back
    left = (1 - t) * mw * (0.38 + 0.62 * saw ** 0.7) * (1 + 0.16 * np.sin(up / 23 + tx))
    right = (1 - t) * mw * (0.38 + 0.62 * ((saw + 0.35) % 1) ** 0.7) * (1 + 0.16 * np.sin(up / 19 + tx * 2))
    dx = X - tx
    body = np.where(dx < 0, left + dx, right - dx)
    trunk = 3.5 - np.abs(dx)
    pines = np.maximum(pines, np.minimum(np.maximum(body, trunk), np.minimum(up, th - up) + 2))
front = np.maximum(np.maximum(bf, tuft), pines)
paint(front, rgb("#131E3F"), edge=0.9, vary=0.03, s=80)
# first light catching the pines' left edges
rim = np.minimum(pines, 3.2 - pines) + np.where(X < 0, 0, 0)
lit_side = np.minimum(rim, np.where(np.gradient(pines, axis=1) > 0.2, 1.0, -1e3))
paint(np.where((Y < 1280), lit_side, -1e3), rgb("#5B6FA3"), edge=0.5, vary=0, alpha=0.9)

img += r.normal(0, 1.3, (H, W, 1))
Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(sys.argv[1])
