"""Watercolour covers, the abstract set (Josef, 2026-11-23: "prioritize abstraction with the watercolors like seen
here", pointing at the round 1 lighthouse headland, "much nicer than the full detail in the autumn"; "4 completely new
feeling covers").

The look: each region is a handful of large wet patches laid side by side and over each other, each drying with a
pooled rim; flat fills, no texture strokes, no small parts. Objects are single silhouettes. Painted to the top; the
title's ink is chosen from the paint (ink.py). Keep the title area (world x 18-200, y 20-175) to sky.

python3 abstract.py [mesa|hills|lake|winter ...] -> out/<name>-xl.png and out/<name>-sm.png"""
import math
import sys
import numpy as np
sys.path.insert(0, ".")
from paint import Paper, ramp_y, ramp_x, blur, S, W, H, XX, YY

ULTRA = "#5B74B8"
CERUL = "#7FB2D6"
PAYNE = "#4A5868"
SIENNA = "#C98A5A"
RAW = "#E6C487"
ROSE = "#E3A3A0"
SAP = "#8FB06A"
OLIVE = "#9A9A5C"
UMBER = "#8A6F5A"
TERRA = "#D9967A"
VIOLET = "#B4A9CC"
APRICOT = "#F0C59A"
SAGE = "#A9BC93"
TEAL = "#78A9A6"
CYPRESS = "#56705A"
MAUVE = "#B596B2"
LEMON = "#F2E2A8"

Xw, Yw = XX / S, YY / S


def ridge(x0, x1, base, waves, n=40):
    """A hill line as a list of points: base height plus a few sine swells (amp, period, phase)."""
    pts = []
    for i in range(n + 1):
        x = x0 + (x1 - x0) * i / n
        y = base + sum(a * math.sin(2 * math.pi * x / per + ph) for a, per, ph in waves)
        pts.append((x, y))
    return pts


def band(top, bottom=360):
    """The area under a ridge line, to the bottom of the cover."""
    return top + [(top[-1][0], bottom), (top[0][0], bottom)]


def sky(p, cols, stops, mask=None):
    """A wet-in-wet sky: one wash per colour, each strongest at its own height and melting into the next."""
    full = np.ones((H, W), np.float32) if mask is None else mask
    for c, (y0, y1, a, b, d) in zip(cols, stops):
        p.wash(full, c, d, rim=0.2, flow=0.35, blotch=0.05, vary=ramp_y(y0, y1, a, b))


def mesa():
    """Desert at dusk: a deep cobalt sky melting to apricot on the horizon; one great flat-topped butte on the right
    in terracotta patches, its shaded flank violet; low far mesas; a desert floor of ochre patches with sage blobs."""
    p = Paper(seed=41)
    rng = np.random.default_rng(42)
    sky(p, [ULTRA, PAYNE, VIOLET, APRICOT], [(0, 240, 1.0, 0.15, 1.7), (0, 190, 1.0, 0.0, 0.9),
                                            (120, 230, 0.0, 1.0, 0.7), (180, 250, 0.0, 1.0, 1.0)])
    # far mesas, pale and flat, one glaze each
    far = p.rough(p.poly([(-10, 258), (-10, 236), (22, 234), (26, 228), (70, 227), (76, 236), (118, 240), (124, 258)]),
                  0.5, 8, fine=0.3)
    p.loose(far, [VIOLET, ROSE, VIOLET], 0.8, n=4, rough=0.3, patch=0.45)
    # the butte: a sheer cap, a stepped skirt of talus; lit face, violet shade
    butte = p.rough(p.poly([(104, 262), (124, 248), (140, 238), (148, 190), (152, 184), (236, 181), (250, 182),
                            (250, 262)]), 0.6, 8, fine=0.35)
    p.wash(butte, APRICOT, 0.6, rim=1.2, flow=0.4)
    for y0, y1, cols in [(180, 214, [TERRA, SIENNA]), (214, 221, [APRICOT, ROSE]), (221, 262, [SIENNA, TERRA, ROSE])]:
        strat = p.rough(p.poly([(-20, y0), (260, y0 - 1), (260, y1), (-20, y1 + 1)]), 1.0, 14, fine=0.4) * butte
        p.loose(strat, cols, 0.9, n=3, rough=0.6, patch=0.55, ground=0.7)
    shade = p.rough(p.poly([(202, 181), (250, 180), (250, 262), (188, 262), (196, 226)]), 2.2, 9, fine=0.6)
    p.wash(shade * butte, VIOLET, 1.1, rim=1.6, flow=0.5, blotch=0.08)                # one shade glaze, ragged edge
    p.wash(p.rough(p.ellipse(214, 214, 16, 22), 3, 8, fine=0.6) * shade * butte, MAUVE, 0.6, rim=1.4, flow=0.5)
    p.wash(shade * butte * ramp_x(196, 250, 0.0, 1.0), UMBER, 0.45, rim=0, flow=0.4)
    p.wash(p.rough(p.poly([(148, 190), (152, 184), (236, 181), (236, 187), (152, 192)]), 0.4, 6) * butte, SIENNA, 0.9,
           rim=1.0)                                                                  # the lit rim of the cap
    # the floor: wide ochre and sienna patches, cooler and deeper toward us
    floor = p.rough(p.poly([(-20, 250), (260, 254), (260, 360), (-20, 360)]), 0.6, 10, fine=0.3)
    p.loose(floor, [RAW, APRICOT, RAW, TERRA], 0.8, n=5, rough=0.6, patch=0.5, ground=0.8)
    p.loose(p.rough(p.poly([(-20, 304), (100, 296), (260, 312), (260, 360), (-20, 360)]), 2, 16) * floor,
            [SIENNA, TERRA], 0.8, n=3, rough=0.6, patch=0.6, ground=0.7)
    # the butte's shadow thrown across the floor, and a dry wash curling toward us
    wash_bed = p.rough(p.stroke([(84, 262), (70, 280), (92, 300), (58, 326), (20, 352)], 7), 1.2, 8)
    p.wash(wash_bed * floor, APRICOT, 0.6, rim=1.4, flow=0.4)
    # sage and juniper as simple blobs, darker toward us
    for x, y, r, c in [(118, 272, 6, SAGE), (130, 276, 9, OLIVE), (44, 320, 11, OLIVE)]:
        p.wash(p.rough(p.ellipse(x + r * 0.9, y + r * 0.35, r * 1.3, r * 0.3), 0.6, 4) * floor, VIOLET, 0.8, rim=1.2)
        b = p.rough(p.ellipse(x, y, r, r * 0.55), r * 0.25, max(2, r * 0.5), fine=0.5)
        p.wash(b, c, 1.0, rim=1.4, flow=0.5, blotch=0.08)
        p.wash(b * ramp_x(x - r * 0.2, x + r, 0, 1), CYPRESS, 0.5, rim=0)
    p.finish()
    return p


def hills():
    """Rolling patchwork hills under a pale morning: field after field in greens, ochres and lavender, each hill's
    fields its own wet patches; a row of dark cypresses along one crest, a small white farmhouse among them."""
    p = Paper(seed=51)
    rng = np.random.default_rng(52)
    sky(p, [LEMON, APRICOT, VIOLET], [(0, 200, 0.6, 1.0, 0.45), (120, 220, 0.0, 1.0, 0.45), (0, 90, 1.0, 0.0, 0.25)])
    hills_def = [  # base, waves, field colours: far to near
        (214, [(8, 150, 0.6), (4, 70, 2.0)], [VIOLET, MAUVE, VIOLET]),
        (232, [(10, 190, 2.4), (5, 80, 0.8)], [SAGE, VIOLET, RAW, SAGE]),
        (258, [(12, 220, 4.0), (6, 90, 1.1)], [RAW, SAGE, APRICOT, SAP]),
        (292, [(14, 240, 1.0), (5, 100, 3.0)], [SAP, RAW, MAUVE, OLIVE, APRICOT]),
        (326, [(10, 260, 2.6), (6, 120, 0.4)], [OLIVE, CYPRESS, SIENNA, OLIVE]),
    ]
    tops = [ridge(-20, 260, base, waves) for base, waves, _ in hills_def]
    crest2 = tops[2]
    ms = [p.rough(p.poly(band(t)), 0.5, 10, fine=0.3) for t in tops]
    for i, (base, waves, cols) in enumerate(hills_def):
        # each hill only down to the next one's edge, a hair of paper between them, so glazes never stack to mud
        m = ms[i]
        if i + 1 < len(ms):
            m = np.clip(m - np.clip(blur(ms[i + 1], 0.5 * S) * 2.2, 0, 1), 0, 1)
        p.loose(m, cols, 0.7 + 0.06 * i, n=4 + i, rough=0.8, patch=0.32, ground=0.55)
    # cypresses on the third crest, unevenly spaced and sized; the farmhouse between them
    cx = [(194, 1.25), (201, 0.8), (150, 0.65)]
    def crest_y(x):
        return float(np.interp(x, [q[0] for q in crest2], [q[1] for q in crest2]))
    hx = 176
    hy = crest_y(hx)
    house = p.rough(p.poly([(hx - 8, hy + 3), (hx - 8, hy - 7), (hx + 7, hy - 7), (hx + 7, hy + 3)]), 0.25, 3)
    p.lift(house, 0.85)
    p.wash(house, APRICOT, 0.45, rim=1.0)
    p.wash(house * (Xw > hx + 1), MAUVE, 1.1, rim=0.8)
    p.wash(p.rough(p.poly([(hx - 9.5, hy - 6.5), (hx + 8.5, hy - 6.5), (hx + 6, hy - 10), (hx - 7, hy - 10)]), 0.2, 2),
           SIENNA, 1.1, rim=1.2)
    for x, s in cx:
        y = crest_y(x) + 2
        t = p.rough(p.ellipse(x, y - 15 * s, 3.2 * s, 16 * s), 0.5, 3, fine=0.4)
        p.wash(t, CYPRESS, 1.5, rim=1.3, flow=0.5, blotch=0.06)
        p.wash(t * ramp_x(x - 1, x + 3 * s, 0, 1), PAYNE, 0.8, rim=0)
        p.wash(p.rough(p.ellipse(x + 9 * s, y + 0.5, 9 * s, 1.8 * s), 0.5, 3), CYPRESS, 1.0, rim=1.0)   # its shadow
    p.finish()
    return p


def lake():
    """An alpine lake: a cool cerulean sky with clouds left as paper; one great peak on the right in angular patches,
    its snow the paper, its shade violet and ultramarine; a dark band of forest on the shore; the lake holding the
    peak upside down in softer patches, a pale streak of wind across it."""
    p = Paper(seed=61)
    rng = np.random.default_rng(62)
    clouds = np.zeros((H, W), np.float32)
    for x, y, rx, ry in [(222, 54, 22, 5)]:                       # one cloud, right of the title, a pooled pale glaze
        clouds = np.maximum(clouds, p.rough(p.ellipse(x, y, rx, ry), 2.5, 12, fine=0.6))
    sky(p, [CERUL, ULTRA], [(0, 200, 1.0, 0.45, 0.8), (0, 140, 1.0, 0.0, 0.35)], mask=np.clip(1 - clouds * 0.9, 0, 1))
    p.wash(clouds, VIOLET, 0.3, rim=1.6, flow=0.4)
    shore = 236
    # far range, pale, left
    far = p.rough(p.poly([(-20, shore), (-20, 206), (10, 196), (34, 204), (52, 190), (78, 206), (110, 214), (130, shore)]),
                  0.6, 6, fine=0.3)
    p.loose(far, [VIOLET, CERUL, VIOLET], 0.7, n=4, rough=0.3, patch=0.4)
    # the peak: faces cut by its ridges; the lit faces mostly paper with a whisper, the shaded faces deep
    # the massif: a long low left flank, a shoulder, the summit right of the title, a second summit beyond
    peak = [(96, shore), (136, 214), (166, 198), (182, 186), (190, 176), (198, 174), (204, 150), (210, 128), (216, 134),
            (226, 148), (236, 156), (246, 150), (254, 158), (260, 164), (260, shore)]
    pk = p.rough(p.poly(peak), 0.5, 6, fine=0.3)
    p.wash(pk, CERUL, 0.25, rim=1.2, flow=0.3)
    faces = [([(210, 128), (216, 134), (226, 148), (236, 156), (246, 150), (254, 158), (260, 164), (260, 236),
               (218, 236), (214, 180)], [VIOLET, ULTRA, MAUVE], 1.0),
             ([(166, 198), (186, 182), (198, 164), (204, 142), (200, 186), (170, 236), (126, 236)], [CERUL, VIOLET], 0.5),
             ([(200, 190), (208, 166), (222, 236), (180, 236)], [ULTRA, PAYNE, VIOLET], 0.9)]
    for pts, cols, d in faces:
        p.loose(p.rough(p.poly(pts), 0.8, 6, fine=0.4) * pk, cols, d, n=4, rough=0.4, patch=0.45)
    # the forest on the shore: one dark band with a ragged top, the trees only its silhouette
    forest = np.zeros((H, W), np.float32)
    for x0, x1, hgt in [(-20, 70, 14), (60, 170, 9), (160, 260, 12)]:       # three dark masses, uneven tops
        pts = [(x0, shore + 4)]
        for i in range(9):
            x = x0 + (x1 - x0) * i / 8
            pts.append((x, shore - hgt * (0.55 + 0.45 * math.sin(i * 1.7 + x0)) - (4 if i in (2, 6) else 0)))
        pts.append((x1, shore + 4))
        forest = np.maximum(forest, p.poly(pts))
    forest = p.rough(forest, 1.5, 6, fine=0.5)
    p.loose(forest, [CYPRESS, TEAL, PAYNE], 1.3, n=5, rough=0.6, patch=0.4, ground=0.8)
    # the lake: teal patches, deeper toward us; the peak mirrored in softer glazes; a pale wind streak
    lake_m = p.rough(p.poly([(-20, shore + 3), (260, shore + 3), (260, 360), (-20, 360)]), 0.3, 10, fine=0.2)
    p.loose(lake_m, [TEAL, CERUL, TEAL, ULTRA], 0.9, n=8, rough=0.4, patch=0.35, ground=0.7,
            vary=ramp_y(shore, 344, 0.7, 1.3))
    # the massif upside down, simplified and softer; its shaded faces darker in the water too
    flip = lambda pts: [(x, 2 * (shore + 3) - y) for x, y in pts]
    refl = p.soften(p.rough(p.poly(flip(peak)), 2.5, 10, fine=0.4), 2.5) * lake_m
    p.loose(refl, [VIOLET, ULTRA, VIOLET], 0.6, n=4, rough=1.0, patch=0.4, ground=0.6)
    p.wash(p.soften(p.poly([(-20, shore + 3), (260, shore + 3), (260, shore + 16), (-20, shore + 14)]), 2) * lake_m,
           CYPRESS, 0.9, rim=0)                                                         # the forest in the water
    for x0, y0, w in [(34, 296, 30), (96, 300, 14), (150, 292, 22)]:              # a few broken glints of wind
        p.lift(p.rough(p.poly([(x0, y0), (x0 + w, y0 - 0.6), (x0 + w, y0 + 0.6), (x0, y0 + 1.2)]), 0.4, 6), 0.45)
    p.finish()
    return p


def winter():
    """A winter dusk: a mauve sky glowing apricot low, a pale sun; snow left as paper with long lavender shadows; a
    stand of firs on the left as dark merged silhouettes, one lone fir on the right; its shadow thrown across."""
    p = Paper(seed=71)
    rng = np.random.default_rng(72)
    sun = p.soften(p.rough(p.ellipse(120, 206, 10, 10), 0.3, 4, fine=0.2), 0.6)
    sky(p, [MAUVE, VIOLET, ROSE, APRICOT], [(0, 220, 1.0, 0.1, 1.2), (0, 120, 1.0, 0.0, 0.5),
                                           (130, 232, 0.0, 1.0, 0.7), (190, 240, 0.0, 1.0, 0.9)],
        mask=np.clip(1 - sun, 0, 1))
    p.wash(sun, LEMON, 0.6, rim=1.6, flow=0.3)                                    # the sun, a flat disc, pooled rim
    snow_top = ridge(-20, 260, 240, [(5, 200, 1.0), (2, 70, 0.3)])
    snow = p.rough(p.poly(band(snow_top)), 0.4, 10, fine=0.0)
    p.lift(snow, 1.0)
    p.wash(snow, VIOLET, 0.12, rim=1.6, flow=0.3)                         # the snow a whisper, its crest edge pooled

    def snow_y(x):
        return float(np.interp(x, [q[0] for q in snow_top], [q[1] for q in snow_top]))
    # the snow: a soft cool glaze deepening toward us, and gentle splotches dropped in wet: rounded, soft-edged,
    # overlapping, different sizes, no hard edge or straight side anywhere
    p.wash(snow * ramp_y(256, 344, 0.0, 1.0), VIOLET, 0.45, rim=0, flow=0.5, blotch=0.05)
    p.wash(snow * ramp_y(296, 344, 0.0, 1.0), CERUL, 0.3, rim=0, flow=0.5, blotch=0.05)
    for cx, cy, rx, ry, col, d in [(170, 268, 34, 9, VIOLET, 0.4), (64, 280, 40, 11, MAUVE, 0.35),
                                   (200, 300, 44, 13, CERUL, 0.4), (110, 310, 50, 14, VIOLET, 0.4),
                                   (20, 326, 42, 15, CERUL, 0.45), (168, 334, 56, 16, VIOLET, 0.45),
                                   (232, 276, 26, 8, MAUVE, 0.3)]:
        sp = p.soften(p.rough(p.ellipse(cx, cy, rx, ry), ry * 0.4, rx * 0.4, fine=0.0), ry * 0.45)
        p.wash(sp * snow, col, d, rim=0, flow=0.5, blotch=0.08)
    # the stand: four firs of stepped flat glazes, three tiers each, the shaded right half a second glaze
    for x, h, w, col in [(30, 64, 14, CYPRESS), (50, 44, 10, TEAL), (66, 30, 7, TEAL)]:
        base = snow_y(x) + 3
        fir_m = np.zeros((H, W), np.float32)
        for k, (t0, t1, ww) in enumerate([(0.0, 0.42, 0.45), (0.25, 0.7, 0.75), (0.5, 1.0, 1.0)]):
            fir_m = np.maximum(fir_m, p.poly([(x, base - h + h * t0), (x + w * ww, base - h + h * t1),
                                              (x - w * ww, base - h + h * t1)]))
        fir_m = p.rough(fir_m, 0.6, 3, fine=0.35)
        p.loose(fir_m, [col, CYPRESS, PAYNE], 1.2, n=3, rough=0.4, patch=0.55, ground=0.8)
    # the lone fir on the right, and its shadow
    lx, lh, lw = 176, 46, 9
    lb = snow_y(lx) + 3
    lone = np.zeros((H, W), np.float32)
    for t0, t1, ww in [(0.0, 0.45, 0.45), (0.28, 0.72, 0.75), (0.52, 1.0, 1.0)]:
        lone = np.maximum(lone, p.poly([(lx, lb - lh + lh * t0), (lx + lw * ww, lb - lh + lh * t1),
                                        (lx - lw * ww, lb - lh + lh * t1)]))
    lone = p.rough(lone, 0.6, 3, fine=0.35)
    p.loose(lone, [CYPRESS, TEAL, PAYNE], 1.2, n=3, rough=0.4, patch=0.55, ground=0.8)
    p.wash(p.soften(p.ellipse(lx + 18, lb + 4, 22, 3.5), 2.0) * snow, VIOLET, 0.7, rim=0, flow=0.4)   # its shadow
    p.finish()
    return p


SCENES = {"mesa": mesa, "hills": hills, "lake": lake, "winter": winter}

if __name__ == "__main__":
    for name in sys.argv[1:] or SCENES:
        p = SCENES[name]()
        p.save(f"out/{name}-xl.png")
        p.save(f"out/{name}-sm.png", (352, 514))
