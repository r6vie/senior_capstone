"""Block print as a wide band for the book page, round 2: the street printed on bare paper. The same black, carved
whites and gold as block.py, laid out 1440 x 620 (cut at 2x). The skyline is tall at both ends and low under the title;
the sky is only the gouge marks themselves, inked in rings round a gold moon on the right; the street's foot is cut
away in level gouge lines until it is paper again. python3 block_band.py out.png [seed]"""
import math
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

W, H = 2880, 1240
S = 2
seed = int(sys.argv[2]) if len(sys.argv) > 2 else 5
r = np.random.default_rng(seed)
PAPER = np.array([250, 250, 247], float)
BLACK = np.array([22, 24, 31], float)
GOLD = np.array([232, 190, 92], float)
FOOT = 1190

blk = Image.new("L", (W * S, H * S), 0)
gold = Image.new("L", (W * S, H * S), 0)
d = ImageDraw.Draw(blk)
g = ImageDraw.Draw(gold)


def P(*v):
    return [x * S for x in v]


def skyline(x):
    """How tall the street stands at x: towers at both ends, low under the title."""
    left = 300 * math.exp(-((x - 180) / 520) ** 2)
    right = 330 * math.exp(-((x - 2600) / 480) ** 2)
    return 940 - left - right


# ---------- the street ----------
roofs, x = [], 0.0
while x < W:
    w = r.uniform(80, 170)
    top = skyline(x + w / 2) + r.uniform(-50, 40)
    roofs.append((x, top, min(W, x + w)))
    x += w
mx, my, mr = 2420, 470, 78
wx, wy = 1480, 975
for xa, top, xb in roofs:
    d.rectangle(P(xa, top, xb, FOOT), fill=255)
# a few things on the roofs: chimneys, one water tower, an aerial
for xa, top, xb in roofs:
    if r.random() < 0.35:
        cx = r.uniform(xa + 14, xb - 30)
        d.rectangle(P(cx, top - r.uniform(18, 36), cx + 16, top), fill=255)
tx = next(xa for xa, top, xb in roofs if xa > 2150)
ttop = [t for xa, t, xb in roofs if xa == tx][0]
d.rectangle(P(tx + 30, ttop - 70, tx + 34, ttop), fill=255)
d.rectangle(P(tx + 70, ttop - 70, tx + 74, ttop), fill=255)
d.rectangle(P(tx + 20, ttop - 130, tx + 84, ttop - 66), fill=255)
d.polygon(P(tx + 14, ttop - 128, tx + 52, ttop - 162, tx + 90, ttop - 128), fill=255)
for xa, top, xb in roofs:
    d.line(P(xa + 3, top + 4, xb - 3, top + 4), fill=0, width=4 * S)
    d.line(P(xa + 3, top + 4, xa + 3, FOOT), fill=0, width=3 * S)
    for yy in range(int(top) + 18, FOOT - 6, 13):
        d.line(P(xa + 8, yy, xa + 8 + r.uniform(8, 20), yy + r.uniform(-1, 1)), fill=0, width=int(2.5 * S))
    cols = max(1, int(xb - xa - 44) // 30)
    for ci in range(cols):
        for yy in range(int(top) + 34, FOOT - 110, 46):
            ox = xa + 36 + ci * 30
            if r.random() < 0.3 and not (abs(ox - wx - 14) < 60 and abs(yy - wy - 20) < 80):
                d.rectangle(P(ox, yy, ox + 14, yy + 22), outline=0, width=3 * S)
# the night shift's window
d.rectangle(P(wx - 4, wy - 4, wx + 44, wy + 60), fill=0)
g.rectangle(P(wx, wy, wx + 40, wy + 56), fill=255)
d.line(P(wx + 20, wy, wx + 20, wy + 56), fill=255, width=3 * S)
d.line(P(wx, wy + 26, wx + 40, wy + 26), fill=255, width=3 * S)
# the foot: level gouge cuts, wider and closer toward the bottom, until the block is gone
y = 1020.0
while y < FOOT + 4:
    t = (y - 1020) / (FOOT - 1020)
    th = 2 + 14 * t ** 1.4
    xa = -20.0
    while xa < W:
        L = r.uniform(80, 360) * (1.2 - t)
        if r.random() < 0.85 + 0.15 * t:
            d.rounded_rectangle(P(xa, y - th / 2, xa + L + 200 * t, y + th / 2), radius=th / 2 * S, fill=0)
        xa += L + r.uniform(6, 30) * (1 - t)
    y += max(5.0, 13 - 9 * t)

# ---------- the sky: no block behind it, only the cut marks, inked, in rings round the moon ----------
rad = mr + 26
while rad < 660:
    n = int(2 * math.pi * rad / 46)
    a0 = r.uniform(0, 6.28)
    for k in range(n):
        a = a0 + k * 2 * math.pi / n + r.normal(0, 0.012)
        px, py = mx + rad * math.cos(a), my + rad * math.sin(a)
        keep = math.exp(-(rad - mr) / 420) * min(1.0, max(0.0, (px - 2120) / 300))
        if r.random() > keep or py > skyline(px) - 40 or py < 60:
            continue
        span = r.uniform(0.45, 0.8) * 2 * math.pi / n
        wdt = max(2.2, 7.5 - rad / 170) * r.uniform(0.75, 1.2)
        pts = []
        for t in np.linspace(0, 1, 9):
            aa = a + span * t
            ww = wdt * math.sin(math.pi * t) ** 0.7 / 2
            pts.append(((mx + (rad + ww) * math.cos(aa)) * S, (my + (rad + ww) * math.sin(aa)) * S))
        for t in np.linspace(1, 0, 9):
            aa = a + span * t
            ww = wdt * math.sin(math.pi * t) ** 0.7 / 2
            pts.append(((mx + (rad - ww) * math.cos(aa)) * S, (my + (rad - ww) * math.sin(aa)) * S))
        d.polygon(pts, fill=255)
    rad += 19 + rad / 60
d.ellipse(P(mx - mr - 9, my - mr - 9, mx + mr + 9, my + mr + 9), outline=255, width=4 * S)
g.ellipse(P(mx - mr, my - mr, mx + mr, my + mr), fill=255)
# stars at both ends, inked crosses
for _ in range(30):
    sx = r.choice([r.uniform(30, 820), r.uniform(2080, W - 30)])
    sy = r.uniform(240, skyline(sx) - 90)
    if (sx - mx) ** 2 + (sy - my) ** 2 < (mr + 70) ** 2:
        continue
    q = r.uniform(4, 8)
    d.line(P(sx - q, sy, sx + q, sy), fill=255, width=int(2.4 * S))
    d.line(P(sx, sy - q, sx, sy + q), fill=255, width=int(2.4 * S))

blk = blk.resize((W, H), Image.LANCZOS)
gold = gold.resize((W, H), Image.LANCZOS)


def rough(mask, amt):
    a = np.asarray(mask.filter(ImageFilter.GaussianBlur(1.4)), float) / 255
    n = np.asarray(Image.fromarray((r.random((H // 3 + 2, W // 3 + 2)) * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC), float) / 255
    return np.clip((a + (n - 0.5) * amt - 0.5) * 6 + 0.5, 0, 1)


def ink(img, a, colour, wear):
    low = np.asarray(Image.fromarray((r.random((H // 70 + 2, W // 70 + 2)) * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC), float) / 255
    salt = (r.random((H, W)) > wear + 0.07 * (low > 0.6)).astype(float)
    salt = np.asarray(Image.fromarray((salt * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.6)), float) / 255
    cover = (a * (0.86 + 0.12 * low) * (0.6 + 0.4 * salt))[..., None]
    return img * (1 - cover * (1 - colour / 255))


img = np.ones((H, W, 3)) * PAPER + r.normal(0, 1.6, (H, W, 1))
ga = np.roll(rough(gold, 0.25), (3, -4), (0, 1))
img = ink(img, ga, GOLD, 0.03)
img = ink(img, rough(blk, 0.3), BLACK, 0.035)
Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(sys.argv[1])
