"""The unwritten book, moving (Josef, 2026-11-23, via the My Book Screen session: watercolour "dropped on there and
just like color and rewrite and rework", on the blank cover of the Getting started screens; a calm loop of about a
minute that never settles into a finished picture).

Each drop is painted once with the cover engine, twice over: wet (soft, no rim) and dry (the pooled rim of a wash
that has dried). The animation only decides how much of each is on the paper at each moment: a drop lands and
blooms outward along an uneven wet front, sits wet, dries (its rim darkens in), is glazed over by the next drops,
and is washed back toward the paper. Glazes combine Beer-Lambert, as in the engine, so overlaps deepen the way real
washes do. Every drop runs on the loop's own clock (time modulo the period), so the last frame flows into the first.

The type zone (the name and later a title, from about 13% down and 15% in, to about 45% of the height) only ever
takes a light veil of paint, so the type stays readable.

python3 blank_loop.py [--preview] -> out/loop/frame_XXXX.png and out/blank-poster.png (472 x 688, the cover at 2x)"""
import math
import os
import sys
import numpy as np

sys.path.insert(0, ".")
import paint

paint.configure(236, 344, 2)
from paint import Paper, fbm, blur, S, W, H  # noqa: E402

PERIOD, FPS = 60.0, 12
LIFE = 26.0                      # a drop's whole life: land, bloom, sit wet, dry, be washed back
BLOOM, DRY_AT, DRY_LEN, WASH_AT = 5.5, 8.0, 6.0, 17.0

ULTRA, CERUL, ROSE, RAW, TEAL, VIOLET, SAGE, APRICOT, SIENNA, MAUVE, PAYNE = (
    "#5B74B8", "#7FB2D6", "#E3A3A0", "#E6C487", "#78A9A6", "#B4A9CC", "#A9BC93", "#F0C59A", "#C98A5A", "#B596B2",
    "#4A5868")

# start (s), centre (world units), radii, rotation, colour, density. Big flat patches, mostly in the lower two
# thirds and the right; a few pass under the type zone and are veiled there. Colours travel round the wheel so that
# what overlaps is always a pair that glazes well.
DROPS = [
    (0.0, (150, 250), (91, 67), 0.3, ULTRA, 0.65),
    (4.5, (80, 292), (80, 57), -0.2, ROSE, 0.61),
    (9.0, (190, 300), (70, 59), 0.6, RAW, 0.68),
    (13.0, (120, 210), (85, 52), -0.4, TEAL, 0.58),
    (17.5, (60, 250), (62, 75), 0.2, APRICOT, 0.65),
    (22.0, (175, 180), (67, 83), 0.9, VIOLET, 0.58),
    (26.5, (110, 300), (101, 57), 0.1, CERUL, 0.61),
    (31.0, (200, 245), (59, 70), -0.6, ROSE, 0.61),
    (35.5, (70, 210), (72, 54), 0.5, SAGE, 0.65),
    (40.0, (150, 290), (83, 65), -0.3, MAUVE, 0.61),
    (44.5, (190, 150), (57, 75), 0.2, RAW, 0.65),
    (49.0, (95, 255), (91, 70), 0.7, ULTRA, 0.58),
    (53.5, (165, 220), (65, 52), -0.8, APRICOT, 0.65),
]

Xw, Yw = paint.XX / S, paint.YY / S


def smooth(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def ease(x):
    """0..1 -> 0..1, quick at first and settling, like a wet front slowing as it spreads."""
    x = np.clip(x, 0, 1)
    return 1 - (1 - x) ** 2.4


def type_veil():
    """1 over the paper, falling to 0.28 over the type zone, with a wide soft edge so no line shows."""
    zone = (smooth(Xw, 236 * 0.10, 236 * 0.18) * smooth(Yw, 344 * 0.08, 344 * 0.15)
            * (1 - smooth(Yw, 344 * 0.42, 344 * 0.52)))
    return 1 - 0.72 * blur(zone.astype(np.float32), 10 * S)


def layers():
    """For each drop: its wet and dry absorbance (how much light each channel loses), and its bloom field: how far
    the wet front has to travel to reach each point, warped so the front is ragged, never a circle."""
    base = Paper(seed=500)
    base.finish()
    paper = base.img.copy()
    out = []
    for i, (t0, (cx, cy), (rx, ry), rot, col, d) in enumerate(DROPS):
        p = Paper(seed=600 + i)
        c, s_ = math.cos(rot), math.sin(rot)
        dx, dy = Xw - cx, Yw - cy
        u, v = (dx * c + dy * s_) / rx, (-dx * s_ + dy * c) / ry
        r = np.sqrt(u * u + v * v)
        r = r + 0.22 * (fbm(46, 700 + i) - 0.5) + 0.07 * (fbm(16, 720 + i) - 0.5)   # a lobed edge, not fur
        shape = np.clip((1.0 - r) * 40, 0, 1).astype(np.float32)
        shape = p.rough(shape, 0.8, 8, fine=0.25)
        wet = Paper(seed=600 + i)
        wet.wash(p.soften(shape, 1.6), col, d, rim=0.15, flow=0.45, blotch=0.12)
        dry = Paper(seed=600 + i)
        dry.wash(shape, col, d * 1.02, rim=1.6, rimw=1.1, flow=0.4, blotch=0.1)
        a_wet = -np.log(np.clip(wet.img / paint.PAPER, 1e-4, 1))
        a_dry = -np.log(np.clip(dry.img / paint.PAPER, 1e-4, 1))
        out.append((t0, a_wet.astype(np.float32), a_dry.astype(np.float32), np.clip(r, 0, 3).astype(np.float32)))
        print("painted drop", i, flush=True)
    return paper.astype(np.float32), out


def frame(t, paper, drops, veil):
    total = np.zeros((H, W, 3), np.float32)
    for t0, a_wet, a_dry, r in drops:
        u = (t - t0) % PERIOD
        if u > LIFE:
            continue
        front = ease(u / BLOOM) * 1.12                         # the wet front's reach, in drop radii
        reveal = np.clip((front - r) / 0.05, 0, 1)            # the wet front's edge
        dry = float(smooth(u, DRY_AT, DRY_AT + DRY_LEN))
        wash = float(smooth(u, WASH_AT, LIFE))                 # washed back toward the paper
        strength = (1 - wash) * float(smooth(u, 0, 0.8))       # a drop lands; nothing pops in
        if strength <= 0.001:
            continue
        w = (reveal * strength * veil)[..., None]
        total += w * ((1 - dry) * a_wet + dry * a_dry)
    img = paper * np.exp(-total)
    return (np.clip(img, 0, 1) * 255).astype(np.uint8)


if __name__ == "__main__":
    from PIL import Image
    preview = "--preview" in sys.argv
    paper, drops = layers()
    veil = type_veil().astype(np.float32)[..., None][..., 0]
    os.makedirs("out/loop", exist_ok=True)
    n = int(PERIOD * FPS)
    step = 30 if preview else 1
    for k in range(0, n, step):
        Image.fromarray(frame(k / FPS, paper, drops, veil)).save(f"out/loop/frame_{k:04d}.png")
    # the poster (and the reduced-motion still): a moment with several drops at different stages
    Image.fromarray(frame(33.0, paper, drops, veil)).save("out/blank-poster.png")
    print("frames", n, "step", step)
