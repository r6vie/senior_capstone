"""Watercolour title pages for the city, blossom and autumn covers (Josef, 2026-11-23: "do the book screens for
blossom, city and autumn"). Same principles as pages.py: the same place as the cover, a much richer scene; 570 x 684
world units at 2 px; the text corner (x 0-470, y 0-350) left as paper, the sky a wet wash bleeding out into it, the
art climbing on the right. Same abstraction as the covers: big wet patches, simple silhouettes, no fussy detail.

python3 pages2.py [city|blossom|autumn ...] -> out/page-<name>.png (1140 x 1368) and out/page-<name>-sm.png"""
import math
import sys
import numpy as np
sys.path.insert(0, ".")
import pages                                     # configures paint for the page size before anything else loads
from pages import (Paper, blur, smooth, ramp_x, ramp_y, ridge, band, y_at, bleed, sky, blob, cottage, H, W, S, Xw,
                   Yw)
from abstract import (ULTRA, CERUL, PAYNE, SIENNA, RAW, ROSE, SAP, OLIVE, UMBER, TERRA, VIOLET, APRICOT, SAGE, TEAL,
                      CYPRESS, MAUVE, LEMON)
from abstract2 import INDIGO, BLUSH, PINK, GOLDEN
import covers
from covers import GOLD, SHADOW, crown, spline


def city():
    """After hours, wider: an indigo night climbing the right side, a pale moon in it, the last warm glow low on the
    horizon; violet towers far off, deeper blue ones nearer, the tallest on the right rising high with its spire;
    warm windows in loose clusters; a long low bridge across the river with a string of lamps; the river holding
    the lights in broken streaks; the near quay in the lower right with two lamps and their pools of light."""
    p = Paper(seed=181)
    rng = np.random.default_rng(182)
    fade = bleed(300, 450, 170)
    moon = p.soften(p.rough(p.ellipse(526, 232, 13, 13), 0.3, 4, fine=0.2), 0.8)
    sky(p, [INDIGO, PAYNE, MAUVE, APRICOT], [(0, 470, 1.0, 0.1, 1.5), (0, 380, 1.0, 0.0, 0.5),
                                            (380, 500, 0.0, 1.0, 0.8), (450, 520, 0.0, 1.0, 1.1)],
        fade * np.clip(1 - moon, 0, 1))
    p.wash(p.soften(p.ellipse(526, 232, 30, 30), 14) * fade * (1 - moon), MAUVE, 0.3, rim=0)     # its halo
    p.wash(moon, LEMON, 0.35, rim=1.4, flow=0.3)
    hz = 528
    far = np.zeros((H, W), np.float32)
    x = -10
    while x < 590:
        w = rng.uniform(14, 30)
        h = rng.uniform(26, 60) + 40 * smooth(np.float32(x), 300, 520)
        far = np.maximum(far, p.poly([(x, hz), (x, hz - h), (x + w, hz - h), (x + w, hz)]))
        x += w + rng.uniform(-6, 2)
    far = p.rough(far, 0.6, 5, fine=0.4)
    p.loose(far * np.clip(fade * 1.4, 0, 1), [VIOLET, MAUVE, VIOLET], 0.6, n=8, rough=0.4, patch=0.3, ground=0.7)
    # near towers: setbacks, one spire; low on the left under the text, climbing to the right
    near = []
    for x, w, h, step in [(-10, 70, 30, 0), (40, 22, 50, 0), (140, 60, 34, 0), (230, 34, 70, 0),
                          (300, 52, 104, 18), (380, 30, 150, 0), (400, 52, 112, 0), (440, 38, 250, 34),
                          (470, 58, 180, 0), (528, 46, 214, 26)]:
        top = hz - h
        pts = [(x, hz + 1), (x, top + step), (x + w * 0.2, top + step), (x + w * 0.2, top), (x + w * 0.8, top),
               (x + w * 0.8, top + step), (x + w, top + step), (x + w, hz + 1)] if step else \
              [(x, hz + 1), (x, top), (x + w, top), (x + w, hz + 1)]
        m = p.rough(p.poly(pts), 0.6, 5, fine=0.4)
        if h >= 250:                                                       # the spire on the tallest
            m = np.maximum(m, p.rough(p.poly([(x + w * 0.46, top), (x + w * 0.5, top - 34), (x + w * 0.54, top)]),
                                      0.2, 2))
        near.append((x, w, h, m))
    nm = np.clip(np.maximum.reduce([n[3] for n in near]), 0, 1)
    p.loose(nm, [INDIGO, ULTRA, MAUVE, INDIGO], 0.85, n=12, rough=0.4, patch=0.22, ground=0.8)
    for x, w, h, m in near:                                                # each right face turned from the glow
        p.wash(m * p.soften(p.poly([(x + w * 0.62, 0), (x + w + 6, 0), (x + w + 6, 700), (x + w * 0.62, 700)]), 2),
               PAYNE, 0.5, rim=0)
    p.wash(near[7][3] * ramp_y(260, hz, 0.0, 1.0) * ramp_x(440, 470, 1.0, 0.0), APRICOT, 0.5, rim=0)
    for i in (5, 7, 9):                                                    # a few soft lights near the spire only
        x, w, h, m = near[i]
        for _ in range(1):
            cy = hz - rng.uniform(0.3, 0.6) * h
            for k in range(int(rng.integers(4, 7))):
                wx = x + rng.uniform(0.18, 0.8) * w
                wy = cy + rng.uniform(-0.12, 0.12) * h
                d = p.rough(p.ellipse(wx, wy, 1.6, 2.2), 0.2, 1, fine=0.1) * m
                p.lift(d, 0.85)
                p.wash(d, str(rng.choice([APRICOT, LEMON, GOLDEN])), 0.9, rim=0.8)
    # the river
    river = p.rough(p.poly([(-20, hz + 1), (600, hz + 1), (600, 700), (-20, 700)]), 0.2, 12, fine=0.1)
    p.wash(river, INDIGO, 0.85, rim=0.4, flow=0.4, blotch=0.06, vary=ramp_y(hz, 684, 0.6, 1.3))
    p.loose(river, [MAUVE, INDIGO, VIOLET], 0.35, n=9, rough=0.6, patch=0.22, ground=0.3)
    for cx, cy, rx in [(90, 548, 70, ), (250, 560, 60), (60, 600, 50)]:
        pk = p.soften(p.rough(p.ellipse(cx, cy, rx, 5), 1.2, 14), 1.4) * river
        p.lift(pk, 0.3)
        p.wash(pk, APRICOT, 0.5, rim=0)
    # the bridge: a long low deck crossing from the left, on a few broad arches, its lamps a string of warm dots
    dk = 566
    deck = p.rough(p.poly([(-20, dk - 8), (360, dk - 3), (360, dk + 4), (-20, dk + 1)]), 0.4, 8, fine=0.3)
    piers = np.zeros((H, W), np.float32)
    for px in [30, 110, 190, 270, 340]:
        y0 = dk - 8 + 5 * (px + 20) / 380
        piers = np.maximum(piers, p.poly([(px - 6, y0), (px + 6, y0), (px + 7, y0 + 30), (px - 7, y0 + 30)]))
    arches = np.zeros((H, W), np.float32)
    for a0, a1 in [(-30, 30), (30, 110), (110, 190), (190, 270), (270, 340)]:
        y0 = dk - 4 + 5 * ((a0 + a1) / 2 + 20) / 380
        arches = np.maximum(arches, p.ellipse((a0 + a1) / 2, y0 + 26, (a1 - a0) / 2 - 4, 22) * (Yw > y0 + 3))
    br = p.rough(np.clip(np.maximum(deck, piers) + p.poly([(-20, dk - 6), (350, dk - 2), (350, dk + 26),
                                                             (-20, dk + 26)]) - arches, 0, 1), 0.4, 5, fine=0.3)
    p.wash(br, INDIGO, 1.2, rim=1.2, flow=0.4)
    p.wash(br, PAYNE, 0.6, rim=0, flow=0.4)
    for lx in [-4, 22, 60, 84, 132, 170, 214, 236, 290, 330]:
        ly = dk - 8 + 5 * (lx + 20) / 380 - 6
        d = p.rough(p.ellipse(lx, ly, 1.8, 1.8), 0.2, 1, fine=0.1)
        p.lift(d, 0.9)
        p.wash(d, GOLDEN, 1.0, rim=0.6)
        p.wash(p.soften(p.ellipse(lx, ly, 6, 6), 3) * (1 - d), APRICOT, 0.25, rim=0)
        if rng.random() < 0.35:                                 # its light in the water below the bridge
            st = p.soften(p.rough(p.ellipse(lx + rng.uniform(-2, 2), dk + 40 + rng.uniform(0, 30), 2.2,
                                            rng.uniform(5, 10)), 0.8, 3), 0.8) * river * (1 - br)
            p.lift(st, 0.4)
            p.wash(st, GOLDEN, 0.6, rim=0.3)
    # the towers' lights in the water: broken wobbling streaks, the brightest under the tall tower
    for x, w, c, d, n in [(404, 8, GOLDEN, 0.7, 4), (459, 14, LEMON, 0.95, 7), (548, 9, APRICOT, 0.7, 4)]:
        for seg in range(n):
            if rng.random() < 0.3:
                continue
            y0 = hz + 8 + seg * 17 + rng.uniform(-5, 5)
            ln = rng.uniform(4, 16)
            sw = w * (1 - seg * 0.06) * rng.uniform(0.6, 1.3)
            st = p.soften(p.rough(p.ellipse(x + rng.uniform(-4, 4), y0, sw / 2, ln / 2), 1.0, 4), 0.8) * river * (1 - br)
            p.lift(st, 0.55 * (1 - seg * 0.07))
            p.wash(st, c, d * (1 - seg * 0.07), rim=0.4)
    p.wash(p.soften(p.poly([(-20, hz + 1), (600, hz + 1), (600, hz + 6), (-20, hz + 6)]), 1.2) * river, MAUVE, 0.6,
           rim=0)
    # the near embankment: one deep violet shape running in diagonally across the lower right, its lit edge
    bank = p.rough(p.poly([(300, 704), (400, 664), (500, 640), (600, 628), (600, 704)]), 2.0, 16, fine=0.4)
    p.loose(bank, [MAUVE, INDIGO, VIOLET], 1.0, n=5, rough=0.8, patch=0.45, ground=0.8)
    p.wash(bank * ramp_y(640, 700, 0.0, 1.0), INDIGO, 0.6, rim=0, flow=0.4)
    p.wash(p.rough(p.poly([(400, 664), (500, 640), (600, 628), (600, 634), (500, 646), (404, 670)]), 0.6, 8) * bank,
           APRICOT, 0.5, rim=0.8)
    p.finish()
    return p


def blossom():
    """Second spring, wider: a blush sky bleeding into the paper; soft blue hills far off; a row of small blossom
    trees and green ones on the far bank; the pond wide and still, a little wooden footbridge across its narrow
    end; the great blossom tree on the right, leaning in, its crown a huge cloud climbing the right side and reaching
    out low over the water; petals drifting down and gathered on the grass."""
    p = Paper(seed=191)
    rng = np.random.default_rng(192)
    fade = bleed(310, 450, 170)
    sky(p, [BLUSH, LEMON, CERUL], [(150, 480, 0.4, 1.0, 0.55), (360, 480, 0.0, 1.0, 0.3), (100, 380, 0.7, 0.0, 0.3)],
        fade)
    hills_top = ridge(-20, 600, 470, [(8, 300, 0.4), (4, 110, 2.0)])
    hills_top = [(x, y - 30 * smooth(np.float32(x), 300, 560)) for x, y in hills_top]
    hm = p.rough(p.poly(band(hills_top)), 0.6, 12, fine=0.3)
    p.loose(hm * np.clip(fade * 1.3, 0, 1), [CERUL, VIOLET, CERUL], 0.6, n=5, rough=0.5, patch=0.4)
    gt = ridge(-20, 600, 498, [(4, 260, 1.2), (3, 90, 0.4)])
    ground = p.rough(p.poly(band(gt)), 0.6, 12, fine=0.3)
    p.loose(ground, [SAGE, SAP, LEMON, SAGE], 0.8, n=9, rough=0.8, patch=0.35, ground=0.7)
    p.loose(p.rough(p.poly([(-20, 640), (300, 620), (600, 650), (600, 704), (-20, 704)]), 3, 24) * ground,
            [SAP, SAGE, SAP], 0.6, n=4, rough=0.8, patch=0.5, ground=0.7)                 # deeper toward us
    # the far bank: small trees, blossom among green, each a soft blob
    for x, r, cols, d in [(30, 16, [SAP, CYPRESS], 0.6), (50, 20, [PINK, MAUVE], 0.85), (70, 13, [BLUSH, PINK], 0.7),
                          (176, 22, [PINK, MAUVE], 0.8), (200, 15, [SAGE, CYPRESS], 0.55), (214, 12, [BLUSH, PINK], 0.6),
                          (290, 14, [SAP, CYPRESS], 0.5)]:
        y = y_at(gt, x) - r * 0.25
        blob(p, x, y - r * 0.2, r, cols, d, flat=0.7, shadow=ground)
    # the pond: a wide irregular oval, the sky and the blossom lying in it
    pond = p.rough(np.maximum(p.ellipse(200, 570, 190, 34), p.ellipse(110, 582, 120, 30)), 9, 40, fine=0.6)
    p.lift(p.soften(pond, 2.5), 0.85)                     # still water: pale, holding the sky
    p.loose(pond, [CERUL, BLUSH, CERUL], 0.55, n=5, rough=0.6, patch=0.55, ground=0.7)
    p.wash(pond * ramp_y(540, 606, 0.0, 1.0), TEAL, 0.35, rim=0, flow=0.5)
    p.wash(p.soften(p.ellipse(190, 540, 200, 8), 3) * pond, SAP, 0.45, rim=0)                 # the far bank in it
    for x, r in [(44, 14), (130, 16), (228, 15)]:
        p.wash(p.soften(p.rough(p.ellipse(x, 556, r * 0.8, 12), 2, 8), 2.5) * pond, PINK, 0.5, rim=0, flow=0.5)
    p.wash(p.soften(p.rough(p.ellipse(350, 574, 60, 20), 3, 12), 4) * pond, PINK, 0.65, rim=0, flow=0.5)
    # a small wooden footbridge across the pond's narrow left end: a low arc of deck, a rail, its ring in the water
    arc = [(16 + 110 * t, 566 - 22 * math.sin(math.pi * t)) for t in np.linspace(0, 1, 18)]
    deck = p.rough(p.stroke(arc, 10, taper=False), 0.3, 3, fine=0.3)
    for cx, cy in [(10, 568), (128, 568)]:                            # grassy banks at both ends
        p.loose(p.rough(p.ellipse(cx, cy, 26, 9), 2.5, 8, fine=0.5), [SAP, SAGE], 0.85, n=2, rough=0.6, patch=0.6,
                ground=0.7)
    bm = deck
    p.lift(np.clip(blur(bm, 0.4 * S) * 1.4, 0, 1), 0.8)
    p.wash(bm, UMBER, 1.2, rim=1.0)
    p.wash(bm, SIENNA, 0.5, rim=0)
    p.wash(p.soften(p.stroke([(x, 2 * 570 - y) for x, y in arc], 7, taper=False), 2) * pond, UMBER, 0.45, rim=0)
    # the great tree: rooted on the right bank, leaning in, limbs reaching up-right and out low over the pond
    tx, tb = 500, 626
    trunk = p.rough(p.poly([(tx - 28, tb + 2), (tx - 14, tb - 24), (tx - 20, tb - 80), (tx - 34, tb - 130),
                            (tx - 8, tb - 138), (tx + 8, tb - 86), (tx + 16, tb - 30), (tx + 34, tb + 2)]), 1.4, 6,
                    fine=0.4)
    limbs = np.maximum.reduce([p.rough(p.stroke(pts, w), 0.6, 4, fine=0.3) for pts, w in
                               [([(tx - 20, tb - 120), (tx - 70, tb - 150), (tx - 130, tb - 160)], 13),
                                ([(tx - 18, tb - 126), (tx + 10, tb - 190), (tx + 50, tb - 250)], 12),
                                ([(tx - 22, tb - 130), (tx - 40, tb - 200), (tx - 30, tb - 260)], 10)]])
    wood = np.clip(np.maximum(trunk, limbs), 0, 1)
    p.wash(p.soften(p.ellipse(tx + 20, tb + 2, 46, 6), 2) * ground, CYPRESS, 0.6, rim=0)
    cr = np.zeros((H, W), np.float32)
    # clear of the text corner: whatever lies left of x 470 stays below y ~350
    for cx, cy, rx, ry in [(500, 400, 70, 50), (540, 330, 52, 50), (520, 260, 46, 40), (470, 310, 34, 30),
                           (440, 420, 54, 32), (380, 448, 50, 26), (330, 460, 36, 18), (560, 420, 40, 44),
                           (575, 270, 30, 40), (490, 455, 50, 22), (410, 400, 36, 26), (548, 214, 30, 26),
                           (575, 360, 30, 40), (300, 470, 24, 12), (470, 370, 40, 30)]:
        cr = np.maximum(cr, p.rough(p.ellipse(cx, cy, rx, ry), ry * 0.3, max(6, rx * 0.4), fine=0.6))
    cr = cr * np.clip(1 - p.soften(p.poly([(-20, -20), (466, -20), (466, 352), (-20, 352)]), 10), 0, 1)
    p.loose(cr, [PINK, BLUSH, MAUVE, BLUSH, PINK], 0.95, n=22, rough=0.8, patch=0.2, ground=0.55)
    p.lift(cr * p.soften(p.ellipse(500, 300, 50, 34), 12), 0.3)
    p.wash(cr * np.clip(ramp_y(260, 480, 0.0, 1.0) * 0.6 + ramp_x(400, 600, 0.0, 1.0) * 0.5, 0, 1), MAUVE, 0.7,
           rim=0, flow=0.5)
    show = np.clip(1 - blur(cr, 2.0 * S) * 1.5, 0, 1)
    p.wash(wood * show, UMBER, 1.3, rim=1.0, blotch=0.06)
    p.wash(wood * show * ramp_x(tx - 20, tx + 24, 0.0, 1.0), PAYNE, 0.6, rim=0)
    # petals: a few drifting below the crown, more gathered on the grass and floating at the pond's edge
    for _ in range(26):
        x, y = rng.uniform(290, 600), rng.uniform(470, 560)
        p.wash(p.rough(p.ellipse(x, y, rng.uniform(1.2, 2.2), rng.uniform(0.8, 1.4)), 0.3, 1, fine=0.2),
               str(rng.choice([PINK, BLUSH, MAUVE])), 0.9, rim=0.8)
    for cx, cy, rx, ry in [(470, 640, 70, 10), (320, 606, 60, 8)]:
        drift = p.soften(p.rough(p.ellipse(cx, cy, rx, ry), ry * 0.4, rx * 0.4, fine=0), ry * 0.5)
        p.loose(drift, [PINK, BLUSH], 0.6, n=3, rough=1.0, patch=0.5, ground=0.4)
    anchor = p.rough(p.poly([(-20, 640), (80, 626), (170, 646), (220, 704), (-20, 704)]), 3, 16, fine=0.5)
    p.loose(anchor, [SAP, CYPRESS, SAGE], 0.8, n=5, rough=0.9, patch=0.45, ground=0.75)    # the near dark
    p.finish()
    return p


def autumn():
    """The long way home, wider: a golden haze climbing the right side over a violet wood; the humpbacked bridge in
    the middle distance, a small cottage and a dark fir beyond it; the river leaving the arch and winding toward us
    in loose gold and violet patches; the banks in warm washes with a few big patches; trees on both banks, and the
    great oak on the right bank rising into the sky; the trees' colours lying in the water as soft blotches."""
    p = Paper(seed=201)
    rng = np.random.default_rng(203)
    fade = bleed(300, 440, 170)
    full = fade
    p.wash(full, GOLD, 0.8, rim=0.4, flow=0.25, blotch=0.04, vary=ramp_y(150, 500, 1.0, 0.6))
    p.wash(full, RAW, 0.35, rim=0, flow=0.25, blotch=0.04, vary=ramp_y(150, 400, 1.0, 0.0))
    p.wash(full * p.soften(p.poly([(-20, 400), (600, 380), (600, 480), (-20, 480)]), 24), ROSE, 0.3, rim=0, flow=0.5)
    p.wash(full * ramp_y(150, 360, 1.0, 0.0), SIENNA, 0.35, rim=0, flow=0.3)
    p.lift(p.soften(p.ellipse(280, 460, 110, 30), 20) * full, 0.35)              # the light breaking behind the bridge
    hz = 490
    # the far wood: one violet band, its top uneven, warmer where the light is
    far = np.zeros((H, W), np.float32)
    for i in range(40):
        far = np.maximum(far, p.ellipse(rng.uniform(-10, 590), rng.uniform(hz - 26, hz - 8), rng.uniform(14, 30),
                                        rng.uniform(10, 20)))
    far = p.soften(np.maximum(far, p.poly([(-20, hz - 12), (600, hz - 16), (600, hz + 8), (-20, hz + 8)])), 3)
    p.wash(far, VIOLET, 0.7, rim=0.4, flow=0.5, blotch=0.08)
    p.wash(far * p.soften(p.ellipse(280, hz - 6, 100, 24), 14), GOLD, 0.6, rim=0, flow=0.4)
    for x, rx, ry, cols in [(46, 18, 14, [RAW, GOLD]), (100, 14, 12, [GOLD, RAW]), (380, 16, 12, [GOLD, RAW]),
                            (440, 20, 16, [RAW, TERRA])]:
        crown(p, x, hz - 8, rx, ry, cols, rng, n=5)
    # the river: narrow at the arch, winding toward us and widening
    bx, sy, brr = 280, 500, 26
    rl = spline([(bx - 30, sy), (bx - 44, sy + 22), (bx - 30, sy + 50), (bx - 60, sy + 84), (bx - 130, sy + 116),
                 (bx - 210, sy + 150), (bx - 300, sy + 190)])
    rr = spline([(bx + 30, sy), (bx + 48, sy + 18), (bx + 76, sy + 44), (bx + 70, sy + 80), (bx + 30, sy + 112),
                 (bx + 46, sy + 150), (bx + 110, sy + 190)])
    river = p.rough(p.poly(rl + rr[::-1]), 6, 24, fine=0.7)
    p.loose(river, [GOLD, SHADOW, VIOLET, GOLD, SHADOW], 0.75, n=10, rough=0.9, patch=0.32, ground=0.6)
    p.wash(river * ramp_y(560, 684, 0.0, 1.0), SHADOW, 0.3, rim=0, flow=0.5)
    # the banks: one warm wash each, a few big patches, deeper toward us
    lbank = p.rough(p.poly([(-20, sy - 4), (bx - 28, sy - 4)] + rl[1:] + [(-20, 704)]), 2.5, 18, fine=0.5)
    rbank = p.rough(p.poly([(bx + 28, sy - 4), (600, sy - 6), (600, 704)] + rr[::-1][:-1]), 2.5, 18, fine=0.5)
    lbank = np.clip(blur(lbank, 2.5 * S) * 2.2, 0, 1) * (1 - river * 0.35)
    rbank = np.clip(blur(rbank, 2.5 * S) * 2.2, 0, 1) * (1 - river * 0.35)
    for bank in (lbank, rbank):
        p.wash(bank, RAW, 0.8, rim=0.8, flow=0.5, blotch=0.08)
        p.loose(bank, [GOLD, SIENNA, RAW, TERRA], 0.55, n=7, rough=2.0, patch=0.45, ground=0.0)
        p.wash(bank * ramp_y(560, 684, 0.0, 1.0), SIENNA, 0.5, rim=0, flow=0.5, blotch=0.06)
    # beyond the bridge: a dark fir on the left bank, the cool accent
    covers.fir(p, 180, hz + 6, 70, 13, rng)
    covers.fir(p, 160, hz + 6, 40, 9, rng)
    # the bridge: lifted to paper, then a few washes, shaded to the right; no masonry
    top = sy - 40 + 8 * np.clip((Xw - bx) / 92, -1.0, 1.0) ** 2
    body = ((Yw >= top) & (Yw <= sy + 6) & (np.abs(Xw - bx) <= 92 + np.clip(Yw - (sy - 20), 0, 26) * 0.9))
    hole = ((((Xw - bx) / brr) ** 2 + ((Yw - sy) / (brr * 0.98)) ** 2) < 1) & (Yw < sy + 1)
    body = p.rough(np.clip(body.astype(np.float32) - hole, 0, 1), 0.9, 6, fine=0.5)
    p.lift(np.clip(blur(body, 0.6 * S) * 1.3, 0, 1), 0.9)
    p.loose(body, [SIENNA, RAW, TERRA], 1.25, n=6, rough=0.6, patch=0.4, ground=0.9)
    p.wash(body * ramp_x(bx - 10, bx + 86, 0.0, 1.0), UMBER, 0.6, rim=0, flow=0.4)
    p.lift(body * np.clip(1 - (Yw - top) / 5, 0, 1) * (Yw >= top), 0.35)      # the parapet catching the light
    hole_m = np.clip(blur(hole.astype(np.float32), 0.8 * S) * 1.8, 0, 1)
    p.lift(hole_m, 0.85)
    p.wash(hole_m, VIOLET, 0.9, rim=0.6, flow=0.4)                        # the shade under the arch
    p.wash(hole_m * ramp_y(sy - brr, sy - 6, 1.0, 0.3), UMBER, 1.2, rim=0, flow=0.5)
    p.wash(hole_m * ramp_y(sy - 10, sy, 0.0, 1.0), GOLD, 0.5, rim=0)        # a sliver of far water low down
    for cx, cy, rx, ry, cols in [(196, sy + 2, 16, 9, [OLIVE, SIENNA, RAW]), (366, sy + 2, 18, 9, [SIENNA, OLIVE, GOLD]),
                                 (232, sy + 6, 9, 5, [OLIVE, SIENNA]), (330, sy + 6, 9, 5, [SIENNA, OLIVE])]:
        crown(p, cx, cy, rx, ry, cols, rng, n=6)
    for dx, dy, rx, ry, c, d in [(-40, 14, 30, 6, SIENNA, 0.55), (34, 18, 26, 5, SIENNA, 0.5), (-6, 22, 18, 5, UMBER, 0.7),
                                 (12, 34, 14, 4, UMBER, 0.5), (-20, 42, 20, 3, SIENNA, 0.4)]:   # a broken reflection
        p.wash(p.soften(p.rough(p.ellipse(bx + dx, sy + dy, rx, ry), 2, 8), 1.5) * river, c, d, rim=0, flow=0.5)
    # trees on the banks, low on the left under the text
    for x, base, h, sp, tw, n, cols in [(64, 560, 110, 0.75, 4.0, 13, [GOLD, TERRA, SIENNA, RAW]),
                                        (100, 530, 60, 0.8, 2.6, 9, [RAW, GOLD, TERRA]),
                                        (420, 540, 80, 0.8, 3.2, 10, [GOLD, RAW, SIENNA])]:
        covers.tree(p, x, base, h, sp, cols, rng, lean=0.03, trunk_w=tw, clumps=n, size=0.2)
        p.wash(p.soften(p.rough(p.poly([(x - 5, base), (x + 5, base - 1), (x + h * 0.7, base + 6),
                                        (x + h * 0.6, base + 10)]), 1.2, 6), 2.5) * np.maximum(lbank, rbank),
               UMBER, 0.75, rim=0)
    # the great oak on the right bank, rising into the sky where the text is not
    covers.tree(p, 530, 640, 340, 0.3, [GOLD, TERRA, RAW, SIENNA, GOLD], rng, lean=-0.02, trunk_w=10, clumps=34,
                dark=TERRA, size=0.09, fork_at=0.37, leaves=8)
    p.wash(p.soften(p.ellipse(544, 642, 44, 7), 3) * rbank, UMBER, 0.6, rim=0)
    # the trees in the water, and the shade under the right bank
    for x, y, w, col in [(40, 600, 50, TERRA), (420, 580, 40, GOLD), (470, 640, 50, TERRA)]:
        p.wash(p.soften(p.rough(p.ellipse(x, y, w * 0.6, 30), 4, 14), 4) * river, col, 0.5, rim=0, flow=0.5)
    p.wash(river * p.soften(p.rough(p.ellipse(340, 600, 30, 70), 4, 14), 5), VIOLET, 0.5, rim=0)
    # a few leaves floating, and the near corners deepening
    for _ in range(14):
        x, y = rng.uniform(80, 380), rng.uniform(560, 680)
        p.wash(p.rough(p.ellipse(x, y, rng.uniform(1.4, 2.4), rng.uniform(0.8, 1.4)), 0.3, 1, fine=0.2) * river,
               str(rng.choice([TERRA, GOLD, SIENNA])), 0.9, rim=0.8)
    p.wash(p.soften(p.ellipse(-20, 704, 160, 70), 24) * lbank, UMBER, 0.8, rim=0, flow=0.5, blotch=0.05)
    p.wash(p.soften(p.ellipse(600, 704, 140, 60), 24) * rbank, UMBER, 0.75, rim=0, flow=0.5, blotch=0.05)
    p.finish()
    return p


SCENES = {"city": city, "blossom": blossom, "autumn": autumn}

if __name__ == "__main__":
    for name in sys.argv[1:] or SCENES:
        p = SCENES[name]()
        p.save(f"out/page-{name}.png")
        p.save(f"out/page-{name}-sm.png", (285, 342))
