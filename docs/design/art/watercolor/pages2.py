"""Watercolour title pages for the city, blossom and autumn covers (Josef, 2026-11-23: "do the book screens for
blossom, city and autumn"). Same principles as pages.py: the same place as the cover, a much richer scene; 570 x 684
world units at 2 px; the text corner (x 0-470, y 0-350) left as paper, the sky a wet wash bleeding out into it, the
art climbing on the right. Same abstraction as the covers: big wet patches, simple silhouettes, no fussy detail.

python3 pages2.py [city|blossom|autumn|beach|lighthouse ...] -> out/page-<name>.png (1140 x 1368) and out/page-<name>-sm.png"""
import math
import sys
import numpy as np
sys.path.insert(0, ".")
import pages                                     # configures paint for the page size before anything else loads
from pages import (Paper, blur, smooth, ramp_x, ramp_y, ridge, band, y_at, bleed, sky, blob, cottage, H, W, S, Xw,
                   Yw)
from abstract import (ULTRA, CERUL, PAYNE, SIENNA, RAW, ROSE, SAP, OLIVE, UMBER, TERRA, VIOLET, APRICOT, SAGE, TEAL,
                      CYPRESS, MAUVE, LEMON)
from abstract2 import INDIGO, BLUSH, PINK, GOLDEN, TURQ
import covers
from covers import GOLD, SHADOW, crown, spline, boat, hull_mask, house_masks


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
    # the bridge: a long low deck crossing the whole river, edge to edge (Josef, 2026-11-23: "make the bridge go all
    # the way to the right side"), on broad arches, its lamps a string of warm dots
    dk = 566
    PIERS = [30, 100, 174, 252, 336, 426, 524]            # the spans open up toward the right, coming toward us
    deck = p.rough(p.poly([(-20, dk - 8), (620, dk + 0.4), (620, dk + 7.4), (-20, dk + 1)]), 0.4, 8, fine=0.3)
    piers = np.zeros((H, W), np.float32)
    for px in PIERS:
        y0 = dk - 8 + 5 * (px + 20) / 380
        piers = np.maximum(piers, p.poly([(px - 6, y0), (px + 6, y0), (px + 7, y0 + 30), (px - 7, y0 + 30)]))
    arches = np.zeros((H, W), np.float32)
    for a0, a1 in zip([-34] + PIERS, PIERS + [690]):
        y0 = dk - 4 + 5 * ((a0 + a1) / 2 + 20) / 380
        arches = np.maximum(arches, p.ellipse((a0 + a1) / 2, y0 + 26, (a1 - a0) / 2 - 4, 22) * (Yw > y0 + 3))
    br = p.rough(np.clip(np.maximum(deck, piers) + p.poly([(-20, dk - 6), (620, dk + 2.4), (620, dk + 34),
                                                             (-20, dk + 26)]) - arches, 0, 1), 0.4, 5, fine=0.3)
    p.wash(br, INDIGO, 1.2, rim=1.2, flow=0.4)
    p.wash(br, PAYNE, 0.6, rim=0, flow=0.4)
    for lx in [-4, 22, 60, 84, 132, 170, 214, 236, 290, 330, 372, 410, 452, 494, 536, 576]:
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
    p.loose(ground, [SAGE, LEMON, SAP, SAGE], 0.5, n=6, rough=0.8, patch=0.35, ground=0.7)
    p.loose(p.rough(p.poly([(-20, 640), (300, 620), (600, 650), (600, 704), (-20, 704)]), 3, 24) * ground,
            [SAP, SAGE, LEMON], 0.4, n=3, rough=0.8, patch=0.5, ground=0.7)                 # deeper toward us
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
    for cx, cy, rx, ry in [(500, 400, 70, 50), (540, 330, 52, 50), (520, 260, 46, 40), (494, 312, 30, 30),
                           (440, 420, 54, 32), (380, 448, 50, 26), (330, 460, 36, 18), (560, 420, 40, 44),
                           (575, 270, 30, 40), (490, 455, 50, 22), (410, 400, 36, 26), (548, 214, 30, 26),
                           (575, 360, 30, 40), (300, 470, 24, 12), (470, 370, 40, 30)]:
        cr = np.maximum(cr, p.rough(p.ellipse(cx, cy, rx, ry), ry * 0.3, max(6, rx * 0.4), fine=0.6))
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
    p.loose(anchor, [SAP, SAGE, LEMON], 0.45, n=5, rough=0.9, patch=0.45, ground=0.75)    # the near dark
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
    top = sy - 40 + 38 * smooth(np.abs(Xw - bx), 40, 140)                    # easing down into long low ramps
    body = ((Yw >= top) & (Yw <= sy + 6) & (np.abs(Xw - bx) <= 140))
    hole = ((((Xw - bx) / brr) ** 2 + ((Yw - sy) / (brr * 0.98)) ** 2) < 1) & (Yw < sy + 1)
    body = p.rough(np.clip(body.astype(np.float32) - hole, 0, 1), 0.9, 6, fine=0.5)
    p.lift(np.clip(blur(body, 0.6 * S) * 1.3, 0, 1), 0.9)
    p.loose(body, [SIENNA, RAW, TERRA], 1.25, n=6, rough=0.6, patch=0.4, ground=0.9)
    p.wash(body * ramp_x(bx - 10, bx + 140, 0.0, 1.0), UMBER, 0.6, rim=0, flow=0.4)
    p.lift(body * np.clip(1 - (Yw - top) / 5, 0, 1) * (Yw >= top), 0.35)      # the parapet catching the light
    hole_m = np.clip(blur(hole.astype(np.float32), 0.8 * S) * 1.8, 0, 1)
    p.lift(hole_m, 0.85)
    p.wash(hole_m, VIOLET, 0.9, rim=0.6, flow=0.4)                        # the shade under the arch
    p.wash(hole_m * ramp_y(sy - brr, sy - 6, 1.0, 0.3), UMBER, 1.2, rim=0, flow=0.5)
    p.wash(hole_m * ramp_y(sy - 10, sy, 0.0, 1.0), GOLD, 0.5, rim=0)        # a sliver of far water low down
    for cx, cy, rx, ry, cols in [(150, sy + 4, 14, 7, [OLIVE, SIENNA, RAW]), (412, sy + 4, 15, 7, [SIENNA, OLIVE, GOLD]),
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


# the beach's dusk palette (abstract2.beach)
DEEP, DUSKBLUE, AQUA, BLUSHSEA = "#3E4F7A", "#5E7FA2", "#8FB3B8", "#C99AA8"
PEACH, ROSEGOLD, CORALG, CREAM, NIGHT, LAVSAND = "#F6D2A8", "#F2B8A0", "#E99A8E", "#FBE3B8", "#3A3150", "#D8C4CC"


def cloud_bank(p, cx, by_, ln, th, glow):
    """A sunset cloud bank: soft puffs on a flat base, violet on top, the underside lit coral and peach."""
    crng = np.random.default_rng(int(cx * 7 + by_))
    c = np.zeros((H, W), np.float32)
    for k in range(9):
        px = cx + (k / 8 - 0.5) * ln * 1.6 + crng.uniform(-4, 4)
        rx = ln * crng.uniform(0.16, 0.26)
        ry = th * crng.uniform(0.45, 0.75) * (1 - abs(k / 8 - 0.5) * 0.8)
        c = np.maximum(c, p.ellipse(px, by_ - ry * 0.7, rx, ry))
    c = p.rough(c * (Yw < by_ + 2), th * 0.12, 10, fine=0.6)
    y0, y1 = by_ - th, by_ + 1
    p.wash(c, VIOLET, 0.55, rim=1.2, flow=0.5, blotch=0.08)
    p.wash(c * ramp_y(y0, y1, 1.0, 0.0), MAUVE, 0.35, rim=0)
    lit = c * ramp_y(y0 + th * 0.2, y1 - th * 0.2, 0.0, 1.0)
    p.lift(lit * glow, 0.85)
    p.wash(lit, CORALG, 0.9 * glow, rim=0.7)
    p.wash(lit * ramp_y(y0 + th * 0.55, y1, 0.0, 1.0), PEACH, 1.0 * glow, rim=0)


def palm(p, pts, w0, s, seed, ground):
    """The beach cover's palm: a tapering bowed trunk, a crown of single tapered leaves that arch and droop, all a
    dark violet silhouette against the glow, a hint of green on the upper leaves, a lavender shadow on the sand."""
    wood = np.zeros((H, W), np.float32)
    for i in range(len(pts) - 1):
        ww = w0 * (1 - 0.6 * i / (len(pts) - 1))
        wood = np.maximum(wood, p.stroke([pts[i], pts[i + 1]], ww, taper=False))
    wood = p.rough(wood, 0.8, 8, fine=0.3)
    p.loose(wood, [NIGHT, PAYNE, NIGHT], 1.5, n=3, rough=0.3, patch=0.5, ground=0.9)
    bx, by = pts[0]
    p.wash(p.soften(p.ellipse(bx - 34 * s, by - 8, 40 * s, 5), 2) * ground, LAVSAND, 1.0, rim=0)
    tx, ty = pts[-1]
    lr = np.random.default_rng(300 + seed)
    fr = np.zeros((H, W), np.float32)
    for ang, ln in [(-172, 44), (-146, 38), (-118, 26), (-90, 16), (-62, 26), (-34, 38), (-8, 44), (160, 34), (20, 34)]:
        a = math.radians(ang + lr.uniform(-5, 5))
        l = ln * s * lr.uniform(0.9, 1.1)
        sx, sy = math.cos(a), math.sin(a)
        line = [(tx + sx * l * t, ty + sy * l * t * 0.85 + l * 0.6 * t ** 2) for t in np.linspace(0, 1, 11)]
        fr = np.maximum(fr, p.stroke(line, 5.2 * s, taper=True))
    fr = p.rough(fr, 0.8, 4, fine=0.7)
    p.wash(fr, NIGHT, 1.5, rim=1.4, flow=0.5, blotch=0.08)
    p.wash(fr * ramp_y(ty - 40, ty + 10, 1.0, 0.0), CYPRESS, 0.5, rim=0)
    p.wash(fr * ramp_y(ty, ty + 80, 0.0, 1.0), PAYNE, 0.6, rim=0)


def beach():
    """Off the clock, wider: a soft violet dusk bleeding into the paper and warming through coral to a peach glow,
    banks of cloud lit coral underneath, climbing the right side; the sun half sunk, a far headland on the horizon,
    a small sailboat; the sea deep at the horizon, slate in the middle, aqua in the shallows, the sun's path broken
    peach dashes; foam in broken runs; pale pink-lit sand with lavender shadows; three palms on the right."""
    p = Paper(seed=211)
    rng = np.random.default_rng(212)
    fade = bleed(300, 440, 170)
    hz = 476
    sun = p.rough(p.ellipse(250, hz + 12, 46, 46), 0.4, 6, fine=0.2) * (Yw < hz)
    sky(p, [INDIGO, MAUVE, CORALG, PEACH], [(150, 400, 0.8, 0.0, 0.3), (150, 476, 1.0, 0.3, 0.6),
                                           (250, 470, 0.0, 1.0, 0.7), (330, 476, 0.0, 1.0, 0.85)],
        fade * np.clip(1 - sun, 0, 1) * p.soften(p.poly([(-20, -20), (600, -20), (600, hz + 1), (-20, hz + 1)]), 0.8))
    p.wash(p.soften(p.ellipse(250, hz - 4, 70, 36), 18) * (1 - sun) * (Yw < hz) * fade, APRICOT, 0.45, rim=0)
    p.wash(sun, CREAM, 0.9, rim=1.4)
    # cloud banks: low across the page under the text, higher only on the right
    for cx, by_, ln, th, glow in [(90, 448, 110, 18, 1.0), (330, 426, 150, 26, 0.9), (520, 372, 80, 22, 0.75)]:
        cloud_bank(p, cx, by_, ln, th, glow)
    bar = p.soften(p.rough(p.stroke([(150, hz - 16), (250, hz - 19), (360, hz - 15)], 6), 2, 16), 1.5)
    p.wash(bar, VIOLET, 0.8, rim=0.6)
    p.wash(bar * ramp_y(hz - 24, hz - 12, 1.0, 0.0), PINK, 0.5, rim=0)
    # a far headland on the right of the horizon
    # a far point of land running in from the right edge
    head = p.rough(p.poly([(360, hz + 1), (392, hz - 6), (430, hz - 14), (480, hz - 26), (530, hz - 34),
                           (600, hz - 36), (600, hz + 1)]), 1.2, 12, fine=0.4)
    p.loose(head, [MAUVE, VIOLET, MAUVE], 0.9, n=4, rough=0.6, patch=0.5)
    p.wash(head * ramp_y(hz - 36, hz, 0.0, 1.0), DUSKBLUE, 0.5, rim=0)
    # the sea
    shore = ridge(-20, 600, 580, [(5, 260, 0.6), (3, 90, 1.4)])
    sea = p.rough(p.poly([(-20, hz), (600, hz)] + shore[::-1]), 0.3, 14, fine=0.1)
    p.loose(sea, [DUSKBLUE, DUSKBLUE, DEEP], 0.45, n=4, rough=0.4, patch=0.6, ground=0.9,
            vary=ramp_y(hz, 590, 1.2, 0.5))
    p.wash(sea * ramp_y(hz, hz + 34, 1.0, 0.0), DEEP, 0.5, rim=0)
    p.wash(sea * ramp_y(hz + 60, 590, 0.0, 1.0), AQUA, 0.5, rim=0)
    for cx, cy, rx in [(140, hz + 26, 50), (370, hz + 36, 60)]:
        p.wash(p.soften(p.rough(p.ellipse(cx, cy, rx, 7), 1.5, 12), 3) * sea, BLUSHSEA, 0.5, rim=0)
    path = p.soften(p.poly([(236, hz), (264, hz), (320, 590), (180, 590)]), 5) * sea
    dashes = np.zeros((H, W), np.float32)
    for k in range(22):
        y = hz + 5 + k * 5 + rng.uniform(-1.5, 1.5)
        half = 12 + (y - hz) * 0.5
        for _ in range(2):
            x0 = 250 + rng.uniform(-half, half * 0.3)
            dashes = np.maximum(dashes, p.rough(p.ellipse(x0 + half * 0.35, y, half * rng.uniform(0.3, 0.65), 2.0),
                                                0.6, 6, fine=0.3))
    dashes = dashes * path * sea
    p.lift(np.clip(dashes * 1.2, 0, 1), 0.9)
    p.wash(dashes, PEACH, 0.8, rim=0.6)
    p.wash(dashes * ramp_y(hz, 590, 0.0, 1.0), ROSEGOLD, 0.6, rim=0)
    for x0, x1, y0 in [(-20, 140, 524), (330, 560, 516), (60, 420, 552)]:
        wv = p.soften(p.rough(p.stroke([(x0, y0), ((x0 + x1) / 2, y0 + 2), (x1, y0 - 1)], 6), 1.5, 18), 2) * sea
        p.wash(wv, DUSKBLUE, 0.4, rim=0)
    # a small sailboat far out on the left
    hull = p.rough(p.poly([(96, hz + 22), (132, hz + 22), (126, hz + 28), (102, hz + 28)]), 0.3, 3)
    sail = p.rough(p.poly([(112, hz + 21), (113, hz - 14), (128, hz + 19)]), 0.3, 3)
    p.wash(np.maximum(hull, sail), NIGHT, 1.0, rim=1.0)
    p.lift(sail * ramp_x(112, 128, 0.0, 0.6), 0.4)
    p.wash(sail * ramp_x(112, 128, 0.0, 1.0), CORALG, 0.5, rim=0)               # its sail catching the glow
    p.wash(p.soften(p.ellipse(114, hz + 34, 18, 3), 1.5) * sea, NIGHT, 0.4, rim=0)
    for x0, x1 in [(-20, 90), (150, 330), (380, 470)]:
        seg = [(x, y - 3) for x, y in shore if x0 <= x <= x1]
        if len(seg) > 1:
            p.lift(p.soften(p.rough(p.stroke(seg, 4.5), 1.2, 10), 1.2), 0.5)
    sand = p.rough(p.poly(band(shore, 704)), 0.8, 14, fine=0.3)
    p.loose(sand, [LEMON, BLUSH, PEACH], 0.4, n=7, rough=0.8, patch=0.45, ground=0.75)
    p.wash(sand * ramp_y(600, 684, 0.0, 1.0), VIOLET, 0.5, rim=0, flow=0.5)
    p.wash(sand * ramp_y(630, 684, 0.0, 1.0), MAUVE, 0.35, rim=0, flow=0.5)
    # three palms on the right: the tall one bowing over the beach, one leaning back, a small one in front
    palm(p, [(560, 710), (566, 640), (556, 560), (530, 480), (500, 400), (478, 360)], 18, 2.2, 0, sand)
    palm(p, [(470, 710), (462, 660), (468, 610), (484, 570), (502, 540)], 12, 1.5, 1, sand)
    for cx, cy, rx, ry in [(430, 680, 110, 22), (560, 660, 70, 16)]:              # the palms' ground in shade
        p.wash(p.soften(p.rough(p.ellipse(cx, cy, rx, ry), ry * 0.4, rx * 0.3), ry * 0.4) * sand, LAVSAND, 0.9,
               rim=0.6, flow=0.5)
        p.wash(p.soften(p.ellipse(cx + 10, cy + 4, rx * 0.6, ry * 0.5), ry * 0.4) * sand, VIOLET, 0.5, rim=0)
    p.finish()
    return p


def lighthouse():
    """Keeping the light, by day, wider: a pale cerulean sky bleeding into the paper with clouds left as bare
    paper; the headland on the right climbing high, its grass in loose patches, its cliff warm on the left and
    deep umber on the right; the white tower with its lantern, the keeper's cottage and a shed painted like the
    harbor's houses; surf round rock groups at its foot; a far headland on the left; the harbor's two wooden
    fishing boats moored in the open water; gulls."""
    p = Paper(seed=221)
    rng = np.random.default_rng(222)
    fade = bleed(300, 440, 190)
    hz = 500
    # the headland: a grassy shoulder rising to the right, a cliff face under it
    top = [(300, 532), (330, 516), (370, 500), (410, 486), (450, 474), (490, 462), (530, 452), (570, 446), (600, 444)]
    under = [(600, 520), (560, 526), (520, 532), (480, 540), (440, 548), (400, 556), (360, 560), (320, 560), (296, 552)]
    foot = [(600, 600), (560, 596), (510, 594), (460, 592), (410, 590), (370, 588), (330, 584), (306, 574),
            (290, 560)]
    face = p.rough(p.poly(under[::-1] + foot), 1.4, 9, fine=0.5)
    grass = p.rough(p.poly(top + under), 1.6, 8, fine=0.6)
    land = np.clip(np.maximum(face, grass) * 1.2, 0, 1)
    tx, tb, k = 500, y_at(top, 500) + 6, 2.2
    ty = tb - 106 * k
    tower = p.rough(p.poly([(tx - 9 * k, tb), (tx - 6.5 * k, ty + 16 * k), (tx + 6.5 * k, ty + 16 * k), (tx + 9 * k, tb)]),
                    0.4, 5, fine=0.2)
    # only the lantern's own shape is kept from the sky: the gallery, the lamp room and the roof, never a box
    lantern = np.maximum.reduce([p.poly([(tx - 22, ty + 18 * k), (tx + 22, ty + 18 * k), (tx + 22, ty + 15 * k),
                                         (tx - 22, ty + 15 * k)]),
                                 p.poly([(tx - 11, ty + 15 * k), (tx + 11, ty + 15 * k), (tx + 11, ty + 7 * k),
                                         (tx - 11, ty + 7 * k)]),
                                 p.poly([(tx - 15, ty + 7.5 * k), (tx + 15, ty + 7.5 * k), (tx, ty - 1 * k)])])
    keep = np.clip(np.maximum(tower, lantern), 0, 1)
    boats = [(30, 606, 200, CERUL, TERRA, 220), (236, 640, 160, RAW, CERUL, None)]
    hulls = np.clip((np.maximum.reduce([blur(hull_mask(p, bx, by, bw), 0.6 * S) for bx, by, bw, *_ in boats]) - 0.7)
                    * 6, 0, 1)
    around = (1 - np.maximum(land, keep)) * (1 - hulls)
    # 1 the sky: pale cerulean bleeding into the paper, clouds left as paper, rose low on the left
    skym = fade * p.soften(p.poly([(-20, -20), (600, -20), (600, hz + 2), (-20, hz + 2)]), 1)
    clouds = np.maximum.reduce([p.soften(p.rough(p.ellipse(x, y, rx, ry), ry * 0.4, rx * 0.3), 10) for x, y, rx, ry in
                                [(90, 450, 80, 14), (300, 440, 70, 12), (420, 400, 50, 16), (560, 330, 50, 22),
                                 (200, 470, 60, 6)]])
    p.wash(skym * (1 - clouds * 0.95) * around, CERUL, 0.65, rim=1.4, flow=0.35, blotch=0.06,
           vary=ramp_y(300, 490, 1.0, 0.6))
    p.wash(p.soften(p.poly([(-20, 450), (240, 460), (300, 504), (-20, 504)]), 16) * skym * around, ROSE, 0.5, rim=0,
           flow=0.3)
    p.wash(p.soften(p.poly([(400, 200), (600, 180), (600, 380), (440, 400)]), 20) * skym * around, ULTRA, 0.3, rim=0,
           flow=0.4)
    # 2 a far headland on the left
    p.wash(p.rough(p.poly([(-10, hz + 1), (20, hz - 12), (70, hz - 20), (120, hz - 16), (170, hz - 6),
                           (200, hz + 1)]), 1.0, 8), ULTRA, 0.5, rim=1.4, flow=0.25)
    # 3 the sea, darkening toward us, ripples lifted dry
    sea = p.rough(p.poly([(-20, hz), (600, hz), (600, 704), (-20, 704)]), 0.4, 12)
    p.wash(sea * around, CERUL, 0.8, rim=1.0, flow=0.3, blotch=0.06, vary=ramp_y(hz, 684, 0.7, 1.2))
    p.wash(p.soften(p.poly([(-20, 580), (600, 572), (600, 704), (-20, 704)]), 20) * around, ULTRA, 0.45, rim=0,
           flow=0.35, vary=ramp_y(572, 684, 0.3, 1.0))
    for x, y, w in [(20, 514, 110), (150, 526, 80)]:                                 # a few long soft ripples
        p.lift(p.soften(p.rough(p.poly([(x, y), (x + w, y - 0.6), (x + w, y + 2), (x, y + 2.6)]), 0.8, 8), 1.2)
               * around, 0.45)
    # 4 the cliff and the grass in loose wet patches, the rock deepening to umber on the right
    p.loose(face, [RAW, SIENNA, RAW, UMBER], 1.0, n=12, rough=0.6, patch=0.35)
    p.wash(face * ramp_x(440, 580, 0.0, 1.0), UMBER, 0.6, rim=0.6, flow=0.5, blotch=0.07)
    p.wash(face * ramp_y(560, 596, 0.0, 1.0), PAYNE, 0.45, rim=0, flow=0.4)
    p.loose(grass, [SAP, OLIVE, RAW, SAP], 0.95, n=14, rough=0.6, patch=0.3)
    p.wash(grass * ramp_x(380, 600, 0.0, 1.0), OLIVE, 0.4, rim=0.2, flow=0.4)
    p.wash(p.soften(p.stroke(under[::-1], 10, taper=False), 4) * np.maximum(face, grass), OLIVE, 0.45, rim=0, flow=0.5)
    # 5 rocks at the waterline and the surf lifted round them
    for x, y, rx, ry in [(470, 600, 26, 9), (360, 594, 12, 5), (296, 572, 6, 3), (560, 610, 18, 6)]:
        r = p.rough(p.ellipse(x, y, rx, ry), rx * 0.15, 3, fine=0.4)
        p.wash(r, UMBER, 1.0, rim=1.0, gran=0.4)
        p.wash(r * ramp_y(y - ry * 0.2, y + ry, 0.0, 1.0), PAYNE, 1.1, rim=0.4)
    for pts, w in [([(286, 566), (320, 586), (380, 594), (440, 600), (510, 606), (600, 608)], 10),
                   ([(450, 626), (520, 632), (600, 634)], 6)]:              # soft wet surf hugging the cliff's foot
        p.lift(p.soften(p.rough(p.stroke(pts, w), 2.0, 14, fine=0.5), 2.5) * (1 - face), 0.75)
    near = p.rough(p.poly([(-20, 660), (150, 652), (330, 664), (600, 650), (600, 704), (-20, 704)]), 4, 30, fine=0.5)
    p.wash(near * around, ULTRA, 0.6, rim=1.2, flow=0.5, blotch=0.08)                 # the near water, deeper
    p.wash(p.soften(p.rough(p.poly([(300, 600), (600, 610), (600, 650), (360, 640)]), 4, 20), 6) * around, ULTRA,
           0.45, rim=0)                                                                 # the headland's shadow
    # 6 the lighthouse: the left face bare paper, the right a soft cool shadow, two bands, the lantern lit
    shade = p.soften(p.poly([(tx + 1, tb), (tx + 1, ty + 16 * k), (tx + 7.5 * k, ty + 16 * k), (tx + 10 * k, tb)]), 3)
    p.loose(shade * np.clip(tower * 1.15, 0, 1), [ULTRA, SHADOW, ULTRA], 0.55, n=5, rough=0.2, patch=0.5,
            vary=ramp_x(tx - 4, tx + 20, 0.2, 1.0))
    for yb in (ty + 46 * k, ty + 76 * k):
        p.wash(p.rough(p.poly([(tx - 20, yb), (tx + 20, yb), (tx + 20, yb + 9), (tx - 20, yb + 9)]), 0.5, 4) * tower,
               SHADOW, 0.3, rim=0.8, flow=0.4)
    p.wash(p.rough(p.poly([(tx - 22, ty + 18 * k), (tx + 22, ty + 18 * k), (tx + 22, ty + 15 * k), (tx - 22, ty + 15 * k)]),
                   0.4, 3), PAYNE, 1.2, rim=0.5)                                          # the gallery
    p.wash(p.rough(p.poly([(tx - 11, ty + 15 * k), (tx + 11, ty + 15 * k), (tx + 11, ty + 7 * k), (tx - 11, ty + 7 * k)]),
                   0.4, 3), GOLD, 1.0, rim=1.2, flow=0.4)                                 # the lamp room
    p.wash(p.rough(p.poly([(tx - 15, ty + 7.5 * k), (tx + 15, ty + 7.5 * k), (tx, ty - 1 * k)]), 0.4, 3), PAYNE, 1.4,
           rim=0.6)
    p.wash(p.rough(p.poly([(tx - 6, tb - 2), (tx - 6, tb - 14), (tx - 1, tb - 14), (tx - 1, tb - 2)]), 0.3, 2), PAYNE,
           0.8, rim=0.4)
    # 7 the keeper's cottage and a shed, painted like the harbor's houses
    for hx, hw, hh, hd in [(400, 36, 22, 10), (448, 20, 14, 6)]:
        hb = y_at(top, hx + hw / 2) + 5
        front, side, roof = (p.rough(m, 0.6, 4, fine=0.3) for m in house_masks(p, hx, hb, hw, hh, hd, "tile"))
        p.lift(np.clip(blur(np.maximum.reduce([front, side, roof]), 0.4 * S) * 1.4, 0, 1), 0.9)
        p.wash(front, RAW, 0.16, rim=1.0, flow=0.4, blotch=0.04)
        p.loose(side, [SHADOW, ULTRA, SHADOW], 0.7, n=3, rough=0.2, patch=0.7)
        p.loose(roof, [TERRA, SIENNA, TERRA], 0.95, n=4, rough=0.2, patch=0.6)
        eave = p.rough(p.poly([(hx, hb - hh), (hx + hw, hb - hh), (hx + hw, hb - hh + 4), (hx, hb - hh + 3)]), 0.4, 3)
        p.wash(eave * front, SHADOW, 0.55, rim=0.2)
        for wx in ([hx + 6, hx + 24] if hw > 30 else [hx + 7]):
            p.wash(p.rough(p.poly([(wx, hb - 15), (wx + 4, hb - 15), (wx + 4, hb - 9), (wx, hb - 9)]), 0.2, 1) * front,
                   PAYNE, 0.85, rim=0.3)
        if hw > 30:
            p.wash(p.rough(p.poly([(hx + 15, hb), (hx + 15, hb - 10), (hx + 20, hb - 10), (hx + 20, hb)]), 0.2, 1)
                   * front, UMBER, 0.9, rim=0.3)
    # 8 the harbor's two boats, moored in the open water
    for bx, by, bw, hull, trim, mast in boats:
        boat(p, bx, by, bw, hull, trim, mast=mast)
    # 9 gulls
    for x, y, g in [(140, 420, 7), (176, 432, 5.5), (330, 390, 6)]:
        left = [(x - g + g * u, y - g * 0.55 * math.sin(math.pi * u) * (1.2 - u)) for u in np.linspace(0, 1, 8)]
        right = [(x + g * u, y - g * 0.55 * math.sin(math.pi * u) * (0.2 + u)) for u in np.linspace(0, 1, 8)]
        p.wash(np.maximum(p.stroke(left, 1.3), p.stroke(right, 1.3)), PAYNE, 1.4, rim=0, gran=0)
    p.finish()
    return p


def lighthouse_dusk():
    """Keeping the light, at dusk, wider (Josef, 2026-11-23: "add a beam of light from the lighthouse at dusk, and
    then make a book screen for it"): the cover's dusk, indigo climbing the right side with the evening star and a few
    stars, melting through violet and rose to a gold band on the horizon, long dark clouds lit gold underneath; the
    headland on the right climbing high, gone cool and dark; the white tower holding the last light, its lantern lit
    and the beam lifted out of the wet sky, sweeping left across the page and dissolving where the sky meets the
    paper; the keeper's cottage with two lit windows; the sunset laid on the water; surf round the rocks."""
    from covers import GOLD_D
    p = Paper(seed=231)
    fade = bleed(290, 430, 250)   # lower than at first: Josef found the dark top made the text hard to read
    hz = 500
    top = [(300, 532), (330, 516), (370, 500), (410, 486), (450, 474), (490, 462), (530, 452), (570, 446), (600, 444)]
    under = [(600, 520), (560, 526), (520, 532), (480, 540), (440, 548), (400, 556), (360, 560), (320, 560), (296, 552)]
    foot = [(600, 600), (560, 596), (510, 594), (460, 592), (410, 590), (370, 588), (330, 584), (306, 574),
            (290, 560)]
    face = p.rough(p.poly(under[::-1] + foot), 1.4, 9, fine=0.5)
    grass = p.rough(p.poly(top + under), 1.6, 8, fine=0.6)
    land = np.clip(np.maximum(face, grass) * 1.2, 0, 1)
    tx, tb, k = 500, y_at(top, 500) + 6, 2.2
    ty = tb - 106 * k
    tower = p.rough(p.poly([(tx - 9 * k, tb), (tx - 6.5 * k, ty + 16 * k), (tx + 6.5 * k, ty + 16 * k), (tx + 9 * k, tb)]),
                    0.4, 5, fine=0.2)
    lantern = np.maximum.reduce([p.poly([(tx - 22, ty + 18 * k), (tx + 22, ty + 18 * k), (tx + 22, ty + 15 * k),
                                         (tx - 22, ty + 15 * k)]),
                                 p.poly([(tx - 11, ty + 15 * k), (tx + 11, ty + 15 * k), (tx + 11, ty + 7 * k),
                                         (tx - 11, ty + 7 * k)]),
                                 p.poly([(tx - 15, ty + 7.5 * k), (tx + 15, ty + 7.5 * k), (tx, ty - 1 * k)])])
    keep = np.clip(np.maximum(tower, lantern), 0, 1)
    around = 1 - np.maximum(land, keep)
    # 1 the dusk sky, bleeding into the paper: indigo high on the right, violet, rose, then gold on the horizon
    skym = fade * p.soften(p.poly([(-20, -20), (600, -20), (600, hz + 2), (-20, hz + 2)]), 1)
    stars = [(560, 176, 2.4), (512, 206, 1.2), (590, 146, 1.2), (482, 232, 1.0), (578, 300, 1.1), (548, 334, 0.9),
             (600, 214, 0.8)]
    starm = np.maximum.reduce([p.soften(p.ellipse(x, y, r, r), r * 0.5) for x, y, r in stars])
    sk = skym * around * (1 - starm)
    sky(p, [ULTRA, PAYNE, VIOLET, ROSE], [(0, 470, 1.0, 0.15, 1.3), (0, 360, 1.0, 0.0, 0.9),
                                         (300, 470, 0.0, 1.0, 0.9), (420, 500, 0.0, 1.0, 0.9)], sk)
    p.wash(p.soften(p.poly([(-20, 470), (380, 462), (600, 474), (600, 503), (-20, 503)]), 10) * sk, GOLD_D, 1.0,
           rim=0, flow=0.4, blotch=0.05)
    p.wash(p.soften(p.ellipse(560, 176, 9, 9), 5) * skym * (1 - starm), LEMON, 0.35, rim=0)       # the evening star
    # the night gathers round the tower so its beam has a dark sky to cut through
    night = p.soften(p.rough(p.ellipse(570, 310, 150, 100), 14, 40), 44) * around * (1 - starm)
    p.wash(night, ULTRA, 0.8, rim=0, flow=0.4, blotch=0.05)
    p.wash(night, PAYNE, 0.5, rim=0, flow=0.4)
    for x, y, w, h in [(40, 452, 190, 8), (150, 474, 150, 6), (290, 440, 150, 9), (420, 410, 120, 7)]:
        cl = p.soften(p.rough(p.stroke([(x, y), (x + w * 0.5, y - 3), (x + w, y - 1)], h), 3, 18, fine=0.6), 2.5)
        p.wash(cl * sk, PAYNE, 0.6, rim=0.8, flow=0.4, blotch=0.05)                             # long dusk clouds
        lit = p.soften(p.rough(p.stroke([(x + 8, y + h * 0.35), (x + w - 12, y + h * 0.35 - 1.2)], h * 0.35), 2, 14), 1.2)
        p.wash(lit * sk, GOLD_D, 0.6, rim=0.2, flow=0.4)                                       # their undersides lit
    # 2 the beam: lifted out of the wet sky with a damp brush, a narrow core in a wider glow, widening and fading
    # as it sweeps left; over bare paper it simply ends, so the text corner stays clean
    lx, ly = tx - 10, ty + 11 * k
    # the cover's angle (it drops about one unit in eight), and it is spent by x ~330, inside the blue
    gone = ramp_x(250, lx, 0.0, 1.0) ** 0.8
    broken = np.clip(0.55 + 0.9 * (pages.warped(40 * S, 77) - 0.5), 0, 1)
    glow = p.soften(p.rough(p.poly([(lx, ly - 6), (-40, ly + 40), (-40, ly + 150), (lx, ly + 8)]), 4, 18), 12) * gone
    core = p.soften(p.rough(p.poly([(lx, ly - 3), (-40, ly + 52), (-40, ly + 98), (lx, ly + 5)]), 2, 14, fine=0.4), 2.5)
    core = core * gone
    stub = p.soften(p.poly([(tx + 10, ly - 4), (620, ly - 30), (620, ly + 4), (tx + 10, ly + 6)]), 6)
    beam = np.clip(np.maximum((glow * 0.55 + core * 0.7) * (0.45 + 0.55 * broken), stub * 0.85), 0, 1) * around
    p.lift(beam, 0.85)
    near = ramp_x(lx - 150, lx, 0.0, 1.0)
    p.wash(beam * fade * near, GOLD_D, 0.55, rim=0, flow=0.5, blotch=0.04)          # warm only near the lamp
    # 3 a far headland on the left, cool
    p.wash(p.rough(p.poly([(-10, hz + 1), (20, hz - 12), (70, hz - 20), (120, hz - 16), (170, hz - 6),
                           (200, hz + 1)]), 1.0, 8), ULTRA, 0.75, rim=1.4, flow=0.25)
    # 4 the sea: ultramarine and violet darkening toward us, the sunset laid on it as one soft lifted glow
    sea = p.rough(p.poly([(-20, hz), (600, hz), (600, 704), (-20, 704)]), 0.4, 12)
    p.wash(sea * around, ULTRA, 1.2, rim=1.0, flow=0.3, blotch=0.06, vary=ramp_y(hz, 684, 0.6, 1.3))
    p.wash(sea * around, VIOLET, 0.6, rim=0, flow=0.3, blotch=0.05)
    gl = p.soften(p.rough(p.ellipse(170, 520, 130, 26), 6, 20), 14) * around * ramp_y(502, 600, 1.0, 0.0)
    p.lift(gl, 0.45)
    p.wash(gl, GOLD_D, 0.8, rim=0, flow=0.5, blotch=0.05)
    p.wash(p.soften(p.poly([(-20, 590), (600, 580), (600, 704), (-20, 704)]), 20) * around, PAYNE, 0.5, rim=0,
           flow=0.35, vary=ramp_y(580, 684, 0.3, 1.0))
    # 5 the cliff and the grass in loose wet patches, then glazed cool: the land has lost the light
    p.loose(face, [RAW, SIENNA, RAW, UMBER], 1.0, n=12, rough=0.6, patch=0.35)
    p.wash(face * ramp_x(440, 580, 0.0, 1.0), UMBER, 0.6, rim=0.6, flow=0.5, blotch=0.07)
    p.loose(grass, [SAP, OLIVE, RAW, SAP], 0.95, n=14, rough=0.6, patch=0.3)
    p.wash(p.soften(p.stroke(under[::-1], 10, taper=False), 4) * np.maximum(face, grass), OLIVE, 0.45, rim=0, flow=0.5)
    p.wash(land, ULTRA, 0.95, rim=0.3, flow=0.4, blotch=0.05, vary=ramp_x(300, 600, 0.6, 1.2))
    p.wash(land, PAYNE, 0.35, rim=0.2, flow=0.4, vary=ramp_x(300, 600, 0.3, 1.2))
    # 6 rocks at the waterline and the surf lifted round them, pale blue-grey in the dusk
    for x, y, rx, ry in [(470, 600, 26, 9), (360, 594, 12, 5), (296, 572, 6, 3), (560, 610, 18, 6)]:
        r = p.rough(p.ellipse(x, y, rx, ry) * (Yw < y + ry * 0.3), rx * 0.12, 3, fine=0.4)   # sits on a flat waterline
        p.wash(r, UMBER, 1.0, rim=1.0, gran=0.4)
        p.wash(r * ramp_y(y - ry * 0.2, y + ry * 0.3, 0.0, 1.0), PAYNE, 1.2, rim=0.4)
        p.wash(r * ramp_x(x - rx, x, 1.0, 0.0) * ramp_y(y - ry, y, 1.0, 0.0), SIENNA, 0.6, rim=0)   # lit top-left
    for pts, w in [([(286, 566), (320, 586), (380, 594), (440, 600), (510, 606), (600, 608)], 10),
                   ([(450, 626), (520, 632), (600, 634)], 6)]:
        fm = p.soften(p.rough(p.stroke(pts, w), 2.0, 14, fine=0.5), 2.5) * (1 - face)
        p.lift(fm, 0.55)
        p.wash(fm, SHADOW, 0.35, rim=0.6, flow=0.3)
    near = p.rough(p.poly([(-20, 660), (150, 652), (330, 664), (600, 650), (600, 704), (-20, 704)]), 4, 30, fine=0.5)
    p.wash(near * around, ULTRA, 0.6, rim=1.2, flow=0.5, blotch=0.08)
    # 7 the lighthouse holds the last light: a rose glaze on the left face, the right in violet shadow, two bands,
    # the lamp room lit gold with its lamp lifted, a soft halo round it
    shade = p.soften(p.poly([(tx + 1, tb), (tx + 1, ty + 16 * k), (tx + 7.5 * k, ty + 16 * k), (tx + 10 * k, tb)]), 3)
    p.wash(tower, ROSE, 0.22, rim=0.8, flow=0.4, blotch=0.04)
    p.loose(shade * np.clip(tower * 1.15, 0, 1), [VIOLET, ULTRA, VIOLET], 0.8, n=5, rough=0.2, patch=0.5,
            vary=ramp_x(tx - 4, tx + 20, 0.2, 1.0))
    p.wash(tower * ramp_x(tx + 4, tx + 20, 0.0, 1.0), ULTRA, 0.35, rim=0.4, flow=0.3)
    for yb in (ty + 46 * k, ty + 76 * k):
        p.wash(p.rough(p.poly([(tx - 20, yb), (tx + 20, yb), (tx + 20, yb + 9), (tx - 20, yb + 9)]), 0.5, 4) * tower,
               VIOLET, 0.75, rim=1.0, flow=0.4)
    room = p.rough(p.poly([(tx - 11, ty + 15 * k), (tx + 11, ty + 15 * k), (tx + 11, ty + 7 * k), (tx - 11, ty + 7 * k)]),
                   0.4, 3)
    p.wash(room, GOLD_D, 1.1, rim=0.8, flow=0.4)
    p.wash(room * ramp_x(tx - 2, tx + 11, 0.0, 1.0), SIENNA, 0.6, rim=0)
    p.lift(room * p.soften(p.ellipse(tx - 2, ty + 11.5 * k, 4.5, 5.5), 2.0), 0.6)
    for mx in (tx - 5, tx + 5):
        p.wash(p.rough(p.stroke([(mx, ty + 7.5 * k), (mx, ty + 14.5 * k)], 1.2, taper=False), 0.1, 1), PAYNE, 1.2, rim=0)
    p.wash(p.rough(p.poly([(tx - 22, ty + 18 * k), (tx + 22, ty + 18 * k), (tx + 22, ty + 15 * k), (tx - 22, ty + 15 * k)]),
                   0.4, 3), PAYNE, 2.2, rim=0.5)                                          # the gallery
    p.wash(p.rough(p.poly([(tx - 15, ty + 7.5 * k), (tx + 15, ty + 7.5 * k), (tx, ty - 1 * k)]), 0.4, 3), PAYNE, 2.4,
           rim=0.6)
    halo = p.soften(p.ellipse(tx, ty + 11 * k, 36, 30), 14) * (1 - np.clip(tower * 1.2, 0, 1)) * (1 - lantern)
    p.lift(halo * fade, 0.5)
    p.wash(halo * fade, GOLD_D, 0.6, rim=0, flow=0.3, blotch=0.03)
    p.wash(p.rough(p.poly([(tx - 6, tb - 2), (tx - 6, tb - 14), (tx - 1, tb - 14), (tx - 1, tb - 2)]), 0.3, 2), PAYNE,
           0.9, rim=0.4)
    # 8 the keeper's cottage and a shed, cool in the dusk, two windows lit
    for hx, hw, hh, hd in [(400, 36, 22, 10), (448, 20, 14, 6)]:
        hb = y_at(top, hx + hw / 2) + 5
        front, side, roof = (p.rough(m, 0.6, 4, fine=0.3) for m in house_masks(p, hx, hb, hw, hh, hd, "tile"))
        p.lift(np.clip(blur(np.maximum.reduce([front, side, roof]), 0.4 * S) * 1.4, 0, 1), 0.9)
        p.wash(front, ROSE, 0.3, rim=1.0, flow=0.4, blotch=0.04)
        p.wash(front, VIOLET, 0.35, rim=0.4, flow=0.4)
        p.loose(side, [ULTRA, VIOLET, ULTRA], 0.85, n=3, rough=0.2, patch=0.7)
        p.loose(roof, [UMBER, SIENNA, UMBER], 1.0, n=4, rough=0.2, patch=0.6)
        for wx in ([hx + 6, hx + 24] if hw > 30 else []):
            p.wash(p.rough(p.poly([(wx, hb - 15), (wx + 4, hb - 15), (wx + 4, hb - 9), (wx, hb - 9)]), 0.2, 1) * front,
                   GOLD_D, 1.3, rim=0.6)
    p.finish()
    return p


SCENES = {"city": city, "blossom": blossom, "autumn": autumn, "beach": beach, "lighthouse": lighthouse,
          "lighthouse-dusk": lighthouse_dusk}

if __name__ == "__main__":
    for name in sys.argv[1:] or SCENES:
        p = SCENES[name]()
        p.save(f"out/page-{name}.png")
        p.save(f"out/page-{name}-sm.png", (285, 342))
