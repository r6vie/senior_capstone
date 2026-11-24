"""Stippled ink: the whole picture is dots. Tone is how close they sit; two inks, indigo and a warm gold.
Dunes under a low moon; the sky's dots thin out to nothing under the title. python3 stipple.py out.png [seed]"""
import math
import sys
import numpy as np
from PIL import Image, ImageDraw

W, H = 944, 1376
S = 3
seed = int(sys.argv[2]) if len(sys.argv) > 2 else 8
r = np.random.default_rng(seed)
Y, X = np.mgrid[0:H, 0:W].astype(float)
xs = np.arange(W, dtype=float)


def rgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], float)


def noise(sx, sy, s):
    g = np.random.default_rng(s).random((int(H / sy) + 3, int(W / sx) + 3))
    return np.asarray(Image.fromarray((g * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC), float) / 255


def stipple(tone, cell=3.0, rad=(0.95, 1.5), gamma=1.0, s=0):
    """One ink. A jittered grid of candidate dots; each is kept with probability tone, so tone is dot density.
    Returns coverage 0..1."""
    rr = np.random.default_rng(seed * 100 + s)
    im = Image.new("L", (W * S, H * S), 0)
    d = ImageDraw.Draw(im)
    gy, gx = np.mgrid[0:int(H / cell) + 1, 0:int(W / cell) + 1]
    px = (gx + rr.uniform(0.1, 0.9, gx.shape) + 0.5 * (gy % 2)) * cell
    py = (gy + rr.uniform(0.1, 0.9, gy.shape)) * cell
    ok = (px >= 0) & (px < W) & (py >= 0) & (py < H)
    px, py = px[ok], py[ok]
    t = np.clip(tone[py.astype(int), px.astype(int)], 0, 1) ** gamma
    keep = rr.random(len(px)) < t
    rads = rr.uniform(rad[0], rad[1], keep.sum()) * (0.85 + 0.3 * t[keep])
    for x, y, q in zip(px[keep], py[keep], rads):
        d.ellipse(((x - q) * S, (y - q) * S, (x + q) * S, (y + q) * S), fill=255)
    return np.asarray(im.resize((W, H), Image.LANCZOS), float) / 255


def crest(y0, parts, s):
    y = np.full(W, float(y0))
    for amp, wl, ph in parts:
        y += amp * np.sin(xs / wl * 2 * np.pi + ph)
    return y


indigo = np.zeros((H, W))
gold = np.zeros((H, W))
# ----- dunes, far to near. Each crest is a sharp line: dark just under it where the face turns from the light -----
dunes = [
    (crest(880, [(26, 900, 0.4), (10, 300, 2)], 1), 0.5, 70, 1.3, 0.0),
    (crest(960, [(44, 1100, 2.2), (14, 380, 1)], 2), 0.62, 95, 0.4, 2.0),
    (crest(1060, [(60, 1300, 4.4), (16, 420, 3)], 3), 0.75, 130, 2.7, 4.0),
    (crest(1190, [(70, 1500, 0.9), (18, 500, 5)], 4), 0.9, 170, 5.1, 1.0),
]
horizon = dunes[0][0]
sky = Y < horizon[None, :]
# sky: dots gather toward the horizon and are gone by the title; a clear halo is left round the moon
mx, my, mr = 640, 742, 96
dm = np.hypot(X - mx, Y - my)
sky_t = np.clip((Y - 490) / 400, 0, 1) ** 2.6 * 0.2
sky_t *= 0.55 + 0.45 * noise(380, 90, 11)                      # faint bands of high cloud
sky_t *= np.clip((dm - mr - 6) / 150, 0, 1) ** 0.7
indigo = np.where(sky, sky_t, indigo)
gold = np.where(sky, np.clip((Y - 660) / 240, 0, 1) ** 2 * 0.4 * np.exp(-((X - mx) / 380) ** 2), gold)
# moon: gold, close-set, with a soft indigo shade down its right side
moon = dm < mr
gold = np.where(moon & sky, 0.97, gold)
shade = np.clip(((X - mx) * 0.8 + (Y - my) * 0.5) / mr - 0.05, 0, 1) ** 1.5 * 0.55 + 0.18 * (noise(34, 34, 12) > 0.62)
indigo = np.where(moon & sky, shade, indigo)

owner = np.zeros((H, W), int)
for i, (c, dark, fall, ph, rp) in enumerate(dunes):
    below = Y >= c[None, :]
    owner[below] = i + 1
    dd = Y - c[None, :]
    slope = np.gradient(c)[None, :]
    # the windward side of each dune is lit, the lee side in shadow: it swaps along the crest
    lee = (0.45 + 0.55 * np.clip(0.5 + 0.5 * np.sin(xs / 520 * 2 * np.pi + ph), 0, 1) ** 1.3)[None, :]
    face = dark * lee * np.exp(-dd / fall) ** 1.15 + 0.03
    # wind ripples on the nearer dunes: fine parallel lines following the slope
    if i >= 2:
        rip = 0.5 + 0.5 * np.sin((dd + 22 * np.sin(X / 90 + rp)) / (5.5 + i) + rp)
        face = face * (0.78 + 0.34 * rip * np.clip(dd / 60, 0, 1))
    line = np.exp(-(dd / 1.3) ** 2) * 1.0                         # the crest itself
    indigo = np.where(below, np.maximum(face, line), indigo)
    gold = np.where(below, 0.5 * (1 - np.exp(-dd / (fall * 0.7))) * np.exp(-dd / (fall * 2.6)) + 0.05, gold)
# the foreground settles into deep shade toward the bottom corners
vign = np.clip((Y - 1180) / 196, 0, 1) ** 1.6 * (0.35 + 0.65 * np.abs(X - 430) / 520)
indigo = np.clip(indigo + (owner > 0) * vign * 0.75, 0, 1)

ci = stipple(indigo, cell=2.15, rad=(0.75, 1.15), s=1)
cg = stipple(gold, cell=2.5, rad=(0.8, 1.25), s=2)
# a few stars, and one small lamp-lit tent on the third dune with its shadow
stars = Image.new("L", (W * S, H * S), 0)
ds = ImageDraw.Draw(stars)
for _ in range(34):
    x, y = r.uniform(20, W - 20), r.uniform(500, 820)
    if math.hypot(x - mx, y - my) > mr + 40:
        q = r.uniform(1.4, 2.6)
        ds.ellipse(((x - q) * S, (y - q) * S, (x + q) * S, (y + q) * S), fill=255)
cs = np.asarray(stars.resize((W, H), Image.LANCZOS), float) / 255

INK, GOLD = rgb("#1F2A4D"), rgb("#D9A441")
img = np.ones((H, W, 3))
img *= 1 - (0.9 * cg)[..., None] * (1 - GOLD / 255)
img *= 1 - (0.95 * ci)[..., None] * (1 - INK / 255)
img *= 1 - (0.9 * cs)[..., None] * (1 - GOLD / 255)
Image.fromarray(np.clip(img * 255, 0, 255).astype(np.uint8)).save(sys.argv[1])
