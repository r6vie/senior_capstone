"""Watercolour, round 2, as a wide band for the book page: the same brush and pigments as wash2.py, laid out 1440 x 620
(painted at 2x). Sky strokes only at the two ends, so the title sits on bare paper; the land and water run across.
python3 wash2_band.py out.png [seed]"""
import sys
import numpy as np
from PIL import Image, ImageFilter

W, H = 2880, 1240
seed = int(sys.argv[2]) if len(sys.argv) > 2 else 6
r = np.random.default_rng(seed)
Y, X = np.mgrid[0:H, 0:W].astype(float)


def rgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], float) / 255


def vnoise(sx, sy, s):
    g = np.random.default_rng(s).random((int(H / sy) + 3, int(W / sx) + 3))
    return np.asarray(Image.fromarray((g * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC), float) / 255


def fbm(sx, sy, s, octaves=4):
    out, amp, tot = 0, 1.0, 0
    for o in range(octaves):
        out = out + amp * vnoise(max(1.5, sx / 2 ** o), max(1.5, sy / 2 ** o), s + o * 17)
        tot += amp
        amp *= 0.5
    return out / tot


def box(a, rx, ry):
    for ax, rr in ((1, rx), (0, ry)):
        if rr > 0:
            k = 2 * rr + 1
            pad = np.pad(a, [(rr, rr) if i == ax else (0, 0) for i in range(2)], mode="edge")
            c = np.cumsum(pad, axis=ax)
            c = np.insert(c, 0, 0, axis=ax)
            a = (np.take(c, np.arange(k, k + a.shape[ax]), axis=ax) - np.take(c, np.arange(0, a.shape[ax]), axis=ax)) / k
    return a


def blur(a, rad):
    rr = max(1, int(round(rad * 0.9)))
    return box(box(box(a, rr, rr), rr, rr), rr, rr)   # three box passes: near enough to a gaussian


def sstep(a, b, v):
    t = np.clip((v - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


PIG = {"blue": rgb("#34507F"), "violet": rgb("#7B6A93"), "peach": rgb("#F3A977"), "gold": rgb("#E8B24A"),
       "dark": rgb("#1F2A44"), "sepia": rgb("#5A4636")}
dens = {k: np.zeros((H, W)) for k in PIG}
TEX = fbm(5, 5, 900, 3)                      # cold-pressed paper
GRAN = np.clip((blur(TEX, 1.2) - 0.5) * 2.6, -1, 1) * 0.55     # where granulating pigment settles
HORIZON = 900


def rimmed(mask, width=4, amount=1.4):
    """Pigment is carried to the drying edge of a wash and left there."""
    e = np.clip((mask - blur(mask, width)) * 3.5, 0, 1)
    return mask * (1 + amount * e)



BRISTLE = blur(fbm(300, 7, 700, 2), 1.5)             # the brush's hairs, dragged level


def stroke(y0, thick, mix, conc, x0=-80, x1=W + 80, tilt=0.0, s=0, taper=0.35, dry=0.0):
    """One pass of a wide flat brush from x0 to x1. Loaded where it starts, thinner as it goes; its long edges
    waver and dry hard; with dry > 0 its far end breaks up over the paper's tooth."""
    rr = np.random.default_rng(s)
    yc = y0 + tilt * (X - W / 2) + 16 * (vnoise(420, 2000, 800 + s) - 0.5) * 2 + 5 * (vnoise(70, 2000, 810 + s) - 0.5)
    cap = np.sqrt(np.clip((X - x0) / 46, 0, 1)) * np.sqrt(np.clip((x1 - X) / 46, 0, 1))
    half = cap * thick / 2 * (1 - taper * np.clip((X - x0) / (x1 - x0), 0, 1) ** 1.5) * (0.9 + 0.2 * vnoise(160, 2000, 820 + s))
    edge = half - np.abs(Y - yc) + 4.5 * (fbm(22, 7, 830 + s, 2) - 0.5) * 2
    m = sstep(0, 3.5, edge) * (X > x0) * (X < x1)
    if dry:
        along = np.clip((X - x0) / (x1 - x0), 0, 1)
        m = m * (1 - sstep(1 - dry, 1.0, along + 0.55 * (BRISTLE - 0.5) + 0.25 * (TEX - 0.5)))
    m = rimmed(m, 4, 0.7)
    load = (1.05 - 0.4 * np.clip((X - x0) / (x1 - x0), 0, 1)) * (0.9 + 0.2 * BRISTLE) * (0.75 + 0.5 * fbm(200, 70, 840 + s, 3))
    for k, wgt in mix.items():
        g = 1 + (0.5 * GRAN if k in ("blue", "violet", "dark") else 0.15 * GRAN)
        dens[k] += m * conc * wgt * load * g
    return m


# ---------- sky: strokes at the two ends only; the middle is left as paper for the title ----------
stroke(380, 64, {"blue": 1.0}, 0.24, x0=-80, x1=760, s=1, dry=0.45, tilt=-0.02)
stroke(452, 104, {"blue": 1.0, "violet": 0.15}, 0.5, x0=-80, x1=900, s=2, tilt=0.015)
stroke(556, 116, {"blue": 0.85, "violet": 0.5}, 0.7, x0=-80, x1=820, s=3, tilt=-0.02, dry=0.25)
stroke(330, 70, {"blue": 1.0}, 0.26, x0=2240, x1=W + 80, s=41, dry=0.0, tilt=0.02)
stroke(420, 110, {"blue": 1.0, "violet": 0.2}, 0.55, x0=2120, x1=W + 80, s=42, tilt=-0.015)
stroke(530, 120, {"blue": 0.8, "violet": 0.55}, 0.7, x0=2060, x1=W + 80, s=43, tilt=0.01)
# near the horizon the strokes run the whole width, warm, low enough to clear the button
stroke(660, 84, {"violet": 0.9, "blue": 0.25}, 0.55, x0=120, x1=880, s=4, tilt=0.0, dry=0.2)
stroke(650, 84, {"violet": 0.9, "blue": 0.3}, 0.55, x0=2180, x1=W + 80, s=44, tilt=0.0)
stroke(806, 72, {"peach": 1.0, "violet": 0.1}, 0.55, s=5, tilt=-0.003)
stroke(858, 46, {"peach": 0.7, "gold": 0.6}, 0.5, x0=400, x1=W - 100, s=6, dry=0.3, tilt=0.002)
# one backrun where a wet stroke met a drying one
for cx, cy, rad in ((2560, 470, 84),):
    d = np.hypot(X - cx, (Y - cy) * 1.2) + 40 * (fbm(46, 46, 71) - 0.5) + 12 * (fbm(9, 9, 72) - 0.5)
    inside, ring = sstep(0, 14, rad - d), np.exp(-((d - rad) / 3.0) ** 2)
    for k in ("blue", "violet"):
        ring_add = 0.3 * ring * (dens[k] > 0.05) * dens[k]
        dens[k] = dens[k] * (1 - 0.5 * inside) + ring_add
for _ in range(16):
    dx = r.choice([r.uniform(30, 820), r.uniform(2140, W - 30)])
    dy, dr = r.uniform(280, 360), r.uniform(1.5, 4.5)
    dens["blue"] += rimmed(sstep(0, 1.5, dr - np.hypot(X - dx, Y - dy)), 1.5, 1.0) * r.uniform(0.08, 0.28)

# ---------- land: dark strokes pressed down then lifted, one at each end and a long low one across ----------
stroke(HORIZON - 14, 46, {"dark": 1.0, "sepia": 0.45}, 0.75, x0=1560, x1=W + 80, s=10, taper=-1.1, tilt=-0.03)
stroke(HORIZON - 34, 38, {"dark": 1.0}, 0.6, x0=2100, x1=W + 80, s=11, taper=-0.6, tilt=-0.05)
stroke(HORIZON - 6, 30, {"dark": 0.9, "sepia": 0.5}, 0.6, x0=-80, x1=980, s=12, taper=0.5, tilt=0.02)
bleed = sstep(0, 26, 40 - np.hypot((X - 2500) / 1.8, Y - (HORIZON - 58))) * sstep(0.45, 0.7, fbm(30, 30, 90))
dens["dark"] += 0.45 * bleed

# ---------- water: strokes, drier and broken, darker toward the viewer, running out to paper ----------
stroke(HORIZON + 40, 40, {"peach": 0.9, "gold": 0.3}, 0.4, x0=-80, x1=1900, s=20, dry=0.5)
stroke(HORIZON + 96, 56, {"violet": 0.8, "blue": 0.4}, 0.6, x0=300, x1=W + 80, s=21, dry=0.0, tilt=0.004)
stroke(HORIZON + 162, 64, {"blue": 1.0, "violet": 0.3}, 0.8, x0=-80, x1=2500, s=22, dry=0.4, tilt=-0.004)
stroke(HORIZON + 232, 60, {"blue": 1.0, "dark": 0.35}, 0.85, x0=700, x1=W + 80, s=23, tilt=0.003, dry=0.35)
stroke(HORIZON + 286, 26, {"blue": 0.9, "dark": 0.2}, 0.5, x0=-80, x1=1300, s=24, dry=0.55)
for k, (yy, x0, x1) in enumerate(((HORIZON + 30, 1700, 2600), (HORIZON + 62, 1900, W + 80), (HORIZON + 96, 2100, 2700))):
    stroke(yy, 15, {"dark": 1.0, "sepia": 0.3}, 0.55 - 0.1 * k, x0=x0, x1=x1, s=30 + k, dry=0.5)

# ---------- one warm touch: a lamp on the land and two dabs beneath it ----------
lx, ly = 2230, HORIZON - 15
lamp = sstep(0, 2, 6.5 - np.hypot(X - lx, Y - ly))
dabs = np.maximum(sstep(0, 2, 5 - np.hypot((X - lx) / 2.2, Y - (HORIZON + 32))), sstep(0, 2, 4 - np.hypot((X - lx - 3) / 2.4, Y - (HORIZON + 64))))
for k in dens:
    dens[k] *= 1 - 0.95 * np.clip(lamp + dabs, 0, 1)
dens["gold"] += 1.0 * lamp + 0.8 * dabs
dens["peach"] += 0.4 * lamp

# ---------- light through pigment on paper ----------
img = np.ones((H, W, 3)) * np.array([250, 250, 247]) / 255
for k, col in PIG.items():
    img *= np.exp(-dens[k][..., None] * -np.log(col)[None, None, :])
img *= (1 - 0.012 * (TEX - 0.5) * 2)[..., None]
img = img * 255 + r.normal(0, 0.9, (H, W, 1))
Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(sys.argv[1])
