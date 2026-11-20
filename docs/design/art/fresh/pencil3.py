"""Coloured pencil, round 3, drawn like a draughtsman: six pencils, one hatching direction, tone built by how close the
lines sit, crisp ridgelines that dissolve into bare paper. A lake at dusk with one light on.
python3 pencil2.py out.png [seed]"""
import math
import sys
import numpy as np
from PIL import Image, ImageDraw

W, H = 944, 1376
S = 2
seed = int(sys.argv[2]) if len(sys.argv) > 2 else 3
r = np.random.default_rng(seed)
Y, X = np.mgrid[0:H, 0:W].astype(float)


def rgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], float)


def noise(sx, sy, s):
    g = np.random.default_rng(s).random((int(H / sy) + 3, int(W / sx) + 3))
    return np.asarray(Image.fromarray((g * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC), float) / 255


PENCILS = {"grey": rgb("#7B8FA8"), "indigo": rgb("#222E4A"), "sienna": rgb("#B9795A"), "ochre": rgb("#E0AE50"),
           "violet": rgb("#8479A6"), "green": rgb("#56705F")}
stay = {k: np.ones((H, W)) for k in PENCILS}
TOOTH = 0.5 + 0.5 * (noise(1.6, 1.6, 77) > 0.3)
HAND = math.radians(-52)     # every tone is hatched this way
CROSS = math.radians(28)     # darks get a second set across it


def hatch(pencil, tone, angle=HAND, gap=2.6, length=(18, 46), width=(1.3, 2.1), press=0.5, clip=None):
    """Even rows of parallel strokes `gap` apart. Along each row a stroke is laid where tone (0..1) allows, so
    tone reads as line density. clip (0..1) trims the pass to a shape, which keeps edges deliberate."""
    im = Image.new("L", (W * S, H * S), 0)
    d = ImageDraw.Draw(im)
    ca, sa = math.cos(angle), math.sin(angle)
    diag = math.hypot(W, H)
    for off in np.arange(-diag, diag, gap):
        o = off + r.normal(0, gap * 0.12)
        t = -diag + r.uniform(0, 40)
        while t < diag:
            L = r.uniform(*length)
            mx, my = W / 2 + ca * (t + L / 2) - sa * o, H / 2 + sa * (t + L / 2) + ca * o
            if 0 <= mx < W and 0 <= my < H and r.random() < tone[int(my), int(mx)]:
                a = angle + r.normal(0, 0.025)
                x0, y0 = mx - math.cos(a) * L / 2, my - math.sin(a) * L / 2
                x1, y1 = mx + math.cos(a) * L / 2, my + math.sin(a) * L / 2
                d.line((x0 * S, y0 * S, x1 * S, y1 * S), fill=int(r.uniform(150, 255)), width=max(1, int(r.uniform(*width) * S)))
            t += L * r.uniform(0.8, 1.25)
    a = np.asarray(im.resize((W, H), Image.LANCZOS), float) / 255
    if clip is not None:
        a = a * clip
    stay[pencil] *= 1 - press * a * TOOTH


def peaks(base, items, s, rough=4):
    """A ridgeline of pointed summits: (centre, height, half-width)."""
    x = np.arange(W, dtype=float)
    y = np.full(W, float(base))
    for c, h, w in items:
        y -= h * np.clip(1 - np.abs(x - c) / w, 0, 1) ** 1.25
    return y + np.interp(x, np.linspace(0, W, 60), np.random.default_rng(s).normal(0, rough, 60))


def soft(v):
    return np.clip(v, 0, 1)


SHORE = 1052
r1 = peaks(830, [(160, 110, 260), (470, 70, 240), (760, 170, 300), (930, 90, 200)], 1)
r2 = peaks(905, [(60, 90, 220), (330, 140, 260), (640, 70, 240), (900, 130, 220)], 2)
r3 = peaks(985, [(210, 60, 260), (560, 110, 280), (860, 80, 240)], 3)

# sky: the lightest even tone, gone well before the title; a warm glow behind the far range
sky = (Y < r1[None, :])
SKYHAND = math.radians(-9)   # the sky is laid in flatter, lighter strokes, so it reads as air and not as rain
cl = soft((noise(300, 70, 8) * 0.7 + noise(90, 30, 9) * 0.3 - 0.47) * 9) * soft((Y - 520) / 60) * soft((r1[None, :] - 30 - Y) / 60)
up = soft((Y - 500) / 300) ** 1.4
hatch("grey", up * 0.95 * sky * (1 - 0.92 * cl), angle=SKYHAND, gap=2.0, length=(22, 60), press=0.3)
under = soft(cl - np.roll(cl, -22, 0)) * cl            # the clouds' undersides, in violet
hatch("violet", under * 0.9 * sky, angle=SKYHAND, gap=2.0, length=(16, 44), press=0.42)
hatch("sienna", soft(np.roll(cl, 14, 0) - cl) * 0.5 * sky * soft((Y - 640) / 120), angle=SKYHAND, gap=2.4, length=(16, 40), press=0.35)
glow = np.exp(-((X - 610) / 300) ** 2) * np.exp(-((Y - 800) / 95) ** 2)
hatch("sienna", glow * 0.95 * sky, angle=SKYHAND, gap=2.2, length=(22, 60), press=0.42)
hatch("ochre", np.exp(-((X - 610) / 190) ** 2) * np.exp(-((Y - 830) / 55) ** 2) * 0.95 * sky, angle=SKYHAND, gap=2.2, length=(22, 60), press=0.55)


def mountain(ridge, below, base_tone, pencil, dark, depth, s):
    """One range: lit and shadowed faces fall diagonally from the summits; the foot dissolves into mist."""
    m = ((Y >= ridge[None, :]) & (Y < below[None, :])).astype(float)
    down = Y - ridge[None, :]
    face = np.sin((X + 0.75 * down) / 34 + 6 * noise(260, 260, s)) * 0.5 + 0.5      # ravines running down-right
    face = soft((face - 0.42) * 3)
    mist = soft(1 - down / depth) ** 0.9
    edge = soft(down / 3)                                                           # a crisp skyline
    tone = (0.5 + 0.5 * face) * mist ** 0.7
    hatch(pencil, tone * m, gap=2.0, clip=m * edge, press=0.34 + 0.5 * base_tone)
    hatch("violet", soft(face * mist) * m * 0.7, gap=2.6, clip=m * edge, press=0.3 * base_tone + 0.1)
    hatch(dark, soft((0.55 - face) * 1.6) * mist * m * 0.55, angle=math.radians(58), gap=3.0, length=(12, 30), clip=m * edge, press=0.3 * base_tone)
    hatch(dark, soft(face * mist * 0.9) * m, angle=CROSS, gap=2.6, length=(14, 36), clip=m * edge, press=0.66 * base_tone)
    hatch(dark, soft((face - 0.5) * 2 * mist) * m, gap=2.4, clip=m * edge, press=0.7 * base_tone)
    # the skyline itself: one firm, slightly broken line
    line = ((np.abs(down - 1.5) < 1.6) & (noise(30, 30, s + 5) > 0.22)).astype(float)
    stay[dark] *= 1 - 0.5 * line * TOOTH * base_tone


mountain(r1, r2, 0.42, "grey", "grey", 150, 11)
mountain(r2, r3, 0.62, "grey", "indigo", 140, 12)
mountain(r3, np.full(W, SHORE + 0.0), 0.85, "indigo", "indigo", 120, 13)
hatch("grey", ((Y >= r3[None, :]) & (Y < SHORE)) * 0.5 * soft(1 - (Y - r3[None, :]) / 120), gap=2.5)

# the far shore: a low dark line of trees
shore = ((Y > SHORE - 7 - 8 * noise(22, 40, 21)) & (Y < SHORE + 2) & (X > 380 + 40 * noise(80, 80, 22))).astype(float)
hatch("indigo", shore * 0.75, gap=1.6, length=(8, 18), clip=shore, press=0.7)

# water: level strokes; it holds the ranges upside down, the glow as a pale path, and darkens toward the viewer
water = (Y > SHORE + 2).astype(float)
dw = soft((Y - SHORE) / (H - SHORE))
refl_y = np.clip(2 * SHORE - Y - 60 * dw, 0, H - 1).astype(int)
mirror = ((refl_y > r3[None, :].repeat(H, 0)) * 0.55 + (refl_y > r2[None, :].repeat(H, 0)) * 0.2) * soft(1 - dw * 1.6)
path = 1 - 0.85 * np.exp(-((X - 610) / (70 + 160 * dw)) ** 2)
ripple = 0.35 + 0.65 * (noise(120, 5, 31) > 0.38)
hatch("grey", water * soft(0.6 + mirror * 0.6 + 0.3 * dw ** 2) * path * ripple, angle=0.0, gap=2.0, length=(20, 70), press=0.5)
hatch("violet", water * soft(mirror * 0.8 + 0.3 * dw) * path * ripple, angle=0.0, gap=2.6, length=(20, 60), press=0.35)
hatch("indigo", water * soft(mirror * 0.9 + 0.8 * dw ** 2.0) * path * ripple, angle=0.0, gap=2.4, length=(20, 70), press=0.5)
hatch("sienna", water * np.exp(-((X - 610) / (60 + 120 * dw)) ** 2) * soft(1 - dw * 1.5) * 0.8 * ripple, angle=0.0, gap=2.6, length=(16, 50), press=0.4)

# the near spit and its pines, the darkest thing in the drawing, placed on the left third
spit_top = 1150 + 7 * np.sin(np.arange(W) / 60.0) + np.clip(np.arange(W) - 250, 0, None) * 0.11
spit = ((Y > spit_top[None, :]) & (Y < spit_top[None, :] + 16 - np.clip(X - 300, 0, None) * 0.1) & (X < 440)).astype(float)
pines = np.zeros((H, W))
rr = np.random.default_rng(seed + 9)
for tx, th in [(40, 210), (92, 150), (130, 250), (182, 180), (226, 120), (268, 205), (318, 140), (352, 90)]:
    base = spit_top[tx] + 6
    up = base - Y
    # a conifer: tiers that widen downward, with notched edges
    half = (th - up) * 0.19 * (0.72 + 0.28 * ((up / 17 + tx) % 1)) + 1.5
    pines = np.maximum(pines, ((up > 0) & (up < th) & (np.abs(X - tx - 3 * np.sin(up / 40 + tx)) < half)).astype(float))
dark = np.maximum(pines, spit)
hatch("indigo", dark * 0.98, gap=1.5, length=(14, 36), clip=dark, press=0.72)
hatch("indigo", dark * 0.9, angle=CROSS, gap=1.7, length=(12, 30), clip=dark, press=0.6)
hatch("green", dark * 0.8, gap=2.0, length=(12, 30), clip=dark, press=0.5)
hatch("sienna", dark * 0.35 * (X % 97 < 50), gap=3.0, length=(14, 30), clip=dark, press=0.4)
# their reflection: broken, level, lighter
ry = np.clip(2 * (spit_top[None, :].repeat(H, 0) + 14) - Y, 0, H - 1).astype(int)
refl = pines[ry, np.arange(W)[None, :].repeat(H, 0)] * (Y > spit_top[None, :] + 16) * soft(1.15 - (Y - spit_top[None, :]) / 210)
hatch("indigo", refl * 0.7 * ripple, angle=0.0, gap=2.0, length=(14, 50), press=0.6)

# one light on, under the pines, and its reflection: the only warm, saturated mark
lx, ly = 381, int(spit_top[388]) - 10
lamp = ((np.abs(X - lx) < 7) & (np.abs(Y - ly) < 8)).astype(float)
for k in ("grey", "indigo", "sienna"):
    stay[k] = 1 - (1 - stay[k]) * (1 - lamp)
hatch("ochre", lamp, angle=0.0, gap=0.8, length=(6, 10), width=(1.6, 2.2), clip=lamp, press=0.95)
streak = ((np.abs(X - lx) < 7 + (Y - ly) * 0.03) & (Y > spit_top[lx] + 18) & (Y < spit_top[lx] + 150)).astype(float)
for k in ("grey", "indigo"):
    stay[k] = 1 - (1 - stay[k]) * (1 - 0.8 * streak)
hatch("ochre", streak * 0.7 * soft(1.1 - (Y - spit_top[lx]) / 170), angle=0.0, gap=2.1, length=(8, 18), clip=streak, press=0.9)


# ---------- round 3: things worth looking at closely ----------
def draw(pencil, lines, width, press):
    im = Image.new("L", (W * S, H * S), 0)
    d = ImageDraw.Draw(im)
    for pts in lines:
        d.line([(x * S, y * S) for x, y in pts], fill=int(r.uniform(170, 255)), width=max(1, int(width * r.uniform(0.8, 1.2) * S)), joint="curve")
    stay[pencil] *= 1 - press * (np.asarray(im.resize((W, H), Image.LANCZOS), float) / 255) * TOOTH


# the far shore becomes a line of small firs, each a few strokes
firs = []
fr = np.random.default_rng(seed + 20)
x = 392.0
while x < W:
    h = fr.uniform(9, 24)
    firs.append([(x, SHORE + 1), (x + fr.uniform(-1, 1), SHORE - h)])
    for k in range(3):
        yy = SHORE - h * (0.25 + 0.22 * k)
        w = h * 0.22 * (1 - k * 0.25)
        firs.append([(x - w, yy + 2), (x, yy - 2), (x + w, yy + 2)])
    x += fr.uniform(5, 11)
draw("indigo", firs, 1.3, 0.75)
draw("green", firs[::2], 1.6, 0.5)

# a cabin beside the pines, and a jetty running out from the spit
cx0, cy0 = 388, int(spit_top[388]) + 2
cabin = ((np.abs(X - cx0) < 22) & (Y > cy0 - 24) & (Y < cy0)).astype(float)
roof = ((Y > cy0 - 42) & (Y <= cy0 - 22) & (np.abs(X - cx0) < (Y - (cy0 - 42)) * 1.45 + 3)).astype(float)
for k in ("grey", "indigo", "violet", "green", "sienna"):
    stay[k] = 1 - (1 - stay[k]) * (1 - 0.9 * np.clip(cabin + roof, 0, 1))
hatch("indigo", roof, gap=1.5, length=(8, 18), clip=roof, press=0.75)
hatch("sienna", roof * 0.7, angle=CROSS, gap=2.2, length=(8, 16), clip=roof, press=0.5)
hatch("grey", cabin * (X > cx0 + 4) * 0.8, gap=2.0, length=(8, 16), clip=cabin, press=0.45)
draw("indigo", [[(cx0 - 22, cy0 - 24), (cx0 - 22, cy0), (cx0 + 22, cy0), (cx0 + 22, cy0 - 24)],
                [(cx0 - 27, cy0 - 21), (cx0, cy0 - 43), (cx0 + 27, cy0 - 21)]], 1.4, 0.8)
jx0, jx1, jy = cx0 + 22, cx0 + 150, cy0 + 4
jetty = [[(jx0, jy), (jx1, jy + 2)], [(jx0, jy + 4), (jx1, jy + 6)]] + [[(px, jy), (px + 1, jy + 20)] for px in range(jx0 + 14, jx1, 26)]
draw("indigo", jetty, 1.5, 0.8)
draw("indigo", [[(px - 4, jy + 26 + 7 * k), (px + 5, jy + 26 + 7 * k)] for px in range(jx0 + 14, jx1, 26) for k in range(4)], 1.2, 0.4)

# reeds in the near corners: long, slightly bowed strokes, some with a seed head
reeds, heads = [], []
gr = np.random.default_rng(seed + 21)
for x0_, x1_, n in ((560, 944, 120), (0, 120, 34)):
    for _ in range(n):
        bx = gr.uniform(x0_, x1_)
        edge_w = (bx - 560) / 384 if x0_ else (120 - bx) / 120
        hgt = gr.uniform(50, 120) + 150 * max(0.0, edge_w) ** 1.5
        lean = gr.uniform(-0.28, 0.28)
        bow = gr.uniform(-0.0012, 0.0012)
        pts = [(bx + lean * t + bow * t * t, H + 6 - t) for t in np.linspace(0, hgt, 8)]
        reeds.append(pts)
        if gr.random() < 0.3:
            tx, ty = pts[-1]
            heads.append([(tx, ty), (tx + lean * 14, ty - 14)])
draw("indigo", reeds, 1.5, 0.8)
draw("green", reeds[::2], 1.9, 0.55)
draw("sienna", heads, 3.4, 0.7)
draw("indigo", heads, 2.2, 0.45)

img = np.ones((H, W, 3))
for k, col in PENCILS.items():
    img *= 1 - (1 - stay[k])[..., None] * (1 - col / 255)
img = img * 255 + r.normal(0, 1.0, (H, W, 1))
Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(sys.argv[1])
