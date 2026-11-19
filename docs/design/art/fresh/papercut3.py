"""Layered cut paper, round 3: one landscape, drawn once in world coordinates, seen two ways. `band` renders the whole
1440 x 620 view for the book page (at 2x); `cover` renders a portrait window onto the same place (the moon, the
cabin, the pines) with the sky carried up for the title, so the cover is a piece of the page's landscape.
The sky is two sheets cut in long gentle curves, palest at the top.
python3 papercut3.py band|cover out.png"""
import sys
import numpy as np
from PIL import Image

MODE = sys.argv[1]
WW = 2880                                      # the world is as wide as the band
if MODE == "band":
    W, H, OX, OY = 2880, 1240, 0, 0
else:
    W, H, OX, OY = 944, 1376, 1936, -136
Y, X = np.mgrid[0:H, 0:W].astype(float)
X += OX
Y += OY
xs = np.arange(W, dtype=float) + OX


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


def n1(scale, s, amp):
    """Wobble along x, fixed in world space so both views agree."""
    pts = np.arange(-400, WW + 400, scale)
    return np.interp(xs, pts, np.random.default_rng(s).normal(0, amp, len(pts)))


def smooth1(v, k):
    return np.convolve(np.pad(v, k, mode="edge"), np.ones(2 * k + 1) / (2 * k + 1), mode="valid")


def g(c, w):
    return np.exp(-((xs - c) / w) ** 2)


mx, my = 2560, 722
d = np.hypot(X - mx, (Y - my) * 0.9)
t = np.clip(d / 700, 0, 1)[..., None]
img = rgb("#FFF8E1") * (1 - t) + rgb("#F8CF93") * t


def shift(a, dy, dx=0):
    """Move a layer down and right without wrapping round the edges."""
    a = np.pad(a, ((dy, 0), (dx, 0)), mode="edge")
    return a[:a.shape[0] - dy, :a.shape[1] - dx]


def sheet(field, colour, lift=7, soft=9, dark=0.34, s=0, fibre=0.03, shine=30):
    """Lay one sheet: field > 0 is paper. It shades what is behind it, its cut edge catches the light."""
    global img
    a = aa(field)
    sh = blur(shift(a, lift, lift // 2), soft)
    img = img * (1 - dark * sh[..., None])
    near = blur(shift(a, 2), 2.0)
    img = img * (1 - 0.18 * near[..., None])
    tex = 1 + fibre * (noise(2.5, 2.5, 300 + s) - 0.5) * 2 + 0.02 * (noise(60, 3, 400 + s) - 0.5) * 2
    col = np.clip(colour[None, None, :] * tex[..., None], 0, 255)
    img = img * (1 - a[..., None]) + col * a[..., None]
    edge = np.clip(a - shift(a, 2), 0, 1) * a
    img = img + edge[..., None] * shine
    return a


def pines(base, s, hmin, hmax, step, where=None):
    """A row of cut pines along a base line; the random row is laid over the whole world, then sampled."""
    edge = base.copy()
    fr = np.random.default_rng(s)
    x = -10.0
    while x < WW + 10:
        h = fr.uniform(hmin, hmax)
        wd = h * fr.uniform(0.2, 0.27)
        step_next = fr.uniform(step * 0.7, step * 1.4)
        if (where is None or where(x)) and xs[0] - 200 < x < xs[-1] + 200:
            b = np.interp(x, xs, base)
            tier = np.abs(xs - x) * (h / wd)
            edge = np.minimum(edge, b - h + tier - 0.12 * h * (np.sin(tier / h * 14) > 0) * (tier < h))
        x += step_next
    return edge


# 1. the back of the sky, with the stars punched through to the glow
moon = np.hypot(X - mx, Y - my) - 82
sky = np.minimum(moon, 1e3)
sr = np.random.default_rng(6)
for _ in range(60):
    sxx, syy = sr.uniform(20, WW - 20), sr.uniform(600, 820)
    if np.hypot(sxx - mx, syy - my) > 130 and not (860 < sxx < 2100 and syy < 800):
        sky = np.minimum(sky, np.hypot(X - sxx, Y - syy) - sr.uniform(1.6, 3.4))
sheet(sky, rgb("#F4C3A2"), lift=5, soft=6, dark=0.2, s=1)
# 2. three sky sheets, set well apart in long easy curves, each only a shade paler than the one behind and casting
# only a faint, wide shadow, so the sky reads as air; the moon is cut through all of them
for k, (base, amp, wl, ph, col) in enumerate([(790, 34, 600, 3.3, "#F7D0B4"), (560, 44, 690, 2.0, "#F9DBC4"),
                                              (320, 50, 770, 0.4, "#FBE5D3")]):
    edge = base + amp * np.sin(xs / wl + ph) + 8 * np.sin(xs / 230 + k)
    sheet(np.minimum(edge[None, :] - Y, moon), rgb(col), lift=10, soft=20, dark=0.12, s=31 + k, fibre=0.02, shine=14)
# the moon is one hole through the whole sky, so it gets one soft shadow, not one per sheet
mm = aa(-moon)[..., None]
glow = rgb("#FFF8E1") * (1 - t) + rgb("#F8CF93") * t
img = img * (1 - mm) + glow * mm
img = img * (1 - 0.22 * blur(shift(aa(moon), 6, 3), 7)[..., None] * mm)
# 3-4. far ranges, low in the middle of the world, rising toward both ends
m1 = smooth1(862 - 170 * g(260, 300) - 160 * g(2230, 240) - 60 * g(2760, 200) - 50 * g(700, 220) + n1(40, 11, 7), 5)
sheet(Y - m1[None, :], rgb("#D992A0"), s=2)
m2 = smooth1(920 - 120 * g(80, 260) - 110 * g(2700, 240) - 70 * g(2060, 230) - 60 * g(560, 200) + n1(34, 12, 6), 4)
sheet(Y - m2[None, :], rgb("#A878A8"), s=3)
# 5. forested ridge
h3 = 985 + 20 * np.sin(xs / 190 + 0.6) - 20 * g(2450, 260)
sheet(Y - pines(h3, 21, 16, 40, 12)[None, :], rgb("#6E689F"), s=4)
# 6. the hill with the cabin; its windows are cut through to the glow
hx = 2380
h4 = 1062 - 44 * g(hx - 18, 300) + 16 * np.sin(xs / 130 + 2)
e4 = pines(h4, 22, 30, 74, 22, where=lambda x: not (hx - 90 < x < hx + 80))
f4 = Y - e4[None, :]
hy = float(np.interp(hx, xs, h4)) + 6 if xs[0] <= hx <= xs[-1] else 1000.0
house = np.minimum(np.minimum(X - (hx - 38), hx + 38 - X), Y - (hy - 46))
roof = np.minimum((50 - np.abs(X - hx)) * 0.72 - ((hy - 46) - Y), (hy - 45) - Y)
chim = np.minimum(np.minimum(X - (hx + 16), hx + 27 - X), Y - (hy - 88)) - 1e3 * (Y > hy - 46)
f4 = np.maximum(np.maximum(f4, np.maximum(house, roof)), chim)
win = np.minimum(np.minimum(X - (hx - 24), hx - 6 - X), np.minimum(Y - (hy - 34), hy - 10 - Y))
win = np.maximum(win, np.minimum(np.minimum(X - (hx + 6), hx + 24 - X), np.minimum(Y - (hy - 34), hy - 10 - Y)))
bars = np.minimum(np.abs(X - (hx - 15)) - 1.3, np.abs(Y - (hy - 22)) - 1.3)
win = np.minimum(win, np.where(X < hx, bars, np.minimum(np.abs(X - (hx + 15)) - 1.3, np.abs(Y - (hy - 22)) - 1.3)))
sheet(np.minimum(f4, -win), rgb("#454E8C"), s=5)
wa = aa(win)[..., None]
img = img * (1 - wa) + rgb("#FFE9A8") * wa
img = img * (1 - 0.25 * blur(shift(aa(-win) * aa(win + 6), 3), 2)[..., None] * wa)
# 7. nearer slope with taller pines
h5 = 1136 + 26 * np.sin(xs / 240 + 4) + 24 * g(1500, 400)
sheet(Y - pines(h5, 23, 60, 150, 40, where=lambda x: not (2250 < x < 2530))[None, :], rgb("#2B3670"), lift=9, soft=11, s=6)
# 8. the front: grass blades and tall pines
h6 = 1196 + 12 * np.sin(xs / 120 + 1)
f6 = Y - h6[None, :]
gr = np.random.default_rng(14)
for _ in range(360):
    gx, gh, lean = gr.uniform(0, WW), gr.uniform(16, 64), gr.uniform(-0.45, 0.45)
    if xs[0] - 80 < gx < xs[-1] + 80:
        up = np.interp(gx, xs, h6) + 3 - Y
        f6 = np.maximum(f6, np.minimum(np.minimum(up, gh - up), (2.6 * (1 - up / gh) + 0.5) - np.abs(X - gx - lean * up - 0.004 * up * up)))
for tx, top, mw in [(2006, 840, 80), (2104, 950, 62), (120, 780, 84), (226, 900, 60), (2800, 860, 70)]:
    base = 1230
    th = base - top
    up = base - Y
    tt = np.clip(up / th, 0, 1)
    tier = th / 8.0
    saw = 1 - ((up + tx) % tier) / tier
    half = (1 - tt) * mw * (0.36 + 0.64 * saw ** 0.75)
    f6 = np.maximum(f6, np.minimum(np.maximum(half - np.abs(X - tx), 4 - np.abs(X - tx)), np.minimum(up, th - up) + 2))
sheet(f6, rgb("#161D45"), lift=10, soft=12, dark=0.4, s=7)
if MODE == "band":
    # the page itself is the last sheet, cut in a long low curve across the foot
    foot = 1212 + 10 * np.sin(xs / 400 + 1) + 6 * np.sin(xs / 150)
    sheet(Y - foot[None, :], rgb("#FAFAF7"), lift=8, soft=10, dark=0.3, s=9, fibre=0.0)
Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(sys.argv[2])
