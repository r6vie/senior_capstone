"""The reference's composition, drawn with the cells renderer, for blind side-by-side judging. 1744 x 690."""
import sys

import numpy as np
from PIL import Image, ImageFilter

sys.path.insert(0, ".")
from cells import Canvas, bars, lambert, mist, ramp, rgb, smooth

W, H = 1744, 690
cv = Canvas(W, H, seed=int(sys.argv[2]) if len(sys.argv) > 2 else 5)
X, Y = cv.X, cv.Y
cv.bevel = 0.3
R = np.random.default_rng(1)


def vnoise(scale, seed):
    r = np.random.default_rng(seed)
    g = r.random((H // scale + 3, W // scale + 3))
    gy, gx = Y / scale, X / scale
    y0, x0 = gy.astype(int), gx.astype(int)
    fy, fx = smooth(gy - y0), smooth(gx - x0)
    a, b = g[y0, x0], g[y0, x0 + 1]
    c, d = g[y0 + 1, x0], g[y0 + 1, x0 + 1]
    return (a + (b - a) * fx) * (1 - fy) + (c + (d - c) * fx) * fy


def ridge(peaks, base, q=1.3, seed=0, wob=0.12):
    f = np.zeros_like(X)
    w = (vnoise(60, seed + 40) - 0.5) * wob
    for cx, top, rx in peaks:
        ry = base - top
        d = (np.abs((X - cx) / rx) ** q + np.abs((Y - base) / ry) ** q) ** (1 / q)
        f = np.maximum(f, smooth(1 - d + w) ** 0.9 * (Y <= base))
    return f


# 1. blue ranges: two layers of long bars, stepped crisp edges
for peaks, base, sd, stops in [
    ([(1240, 38, 430), (985, 112, 110), (1730, 222, 130)], 330, 1, [(0, "#0F4B6A"), (0.4, "#16608A"), (0.75, "#1F729B"), (1, "#3486B0")]),
    ([(360, 150, 240), (180, 250, 230), (620, 250, 160)], 330, 5, [(0, "#11506F"), (0.4, "#18658C"), (0.75, "#2479A2"), (1, "#3A8BB3")]),
]:
    blue = ridge(peaks, base, seed=sd)
    bcol = ramp(lambert(blue * 220, X, Y), stops)
    bcol, keep = mist(bcol, Y, base - 40, base + 5, 1.0)
    bars(cv, (blue > 0.02) * keep, bcol, 8, 14, 48, jitter=0.03)


def mounds(peaks, base, sd, mist_h=80):
    f = ridge(peaks, base, q=1.5, seed=sd) * (0.96 + 0.08 * vnoise(70, sd))
    sh = lambert(f * 520, X, Y)
    col = ramp(sh, [(0, "#A59E93"), (0.3, "#C8C1B5"), (0.55, "#E4DFD6"), (0.8, "#F6F3EE"), (1, "#FFFFFF")])
    col, keep = mist(col, Y, base - mist_h, base + 10, 1.0)
    cv.layer((f > 0.05) * keep, col, (14, 12), jitter=0.025)
    return f


def coral_band(peaks, base, sd):
    f = ridge(peaks, base, q=1.4, seed=sd)
    col = ramp(lambert(f * 120, X, Y), [(0, "#C4553C"), (0.5, "#DB6A4F"), (1, "#E87A5E")])
    col, keep = mist(col, Y, base - 30, base + 5, 1.0)
    bars(cv, (f > 0.04) * keep, col, 5, 16, 60, jitter=0.025, alt=0.03)


# 2..3. strata: back cream, coral, middle cream, coral, front cream, each misting at its foot
mounds([(965, 112, 150), (1300, 135, 240), (330, 222, 190)], 330, 11, 60)
coral_band([(470, 280, 170), (930, 205, 160), (1450, 215, 260)], 360, 2)
mounds([(250, 262, 210), (1060, 225, 200), (1620, 300, 200)], 400, 12, 70)
coral_band([(700, 330, 160), (1300, 300, 200)], 420, 3)
mounds([(1185, 290, 230), (1590, 340, 230), (840, 300, 130), (110, 330, 160)], 470, 13, 80)


# 4. terraced island plates: many thin courses, each lip a tan and green edge
def island(cx, cy, rx, ry, levels, seed, step=6):
    r = np.random.default_rng(seed)
    for i in range(levels):
        s = 1 - i / (levels + 2.0)
        n = (vnoise(34, seed + i) - 0.5) * 0.6
        m = (((X - cx - r.uniform(-25, 25)) / (rx * s)) ** 2 + ((Y - (cy - i * step)) / (ry * s)) ** 2 + n) < 1
        m = m.astype(float)
        lip = (m > 0) & (np.roll(m, -step, axis=0) == 0)
        top = ramp(vnoise(20, seed + 5 * i), [(0, "#6E9150"), (1, "#8FB06A")])
        side = np.where((((Y // 3) % 2) == 0)[..., None], rgb("#B39672"), rgb("#7C9656"))
        col = np.where(lip[..., None], side, top)
        bars(cv, m, col, 3, 18, 80, jitter=0.03)


island(330, 600, 380, 85, 5, 21)
island(1390, 590, 380, 60, 4, 22)
island(800, 420, 110, 40, 3, 23)


# 5. bonsai trees: trunk, then flat leaf pads lit from above, in small square cells
def tree(x, g, size, seed):
    r = np.random.default_rng(seed)
    h = size * r.uniform(1.4, 2.4)
    lean = r.uniform(-0.25, 0.25)
    tw = max(3, size * 0.12)
    t = (np.abs(X - (x + (g - Y) * lean)) < tw) & (Y > g - h) & (Y < g)
    tc = ramp(np.clip((X - x) / (2 * tw) + 0.5, 0, 1), [(0, "#9A6A4D"), (1, "#5D3B2A")])
    cv.layer(t.astype(float), tc, (4, 4), jitter=0.05)
    shade_ = (((X - x) / (size * 1.3)) ** 2 + ((Y - g - 2) / (size * 0.3)) ** 2) < 1
    cv.img[shade_] = cv.img[shade_] * 0.82
    pads = np.zeros_like(X)
    top = g - h
    for k in range(r.integers(5, 9)):
        px = x + lean * h + r.uniform(-1.0, 1.0) * size
        py = top + r.uniform(-0.6, 0.5) * size
        rx, ry = size * r.uniform(0.45, 0.8), size * r.uniform(0.35, 0.55)
        d = ((X - px) / rx) ** 2 + ((Y - py) / ry) ** 2
        pads = np.maximum(pads, smooth(1 - d) ** 0.7)
    if not (pads > 0).any():
        return
    sh = lambert(pads * 30, X, Y, light=(-0.4, -0.85, 0.45))
    col = ramp(sh, [(0, "#1F3A22"), (0.3, "#2F5530"), (0.6, "#4E7C42"), (0.85, "#79A25E"), (1, "#A9C784")])
    cv.layer((pads > 0.06).astype(float), col, (6, 6), jitter=0.07)


trees = []
while len(trees) < 75:
    x = R.uniform(40, 780)
    g = R.uniform(470, 660)
    if (x - 330) ** 2 / 370 ** 2 + (g - 600) ** 2 / 90 ** 2 < 0.85:
        trees.append((x, g, R.uniform(18, 34)))
while len(trees) < 140:
    x = R.uniform(1030, 1744)
    g = R.uniform(530, 625)
    if (x - 1390) ** 2 / 370 ** 2 + (g - 590) ** 2 / 65 ** 2 < 0.9:
        trees.append((x, g, R.uniform(17, 31)))
for _ in range(10):
    trees.append((R.uniform(720, 880), R.uniform(385, 430), R.uniform(15, 22)))

# 6. the river: zigzag bars between the islands (painted before the near trees)
yy = Y
rx_ = 960 - (yy - 420) * 0.36 + 60 * np.sign(np.sin((yy - 420) / 30)) * np.abs(np.sin((yy - 420) / 30)) ** 0.5
half = 26 + (yy - 420) * 0.42
river = ((np.abs(X - rx_) < half) & (Y > 420) & (Y < 690)).astype(float)
wcol = ramp(vnoise(30, 31), [(0, "#1F6A9C"), (0.45, "#2E83B9"), (0.8, "#4C9ACB"), (1, "#C9DCE8")])
wcol, keep = mist(wcol, Y, 640, 700, 0.7)

trees.sort(key=lambda t: t[1])
river_done = False
for i, (x, g, s) in enumerate(trees):
    if not river_done and g > 520:
        bars(cv, river * keep, wcol, 7, 26, 110, jitter=0.04)
        foam = ((np.abs(np.abs(X - rx_) - half) < 10) & (Y > 420) & (Y < 690)).astype(float)
        bars(cv, foam, np.ones((H, W, 3)) * rgb("#EEF3F5"), 7, 10, 30, jitter=0.02)
        river_done = True
    tree(x, g, s, i)

img = Image.fromarray((np.clip(cv.img, 0, 1) * 255).round().astype(np.uint8))
img = img.filter(ImageFilter.GaussianBlur(0.45))
img.save(sys.argv[1] if len(sys.argv) > 1 else "ref_try.png")
