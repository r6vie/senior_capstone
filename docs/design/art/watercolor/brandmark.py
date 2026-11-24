"""Brand round 2, identity C (wet ink): the Trove mark painted with the cover engine.

An open book made of two wet patches, one per page, that meet and overlap at the gutter, so the overlap glazes
darker: two people's colours making a third. Each member's mark takes the two main colours of their own cover.

python3 brandmark.py -> out/brand-<name>.png (and .webp)"""
import math
import sys
import numpy as np
sys.path.insert(0, ".")
import paint

paint.configure(200, 150, 4)
from paint import Paper  # noqa: E402

PAIRS = {
    "lake": ("#5B74B8", "#E6C487", 3),      # ultramarine and raw sienna
    "coast": ("#78A9A6", "#E3A3A0", 5),     # teal and rose
    "forest": ("#56705A", "#F0C59A", 8),    # cypress and apricot
    "dusk": ("#4A5868", "#D9967A", 11),     # payne and terracotta
    "mesa": ("#B4A9CC", "#C98A5A", 13),     # violet and sienna
}


def page(p, side):
    """One page of the open book, side -1 left, +1 right, seen from the front: the outer corners stand high and the
    page sweeps down into the gutter (a gull wing), the foot does the same, lower. The inner edge bows toward the
    other page, so the two overlap in a lens: narrow at head and foot, widest mid-page, where the glazes stack."""
    ox = 100 + side * 90
    n = 30
    head, foot = [], []
    for i in range(n + 1):
        t = i / n                                  # 0 at the outer edge, 1 at the gutter
        x = ox + (100 - ox) * t
        head.append((x, 26 + 30 * t ** 1.6 - 6 * math.sin(math.pi * t)))
        foot.append((x, 116 + 20 * t ** 1.6 - 5 * math.sin(math.pi * t)))
    inner = []
    for i in range(n + 1):                         # gutter edge, head to foot, bowed past the centre line
        v = i / n
        y = head[-1][1] + (foot[-1][1] - head[-1][1]) * v
        inner.append((100 - side * (3 + 7 * math.sin(math.pi * v)), y))
    m = p.poly(head + inner + foot[::-1])
    return p.rough(m, 1.2, 11, fine=0.3)


def mark(name):
    a, b, seed = PAIRS[name]
    p = Paper(seed)
    left, right = page(p, -1), page(p, 1)
    p.wash(left, b, 1.0, rim=1.0, flow=0.35, blotch=0.14)
    p.wash(right, a, 0.95, rim=1.0, flow=0.35, blotch=0.14)
    # where the pages overlap, one more wet glaze of the darker colour, so the lens blooms rather than banding
    p.wash(p.soften(left * right, 1.5), a, 0.2, rim=0.6, flow=0.5, blotch=0.2)
    save_clear(p.img, f"out/brand-{name}.png")
    return p


def save_clear(img, path):
    """Lift the paint off its paper so the mark sits on any light ground: the alpha is how much each pixel darkens
    the paper in its most-absorbed channel, and the colour is what, laid at that alpha over paper, gives the pixel
    back. The faint tooth of bare paper falls under the threshold and goes clear."""
    from PIL import Image
    paper = paint.PAPER.reshape(1, 1, 3)
    a = np.clip(((paper - img) / paper).max(axis=2), 0, 1)
    a = np.where(a < 0.035, 0, a)
    col = np.where(a[..., None] > 0, (img - (1 - a[..., None]) * paper) / np.maximum(a[..., None], 1e-3), 0)
    rgba = np.dstack([np.clip(col, 0, 1), a])
    ys, xs = np.nonzero(a > 0.02)
    pad = 8
    crop = rgba[max(0, ys.min() - pad):ys.max() + pad, max(0, xs.min() - pad):xs.max() + pad]
    Image.fromarray((crop * 255).astype(np.uint8), "RGBA").save(path)


if __name__ == "__main__":
    for n in (sys.argv[1:] or PAIRS):
        mark(n)
        print("painted", n)
