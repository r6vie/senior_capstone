"""Layered cut paper, round 2: the sky runs to the top of the cover. Cloud banks hang from the top edge, each a sheet
paler than the one behind, so the title sits whole on the palest paper. The moon, stars and lit window are holes
through to the glow. python3 papercut2.py out.png [seed]"""
import sys
import numpy as np
from PIL import Image

W, H = 944, 1376
seed = int(sys.argv[2]) if len(sys.argv) > 2 else 5
r = np.random.default_rng(seed)
Y, X = np.mgrid[0:H, 0:W].astype(float)
xs = np.arange(W, dtype=float)


def rgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], float)


def noise(sx, sy, s):
    g = np.random.default_rng(s).random((int(H / sy) + 3, int(W / sx) + 3))
    return np.asarray(Image.fromarray((g * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC), float) / 255


def box(a, rx, ry):
    for ax, rr in ((1, rx), (0, ry)):
        if rr > 0:
            k = 2 * rr + 1
            pad = np.pad(a, [(rr, rr) if i == ax else (0, 0) for i in range(2)], mode="edge")
            c = np.insert(np.cumsum(pad, axis=ax), 0, 0, axis=ax)
            a = (np.take(c, np.arange(k, k + a.shape[ax]), axis=ax) - np.take(c, np.arange(0, a.shape[ax]), axis=ax)) / k
    return a


def blur(a, rad):
    rr = max(1, int(round(rad * 0.9)))
    return box(box(box(a, rr, rr), rr, rr), rr, rr)


def aa(field):
    return np.clip(field + 0.5, 0, 1)


# the glow behind everything: warm light, brightest behind the moon
mx, my = 452, 712
d = np.hypot(X - mx, (Y - my) * 0.9)
t = np.clip(d / 620, 0, 1)[..., None]
img = rgb("#FFF8E1") * (1 - t) + rgb("#F8CF93") * t


def sheet(field, colour, lift=7, soft=9, dark=0.34, s=0, fibre=0.03):
    """Lay one sheet. field > 0 is paper. It shades what is behind it (offset down-right, as lit from the upper
    left), shows a hairline of lit edge where it was cut, and carries faint paper fibre."""
    global img
    a = aa(field)
    sh = blur(np.roll(np.roll(a, lift, 0), lift // 2, 1), soft)
    img = img * (1 - dark * sh[..., None])
    near = blur(np.roll(a, 2, 0), 2.0)                       # a tighter contact shadow
    img = img * (1 - 0.18 * near[..., None])
    tex = 1 + fibre * (noise(2.5, 2.5, 300 + s) - 0.5) * 2 + 0.02 * (noise(60, 3, 400 + s) - 0.5) * 2
    col = np.clip(colour[None, None, :] * tex[..., None], 0, 255)
    img = img * (1 - a[..., None]) + col * a[..., None]
    edge = np.clip(a - np.roll(a, 2, 0), 0, 1) * a          # the cut edge catches the light
    img = img + edge[..., None] * 30
    return a


def n1(scale, s, amp):
    pts = np.arange(-scale, W + 2 * scale, scale)
    return np.interp(xs, pts, np.random.default_rng(s).normal(0, amp, len(pts)))


def smooth1(v, k):
    return np.convolve(np.pad(v, k, mode="edge"), np.ones(2 * k + 1) / (2 * k + 1), mode="valid")


def pines(base, s, hmin, hmax, step, where=None):
    edge = base.copy()
    fr = np.random.default_rng(s)
    x = -10.0
    while x < W + 10:
        if where is None or where(x):
            h = fr.uniform(hmin, hmax)
            wd = h * fr.uniform(0.2, 0.27)
            b = np.interp(x, xs, base)
            tier = np.abs(xs - x) * (h / wd)
            edge = np.minimum(edge, b - h + tier - 0.12 * h * (np.sin(tier / h * 14) > 0) * (tier < h))
        x += fr.uniform(step * 0.7, step * 1.4)
    return edge


def bank(base, depth, s, n=9, wobble=10):
    """A cloud bank hanging from the top edge: its lower edge is a row of round scallops."""
    cr = np.random.default_rng(s)
    e = np.full(W, float(base))
    cs = np.linspace(-60, W + 60, n) + cr.uniform(-40, 40, n)
    for c in cs:
        rad = cr.uniform(0.7, 1.25) * depth
        e = np.maximum(e, base + np.sqrt(np.clip(rad ** 2 - (xs - c) ** 2, 0, None)) * 0.55)
    return smooth1(e + n1(60, s + 3, wobble * 0.2), 2)


def puff(parts, bottom):
    """A floating cloud: round tops, cut flat underneath."""
    f = np.full((H, W), -1e3)
    for cx, cy, rad in parts:
        f = np.maximum(f, rad - np.hypot(X - cx, Y - cy))
    return np.minimum(f, bottom - Y)


# 1. sky sheet: the moon and a few stars are holes punched through to the glow
sky = np.minimum(np.hypot(X - mx, Y - my) - 82, 1e3)
sr = np.random.default_rng(seed + 1)
for _ in range(26):
    sxx, syy = sr.uniform(20, W - 20), sr.uniform(520, 860)
    if np.hypot(sxx - mx, syy - my) > 130:
        sky = np.minimum(sky, np.hypot(X - sxx, Y - syy) - sr.uniform(1.6, 3.6))
sheet(sky, rgb("#F2B28E"), lift=5, soft=6, dark=0.28, s=1)
# 2-3. far ranges
m1 = smooth1(880 - 150 * np.exp(-((xs - 250) / 190) ** 2) - 210 * np.exp(-((xs - 720) / 230) ** 2)
             - 70 * np.exp(-((xs - 470) / 110) ** 2) + n1(40, 11, 7), 5)
sheet(Y - m1[None, :], rgb("#D992A0"), s=2)
m2 = smooth1(940 - 120 * np.exp(-((xs - 80) / 200) ** 2) - 150 * np.exp(-((xs - 520) / 210) ** 2)
             - 110 * np.exp(-((xs - 900) / 170) ** 2) + n1(34, 12, 6), 4)
sheet(Y - m2[None, :], rgb("#A878A8"), s=3)
# 4. forested ridge
h3 = 1010 + 26 * np.sin(xs / 190 + 0.6) - 30 * np.exp(-((xs - 830) / 200) ** 2)
sheet(Y - pines(h3, 21, 16, 40, 12)[None, :], rgb("#6E689F"), s=4)
# 5. the hill with the house; its window is cut right through to the glow
h4 = 1100 - 54 * np.exp(-((xs - 300) / 260) ** 2) + 18 * np.sin(xs / 130 + 2)
e4 = pines(h4, 22, 30, 74, 22, where=lambda x: not (230 < x < 400))
f4 = Y - e4[None, :]
hx, hy = 318, float(np.interp(318, xs, h4)) + 6
house = np.minimum(np.minimum(X - (hx - 38), hx + 38 - X), Y - (hy - 46))
roof = np.minimum((50 - np.abs(X - hx)) * 0.72 - ((hy - 46) - Y), (hy - 45) - Y)
chim = np.minimum(np.minimum(X - (hx + 16), hx + 27 - X), Y - (hy - 88)) - 1e3 * (Y > hy - 46)
f4 = np.maximum(np.maximum(f4, np.maximum(house, roof)), chim)
win = np.minimum(np.minimum(X - (hx - 24), hx - 6 - X), np.minimum(Y - (hy - 34), hy - 10 - Y))
win = np.maximum(win, np.minimum(np.minimum(X - (hx + 6), hx + 24 - X), np.minimum(Y - (hy - 34), hy - 10 - Y)))
bars = np.minimum(np.abs(X - (hx - 15)) - 1.3, np.abs(Y - (hy - 22)) - 1.3)
win = np.minimum(win, np.where(X < hx, bars, np.minimum(np.abs(X - (hx + 15)) - 1.3, np.abs(Y - (hy - 22)) - 1.3)))
sheet(np.minimum(f4, -win), rgb("#454E8C"), s=5)
wa = aa(win)[..., None]                                   # the window: straight through to the glow
img = img * (1 - wa) + rgb("#FFE9A8") * wa
img = img * (1 - 0.25 * blur(np.roll(aa(-win) * aa(win + 6), 3, 0), 2)[..., None] * wa)
# 6. nearer slope with taller pines
h5 = 1210 + 34 * np.sin(xs / 240 + 4) + 40 * np.clip((500 - xs) / 500, 0, 1)
sheet(Y - pines(h5, 23, 60, 150, 40, where=lambda x: x > 470 or x < 60)[None, :], rgb("#2B3670"), lift=9, soft=11, s=6)
# 7. the front: grass blades and two tall pines at the left edge
h6 = 1320 + 16 * np.sin(xs / 120 + 1)
f6 = Y - h6[None, :]
gr = np.random.default_rng(seed + 9)
for _ in range(120):
    gx, gh, lean = gr.uniform(0, W), gr.uniform(16, 64), gr.uniform(-0.45, 0.45)
    up = np.interp(gx, xs, h6) + 3 - Y
    f6 = np.maximum(f6, np.minimum(np.minimum(up, gh - up), (2.6 * (1 - up / gh) + 0.5) - np.abs(X - gx - lean * up - 0.004 * up * up)))
for tx, top, mw in [(70, 930, 80), (168, 1040, 62)]:
    base = 1340
    th = base - top
    up = base - Y
    tt = np.clip(up / th, 0, 1)
    tier = th / 8.0
    saw = 1 - ((up + tx) % tier) / tier
    half = (1 - tt) * mw * (0.36 + 0.64 * saw ** 0.75)
    f6 = np.maximum(f6, np.minimum(np.maximum(half - np.abs(X - tx), 4 - np.abs(X - tx)), np.minimum(up, th - up) + 2))
sheet(f6, rgb("#161D45"), lift=10, soft=12, dark=0.4, s=7)

# the sky's upper layers, back to front: each bank reaches less far down and is paler, so the title sits on the
# palest sheet, whole, with no cut edge running through it
sheet(bank(575, 46, 31, n=10)[None, :] - Y, rgb("#F6C6A2"), lift=7, soft=9, dark=0.3, s=31)
sheet(puff([(150, 640, 26), (196, 626, 36), (246, 640, 26)], 652), rgb("#F8D5B6"), lift=6, soft=7, dark=0.28, s=33)
sheet(bank(500, 40, 32, n=9)[None, :] - Y, rgb("#F9D9BC"), lift=7, soft=9, dark=0.28, s=32)
sheet(bank(440, 40, 34, n=8)[None, :] - Y, rgb("#FCEAD6"), lift=6, soft=8, dark=0.24, s=34, fibre=0.02)
Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(sys.argv[1])
