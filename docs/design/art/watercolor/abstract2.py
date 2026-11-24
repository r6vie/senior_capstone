"""Watercolour covers, the abstract set, second four (Josef, 2026-11-23: "create 4 new gorgeous original covers").
Same language as abstract.py: big wet patches with pooled rims, flat fills, simple silhouettes, painted to the top,
the title's ink chosen from the paint (ink.py), the title area (world x 18-200, y 20-175) kept to calm sky. Each one
is a feeling the set does not have yet: a city at night, spring blossom, a prairie storm, a beach at sunset.

python3 abstract2.py [city|blossom|prairie|beach ...] -> out/<name>-xl.png and out/<name>-sm.png"""
import math
import sys
import numpy as np
sys.path.insert(0, ".")
from paint import Paper, ramp_y, ramp_x, blur, S, W, H
from abstract import (ULTRA, CERUL, PAYNE, SIENNA, RAW, ROSE, SAP, OLIVE, UMBER, TERRA, VIOLET, APRICOT, SAGE, TEAL,
                      CYPRESS, MAUVE, LEMON, Xw, Yw, ridge, band, sky)

INDIGO = "#4B4F86"
CORAL = "#EFA48A"
BLUSH = "#F2C4C6"
PINK = "#E6A7B8"
TURQ = "#6FB8B4"
SLATE = "#7C8296"
GOLDEN = "#EDC66E"


def y_at(line, x):
    return float(np.interp(x, [q[0] for q in line], [q[1] for q in line]))


def city():
    """A city at night on its river: an indigo sky with a warm glow low on the horizon; towers in loose blue and
    violet glazes, taller toward the right, nearer ones darker; a few lit windows in warm clusters, not a grid; the
    river holding long broken streaks of the lights."""
    p = Paper(seed=81)
    rng = np.random.default_rng(82)
    sky(p, [INDIGO, PAYNE, MAUVE, APRICOT], [(0, 220, 1.0, 0.0, 1.35), (0, 150, 1.0, 0.0, 0.6),
                                            (140, 236, 0.0, 1.0, 0.8), (190, 250, 0.0, 1.0, 1.1)])
    river_y = 278
    # far towers, pale and violet, one glaze each
    far = np.zeros((H, W), np.float32)
    for x, w, h in [(-6, 22, 34), (14, 16, 48), (30, 24, 28), (52, 14, 56), (64, 22, 40), (90, 18, 30), (106, 12, 62),
                    (122, 26, 44), (150, 16, 70), (168, 24, 50), (196, 18, 96), (214, 30, 76)]:
        far = np.maximum(far, p.poly([(x, river_y), (x, river_y - h), (x + w, river_y - h), (x + w, river_y)]))
    far = p.rough(far, 0.5, 4, fine=0.4)
    p.loose(far, [VIOLET, MAUVE, VIOLET], 0.6, n=6, rough=0.4, patch=0.3, ground=0.7)
    # near towers, deeper blue, the tallest on the right
    near = []
    # near towers with setbacks and one spire, so the skyline is not a row of boxes; tallest on the right
    for x, w, h, step in [(-8, 44, 20, 0), (24, 12, 36, 0), (40, 20, 24, 0), (96, 40, 18, 0), (130, 10, 30, 0),
                          (152, 18, 58, 12), (168, 26, 80, 0), (200, 22, 132, 26), (222, 20, 100, 14), (186, 14, 46, 0)]:
        top = river_y - h
        pts = [(x, river_y + 1), (x, top + step), (x + w * 0.2, top + step), (x + w * 0.2, top), (x + w * 0.8, top),
               (x + w * 0.8, top + step), (x + w, top + step), (x + w, river_y + 1)] if step else \
              [(x, river_y + 1), (x, top), (x + w, top), (x + w, river_y + 1)]
        m = p.rough(p.poly(pts), 0.5, 4, fine=0.4)
        if h > 120:                                             # the spire on the tallest
            m = np.maximum(m, p.rough(p.poly([(x + w * 0.45, top), (x + w * 0.5, top - 18), (x + w * 0.55, top)]),
                                      0.2, 2))
        near.append((x, w, h, m))
    nm = np.clip(np.maximum.reduce([n[3] for n in near]), 0, 1)
    p.loose(nm, [INDIGO, ULTRA, MAUVE, INDIGO], 0.85, n=8, rough=0.4, patch=0.25, ground=0.8)
    for x, w, h, m in near:                                     # each tower's right face turned from the glow, soft
        p.wash(m * p.soften(p.poly([(x + w * 0.62, 0), (x + w + 4, 0), (x + w + 4, 360), (x + w * 0.62, 360)]), 1.6),
               PAYNE, 0.5, rim=0)
    p.lift(p.soften(p.ellipse(211, 166, 26, 40), 8) * (1 - nm), 0.25)   # the tallest tower catches the last glow
    p.wash(near[7][3] * ramp_y(146, 278, 0.0, 1.0) * ramp_x(200, 216, 1.0, 0.0), APRICOT, 0.5, rim=0)
    # lit windows: warm dabs lifted out of the blue, in a few clusters on most towers
    for x, w, h, m in near:
        if rng.random() < 0.2:
            continue
        cy = river_y - rng.uniform(0.3, 0.7) * h
        for k in range(int(rng.integers(4, 9))):
            wx = x + rng.uniform(0.18, 0.8) * w
            wy = cy + rng.uniform(-0.18, 0.18) * h
            d = p.rough(p.ellipse(wx, wy, 1.1, 1.5), 0.15, 1, fine=0.1) * m
            p.lift(d, 0.85)
            p.wash(d, str(rng.choice([APRICOT, LEMON, GOLDEN])), 0.9, rim=0.8)
    # the river: dark patches, the glow and the lights as long soft vertical streaks broken by ripples
    river = p.rough(p.poly([(-20, river_y + 1), (260, river_y + 1), (260, 360), (-20, 360)]), 0.2, 12, fine=0.1)
    p.wash(river, INDIGO, 0.8, rim=0.4, flow=0.4, blotch=0.06, vary=ramp_y(262, 344, 0.7, 1.3))
    p.loose(river, [MAUVE, INDIGO, VIOLET], 0.35, n=7, rough=0.6, patch=0.22, ground=0.3)
    for cx, cy, rx in [(60, 292, 40), (150, 300, 34), (40, 318, 28)]:     # the sky's peach caught in the water
        pk = p.soften(p.rough(p.ellipse(cx, cy, rx, 3.5), 1.0, 10), 1.0) * river
        p.lift(pk, 0.3)
        p.wash(pk, APRICOT, 0.5, rim=0)
    # the lights in the water: three broken, wobbling smears fading with depth, the brightest under the tall tower
    for x, w, c, d, n in [(58, 5, APRICOT, 0.7, 4), (166, 5, GOLDEN, 0.7, 5), (211, 9, LEMON, 0.95, 7)]:
        for seg in range(n):
            if rng.random() < 0.2:
                continue
            y0 = river_y + 4 + seg * 11 + rng.uniform(-2, 2)
            ln = rng.uniform(4, 8)
            sw = w * (1 - seg * 0.08) * rng.uniform(0.6, 1.3)
            st = p.soften(p.rough(p.ellipse(x + rng.uniform(-3, 3), y0, sw / 2, ln / 2), 0.8, 3), 0.6) * river
            p.lift(st, 0.55 * (1 - seg * 0.1))
            p.wash(st, c, d * (1 - seg * 0.1), rim=0.4)
    p.wash(p.soften(p.poly([(-20, river_y + 1), (260, river_y + 1), (260, river_y + 5), (-20, river_y + 5)]), 1.0)
           * river, MAUVE, 0.6, rim=0)                                        # the glow on the water's edge
    p.finish()
    return p


def blossom():
    """Spring: a pale blush sky; one great blossom tree leaning in from the right, its crown a cloud of pink and
    mauve patches with paper between them; soft blue hills far off; a still pond holding the pink; a bank of fresh
    green and a few fallen petals gathered at the water."""
    p = Paper(seed=91)
    rng = np.random.default_rng(92)
    sky(p, [BLUSH, LEMON, CERUL], [(0, 240, 0.5, 1.0, 0.45), (120, 240, 0.0, 1.0, 0.3), (0, 120, 0.6, 0.0, 0.25)])
    hills = p.rough(p.poly(band(ridge(-20, 260, 236, [(6, 160, 0.4), (3, 60, 2.0)]))), 0.5, 10, fine=0.3)
    p.loose(hills, [CERUL, VIOLET, CERUL], 0.6, n=4, rough=0.5, patch=0.4)
    ground_top = ridge(-20, 260, 252, [(3, 220, 1.2), (2, 70, 0.4)])
    ground = p.rough(p.poly(band(ground_top)), 0.5, 10, fine=0.3)
    p.loose(ground, [SAGE, SAP, LEMON, SAGE], 0.8, n=6, rough=0.8, patch=0.35, ground=0.7)
    # the pond: a wide oval of cool water, the pink of the crown lying in it
    pond = p.rough(p.ellipse(84, 304, 84, 16), 3.5, 18, fine=0.5)      # an irregular shore, no paper rim
    p.loose(pond, [CERUL, TEAL], 0.7, n=2, rough=0.6, patch=0.7, ground=0.8)
    p.wash(p.soften(p.ellipse(150, 300, 50, 9), 3) * pond, PINK, 0.6, rim=0, flow=0.5)
    p.wash(p.soften(p.ellipse(92, 290, 94, 5), 2) * pond, SAP, 0.4, rim=0)              # the far bank in the water
    # the trunk rooted in the grass on the right, leaning in, its limbs reaching left and up into the crown
    trunk = p.rough(p.poly([(196, 286), (202, 270), (198, 248), (190, 224), (184, 206), (192, 204), (202, 222),
                            (212, 246), (218, 268), (226, 286)]), 0.8, 4, fine=0.4)     # tapering, flaring at the root
    limbs = np.maximum.reduce([p.rough(p.stroke(pts, w), 0.5, 3, fine=0.3) for pts, w in
                               [([(196, 222), (172, 212), (156, 210)], 4.5), ([(192, 210), (204, 186), (222, 164)], 4)]])
    wood = np.clip(np.maximum(trunk, limbs), 0, 1)
    p.wash(p.soften(p.ellipse(216, 287, 18, 3), 1.2) * ground, CYPRESS, 0.6, rim=0)

    # the crown: big soft clouds of blossom, overlapping, paper left between them; clear of the title's corner
    crown = np.zeros((H, W), np.float32)
    for cx, cy, rx, ry in [(208, 188, 36, 28), (232, 158, 24, 26), (180, 202, 28, 18), (224, 210, 28, 18),
                           (200, 162, 20, 16), (154, 212, 24, 12), (238, 196, 16, 22), (190, 222, 26, 10),
                           (162, 196, 24, 16), (132, 210, 20, 10), (240, 226, 18, 14), (176, 222, 20, 10)]:
        crown = np.maximum(crown, p.rough(p.ellipse(cx, cy, rx, ry), ry * 0.3, max(4, rx * 0.4), fine=0.6))
    p.loose(crown, [PINK, BLUSH, MAUVE, BLUSH, PINK], 0.95, n=16, rough=0.8, patch=0.2, ground=0.55)
    # volume: the crown lit on its upper left, turning mauve toward its lower right
    p.lift(crown * p.soften(p.ellipse(194, 168, 30, 18), 8), 0.3)
    p.wash(crown * np.clip(ramp_y(160, 232, 0.0, 1.0) * 0.6 + ramp_x(170, 240, 0.0, 1.0) * 0.6, 0, 1), MAUVE, 0.7,
           rim=0, flow=0.5)
    # the wood over it, vanishing into the blossom: full below the crown, gone inside it
    show = np.clip(1 - blur(crown, 1.5 * S) * 1.5, 0, 1)
    p.wash(wood * show, UMBER, 1.3, rim=1.0, blotch=0.06)
    p.wash(wood * show * ramp_x(204, 246, 0.0, 1.0), PAYNE, 0.6, rim=0)
    # its shadow on the grass, and a drift of petals gathered at the water's edge
    anchor = p.rough(p.poly([(-20, 318), (40, 312), (90, 326), (120, 352), (-20, 352)]), 3, 14, fine=0.5)
    p.loose(anchor, [CYPRESS, VIOLET, SAP], 0.9, n=4, rough=0.9, patch=0.45, ground=0.75)   # the near dark
    p.finish()
    return p


def barn(p, x, base, w, h, d, walls, roof, ground=None):
    """A barn three-quarter on, the gable toward us and lit under a gambrel roof, the side turning into shade."""
    a = w * 0.55
    sk = d * 0.08
    gable = [(x, base), (x - 0.3, base - h), (x + w * 0.14, base - h - a * 0.62), (x + w / 2, base - h - a),
             (x + w * 0.86, base - h - a * 0.62), (x + w + 0.3, base - h), (x + w, base)]
    side = [(x + w, base), (x + w + 0.3, base - h), (x + w + d, base - h - sk), (x + w + d - 0.3, base - sk)]
    rf = [(x + w / 2 - 0.6, base - h - a - 0.5), (x + w / 2 + d, base - h - a - sk - 0.5), (x + w + d + 1.6, base - h - sk + 1),
          (x + w + 0.8, base - h + 1.2)]
    gm, sm, rm = (p.rough(p.poly(q), 0.5, 3, fine=0.4) for q in (gable, side, rf))
    if ground is not None:
        p.wash(p.soften(p.poly([(x + 1, base - 0.5), (x + w + d, base - sk - 0.5), (x + w + d + 16, base + 2.5),
                                (x + 6, base + 2.5)]), 0.8) * ground, PAYNE, 0.6, rim=0)   # its shadow, from its foot
    p.lift(np.clip(blur(np.maximum.reduce([gm, sm, rm]), 0.3 * S) * 1.4, 0, 1), 0.85)
    p.loose(gm, walls, 0.9, n=2, rough=0.3, patch=0.7, ground=0.7)
    p.loose(sm, walls, 0.9, n=2, rough=0.3, patch=0.7, ground=0.7)
    p.wash(sm, PAYNE, 0.7, rim=0.8)
    p.wash(rm, roof, 1.1, rim=1.0)


def prairie():
    """A prairie storm: a slate sky, a great storm cloud towering on the right in violet and grey patches with a
    lit gold rim, a veil of rain beneath it; low light breaking gold on the left horizon; the prairie in long golden
    patches; a small rust barn and a windbreak of trees under the light; a road running straight to the horizon."""
    p = Paper(seed=101)
    rng = np.random.default_rng(102)
    sky(p, [SLATE, PAYNE, VIOLET, GOLDEN], [(0, 240, 1.0, 0.25, 1.4), (0, 190, 1.0, 0.0, 0.9),
                                           (120, 230, 0.0, 1.0, 0.4), (200, 244, 0.0, 1.0, 0.8)],
        mask=np.clip(1 - p.soften(p.poly([(-20, 230), (170, 234), (170, 246), (-20, 246)]), 6) * 0.5, 0, 1))
    glow = p.soften(p.poly([(-20, 230), (170, 234), (170, 246), (-20, 246)]), 6) * (Yw < 246)
    p.wash(glow, GOLDEN, 0.7, rim=0)                                    # the light breaking low, in the sky only
    # the storm cloud: a tower of patches on the right, its top catching gold, its belly dark
    cloud = np.zeros((H, W), np.float32)
    # an anvil on a tower, rising from a broad base on the horizon
    for cx, cy, rx, ry in [(232, 84, 26, 12), (232, 112, 20, 24), (234, 144, 22, 26), (226, 176, 26, 24),
                           (236, 194, 32, 24), (200, 212, 40, 18), (222, 226, 56, 20), (162, 230, 40, 14)]:
        cloud = np.maximum(cloud, p.ellipse(cx, cy, rx, ry))
    cloud = p.rough(np.clip(blur(cloud, 3 * S) * 1.6, 0, 1), 3, 14, fine=0.6)     # one mass, billowing at the edge
    cloud = cloud * np.clip(1 - p.soften(p.poly([(-20, -20), (196, -20), (196, 186), (-20, 186)]), 7), 0, 1)
    p.lift(cloud * ramp_y(70, 120, 0.6, 0.0), 0.5)
    p.loose(cloud, [VIOLET, SLATE, MAUVE, SLATE], 0.85, n=5, rough=1.2, patch=0.55, ground=0.75,
            vary=ramp_y(70, 200, 0.6, 1.3))
    p.wash(cloud * ramp_y(70, 110, 1.0, 0.0) * ramp_x(180, 240, 1.0, 0.4), GOLDEN, 0.6, rim=0)
    rain = p.soften(p.poly([(182, 228), (250, 226), (244, 248), (170, 248)]), 5)      # one soft slanting veil
    p.wash(rain, SLATE, 0.6, rim=0, flow=0.6)
    # the prairie: long golden patches to the horizon, deeper toward us
    hz = 246
    land = p.rough(p.poly([(-20, hz), (260, hz - 1), (260, 360), (-20, 360)]), 0.3, 12, fine=0.2)
    p.wash(land, GOLDEN, 0.6, rim=0.4, flow=0.4)                      # one ground wash first, so no seams show
    for y0, y1, cols, tilt in [(hz, 258, [GOLDEN, RAW], 2), (254, 284, [RAW, SAGE, GOLDEN], -6),
                               (278, 320, [GOLDEN, OLIVE, RAW], 8), (312, 360, [OLIVE, SIENNA, GOLDEN], -4)]:
        b = p.rough(p.poly([(-20, y0), (260, y0 + tilt), (260, y1 + tilt), (-20, y1)]), 2.5, 20, fine=0.4)
        p.loose(b * land, cols, 0.85, n=4, rough=0.9, patch=0.4, ground=0.7)
    p.wash(land * ramp_x(120, 260, 0.0, 1.0) * ramp_y(hz, 300, 1.0, 0.3), SLATE, 0.5, rim=0)   # the storm's shade
    # the road, straight to the horizon, a pale wash narrowing away
    track = p.soften(p.rough(p.poly([(97, hz + 2), (101, hz + 2), (114, 300), (130, 360), (78, 360), (88, 300)]),
                             2.0, 10, fine=0.4), 1.2) * land          # one soft pale wash, tapering away
    p.lift(track, 0.25)
    p.wash(track, APRICOT, 0.6, rim=0.4)
    # the windbreak and the barn under the light, left of the road
    trees = np.zeros((H, W), np.float32)
    for x, r in [(22, 8), (32, 10), (44, 7), (54, 9)]:
        trees = np.maximum(trees, p.rough(p.ellipse(x, hz - r * 0.7, r, r * 0.9), r * 0.3, 3, fine=0.5))
    p.loose(trees, [CYPRESS, OLIVE, CYPRESS], 1.2, n=4, rough=0.5, patch=0.4, ground=0.8)
    barn(p, 58, hz + 4, 17, 11, 20, [SIENNA, UMBER], PAYNE, ground=land)
    p.finish()
    return p


def beach():
    """A beach at sunset (recoloured, Josef: "less all-orange and more gorgeous"): an indigo and mauve dusk melting
    through pink to a peach glow on the horizon, the sun half sunk on the horizon; the sea turquoise near and
    deep blue far, a broad path of light on it; waves as pale lifted bands; warm sand in wide patches; two palms
    leaning in from the right, their fronds a few long dark strokes; dune grass in clumps."""
    p = Paper(seed=111)
    rng = np.random.default_rng(112)
    hz = 214
    # the dusk palette below the horizon: the sea and sand take their light from the sky, the palms go dark
    DEEP, DUSKBLUE, AQUA, BLUSHSEA = "#3E4F7A", "#5E7FA2", "#8FB3B8", "#C99AA8"
    PEACH, ROSEGOLD, CORALG, CREAM, NIGHT, LAVSAND = ("#F6D2A8", "#F2B8A0", "#E99A8E", "#FBE3B8", "#3A3150",
                                                      "#D8C4CC")
    sun = p.rough(p.ellipse(104, hz + 6, 24, 24), 0.3, 4, fine=0.2) * (Yw < hz)     # large, sinking
    # lighter (Josef: "a little less dark, a little more light and orange in the sky, keep some violet but less
    # night"): a soft violet dusk at the top, warming through coral to a peach glow that climbs high
    sky(p, [INDIGO, MAUVE, CORALG, PEACH], [(0, 120, 0.7, 0.0, 0.3), (0, 214, 1.0, 0.3, 0.6),
                                           (40, 200, 0.0, 1.0, 0.7), (100, 214, 0.0, 1.0, 0.85)],
        mask=np.clip(1 - sun, 0, 1) * p.soften(p.poly([(-20, -20), (260, -20), (260, hz + 1), (-20, hz + 1)]), 0.6))
    # the sky stops at the horizon, so its pinks and peach don't muddy the sea and sand
    p.wash(p.soften(p.ellipse(104, hz - 2, 40, 22), 10) * (1 - sun) * (Yw < hz), APRICOT, 0.45, rim=0)   # its halo
    p.wash(sun, CREAM, 0.9, rim=1.4)
    # sunset-lit clouds (Josef: "add some sunset illuminated clouds"): long low banks, violet bodies whose undersides
    # catch the sun in coral and gold, brightest nearest it; under the title on the left, higher only at the right edge
    for cx, by_, ln, th, glow in [(26, 190, 64, 15, 1.0), (176, 176, 80, 19, 0.9), (228, 138, 44, 17, 0.7),
                                  (196, 200, 56, 8, 1.0), (236, 104, 30, 11, 0.5)]:
        crng = np.random.default_rng(int(cx * 7 + by_))
        c = np.zeros((H, W), np.float32)
        for k in range(7):                                       # a bank of soft puffs on a flat base
            px = cx + (k / 6 - 0.5) * ln * 1.6 + crng.uniform(-3, 3)
            rx = ln * crng.uniform(0.2, 0.32)
            ry = th * crng.uniform(0.45, 0.75) * (1 - abs(k / 6 - 0.5) * 0.8)
            c = np.maximum(c, p.ellipse(px, by_ - ry * 0.7, rx, ry))
        c = p.rough(c * (Yw < by_ + 1.5), th * 0.12, 8, fine=0.6)
        y0, y1 = by_ - th, by_ + 1
        p.wash(c, VIOLET, 0.55, rim=1.2, flow=0.5, blotch=0.08)
        p.wash(c * ramp_y(y0, y1, 1.0, 0.0), MAUVE, 0.35, rim=0)                   # the tops in shade
        lit = c * ramp_y(y0 + th * 0.2, y1 - th * 0.2, 0.0, 1.0)
        p.lift(lit * glow, 0.85)
        p.wash(lit, CORALG, 0.9 * glow, rim=0.7)                                     # the undersides alight
        p.wash(lit * ramp_y(y0 + th * 0.55, y1, 0.0, 1.0), PEACH, 1.0 * glow, rim=0)
    bar = p.soften(p.rough(p.stroke([(40, hz - 10), (110, hz - 12), (190, hz - 9)], 4), 1.5, 12), 1.0)
    p.wash(bar, VIOLET, 0.8, rim=0.6)                                    # a cloud bar across the sun
    p.wash(bar * ramp_y(hz - 14, hz - 6, 1.0, 0.0), PINK, 0.5, rim=0)        # its top lit pink
    sea = p.rough(p.poly([(-20, hz), (260, hz), (260, 276), (-20, 270)]), 0.2, 12, fine=0.1)
    p.loose(sea, [DUSKBLUE, DEEP, DUSKBLUE], 0.6, n=4, rough=0.5, patch=0.5, ground=0.9,
            vary=ramp_y(hz, 276, 1.3, 0.5))
    p.wash(sea * ramp_y(hz, hz + 22, 1.0, 0.0), DEEP, 0.7, rim=0)              # deep at the horizon
    p.wash(sea * ramp_y(hz + 30, 276, 0.0, 1.0), AQUA, 0.5, rim=0)             # muted aqua only in the shallows
    for cx, cy, rx in [(62, hz + 14, 22), (150, hz + 20, 26)]:                  # the sky's blush beside the path
        p.wash(p.soften(p.rough(p.ellipse(cx, cy, rx, 4), 1, 8), 2) * sea, BLUSHSEA, 0.5, rim=0)
    path = p.soften(p.poly([(96, hz), (112, hz), (134, 276), (74, 276)]), 3) * sea      # under the sun at x 104
    # the path as broken horizontal dashes of peach and rose gold, lifted to paper first so no yellow greens the blue
    dashes = np.zeros((H, W), np.float32)
    for k in range(14):
        y = hz + 3 + k * 4.2 + rng.uniform(-1, 1)
        half = 6 + (y - hz) * 0.45
        for _ in range(2):
            x0 = 104 + rng.uniform(-half, half * 0.3)
            dashes = np.maximum(dashes, p.rough(p.ellipse(x0 + half * 0.35, y, half * rng.uniform(0.35, 0.7), 1.3),
                                                0.4, 4, fine=0.3))
    dashes = dashes * path * sea
    p.lift(np.clip(dashes * 1.2, 0, 1), 0.9)
    p.wash(dashes, PEACH, 0.8, rim=0.6)
    p.wash(dashes * ramp_y(hz, 276, 0.0, 1.0), ROSEGOLD, 0.6, rim=0)
    for x0, x1, y0 in [(-20, 70, 244), (150, 260, 238), (20, 200, 258)]:    # swells, soft and lighter, broken
        wv = p.soften(p.rough(p.stroke([(x0, y0), ((x0 + x1) / 2, y0 + 1), (x1, y0 - 0.5)], 3.5), 1.0, 14), 1.2) * sea
        p.wash(wv, DUSKBLUE, 0.4, rim=0)
    shore = ridge(-20, 260, 274, [(3, 140, 0.6)])
    for x0, x1 in [(-20, 40), (70, 150), (176, 220)]:          # foam in broken soft runs, not a ruled line
        seg = [(x, y - 1.5) for x, y in shore if x0 <= x <= x1]
        if len(seg) > 1:
            p.lift(p.soften(p.rough(p.stroke(seg, 2.4), 0.8, 8), 0.8), 0.5)
    sand = p.rough(p.poly(band(shore)), 0.6, 12, fine=0.3)
    p.loose(sand, [LEMON, BLUSH, PEACH], 0.4, n=5, rough=0.8, patch=0.45, ground=0.75)   # pale, pink-lit sand
    p.wash(sand * ramp_y(296, 344, 0.0, 1.0), VIOLET, 0.5, rim=0, flow=0.5)          # the near sand cooler
    p.wash(sand * ramp_y(310, 344, 0.0, 1.0), MAUVE, 0.35, rim=0, flow=0.5)
    # two palms leaning in from the right, the trunks curved, the fronds long tapered strokes
    # two palms: each trunk a strong bow, thick at the foot and tapering, each crown a fountain of long crescent
    # leaves, broad in the middle, arching up and over and drooping to a fine tip
    def frond(tx, ty, ang, l, wmax):
        sx, sy = math.cos(math.radians(ang)), math.sin(math.radians(ang))
        cen = [(tx + sx * l * t, ty + sy * l * t * 0.9 + l * 0.75 * t * t) for t in np.linspace(0, 1, 14)]
        left, right = [], []
        for i, (cx, cy) in enumerate(cen):
            t = i / (len(cen) - 1)
            nx0, ny0 = cen[min(i + 1, len(cen) - 1)][0] - cen[max(i - 1, 0)][0], \
                cen[min(i + 1, len(cen) - 1)][1] - cen[max(i - 1, 0)][1]
            n = math.hypot(nx0, ny0) or 1
            nx, ny = -ny0 / n, nx0 / n
            w = wmax * math.sin(math.pi * min(1.0, t * 1.15)) ** 0.7 * (1 - 0.35 * t) + 0.4
            left.append((cx + nx * w * 0.55, cy + ny * w * 0.55))           # the upper edge narrower,
            right.append((cx - nx * w, cy - ny * w))                         # the leaflets hang below
        return p.poly(left + right[::-1])

    # both palms on the right: the tall one bowing left over the beach, a smaller one leaning right behind it
    for pts, w0, s, seed in [([(232, 356), (236, 320), (230, 282), (214, 244), (192, 212), (174, 198)], 9.0, 1.15, 0),
                             ([(184, 356), (180, 330), (184, 302), (194, 276), (206, 254)], 6.0, 0.8, 1)]:
        wood = np.zeros((H, W), np.float32)
        for i in range(len(pts) - 1):
            ww = w0 * (1 - 0.6 * i / (len(pts) - 1))
            wood = np.maximum(wood, p.stroke([pts[i], pts[i + 1]], ww, taper=False))
        wood = p.rough(wood, 0.5, 6, fine=0.3)
        p.loose(wood, [NIGHT, PAYNE, NIGHT], 1.5, n=3, rough=0.3, patch=0.5, ground=0.9)   # dark against the glow
        bx, by = pts[0]
        p.wash(p.soften(p.ellipse(bx - 34 * s, by - 6, 40 * s, 4), 1.5) * sand, LAVSAND, 1.0, rim=0)
        tx, ty = pts[-1]
        # the crown: each leaf one tapered brushstroke that rises out of the top, arches and droops to a point;
        # the leaves are one dark wet silhouette with a little lighter green dropped into the upper ones
        lr = np.random.default_rng(300 + seed)
        fr = np.zeros((H, W), np.float32)
        for ang, ln in [(-172, 44), (-146, 38), (-118, 26), (-90, 16), (-62, 26), (-34, 38), (-8, 44),
                        (160, 34), (20, 34)]:
            a = math.radians(ang + lr.uniform(-5, 5))
            l = ln * s * lr.uniform(0.9, 1.1)
            sx, sy = math.cos(a), math.sin(a)
            line = [(tx + sx * l * t, ty + sy * l * t * 0.85 + l * 0.6 * t ** 2) for t in np.linspace(0, 1, 9)]
            fr = np.maximum(fr, p.stroke(line, 5.2 * s, taper=True))
        fr = p.rough(fr, 0.5, 2.5, fine=0.7)
        p.wash(fr, NIGHT, 1.5, rim=1.4, flow=0.5, blotch=0.08)
        p.wash(fr * ramp_y(ty - 20, ty + 6, 1.0, 0.0), CYPRESS, 0.5, rim=0)       # a hint of green on top
        p.wash(fr * ramp_y(ty, ty + 40, 0.0, 1.0), PAYNE, 0.6, rim=0)
    p.finish()
    return p


SCENES = {"city": city, "blossom": blossom, "prairie": prairie, "beach": beach}

if __name__ == "__main__":
    for name in sys.argv[1:] or SCENES:
        p = SCENES[name]()
        p.save(f"out/{name}-xl.png")
        p.save(f"out/{name}-sm.png", (352, 514))
