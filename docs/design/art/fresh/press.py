"""Letterpress: the title is the picture. Wood type locked up to the full measure, two inks, overprinted.
python3 press.py out.png "The Night Shift Knows" "Maya Okafor" [seed]"""
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H = 944, 1376
title, author = sys.argv[2], sys.argv[3]
seed = int(sys.argv[4]) if len(sys.argv) > 4 else 3
r = np.random.default_rng(seed)
SUP = "/System/Library/Fonts/Supplemental/"
FACES = [(SUP + "SuperClarendon.ttc", 7), (SUP + "DIN Condensed Bold.ttf", 0), (SUP + "Futura.ttc", 4),
         (SUP + "Rockwell.ttc", 2), (SUP + "Bodoni 72.ttc", 2)]
PAPER = np.array([246, 243, 234], float)
INK1 = np.array([24, 62, 54], float)      # bottle green
INK2 = np.array([240, 176, 150], float)    # a warm second ink, printed first
L, R = 138, 880                           # the measure: clear of the hinge on the left


def font(i, size):
    path, idx = FACES[i % len(FACES)]
    return ImageFont.truetype(path, size, index=idx)


def fit(word, face, width):
    """Largest size at which the word fills the measure."""
    lo, hi = 20, 900
    while hi - lo > 1:
        mid = (lo + hi) // 2
        b = font(face, mid).getbbox(word)
        lo, hi = (mid, hi) if b[2] - b[0] <= width else (lo, mid)
    return lo


def impression(mask, ink, img, wear=0.05):
    """Print a mask in one ink: multiply onto the sheet, with thin patches, salty specks and a darker squeezed rim."""
    a = np.asarray(mask, float) / 255
    low = np.asarray(Image.fromarray((r.random((H // 60 + 2, W // 60 + 2)) * 255).astype(np.uint8)).resize((W, H), Image.BICUBIC), float) / 255
    salt = (r.random((H, W)) > wear + 0.10 * (low > 0.62)).astype(float)
    salt = np.asarray(Image.fromarray((salt * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.6)), float) / 255
    rim = np.asarray(mask.filter(ImageFilter.GaussianBlur(3)), float) / 255
    cover = a * (0.80 + 0.14 * low) * (0.55 + 0.45 * salt) + 0.10 * a * (1 - rim) * 4 * rim
    cover = np.clip(cover, 0, 1)[..., None]
    return img * (1 - cover * (1 - ink / 255))


img = np.ones((H, W, 3)) * PAPER
img += r.normal(0, 2.2, (H, W, 1))

words = title.upper().split()
small = [w for w in words if len(w) <= 3]
big = [w for w in words if len(w) > 3]
# first ink: one large disc behind the type, off the measure, like a second forme
m2 = Image.new("L", (W, H), 0)
d2 = ImageDraw.Draw(m2)
cx, cy, rad = 640, 560, 300
d2.ellipse((cx - rad, cy - rad, cx + rad, cy + rad), fill=255)
img = impression(m2, INK2, img, wear=0.03)

m1 = Image.new("L", (W, H), 0)
d = ImageDraw.Draw(m1)
y = 150
if small:
    f = font(1, 86)
    d.text((L, y), " ".join(small), font=f, fill=255)
    d.rectangle((L + f.getlength(" ".join(small)) + 26, y + 26, R, y + 34), fill=255)
    y += 104
for i, w in enumerate(big):
    face = [0, 1, 2, 3][i % 4]
    size = min(fit(w, face, R - L), 330)
    f = font(face, size)
    b = f.getbbox(w)
    d.text((L - b[0] + r.integers(-2, 3), y - b[1]), w, font=f, fill=255)
    y += (b[3] - b[1]) + 30
# foot: a rule, the name, a rule
d.rectangle((L, 1196, R, 1202), fill=255)
f = font(1, 64)
sp = author.upper()
d.text((L, 1226), sp, font=f, fill=255)
d.rectangle((L, 1296, R, 1299), fill=255)
img = impression(m1, INK1, img)
Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).save(sys.argv[1])
