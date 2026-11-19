"""Loose watercolour: one big wet-in-wet sky over a tidal shore, edge to edge, its upper edge drying ragged on
white paper under the title. Pigment is modelled as density on paper: washes pool at their edges, granulate in the
paper's tooth, bloom where water runs back, and mix by absorbing light. python3 wash.py out.png [seed]"""
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


# ---------- the sky: one wash, dilute at the top, its edge ragged where it dried ----------
top = 500 + 190 * (fbm(330, 330, 1) - 0.5) * 2 + 46 * (fbm(60, 60, 2) - 0.5) + 14 * (fbm(14, 14, 3) - 0.5)
sky = sstep(0, 5, Y - top) * (Y < HORIZON + 4)
sky = rimmed(sky, 5, 1.0)
warp = Y + 150 * (fbm(260, 200, 4) - 0.5)
conc = np.clip((Y - 440) / 520, 0.05, 1) ** 0.75 * (0.7 + 0.6 * fbm(230, 130, 5))
# clouds: paler passages lifted out of the wet wash, with violet settling beneath them
cloud = sstep(0.5, 0.66, fbm(300, 80, 6)) * sstep(520, 640, Y) * (1 - sstep(880, 980, Y))
under = np.roll(cloud, 26, 0) * (1 - cloud)
w_blue = 1 - sstep(600, 860, warp)
w_peach = sstep(770, 965, warp)
w_violet = np.exp(-((warp - 770) / 95) ** 2)
dens["blue"] += sky * conc * (0.95 * w_blue + 0.12) * (1 - 0.7 * cloud) * (1 + 0.5 * GRAN)
dens["violet"] += sky * conc * (0.6 * w_violet + 0.4 * under * (1 - w_peach)) * (1 - 0.55 * cloud) * (1 + 0.4 * GRAN)
dens["peach"] += sky * conc * 1.15 * w_peach * (1 - 0.3 * cloud)
dens["gold"] += sky * 0.55 * np.exp(-((X - 380) / 260) ** 2) * np.exp(-((Y - 968) / 46) ** 2)
# backruns: water creeping back into the damp wash leaves pale flowers with a dark, feathered edge
for cx, cy, rad in ((180, 600, 95), (735, 560, 120), (520, 720, 70)):
    d = np.hypot(X - cx, (Y - cy) * 1.15) + 46 * (fbm(46, 46, int(cx)) - 0.5) + 14 * (fbm(9, 9, int(cy)) - 0.5)
    inside = sstep(0, 14, rad - d)
    ring = np.exp(-((d - rad) / 3.2) ** 2)
    for k in ("blue", "violet"):
        dens[k] *= 1 - 0.5 * inside * sky.clip(0, 1)
        dens[k] += 0.2 * ring * sky.clip(0, 1) * conc
# a few stray drops beyond the edge
for _ in range(16):
    dx, dy, dr = r.uniform(30, W - 30), r.uniform(430, 560), r.uniform(1.5, 5)
    drop = sstep(0, 1.5, dr - np.hypot(X - dx, Y - dy))
    dens["blue"] += rimmed(drop, 1.5, 1.0) * r.uniform(0.08, 0.3)

# ---------- far shore, wet on damp: a soft blue-violet band ----------
far = HORIZON - 22 - 20 * fbm(170, 170, 20) - 30 * sstep(300, 0, X)
farm = blur(((Y > far) & (Y < HORIZON + 2)).astype(float), 3.5)
dens["violet"] += farm * 0.4
dens["blue"] += farm * 0.35 * (1 + 0.4 * GRAN)

# ---------- the headland, wet on dry: the one dark, crisp shape ----------
hl = 56 * sstep(430, 760, X) + 34 * sstep(700, 944, X) + 22 * (fbm(26, 26, 30) - 0.5) * sstep(430, 600, X) \
     + 9 * (fbm(7, 7, 31) - 0.5) * sstep(430, 560, X)
head = sstep(0, 2.5, Y - (HORIZON - hl)) * (Y < HORIZON) * (X > 430)
head = rimmed(head, 3, 0.6)
for k in ("blue", "violet", "peach", "gold"):      # the headland was painted on dry paper: little sky under it
    dens[k] *= 1 - 0.75 * head.clip(0, 1)
dens["dark"] += head * (0.75 + 0.9 * fbm(60, 40, 32)) * (1 + 0.35 * GRAN)
dens["sepia"] += head * 0.6 * fbm(70, 40, 33)

# ---------- water: the sky again, pulled sideways, darker toward the viewer ----------
below = sstep(0, 3, Y - HORIZON - 3)                        # a hairline of dry paper at the waterline
src = np.clip(HORIZON - (Y - HORIZON) * 1.15, 0, H - 1).astype(int)
cols = np.arange(W)[None, :].repeat(H, 0)
depth = np.clip((Y - HORIZON) / (H - HORIZON), 0, 1)
for k in ("blue", "violet", "peach", "gold"):
    refl = box(dens[k][src, cols], 60, 2)
    dens[k] += below * refl * (0.95 - 0.15 * depth)
dens["blue"] += below * (0.12 + 0.5 * depth ** 1.7) * (1 + 0.5 * GRAN) * (0.75 + 0.5 * fbm(300, 26, 40))
dens["violet"] += below * 0.3 * depth * fbm(260, 30, 41)
hsrc = np.clip(2 * HORIZON - Y, 0, H - 1).astype(int)
hre = box((head.clip(0, 1))[hsrc, cols], 5, 16) * below * np.clip(1.1 - (Y - HORIZON) / 150, 0, 1)
dens["dark"] += hre * 0.7 * (0.6 + 0.6 * fbm(120, 6, 42))
dens["sepia"] += hre * 0.4
# dry brush: the loaded brush skips over the paper's tooth and leaves sparkle on the water
skip = sstep(0.57, 0.66, fbm(70, 3, 50, 2) * 0.6 + TEX * 0.4) * below * np.exp(-((X - 380) / 330) ** 2) * (1 - 0.6 * depth)
ripple = sstep(0.62, 0.7, fbm(160, 4, 51, 2)) * below * (0.35 + 0.5 * depth)
for k in dens:
    dens[k] *= 1 - 0.9 * skip
dens["blue"] += ripple * 0.45
dens["dark"] += ripple * 0.12 * depth

# ---------- one light on the headland, and its trail on the water ----------
lx, ly = 640, HORIZON - 12
lamp = sstep(0, 2, 7 - np.hypot(X - lx, Y - ly))
trail = sstep(0, 3, 7 + (Y - HORIZON) * 0.03 - np.abs(X - lx)) * below * np.clip(1 - (Y - HORIZON) / 190, 0, 1) \
        * sstep(0.4, 0.6, fbm(40, 5, 60, 2))
for k in dens:
    dens[k] *= 1 - 0.95 * np.clip(lamp + 0.8 * trail, 0, 1)
dens["gold"] += 0.9 * lamp + 0.7 * trail
dens["peach"] += 0.5 * lamp

# ---------- light through pigment on paper ----------
img = np.ones((H, W, 3))
for k, col in PIG.items():
    img *= np.exp(-dens[k][..., None] * -np.log(col)[None, None, :])
img *= (1 - 0.012 * (TEX - 0.5) * 2)[..., None]
img = img * 255 + r.normal(0, 0.9, (H, W, 1))
Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(sys.argv[1])
