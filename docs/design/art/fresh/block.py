"""Block print: a night cut in lino. Black block, carved white marks, one second colour for the light.
python3 block.py out.png [seed]"""
import math
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

W, H = 944, 1376
S = 2  # draw large, reduce: the cuts come out clean
seed = int(sys.argv[2]) if len(sys.argv) > 2 else 5
r = np.random.default_rng(seed)
PAPER = np.array([246, 243, 234], float)
BLACK = np.array([22, 24, 31], float)
GOLD = np.array([232, 190, 92], float)
DY = -6
X0, Y0, X1, Y1 = 138, 430 + DY, 884, 1210 + DY  # the block, clear of the hinge; title above, name below

blk = Image.new("L", (W * S, H * S), 0)   # where black prints
gold = Image.new("L", (W * S, H * S), 0)  # where the second colour prints
d = ImageDraw.Draw(blk)
g = ImageDraw.Draw(gold)


def P(*v):
    return [x * S for x in v]


d.rectangle(P(X0, Y0, X1, Y1), fill=255)
mx, my, mr = 640, 640 + DY, 74
# the sky: rings of short gouge cuts around the moon, each a lens-shaped nick
rad = mr + 26
while rad < 900:
    n = int(2 * math.pi * rad / 46)
    a0 = r.uniform(0, 6.28)
    for k in range(n):
        if r.random() < 0.16:
            continue
        a = a0 + k * 2 * math.pi / n + r.normal(0, 0.012)
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
        d.polygon(pts, fill=0)
    rad += 19 + rad / 60
# moon: cleared from the black, printed in the second colour, with a carved crescent of shade
d.ellipse(P(mx - mr - 5, my - mr - 5, mx + mr + 5, my + mr + 5), fill=0)
g.ellipse(P(mx - mr, my - mr, mx + mr, my + mr), fill=255)

# the street: roofs as solid black, with a carved outline and a few cut windows
roofs = [(138, 1010, 250), (250, 930, 372), (372, 1040, 470), (470, 960, 610), (610, 1070, 700), (700, 900, 810),
         (810, 1000, 884)]
roofs = [(a, t + DY, b_) for a, t, b_ in roofs]
wx, wy = 520, 1024 + DY
for xa, top, xb in roofs:
    d.rectangle(P(xa, top, xb, Y1), fill=255)
for xa, top, xb in roofs:
    d.line(P(xa + 3, top + 4, xb - 3, top + 4), fill=0, width=4 * S)   # roof edge
    d.line(P(xa + 3, top + 4, xa + 3, Y1), fill=0, width=3 * S)         # one lit side
    # hatching down the lit side
    for yy in range(top + 18, Y1 - 6, 13):
        d.line(P(xa + 8, yy, xa + 8 + r.uniform(8, 20), yy + r.uniform(-1, 1)), fill=0, width=int(2.5 * S))
    cols = max(1, (xb - xa - 44) // 30)
    for ci in range(cols):
        for yy in range(top + 34, Y1 - 30, 46):
            ox = xa + 36 + ci * 30
            if r.random() < 0.3 and not (abs(ox - wx - 14) < 60 and abs(yy - wy - 20) < 80):
                d.rectangle(P(ox, yy, ox + 14, yy + 22), outline=0, width=3 * S)
# one lit window: the night shift
d.rectangle(P(wx - 4, wy - 4, wx + 44, wy + 60), fill=0)
g.rectangle(P(wx, wy, wx + 40, wy + 56), fill=255)
d.line(P(wx + 20, wy, wx + 20, wy + 56), fill=255, width=3 * S)
d.line(P(wx, wy + 26, wx + 40, wy + 26), fill=255, width=3 * S)
# stars: small crossed nicks
for _ in range(26):
    sx, sy = r.uniform(X0 + 20, X1 - 20), r.uniform(Y0 + 16, 880)
    if (sx - mx) ** 2 + (sy - my) ** 2 < (mr + 60) ** 2:
        continue
    q = r.uniform(4, 8)
    d.line(P(sx - q, sy, sx + q, sy), fill=0, width=int(2.4 * S))
    d.line(P(sx, sy - q, sx, sy + q), fill=0, width=int(2.4 * S))

blk = blk.resize((W, H), Image.LANCZOS)
gold = gold.resize((W, H), Image.LANCZOS)


def rough(mask, amt):
    """The block's edge wanders a little: blur with noise, then cut hard again."""
    a = np.asarray(mask.filter(ImageFilter.GaussianBlur(1.4)), float) / 255
    n = np.asarray(Image.fromarray((r.random((H // 3 + 2, W // 3 + 2)) * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC), float) / 255
    return np.clip((a + (n - 0.5) * amt - 0.5) * 6 + 0.5, 0, 1)


def ink(img, a, colour, wear):
    low = np.asarray(Image.fromarray((r.random((H // 70 + 2, W // 70 + 2)) * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC), float) / 255
    salt = (r.random((H, W)) > wear + 0.07 * (low > 0.6)).astype(float)
    salt = np.asarray(Image.fromarray((salt * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.6)), float) / 255
    cover = (a * (0.86 + 0.12 * low) * (0.6 + 0.4 * salt))[..., None]
    return img * (1 - cover * (1 - colour / 255))


img = np.ones((H, W, 3)) * PAPER + r.normal(0, 2.2, (H, W, 1))
# the second colour is printed first and a touch out of register
ga = np.roll(rough(gold, 0.25), (3, -4), (0, 1))
img = ink(img, ga, GOLD, 0.03)
img = ink(img, rough(blk, 0.3), BLACK, 0.035)
Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(sys.argv[1])
