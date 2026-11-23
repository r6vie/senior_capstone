"""Watercolour title pages for the abstract covers (Josef, 2026-11-23: "the more elaborate book screens for these 4 new
designs, same principles as the book screen for the strata covers").

Same principles as the strata pages: one page per cover, the same place as a much richer scene; 570 x 684 world units
(1140 x 1368 px, the page at 2x); the text holds the upper left (x 0-470, y 0-350), so that stays bare paper and the
art climbs on the right. Watercolour has no hard top edge here: the sky is a wet wash that bleeds out into the paper
toward the text. Same abstraction as the covers (abstract.py): big wet patches with pooled rims, simple silhouettes.

python3 pages.py [mesa|hills|lake|winter ...] -> out/page-<name>.png (1140 x 1368) and out/page-<name>-sm.png"""
import math
import sys
import numpy as np
sys.path.insert(0, ".")
import paint
paint.configure(570, 684, 2)
from paint import Paper, blur, smooth, warped
from abstract import (ULTRA, CERUL, PAYNE, SIENNA, RAW, ROSE, SAP, OLIVE, UMBER, TERRA, VIOLET, APRICOT, SAGE, TEAL,
                      CYPRESS, MAUVE, LEMON)

S, W, H = paint.S, paint.W, paint.H
Xw, Yw = paint.XX / S, paint.YY / S
TX, TY = 470, 350                     # the text block's corner


def ramp_y(y0, y1, a, b):
    return a + (b - a) * np.clip((Yw - y0) / max(1e-6, y1 - y0), 0, 1)


def ramp_x(x0, x1, a, b):
    return a + (b - a) * np.clip((Xw - x0) / max(1e-6, x1 - x0), 0, 1)


def ridge(x0, x1, base, waves, n=60):
    return [(x0 + (x1 - x0) * i / n, base + sum(a * math.sin(2 * math.pi * (x0 + (x1 - x0) * i / n) / per + ph)
                                                 for a, per, ph in waves)) for i in range(n + 1)]


def band(top, bottom=700):
    return top + [(top[-1][0], bottom), (top[0][0], bottom)]


def y_at(line, x):
    return float(np.interp(x, [q[0] for q in line], [q[1] for q in line]))


def bleed(low=300, high=430, climb=150):
    """Where the sky may be painted: full strength low on the page, gone in the text corner, climbing up the right
    side; its edge is a wet edge, uneven, not a ruled gradient."""
    rise = smooth(Xw, 320, 660) * climb                 # a gentle diagonal sweep up to the right, not a column
    t = smooth(Yw + rise, low, high)
    n = (warped(60 * S, 909) - 0.5) * 0.5
    return np.clip(t + n * t * (1 - t) * 4, 0, 1).astype(np.float32)


def sky(p, cols, stops, fade):
    for c, (y0, y1, a, b, d) in zip(cols, stops):
        p.wash(fade, c, d, rim=0.0, flow=0.35, blotch=0.05, vary=ramp_y(y0, y1, a, b))


def blob(p, x, y, r, cols, d=1.0, flat=0.55, shadow=None):
    """A bush or rock as one soft-rimmed patch, its shade glazed on the right, a cast shadow thrown right."""
    if shadow is not None:
        p.wash(p.rough(p.ellipse(x + r * 0.9, y + r * flat * 0.6, r * 1.3, r * 0.28), 0.8, 4) * shadow, VIOLET, 0.7,
               rim=1.0)
    b = p.rough(p.ellipse(x, y, r, r * flat), r * 0.22, max(2, r * 0.5), fine=0.5)
    p.wash(b, cols[0], d, rim=1.4, flow=0.5, blotch=0.08)
    p.wash(b * ramp_x(x - r * 0.2, x + r, 0, 1), cols[1] if len(cols) > 1 else PAYNE, 0.6, rim=0)


def cottage(p, x, base, w, h, d, walls, roofs, window=None, snow_roof=False, ground=None, k=1.0):
    """A small house seen three-quarter on, painted by hand rather than built from boxes: the gable end toward us and
    lit, the long side wall turning away into shade, one roof plane over it; every edge wobbles a little, each part
    is a couple of loose wet patches. x: the gable's left corner; w, h: gable width and wall height; d: how far the
    side wall runs back. window: a colour for one small lit window in the gable."""
    a = w * 0.6                                                  # the gable's rise
    sk = d * 0.08                                                # the side wall climbs a hair as it recedes
    gable = [(x, base), (x - 0.4, base - h), (x + w / 2, base - h - a), (x + w + 0.3, base - h), (x + w, base)]
    side = [(x + w, base), (x + w + 0.3, base - h), (x + w + d, base - h - sk), (x + w + d - 0.4, base - sk)]
    roof = [(x + w / 2 - 0.8, base - h - a - 0.6), (x + w / 2 + d, base - h - a - sk - 0.6),
            (x + w + d + 2.5, base - h - sk + 1.4), (x + w + 1.2, base - h + 1.6)]
    gm = p.rough(p.poly(gable), 0.45, 3, fine=0.35)
    sm = p.rough(p.poly(side), 0.45, 3, fine=0.35)
    rm = p.rough(p.poly(roof), 0.45, 3, fine=0.35)
    if ground is not None:                                       # its shadow, thrown right
        p.wash(p.soften(p.ellipse(x + w + d * 0.8, base + 1.5, d * 0.9 + w * 0.4, 2.6), 1.2) * ground, VIOLET, 0.7,
               rim=0)
    p.lift(np.clip(blur(np.maximum.reduce([gm, sm, rm]), 0.4 * S) * 1.4, 0, 1), 0.85)
    p.loose(gm, walls, 0.75 * k, n=2, rough=0.4, patch=0.7, ground=0.6)
    p.loose(sm, walls, 0.8 * k, n=2, rough=0.4, patch=0.7, ground=0.6)
    p.wash(sm, VIOLET, 0.8 * k, rim=1.0, flow=0.4)
    p.wash(sm, PAYNE, 0.35 * k, rim=0, flow=0.4)
    if snow_roof:
        p.wash(rm, VIOLET, 0.35, rim=1.6, flow=0.3)
        p.wash(rm * ramp_y(base - h - a, base - h, 0.0, 0.8), CERUL, 0.4, rim=0)
    else:
        p.loose(rm, roofs, 1.0 * k, n=2, rough=0.4, patch=0.7, ground=0.7)
    # the verge: a darker line where the roof edge overhangs the gable
    p.wash(p.rough(p.stroke([(x - 1.2, base - h + 1.0), (x + w / 2 - 0.4, base - h - a - 0.6),
                             (x + w + 1.2, base - h + 1.2)], 1.1, taper=False), 0.2, 2), roofs[-1] if not snow_roof
           else VIOLET, 1.0 * k, rim=0.6)
    if window:
        wx, wy = x + w * 0.5, base - h * 0.48
        win = p.rough(p.ellipse(wx, wy, w * 0.11, h * 0.16), 0.25, 2, fine=0.2)
        p.wash(win, window, 1.2, rim=1.0)


def mesa():
    """The high desert at dusk, wider: a cobalt dusk climbing the right side with the evening star, apricot on the
    horizon; the great butte on the right in uneven strata, a second smaller butte and a lone spire in the middle
    distance, a far line of mesas; the desert floor in ochre and sienna patches, a dry wash winding toward us between
    clusters of sage, a single juniper in front."""
    p = Paper(seed=141)
    rng = np.random.default_rng(142)
    fade = bleed(330, 470, 130)
    sky(p, [ULTRA, VIOLET, ROSE, APRICOT], [(0, 470, 1.0, 0.0, 1.6), (300, 500, 0.0, 1.0, 0.7),
                                           (380, 520, 0.0, 1.0, 0.6), (440, 520, 0.0, 1.0, 1.0)], fade)
    hz = 520
    far = p.rough(p.poly([(-10, hz + 4), (-10, 492), (40, 488), (46, 478), (120, 476), (128, 488), (200, 492),
                          (230, 498), (300, 500), (310, hz + 4)]), 0.6, 10, fine=0.3)
    p.loose(far, [VIOLET, ROSE, VIOLET], 0.8, n=4, rough=0.4, patch=0.4)
    # the second butte and its spire in the middle distance
    b2 = p.rough(p.poly([(232, hz + 6), (246, 484), (256, 474), (258, 446), (326, 442), (330, 474), (346, 486), (360, hz + 6)]), 0.6, 8, 0.3)
    p.wash(b2, APRICOT, 0.6, rim=1.2)
    for y0, y1, cols in [(430, 458, [TERRA, ROSE]), (458, 464, [APRICOT]), (464, hz + 6, [SIENNA, TERRA])]:
        st = p.rough(p.poly([(200, y0), (380, y0 - 1), (380, y1), (200, y1 + 1)]), 1.0, 16, fine=0.4) * b2
        p.loose(st, cols, 0.8, n=3, rough=0.6, patch=0.55, ground=0.7)
    p.wash(p.rough(p.poly([(310, 437), (340, 470), (362, hz + 6), (306, hz + 6), (312, 470)]), 1.6, 9) * b2, VIOLET,
           1.0, rim=1.4, flow=0.4)
    spire = p.rough(p.poly([(186, hz + 10), (196, 488), (200, 462), (204, 448), (216, 446), (220, 466), (226, 490),
                            (238, hz + 10)]), 0.6, 6, 0.3)
    p.loose(spire, [TERRA, SIENNA, APRICOT], 1.0, n=3, rough=0.4, patch=0.6, ground=0.7)
    p.wash(spire * (Xw > 212), VIOLET, 1.0, rim=1.0)
    # the great butte on the right, climbing high where the text is not
    butte = p.rough(p.poly([(372, hz + 8), (396, 498), (414, 486), (424, 392), (430, 384), (570, 378), (590, 380),
                            (590, hz + 8)]), 0.7, 10, fine=0.35)
    p.wash(butte, APRICOT, 0.6, rim=1.2, flow=0.4)
    for y0, y1, cols in [(376, 430, [TERRA, SIENNA]), (430, 442, [APRICOT, ROSE]), (442, 474, [SIENNA, TERRA]),
                         (474, hz + 8, [ROSE, APRICOT, TERRA])]:
        st = p.rough(p.poly([(300, y0), (600, y0 - 1), (600, y1), (300, y1 + 1)]), 1.2, 18, fine=0.4) * butte
        p.loose(st, cols, 0.9, n=4, rough=0.6, patch=0.5, ground=0.7)
    shade = p.rough(p.poly([(500, 380), (590, 378), (590, hz + 8), (482, hz + 8), (494, 452)]), 2.4, 10, fine=0.6)
    p.wash(shade * butte, VIOLET, 1.1, rim=1.6, flow=0.5, blotch=0.08)
    p.wash(shade * butte * ramp_x(494, 590, 0.0, 1.0), UMBER, 0.45, rim=0, flow=0.4)
    p.wash(p.rough(p.poly([(424, 392), (430, 384), (570, 378), (570, 385), (430, 391)]), 0.5, 8) * butte, SIENNA, 0.9,
           rim=1.0)
    # talus: each butte's foot spreads into the floor in an uneven skirt, so none stands on a ruled line
    for pts in [[(214, hz + 14), (240, hz - 4), (262, hz - 10), (300, hz - 12), (340, hz - 8), (372, hz + 2), (390, hz + 16)],
                [(170, hz + 12), (196, hz + 2), (228, hz + 8), (244, hz + 18)],
                [(352, hz + 20), (380, hz - 4), (410, hz - 14), (470, hz - 18), (540, hz - 12), (600, hz - 8),
                 (600, hz + 26)]]:
        tal = p.rough(p.poly(pts), 1.6, 8, fine=0.5)
        p.loose(tal, [ROSE, APRICOT, TERRA], 0.8, n=3, rough=0.8, patch=0.5, ground=0.7)
        p.wash(tal * ramp_x(pts[0][0], pts[-1][0], 0, 1), VIOLET, 0.45, rim=0)
    # the floor: wide patches, warmer and deeper toward us
    floor = p.rough(p.poly([(-20, hz), (600, hz + 4), (600, 700), (-20, 700)]), 0.6, 12, fine=0.3)
    p.loose(floor, [RAW, APRICOT, RAW, ROSE], 0.6, n=7, rough=0.7, patch=0.4, ground=0.7)
    p.loose(p.rough(p.poly([(-20, 610), (200, 598), (600, 622), (600, 700), (-20, 700)]), 3, 24) * floor,
            [TERRA, SIENNA], 0.6, n=4, rough=0.7, patch=0.5, ground=0.7)
    p.wash(p.rough(p.poly([(380, hz + 8), (600, hz + 10), (600, 556), (480, 548)]), 1.6, 12) * floor, VIOLET, 0.8,
           rim=1.2, flow=0.4)                                               # the butte's shadow across the floor
    bed = p.rough(p.stroke([(250, hz + 8), (236, 556), (250, 590), (200, 630), (130, 668), (70, 704)], 26), 3.0, 16)
    p.wash(bed * floor, APRICOT, 0.6, rim=1.4, flow=0.4)
    for x, y, r, c in [(150, 548, 5, SAGE), (162, 552, 13, OLIVE), (178, 557, 4, SAGE), (334, 562, 17, OLIVE),
                       (352, 569, 6, SAGE), (64, 588, 8, SAGE)]:
        blob(p, x, y, r, [c, CYPRESS], 1.0, shadow=floor)
    blob(p, 92, 640, 22, [CYPRESS, PAYNE], 1.1, flat=0.6, shadow=floor)                    # the juniper in front
    # the near plane: a shelf of dark rock across the lower right, its top lit, its face in shade
    shelf = p.rough(p.poly([(360, 704), (380, 646), (420, 624), (470, 616), (520, 606), (570, 600), (600, 604),
                            (600, 704)]), 2.0, 12, fine=0.5)
    p.loose(shelf, [SIENNA, UMBER, TERRA], 1.1, n=5, rough=0.8, patch=0.4, ground=0.8)
    p.wash(shelf * ramp_y(620, 690, 0.2, 1.0), PAYNE, 0.8, rim=0, flow=0.4)
    p.wash(p.rough(p.poly([(380, 646), (420, 624), (470, 616), (520, 606), (570, 600), (570, 608), (470, 624),
                           (420, 632), (384, 652)]), 0.8, 8) * shelf, APRICOT, 0.6, rim=1.0)
    p.finish()
    return p


def hills():
    """Slow harvest, wider: a pale lemon morning bleeding into the paper; far blue hills with a hill town on one, its
    houses a few cream blocks and a tower; field after field in patches; a white road winding up through them
    lined with cypresses to a farmhouse; a row of olive trees, a lavender field in front."""
    p = Paper(seed=151)
    rng = np.random.default_rng(152)
    fade = bleed(320, 460, 110)
    sky(p, [LEMON, APRICOT, VIOLET], [(200, 470, 0.0, 1.0, 0.55), (360, 480, 0.0, 1.0, 0.45),
                                      (100, 300, 1.0, 0.0, 0.2)], fade)
    defs = [(430, [(10, 260, 0.6), (6, 120, 2.0)], [VIOLET, MAUVE, VIOLET]),
            (462, [(14, 330, 2.4), (6, 140, 0.8)], [SAGE, VIOLET, RAW, SAGE]),
            (500, [(16, 380, 4.0), (8, 160, 1.1)], [RAW, SAGE, APRICOT, SAP]),
            (548, [(18, 420, 1.0), (7, 180, 3.0)], [SAP, RAW, MAUVE, OLIVE, APRICOT]),
            (604, [(16, 460, 2.6), (8, 200, 0.4)], [OLIVE, SAP, SIENNA, RAW]),
            (658, [(10, 500, 1.4), (6, 220, 2.2)], [MAUVE, VIOLET, SAP])]
    tilts = [0.0, -0.05, 0.06, -0.04, 0.05, -0.03]
    tops = [[(x, y + k * (x - 285)) for x, y in ridge(-20, 600, base, waves)] for (base, waves, _), k in zip(defs, tilts)]
    # the far hill rises on the right, under the town
    tops[0] = [(x, y - 70 * smooth(np.float32(x), 360, 520)) for x, y in tops[0]]
    ms = [p.rough(p.poly(band(t)), 0.6, 14, fine=0.3) for t in tops]
    for i, (base, waves, cols) in enumerate(defs):
        m = ms[i]
        if i + 1 < len(ms):
            m = np.clip(m - np.clip(blur(ms[i + 1], 0.5 * S) * 2.2, 0, 1), 0, 1)
        p.loose(m, cols, 0.7 + 0.05 * i, n=5 + i, rough=1.0, patch=0.25, ground=0.55)
    # lavender rows in the nearest field: a few soft violet bands following the hill
    near = tops[5]
    for k in range(5):
        row = [(x, y + 8 + k * 7) for x, y in near]
        p.wash(p.rough(p.stroke(row[::3], 3.2), 0.6, 10) * ms[5], VIOLET, 0.8, rim=1.0, flow=0.4)
    # the hill town on the far rise: a huddle of small pale cottages under tiled roofs, stepping up the hill, and a
    # campanile with a pointed cap among them; pale, because it is far
    tx = 500
    ty = y_at(tops[0], tx) - 4
    tower = p.rough(p.poly([(tx, ty + 6), (tx - 0.3, ty - 18), (tx + 8.3, ty - 18), (tx + 8, ty + 6)]), 0.4, 3, fine=0.3)
    cap = p.rough(p.poly([(tx - 1, ty - 17), (tx + 4, ty - 27), (tx + 9, ty - 17)]), 0.3, 2, fine=0.3)
    p.lift(np.maximum(tower, cap), 0.8)
    p.wash(tower, APRICOT, 0.35, rim=1.0)
    p.wash(tower * (Xw > tx + 4.5), MAUVE, 0.7, rim=0.6)
    p.wash(cap, TERRA, 0.8, rim=1.0)
    for x, w, h, d in [(466, 9, 6, 10), (484, 8, 7, 9), (508, 10, 6, 11), (526, 8, 5, 9), (494, 7, 5, 6)]:
        y = y_at(tops[0], x + w / 2) + 5
        cottage(p, x, y, w, h, d, [APRICOT, RAW], [ROSE, TERRA], k=0.6)
    # the white road winding up from the front to the farmhouse
    road = [(150, 700), (210, 640), (300, 610), (340, 580), (400, 556), (430, 534)]
    left = [(x - (2 + (y - 534) * 0.07), y) for x, y in road]
    right = [(x + (2 + (y - 534) * 0.07), y) for x, y in road]
    rd = p.rough(p.poly(left + right[::-1]), 0.8, 12, fine=0.3)       # widening toward us, a pale ochre wash
    p.lift(rd, 0.6)
    p.wash(rd, RAW, 0.45, rim=1.2, flow=0.4)
    hx, hy = 436, y_at(tops[3], 436) + 2
    cottage(p, hx - 16, hy + 4, 15, 12, 20, [APRICOT, RAW], [TERRA, SIENNA], window=UMBER, ground=ms[3])
    for x, s in [(338, 1.1), (348, 0.75), (392, 0.9), (452, 1.4), (462, 1.0), (474, 0.7)]:
        y = y_at(road, x) if x < 430 else hy + 2
        y = min(y, y_at(tops[3], x) + 30) - 2
        t = p.rough(p.ellipse(x, y - 20 * s, 4.0 * s, 21 * s), 0.6, 3, fine=0.4)
        p.wash(p.rough(p.ellipse(x + 11 * s, y + 0.5, 11 * s, 2.2 * s), 0.5, 3), CYPRESS, 0.9, rim=1.0)
        p.wash(t, CYPRESS, 1.5, rim=1.3, flow=0.5, blotch=0.06)
        p.wash(t * ramp_x(x - 1, x + 4 * s, 0, 1), PAYNE, 0.8, rim=0)
    # a row of round olive trees on the fourth hill
    for x, dy, r in [(52, 18, 7), (74, 10, 12), (92, 22, 6), (130, 12, 9), (168, 24, 5)]:
        y = y_at(tops[4], x) + dy
        blob(p, x, y, r, [OLIVE, CYPRESS], 1.0, flat=0.8, shadow=ms[4])
    near_patch = p.rough(p.ellipse(470, 640, 80, 18), 4, 16, fine=0.5) * ms[5]
    p.loose(near_patch, [CYPRESS, OLIVE], 0.9, n=3, rough=0.8, patch=0.5, ground=0.7)   # the near dark
    p.finish()
    return p


def lake():
    """Above the tree line, wider: a cerulean sky bleeding into the paper; the massif on the right climbing high,
    lesser peaks stepping back to the left; forest masses on the shore and a small cabin with a dock; the lake
    holding the mountains, a canoe on it; near-shore boulders and a dark fir in the front corner."""
    p = Paper(seed=161)
    rng = np.random.default_rng(162)
    fade = bleed(320, 450, 150)
    sky(p, [CERUL, ULTRA], [(100, 470, 1.0, 0.5, 0.85), (100, 360, 1.0, 0.0, 0.35)], fade)
    shore = 486
    far = p.rough(p.poly([(-20, shore), (-20, 436), (40, 420), (80, 432), (120, 410), (170, 428), (220, 438),
                          (280, shore)]), 0.7, 8, fine=0.3)
    p.loose(far * fade, [VIOLET, CERUL, VIOLET], 0.7, n=5, rough=0.4, patch=0.35)
    mid = [(170, shore), (214, 450), (240, 436), (262, 426), (276, 412), (294, 418), (312, 410), (336, 430), (380, shore)]
    mm = p.rough(p.poly(mid), 0.6, 8, fine=0.3)
    p.wash(mm, CERUL, 0.3, rim=1.2)
    p.loose(p.rough(p.poly([(290, 404), (318, 418), (350, 432), (380, shore), (300, shore)]), 1, 8) * mm,
            [VIOLET, MAUVE], 0.9, n=3, rough=0.4, patch=0.5)
    peak = [(330, shore), (380, 454), (420, 432), (446, 408), (462, 396), (476, 372), (488, 334), (498, 300), (510, 262),
            (524, 238), (536, 252), (548, 270), (562, 262), (576, 280), (592, 300), (610, 312), (630, 320),
            (630, shore)]
    pk = p.rough(p.poly(peak), 0.6, 8, fine=0.3)
    p.wash(pk, CERUL, 0.25, rim=1.2, flow=0.3)
    faces = [([(524, 238), (536, 252), (548, 270), (562, 262), (576, 280), (592, 300), (610, 312), (630, 320),
               (630, shore), (540, shore), (534, 330)], [VIOLET, ULTRA, MAUVE], 1.0),
             ([(420, 432), (446, 408), (462, 396), (476, 372), (488, 334), (498, 300), (510, 262), (506, 330), (470, 420),
               (420, shore), (360, shore)],
              [CERUL, VIOLET], 0.5),
             ([(510, 330), (530, 300), (556, 380), (548, shore), (496, shore), (506, 420)], [ULTRA, PAYNE, VIOLET], 0.9)]
    for pts, cols, d in faces:
        p.loose(p.rough(p.poly(pts), 1.0, 8, fine=0.4) * pk, cols, d, n=5, rough=0.5, patch=0.4)
    forest = np.zeros((H, W), np.float32)
    for x0, x1, hgt in [(-20, 130, 22), (110, 300, 14), (280, 430, 20), (410, 600, 16)]:
        pts = [(x0, shore + 6)]
        for i in range(11):
            x = x0 + (x1 - x0) * i / 10
            pts.append((x, shore - hgt * (0.55 + 0.45 * math.sin(i * 1.7 + x0)) - (7 if i in (3, 7) else 0)))
        pts.append((x1, shore + 6))
        forest = np.maximum(forest, p.poly(pts))
    forest = p.rough(forest, 2.0, 7, fine=0.5)
    p.loose(forest, [CYPRESS, TEAL, PAYNE], 1.3, n=7, rough=0.6, patch=0.3, ground=0.8)
    # the cabin and its dock on the left shore
    cx, cy = 150, shore + 2
    cottage(p, cx - 16, cy, 14, 10, 18, [SIENNA, RAW], [PAYNE, UMBER], window=LEMON)
    lake_m = p.rough(p.poly([(-20, shore + 5), (600, shore + 5), (600, 700), (-20, 700)]), 0.3, 12, fine=0.2)
    p.loose(lake_m, [TEAL, CERUL, TEAL, ULTRA], 0.85, n=6, rough=0.5, patch=0.42, ground=0.75,
            vary=ramp_y(shore, 684, 0.7, 1.3))
    flip = lambda pts: [(x, 2 * (shore + 5) - y) for x, y in pts]
    refl = p.soften(p.rough(p.poly(flip(peak)), 3, 12, fine=0.4), 3) * lake_m
    p.loose(refl, [VIOLET, ULTRA, VIOLET], 0.6, n=5, rough=1.0, patch=0.35, ground=0.6)
    p.wash(p.soften(p.rough(p.poly(flip(mid)), 2, 10, fine=0.4), 2.5) * lake_m, VIOLET, 0.45, rim=0, flow=0.5)
    p.wash(p.soften(p.poly([(-20, shore + 5), (600, shore + 5), (600, shore + 26), (-20, shore + 22)]), 3) * lake_m,
           CYPRESS, 0.9, rim=0)
    dock = p.rough(p.poly([(cx + 6, shore + 3), (cx + 52, shore + 5), (cx + 52, shore + 9), (cx + 6, shore + 8)]),
                   0.3, 3)                                                   # the jetty, straight out from the shore
    p.wash(dock, UMBER, 1.2, rim=1.0)
    canoe = p.rough(p.poly([(250, 566), (296, 563), (290, 569), (256, 571)]), 0.3, 3)
    p.wash(canoe, SIENNA, 1.4, rim=1.2)
    p.wash(p.soften(p.poly([(250, 572), (296, 569), (292, 575), (256, 577)]), 1.5) * lake_m, PAYNE, 0.5, rim=0)
    # near shore: boulders and a dark fir in the front right corner
    for x, y, r in [(470, 660, 26), (512, 646, 18), (430, 676, 14)]:
        blob(p, x, y, r, [UMBER, PAYNE], 1.0, flat=0.6)
    fx, fb, fh, fw = 548, 690, 150, 30
    fm = np.zeros((H, W), np.float32)
    for t0, t1, ww in [(0.0, 0.4, 0.45), (0.22, 0.66, 0.75), (0.45, 1.0, 1.0)]:
        fm = np.maximum(fm, p.poly([(fx, fb - fh + fh * t0), (fx + fw * ww, fb - fh + fh * t1),
                                    (fx - fw * ww, fb - fh + fh * t1)]))
    p.loose(p.rough(fm, 1.0, 4, fine=0.5), [CYPRESS, PAYNE, TEAL], 1.3, n=4, rough=0.5, patch=0.45, ground=0.85)
    p.finish()
    return p


def winter():
    """First snow, wider: a mauve dusk bleeding into the paper, the low sun; far blue hills with a dark forest band;
    snowfields rolling toward us shaded in gentle splotches; a cabin with a lit window among firs on the right, a
    fence of a few posts running down the slope, a stand of firs on the left."""
    p = Paper(seed=171)
    rng = np.random.default_rng(172)
    fade = bleed(330, 470, 130)
    sun = p.soften(p.rough(p.ellipse(380, 456, 15, 15), 0.3, 4, fine=0.2), 0.6)
    sky(p, [MAUVE, VIOLET, ROSE, APRICOT], [(100, 480, 1.0, 0.2, 1.2), (300, 470, 1.0, 0.0, 0.4),
                                           (380, 496, 0.0, 1.0, 0.7), (440, 500, 0.0, 1.0, 0.9)],
        fade * np.clip(1 - sun, 0, 1))
    p.wash(sun, LEMON, 0.6, rim=1.6, flow=0.3)
    far = p.rough(p.poly(band(ridge(-20, 600, 492, [(8, 260, 1.0), (4, 110, 2.0)]))), 0.5, 10)
    p.loose(far * fade, [VIOLET, CERUL, VIOLET], 0.6, n=5, rough=0.5, patch=0.35)
    band_top = ridge(-20, 600, 500, [(4, 90, 0.4), (3, 37, 1.1)])
    fb = p.rough(p.poly(band(band_top, 512)), 0.8, 4, fine=0.6)
    p.loose(fb, [CYPRESS, TEAL, PAYNE], 1.0, n=6, rough=0.6, patch=0.3, ground=0.8)
    snow_top = ridge(-20, 600, 508, [(10, 380, 1.0), (4, 140, 0.3)])
    snow_top = [(x, y - 40 * smooth(np.float32(x), 380, 560)) for x, y in snow_top]   # a rise on the right
    snow = p.rough(p.poly(band(snow_top)), 0.5, 12, fine=0.0)
    p.lift(snow, 1.0)
    p.wash(snow, VIOLET, 0.12, rim=1.6, flow=0.3)
    p.wash(snow * ramp_y(520, 684, 0.0, 1.0), VIOLET, 0.45, rim=0, flow=0.5, blotch=0.05)
    p.wash(snow * ramp_y(580, 684, 0.0, 1.0), CERUL, 0.3, rim=0, flow=0.5, blotch=0.05)
    for cx, cy, rx, ry, col, d in [(420, 532, 70, 14, VIOLET, 0.4), (150, 548, 80, 16, MAUVE, 0.35),
                                   (300, 580, 90, 18, CERUL, 0.4), (500, 600, 80, 20, VIOLET, 0.4),
                                   (90, 620, 90, 22, CERUL, 0.45), (330, 650, 110, 24, VIOLET, 0.45),
                                   (560, 560, 50, 14, MAUVE, 0.3)]:
        sp = p.soften(p.rough(p.ellipse(cx, cy, rx, ry), ry * 0.4, rx * 0.4, fine=0.0), ry * 0.45)
        p.wash(sp * snow, col, d, rim=0, flow=0.5, blotch=0.08)

    def fir(x, h, w, cols, base=None):
        base = y_at(snow_top, x) + 4 if base is None else base
        m = np.zeros((H, W), np.float32)
        for t0, t1, ww in [(0.0, 0.42, 0.45), (0.25, 0.7, 0.75), (0.5, 1.0, 1.0)]:
            m = np.maximum(m, p.poly([(x, base - h + h * t0), (x + w * ww, base - h + h * t1),
                                      (x - w * ww, base - h + h * t1)]))
        p.wash(p.soften(p.ellipse(x + w * 1.6, base + 2, w * 1.8, w * 0.22), 1.5) * snow, VIOLET, 0.6, rim=0)
        p.loose(p.rough(m, 0.8, 3, fine=0.4), cols, 1.2, n=3, rough=0.4, patch=0.55, ground=0.8)

    for x, h, w in [(70, 70, 15), (22, 58, 13), (112, 44, 10), (52, 150, 32)]:    # small ones behind, one dominant
        fir(x, h, w, [CYPRESS, PAYNE, TEAL])
    # the cabin on the rise, a warm window, firs behind and beside it
    for x, h, w in [(478, 96, 20), (548, 120, 24), (572, 80, 18)]:
        fir(x, h, w, [CYPRESS, TEAL, PAYNE])
    cx = 516
    cy = y_at(snow_top, cx) + 6
    cottage(p, cx - 24, cy, 20, 14, 24, [SIENNA, UMBER], [UMBER], window=APRICOT, snow_roof=True, ground=snow)
    p.wash(p.soften(p.ellipse(cx - 14, cy + 10, 14, 4), 3) * snow, APRICOT, 0.35, rim=0)   # the window's glow
    # a fence of a few posts running down the slope toward us
    for i, (x, y, lean) in enumerate([(444, 558, 1.0), (436, 562, -0.6), (356, 600, 1.6), (262, 646, -1.2)]):
        hgt = 10 + i * 3.0
        p.wash(p.rough(p.stroke([(x, y), (x + lean, y - hgt)], 2 + i * 0.45, taper=False), 0.2, 2), UMBER, 1.2,
               rim=0.8)
        p.wash(p.soften(p.ellipse(x + hgt * 0.6, y + 1, hgt * 0.7, 1.2 + i * 0.2), 1) * snow, VIOLET, 0.5, rim=0)
    p.wash(p.soften(p.ellipse(358, 600, 9, 4), 1.5) * snow, VIOLET, 0.4, rim=0)          # a drift against one post
    # the near plane: a big dark spruce in the front right corner, and rocks breaking the snow at its foot
    fir(548, 200, 40, [CYPRESS, PAYNE, TEAL], base=700)
    for x, y, r in [(470, 676, 16), (500, 668, 10)]:
        blob(p, x, y, r, [PAYNE, UMBER], 1.0, flat=0.55)
    p.finish()
    return p


SCENES = {"mesa": mesa, "hills": hills, "lake": lake, "winter": winter}

if __name__ == "__main__":
    for name in sys.argv[1:] or SCENES:
        p = SCENES[name]()
        p.save(f"out/page-{name}.png")
        p.save(f"out/page-{name}-sm.png", (285, 342))
