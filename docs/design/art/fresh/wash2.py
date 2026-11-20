"""Watercolour, round 2: not a picture of a place but a handful of loaded brushstrokes that add up to one.
Broad level strokes of sky and water, glazed where they overlap, with paper left bare between them; one dark
stroke for the land. Pigment pools at stroke edges, drags dry at stroke ends, granulates and blooms.
python3 wash2.py out.png [seed]"""
import sys
import numpy as np
from PIL import Image, ImageFilter

W, H = 944, 1376
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
HORIZON = 1010


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


# ---------- sky: six strokes, left to right, each a little different; white paper shows between some ----------
stroke(522, 70, {"blue": 1.0}, 0.22, x1=760, s=1, dry=0.45, tilt=-0.02)
stroke(600, 120, {"blue": 1.0, "violet": 0.15}, 0.5, s=2, tilt=0.015)
stroke(706, 128, {"blue": 0.85, "violet": 0.5}, 0.72, s=3, tilt=-0.02)
stroke(792, 92, {"violet": 0.9, "blue": 0.25}, 0.6, x0=120, s=4, dry=0.0, tilt=0.02)
stroke(868, 96, {"peach": 1.0, "violet": 0.1}, 0.55, s=5, tilt=-0.01)
stroke(938, 70, {"peach": 0.7, "gold": 0.6}, 0.5, x1=820, s=6, dry=0.3, tilt=0.01)
# one backrun where a wet stroke met a drying one
for cx, cy, rad in ((690, 650, 84),):
    d = np.hypot(X - cx, (Y - cy) * 1.2) + 40 * (fbm(46, 46, 71) - 0.5) + 12 * (fbm(9, 9, 72) - 0.5)
    inside, ring = sstep(0, 14, rad - d), np.exp(-((d - rad) / 3.0) ** 2)
    for k in ("blue", "violet"):
        ring_add = 0.3 * ring * (dens[k] > 0.05) * dens[k]
        dens[k] = dens[k] * (1 - 0.5 * inside) + ring_add
for _ in range(14):
    dx, dy, dr = r.uniform(30, W - 30), r.uniform(440, 520), r.uniform(1.5, 4.5)
    dens["blue"] += rimmed(sstep(0, 1.5, dr - np.hypot(X - dx, Y - dy)), 1.5, 1.0) * r.uniform(0.08, 0.28)

# ---------- land: one dark stroke, pressed down then lifted, with a second darker touch while it was wet ----------
land = stroke(HORIZON - 14, 46, {"dark": 1.0, "sepia": 0.45}, 0.75, x0=360, s=10, taper=-1.1, tilt=-0.03)
stroke(HORIZON - 34, 38, {"dark": 1.0}, 0.6, x0=640, s=11, taper=-0.6, tilt=-0.05)
# it bled a little into the damp sky at one place
bleed = sstep(0, 26, 40 - np.hypot((X - 800) / 1.8, Y - (HORIZON - 58))) * sstep(0.45, 0.7, fbm(30, 30, 90))
dens["dark"] += 0.45 * bleed

# ---------- water: four strokes right to left, drier and broken, darker toward the viewer ----------
stroke(HORIZON + 44, 44, {"peach": 0.9, "gold": 0.3}, 0.4, x0=-80, x1=700, s=20, dry=0.5)
stroke(HORIZON + 112, 66, {"violet": 0.8, "blue": 0.4}, 0.6, x0=140, s=21, dry=0.0, tilt=0.01)
stroke(HORIZON + 196, 84, {"blue": 1.0, "violet": 0.3}, 0.8, x1=880, s=22, dry=0.4, tilt=-0.01)
stroke(HORIZON + 310, 130, {"blue": 1.0, "dark": 0.35}, 0.95, s=23, tilt=0.01)
# the land's reflection: three short dry touches under it
for k, (yy, x0, x1) in enumerate(((HORIZON + 30, 520, 900), (HORIZON + 62, 600, 944 + 80), (HORIZON + 96, 700, 930))):
    stroke(yy, 15, {"dark": 1.0, "sepia": 0.3}, 0.55 - 0.1 * k, x0=x0, x1=x1, s=30 + k, dry=0.5)

# ---------- one warm touch: a lamp on the land and two dabs beneath it ----------
lx, ly = 596, HORIZON - 15
lamp = sstep(0, 2, 6.5 - np.hypot(X - lx, Y - ly))
dabs = np.maximum(sstep(0, 2, 5 - np.hypot((X - lx) / 2.2, Y - (HORIZON + 32))), sstep(0, 2, 4 - np.hypot((X - lx - 3) / 2.4, Y - (HORIZON + 64))))
for k in dens:
    dens[k] *= 1 - 0.95 * np.clip(lamp + dabs, 0, 1)
dens["gold"] += 1.0 * lamp + 0.8 * dabs
dens["peach"] += 0.4 * lamp

# ---------- light through pigment on paper ----------
img = np.ones((H, W, 3))
for k, col in PIG.items():
    img *= np.exp(-dens[k][..., None] * -np.log(col)[None, None, :])
img *= (1 - 0.012 * (TEX - 0.5) * 2)[..., None]
img = img * 255 + r.normal(0, 0.9, (H, W, 1))
Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(sys.argv[1])
