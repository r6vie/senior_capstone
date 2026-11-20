"""Coloured pencil landscape: thousands of short strokes, edge to edge at the foot, thinning to bare white paper
under the title. A farm road at dusk with one lit window. python3 pencil.py out.png [seed]"""
import math
import sys
import numpy as np
from PIL import Image, ImageDraw

W, H = 944, 1376
S = 2
seed = int(sys.argv[2]) if len(sys.argv) > 2 else 4
r = np.random.default_rng(seed)
Y, X = np.mgrid[0:H, 0:W].astype(float)


def rgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], float)


def noise(sx, sy, s):
    g = np.random.default_rng(s).random((int(H / sy) + 3, int(W / sx) + 3))
    return np.asarray(Image.fromarray((g * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC), float) / 255


def ridge(base, waves, s):
    x = np.arange(W)
    rr = np.random.default_rng(s)
    y = np.full(W, float(base))
    for amp, wl in waves:
        y += amp * np.sin(x / wl * 2 * np.pi + rr.uniform(0, 6.28))
    return y


PENCILS = {k: rgb(v) for k, v in {
    "sky": "#8FB2D6", "dusk": "#E8A77C", "far": "#6F86B3", "hill": "#5C8A64", "field": "#C9A441", "green": "#3F6B4A",
    "dark": "#243A5E", "earth": "#9A6B4A", "light": "#F2C14E"}.items()}
BATCH = 5
layers = {k: [Image.new("L", (W * S, H * S), 0) for _ in range(BATCH)] for k in PENCILS}
draws = {k: [ImageDraw.Draw(im) for im in v] for k, v in layers.items()}


def hatch(pencil, tone, angle, n, length=(16, 44), width=(2.2, 3.8), wob=0.22, curve=0.0):
    """Scatter n candidate strokes; a stroke is kept with probability tone(x, y) (HxW array, 0..1).
    angle: radians, or an HxW field of angles so strokes can follow the land."""
    xs, ys = r.uniform(0, W, n), r.uniform(0, H, n)
    keep = r.random(n) < tone[ys.astype(int).clip(0, H - 1), xs.astype(int).clip(0, W - 1)]
    for x, y in zip(xs[keep], ys[keep]):
        a = (angle[int(y), int(x)] if isinstance(angle, np.ndarray) else angle) + r.normal(0, wob)
        L = r.uniform(*length)
        dx, dy = math.cos(a) * L / 2, math.sin(a) * L / 2
        b = r.normal(0, curve) * L
        pts = [((x - dx) * S, (y - dy) * S), ((x - dy / L * b) * S, (y + dx / L * b) * S), ((x + dx) * S, (y + dy) * S)]
        draws[pencil][r.integers(BATCH)].line(pts, fill=int(r.uniform(120, 230)), width=int(r.uniform(*width) * S),
                                              joint="curve")


def band(top, bottom):
    """1 between two skylines (arrays over x), 0 outside."""
    return ((Y >= top[None, :]) & (Y < bottom[None, :])).astype(float)


def slope(line):
    return np.arctan(np.gradient(line))[None, :] * np.ones((H, 1))


far = ridge(800, [(30, 640), (14, 230)], 1)
hill = ridge(880, [(36, 520), (16, 190)], 2)
field = ridge(985, [(22, 700), (8, 210)], 3)
bottom = np.full(W, H + 10.0)
DIAG = math.radians(-52)   # the hand's own direction

# sky: sparse strokes, none near the title, more toward the horizon; a warm band low down
sky = (Y < far[None, :]).astype(float)
up = np.clip((Y - 470) / 330, 0, 1)
cloud = noise(260, 70, 7)
hatch("sky", sky * up ** 1.4 * (0.3 + 0.7 * (cloud > 0.45)), math.radians(-16), 60000, length=(26, 70), wob=0.12)
hatch("dusk", sky * np.clip((Y - 620) / 170, 0, 1) ** 1.2 * 0.9, 0.05, 30000, length=(24, 70), wob=0.08)
hatch("light", sky * np.clip(1 - np.hypot(X - 300, (Y - 790) * 1.4) / 150, 0, 1) * 0.9, 0.0, 3000, length=(20, 50), wob=0.1)
# far range: cool, hatched in the hand's direction then along its back
m = band(far, hill)
hatch("far", m * 0.95, DIAG, 60000)
hatch("far", m * 0.8, slope(far), 30000, wob=0.12)
hatch("dark", m * np.clip((Y - far[None, :]) / 80, 0, 1) * 0.5, DIAG, 20000)
# green hills, darker in their hollows
m = band(hill, field)
shade = 0.45 + 0.55 * noise(200, 60, 9)
hatch("hill", m * 0.95, DIAG, 70000)
hatch("green", m * shade * 0.8, slope(hill), 45000, wob=0.15)
hatch("field", m * (1 - shade) * 0.7, slope(hill), 20000, wob=0.15)
# the near field: furrows that fan out from a point on the horizon, ochre with green and earth
vx, vy = 620, 960
furrow = np.arctan2(Y - vy, X - vx)
m = band(field, bottom)
depth = np.clip((Y - field[None, :]) / 380, 0, 1)
stripe = (np.sin(furrow * 46) > 0).astype(float)
hatch("field", m * (0.6 + 0.4 * stripe), furrow, 70000, length=(18, 60), wob=0.06)
hatch("earth", m * (1 - stripe) * (0.4 + 0.5 * depth), furrow, 45000, length=(18, 60), wob=0.06)
hatch("green", m * stripe * 0.35, furrow, 12000, length=(14, 40), wob=0.08)
hatch("dark", m * depth ** 2 * 0.5, DIAG, 16000)
# the road: left almost bare, it runs to the same point
road = m * (np.abs(furrow - math.radians(118)) < 0.085 + 0.02 * depth)
for k in ("field", "earth", "green", "dark"):
    for im in layers[k]:
        px = np.asarray(im, np.uint8)
    # (road is cleared after compositing, below)
# trees: a windbreak of poplars on the field edge, upright strokes, dark on the right
trees = np.zeros((H, W))
rr = np.random.default_rng(seed + 9)
for tx in list(rr.uniform(40, 420, 9)) + list(rr.uniform(760, 930, 4)):
    th, tw = rr.uniform(90, 170), rr.uniform(16, 26)
    by = field[int(tx)] + 12
    e = ((X - tx) / tw) ** 2 + ((Y - (by - th / 2)) / (th / 2)) ** 2
    trees = np.maximum(trees, (e < 1).astype(float) * (0.75 + 0.25 * (X > tx)) * (np.abs(tx - 620) > 110))
hatch("green", trees * 0.95, math.radians(-88), 60000, length=(10, 26), wob=0.12)
hatch("dark", trees * (X % 1 < 2) * 0.55 * (trees > 0.8), math.radians(-88), 30000, length=(10, 24), wob=0.12)
# the house at the road's end: walls left as paper, a roof, one lit window
hx, hy, hw, hh = 620, field[620] + 4, 116, 62
wall = ((np.abs(X - hx) < hw / 2) & (Y > hy - hh) & (Y < hy)).astype(float)
roof = ((Y > hy - hh - 46) & (Y <= hy - hh + 2) & (np.abs(X - hx) < (Y - (hy - hh - 46)) * 1.45 + 4)).astype(float)
win = ((np.abs(X - hx + 22) < 11) & (np.abs(Y - hy + 30) < 14)).astype(float)
hatch("earth", roof, DIAG, 60000, length=(8, 18))
hatch("dark", roof * 0.8, DIAG, 40000, length=(8, 18))
hatch("dark", wall * (X > hx + 14) * 0.7, DIAG, 40000, length=(8, 16))
outline = (np.abs(np.abs(X - hx) - hw / 2) < 2.5) & (Y > hy - hh) & (Y < hy) | (np.abs(Y - hy) < 2.5) & (np.abs(X - hx) < hw / 2)
hatch("dark", outline.astype(float), math.radians(-88), 120000, length=(6, 14), width=(1.6, 2.4), wob=0.05)
hatch("light", win, 0.0, 200000, length=(5, 12), width=(2, 3))
hatch("dusk", win * 0.5, 0.0, 60000, length=(5, 12))

# composite: each pencil lays wax on the paper's tooth; overlapping strokes build up
tooth = 0.55 + 0.45 * (noise(1.7, 1.7, 77) > 0.34)
img = np.ones((H, W, 3))
clear = 1 - wall * (1 - win) * 0.9
road_clear = 1 - road * 0.75
for k, col in PENCILS.items():
    stay = np.ones((H, W))
    for im in layers[k]:
        a = np.asarray(im.resize((W, H), Image.LANCZOS), float) / 255
        stay *= 1 - 0.62 * a * tooth
    cov = 1 - stay
    if k in ("sky", "far", "hill", "green", "field"):
        cov = cov * (1 - wall * 0.92)
    if k == "dusk":
        cov = cov * clear
    if k in ("field", "earth", "green", "dark"):
        cov = cov * road_clear
    img *= 1 - cov[..., None] * (1 - col / 255)
img = img * 255 + r.normal(0, 1.2, (H, W, 1))
Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(sys.argv[1])
