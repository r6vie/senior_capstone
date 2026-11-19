"""Block print as a wide band for the book page: the same black block, carved marks and gold as block.py, laid out
1440 x 620 (cut at 2x). Two tall panels of carved night at the ends, joined by one long street that stays low under
the title. python3 block_band.py out.png [seed]"""
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
FOOT = 1170
LP, RP = (0, 330, 740), (2170, 280, W)   # the night panels: (x0, top, x1)

blk = Image.new("L", (W * S, H * S), 0)
gold = Image.new("L", (W * S, H * S), 0)
d = ImageDraw.Draw(blk)
g = ImageDraw.Draw(gold)


def P(*v):
    return [x * S for x in v]


d.rectangle(P(LP[0], LP[1], LP[2], FOOT), fill=255)
d.rectangle(P(RP[0], RP[1], RP[2], FOOT), fill=255)
mx, my, mr = 2560, 560, 74


def gouge_rings(cx, cy, r0, r1, box):
    """Rings of short lens-shaped nicks around a centre, cut only inside box (x0, y0, x1, y1)."""
    rad = r0
    while rad < r1:
        n = int(2 * math.pi * rad / 46)
        a0 = r.uniform(0, 6.28)
        for k in range(n):
            if r.random() < 0.16:
                continue
            a = a0 + k * 2 * math.pi / n + r.normal(0, 0.012)
            px, py = cx + rad * math.cos(a), cy + rad * math.sin(a)
            if not (box[0] + 14 < px < box[2] - 14 and box[1] + 14 < py < box[3]):
                continue
            span = r.uniform(0.45, 0.8) * 2 * math.pi / n
            wdt = max(2.2, 7.5 - rad / 170) * r.uniform(0.75, 1.2)
            pts = []
            for t in np.linspace(0, 1, 9):
                aa = a + span * t
                ww = wdt * math.sin(math.pi * t) ** 0.7 / 2
                pts.append(((cx + (rad + ww) * math.cos(aa)) * S, (cy + (rad + ww) * math.sin(aa)) * S))
            for t in np.linspace(1, 0, 9):
                aa = a + span * t
                ww = wdt * math.sin(math.pi * t) ** 0.7 / 2
                pts.append(((cx + (rad - ww) * math.cos(aa)) * S, (cy + (rad - ww) * math.sin(aa)) * S))
            d.polygon(pts, fill=0)
        rad += 19 + rad / 60


# right panel: rings round the moon; left panel: rings round a moon that has set off the edge of the block
gouge_rings(mx, my, mr + 26, 900, (RP[0], RP[1], RP[2], 980))
gouge_rings(-160, 260, 220, 1100, (LP[0], LP[1], LP[2], 980))
d.ellipse(P(mx - mr - 5, my - mr - 5, mx + mr + 5, my + mr + 5), fill=0)
g.ellipse(P(mx - mr, my - mr, mx + mr, my + mr), fill=255)

# the street: one row of roofs the whole width, low in the middle, taller inside the panels
roofs, x = [], 0
while x < W:
    w = r.uniform(90, 190)
    inside = x < LP[2] or x > RP[0]
    top = r.uniform(760, 900) if inside else r.uniform(850, 940)
    roofs.append((x, top, min(W, x + w)))
    x += w
wx, wy = 1480, 960
for xa, top, xb in roofs:
    d.rectangle(P(xa, top, xb, FOOT), fill=255)
for xa, top, xb in roofs:
    d.line(P(xa + 3, top + 4, xb - 3, top + 4), fill=0, width=4 * S)
    d.line(P(xa + 3, top + 4, xa + 3, FOOT), fill=0, width=3 * S)
    for yy in range(int(top) + 18, FOOT - 6, 13):
        d.line(P(xa + 8, yy, xa + 8 + r.uniform(8, 20), yy + r.uniform(-1, 1)), fill=0, width=int(2.5 * S))
    cols = max(1, int(xb - xa - 44) // 30)
    for ci in range(cols):
        for yy in range(int(top) + 34, FOOT - 30, 46):
            ox = xa + 36 + ci * 30
            if r.random() < 0.3 and not (abs(ox - wx - 14) < 60 and abs(yy - wy - 20) < 80):
                d.rectangle(P(ox, yy, ox + 14, yy + 22), outline=0, width=3 * S)
# one lit window: the night shift
d.rectangle(P(wx - 4, wy - 4, wx + 44, wy + 60), fill=0)
g.rectangle(P(wx, wy, wx + 40, wy + 56), fill=255)
d.line(P(wx + 20, wy, wx + 20, wy + 56), fill=255, width=3 * S)
d.line(P(wx, wy + 26, wx + 40, wy + 26), fill=255, width=3 * S)
for _ in range(40):
    side = LP if r.random() < 0.45 else RP
    sx, sy = r.uniform(side[0] + 24, side[2] - 24), r.uniform(side[1] + 20, 740)
    if (sx - mx) ** 2 + (sy - my) ** 2 < (mr + 60) ** 2:
        continue
    q = r.uniform(4, 8)
    d.line(P(sx - q, sy, sx + q, sy), fill=0, width=int(2.4 * S))
    d.line(P(sx, sy - q, sx, sy + q), fill=0, width=int(2.4 * S))

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
