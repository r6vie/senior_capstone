"""Watercolour covers, set 1 (Josef, 2026-11-21: "a new page ... 10 watercolor theme books, make the first three and
obsess over them, only covers"). Illustrated watercolour, not a photograph and not abstract strokes: a clear subject
built from a few transparent glazes, wet-in-wet skies, pooled hard edges, granulation, and bare white paper doing the
work of every white in the picture. The title and name sit on bare paper at the top; left of world x ~200 the paint
stays below y ~180 (the shelf-size name line), only the right edge may rise higher.

python3 covers.py [lighthouse|harbor|autumn ...] -> out/<name>-xl.png (944 x 1376) and out/<name>-sm.png (352 x 514)"""
import math
import sys
import numpy as np
sys.path.insert(0, ".")
from paint import Paper, ramp_y, ramp_x, fbm, blur, S, W, H

# pigments as the colour each one lets through (transmittance); density sets how strong a wash is
ULTRA = "#5B74B8"        # ultramarine
CERUL = "#7FB2D6"        # cerulean
PAYNE = "#4A5868"        # payne's grey
SIENNA = "#C98A5A"       # burnt sienna
RAW = "#E6C487"          # raw sienna
ROSE = "#E3A3A0"         # a quiet rose, nowhere near the UI red
SAP = "#8FB06A"          # sap green
OLIVE = "#9A9A5C"
UMBER = "#8A6F5A"
GOLD_D = "#EBB86A"        # the deeper gold of a sunset band


def lighthouse():
    """Keeping the light: a white lighthouse on a grassy headland on the right, the only thing above the name
    line; a wet-in-wet morning sky with clouds left as bare paper and one backrun, warm low on the left; the sea in
    glazes darkening toward us; the cliff lit warm on its left, deep in shadow on its right (the dark anchor); surf
    dragged dry round three rock groups at its foot; a far headland and two gulls."""
    p = Paper(seed=11)
    rng = np.random.default_rng(5)
    tx, ty, tb = 206, 112, 218
    tower = p.rough(p.poly([(tx - 9, tb), (tx - 6.5, ty + 16), (tx + 6.5, ty + 16), (tx + 9, tb)]), 0.25, 3, fine=0.2)
    lantern = p.poly([(tx - 8, ty + 16), (tx + 8, ty + 16), (tx + 8, ty + 4), (tx - 8, ty + 4)])
    keep_white = np.clip(np.maximum(tower, lantern), 0, 1)
    # the headland: a long grassy shoulder that dips, a cliff face below it
    top = [(104, 256), (116, 246), (134, 238), (156, 231), (178, 224), (200, 217), (222, 212), (260, 210)]
    under = [(260, 240), (226, 244), (200, 250), (176, 256), (152, 262), (130, 266), (112, 266), (102, 262)]
    foot = [(260, 282), (234, 280), (208, 280), (184, 279), (160, 278), (140, 277), (122, 276), (108, 272),
            (98, 266)]
    face = p.rough(p.poly(under[::-1] + foot), 0.9, 5, fine=0.5)
    grass = p.rough(p.poly(top + under), 1.0, 4, fine=0.6)
    land = np.clip(np.maximum(face, grass) * 1.2, 0, 1)
    around = 1 - np.maximum(land, keep_white)
    # 1 sky at dusk, over the whole cover: deep indigo at the top, melting wet-in-wet through violet and rose to a
    # band of gold on the horizon; a few long clouds lifted pale; the title sits in cream on the dark top
    full = np.ones((H, W), np.float32)
    p.wash(full * around, ULTRA, 1.7, rim=1.2, flow=0.3, blotch=0.06, vary=ramp_y(0, 236, 1.0, 0.15))
    p.wash(full * around, PAYNE, 0.9, rim=0.6, flow=0.35, blotch=0.06, vary=ramp_y(0, 170, 1.0, 0.0))
    p.wash(p.soften(p.poly([(-20, 150), (260, 140), (260, 236), (-20, 236)]), 18) * around, VIOLET, 0.9, rim=0,
           flow=0.4, blotch=0.05)
    p.wash(p.soften(p.poly([(-20, 196), (260, 190), (260, 252), (-20, 252)]), 10) * around, ROSE, 0.9, rim=0,
           flow=0.4, blotch=0.05)
    p.wash(p.soften(p.poly([(-20, 224), (200, 220), (260, 230), (260, 252), (-20, 252)]), 6) * around, GOLD_D, 1.0,
           rim=0, flow=0.4, blotch=0.05)
    for x, y, w, h in [(-10, 204, 100, 5), (60, 214, 80, 4), (130, 196, 80, 5)]:
        cl = p.soften(p.rough(p.stroke([(x, y), (x + w * 0.5, y - 1.5), (x + w, y - 0.5)], h), 1.6, 10, fine=0.6), 1.2)
        p.wash(cl * around, PAYNE, 0.55, rim=0.8, flow=0.4, blotch=0.05)               # long dusk clouds
        under_lit = p.soften(p.rough(p.stroke([(x + 4, y + h * 0.35), (x + w - 6, y + h * 0.35 - 0.6)], h * 0.35),
                                     1.0, 8), 0.6)
        p.wash(under_lit * around, GOLD_D, 0.6, rim=0.2, flow=0.4)                    # their undersides lit
    # 2 far headland
    p.wash(p.rough(p.poly([(-6, 251), (6, 245), (22, 241), (40, 242), (58, 247), (74, 251)]), 0.8, 5),
           ULTRA, 0.5, rim=1.4, flow=0.25, blotch=0.05)
    # 3 the sea
    sea = p.rough(p.poly([(-20, 251), (260, 251), (260, 360), (-20, 360)]), 0.3, 8)
    p.wash(sea * around, ULTRA, 1.2, rim=1.0, flow=0.3, blotch=0.06, vary=ramp_y(251, 344, 0.6, 1.3))
    p.wash(sea * around, VIOLET, 0.6, rim=0, flow=0.3, blotch=0.05)
    gl = p.soften(p.rough(p.ellipse(56, 262, 46, 14), 4, 10), 7) * around * ramp_y(252, 300, 1.0, 0.0)
    p.lift(gl, 0.45)
    p.wash(gl, GOLD_D, 0.8, rim=0, flow=0.5, blotch=0.05)                            # the sunset in the water
    p.wash(p.soften(p.poly([(-20, 290), (260, 286), (260, 360), (-20, 360)]), 10) * around, PAYNE, 0.5, rim=0,
           flow=0.35, blotch=0.06, vary=ramp_y(286, 344, 0.3, 1.0))
    p.wash(p.soften(p.ellipse(54, 272, 22, 22), 8) * around * ramp_y(252, 300, 1.0, 0.0), RAW, 0.25, rim=0,
           flow=0.4)                                                                 # one soft glow, no dashes
    p.wash(p.soften(p.rough(p.poly([(-20, 312), (150, 304), (200, 318), (-20, 330)]), 3, 14), 4) * around, ULTRA,
           0.3, rim=0, flow=0.4, blotch=0.04)
    # 4 the rocky edge and the grass, both built from loose wet patches; the grass glaze runs down into the ochre
    # of the rock wet-in-wet, so there is no seam; the rock deepens to umber on the right, the dark anchor
    p.loose(face, [RAW, SIENNA, RAW, UMBER], 1.0, n=9, rough=0.6, patch=0.35)
    p.wash(face * ramp_x(200, 250, 0.0, 1.0), UMBER, 0.6, rim=0.6, flow=0.5, blotch=0.07)
    p.wash(face * ramp_y(268, 282, 0.0, 1.0), PAYNE, 0.45, rim=0, flow=0.4)
    p.loose(grass, [SAP, OLIVE, RAW, SAP], 0.95, n=10, rough=0.6, patch=0.3)
    p.wash(grass * ramp_x(150, 250, 0.0, 1.0), OLIVE, 0.4, rim=0.2, flow=0.4, blotch=0.05)
    p.wash(p.soften(p.stroke(under[::-1], 5.0, taper=False), 2.0) * np.maximum(face, grass), OLIVE, 0.45, rim=0,
           flow=0.5, blotch=0.05)                                             # the green bleeding into the rock
    p.wash(np.maximum(face, grass), ULTRA, 0.95, rim=0.3, flow=0.4, blotch=0.05,
           vary=ramp_x(100, 250, 0.6, 1.2))                                  # dusk: the land goes cool
    p.wash(np.maximum(face, grass), PAYNE, 0.35, rim=0.2, flow=0.4, vary=ramp_x(100, 250, 0.3, 1.2))
    # 5 three rock groups at the waterline, two values each; the surf lifted as broad, broken paper round them
    for i, (x, y, rx, ry) in enumerate([(176, 282, 12, 4), (124, 279, 5, 2.2), (92, 270, 2.6, 1.2)]):
        r = p.rough(p.ellipse(x, y, rx, ry), rx * 0.15, 2, fine=0.4)
        p.wash(r, UMBER, 1.0, rim=1.0, gran=0.4, blotch=0.05)
        p.wash(r * ramp_y(y - ry * 0.2, y + ry, 0.0, 1.0), PAYNE, 1.1, rim=0.4, blotch=0.04)
    for i, (pts, w) in enumerate([([(84, 272), (110, 280), (146, 285), (176, 290), (210, 290), (250, 292)], 4.5),
                                  ([(150, 296), (190, 300), (230, 302)], 2.6)]):
        fm = p.soften(p.rough(p.stroke(pts, w * 0.7), 1.0, 8, fine=0.4), 0.4) * (1 - face)
        p.lift(fm, 0.35)
        p.wash(fm, SHADOW, 0.35, rim=0.6, flow=0.3)                                  # foam, pale blue-grey
    # 6 the lighthouse: a tapered tower, its left face bare paper, the right face a soft cool shadow built loose,
    # two faint bands, the lantern one warm glaze under a dark cap; the cottage a cream block standing on the grass
    shade = p.soften(p.poly([(tx + 0.5, tb), (tx + 0.5, ty + 16), (tx + 7.5, ty + 16), (tx + 10, tb)]), 2.0)
    p.wash(tower, ROSE, 0.22, rim=0.8, flow=0.4, blotch=0.04)
    p.loose(shade * np.clip(tower * 1.15, 0, 1), [VIOLET, ULTRA, VIOLET], 0.8, n=5, rough=0.2, patch=0.5,
            vary=ramp_x(tx - 2, tx + 9, 0.2, 1.0))
    p.wash(shade * np.clip(tower * 1.15, 0, 1), SIENNA, 0.12, rim=0.4)
    p.wash(tower * ramp_x(tx + 2, tx + 9, 0.0, 1.0), ULTRA, 0.35, rim=0.4, flow=0.3)  # the shaded right third
    for yb in (ty + 46, ty + 76):
        p.wash(p.rough(p.poly([(tx - 9, yb), (tx + 9, yb), (tx + 9, yb + 4), (tx - 9, yb + 4)]), 0.3, 3) * tower,
               VIOLET, 0.75, rim=1.0, flow=0.4)
    p.wash(p.rough(p.poly([(tx - 10, ty + 18), (tx + 10, ty + 18), (tx + 10, ty + 15), (tx - 10, ty + 15)]), 0.25, 2),
           PAYNE, 1.2, rim=0.5)                                                # the gallery
    p.wash(p.rough(p.poly([(tx - 5, ty + 15), (tx + 5, ty + 15), (tx + 5, ty + 7), (tx - 5, ty + 7)]), 0.25, 2),
           GOLD_D, 1.2, rim=1.2, flow=0.4)     # the lamp room, one warm glaze
    p.wash(p.rough(p.poly([(tx - 7, ty + 7.5), (tx + 7, ty + 7.5), (tx, ty - 1)]), 0.25, 2), PAYNE, 1.4, rim=0.6)
    halo = p.soften(p.ellipse(tx, ty + 11, 16, 13), 6) * (1 - np.clip(tower * 1.2, 0, 1))
    p.lift(halo, 0.55)
    p.wash(halo, GOLD_D, 0.6, rim=0, flow=0.3, blotch=0.03)
    p.wash(p.rough(p.poly([(tx - 2.6, tb - 1), (tx - 2.6, tb - 6), (tx - 0.2, tb - 6), (tx - 0.2, tb - 1)]), 0.2, 2),
           PAYNE, 0.8, rim=0.4)
    cx0 = 184
    gy = 254 - (cx0 - 104) * 0.29                                                # the grass line under the cottage
    cottage = p.rough(p.poly([(cx0 - 10, gy + 2), (cx0 - 10, gy - 8), (cx0 + 6, gy - 8), (cx0 + 6, gy + 2)]), 0.3, 3)
    cside = p.rough(p.poly([(cx0 + 6, gy + 2), (cx0 + 6, gy - 8), (cx0 + 12, gy - 10), (cx0 + 12, gy)]), 0.3, 3)
    p.wash(cottage, ROSE, 0.25, rim=1.2)
    p.loose(cside, [SHADOW, ULTRA], 0.7, n=3, rough=0.2, patch=0.6)
    p.loose(p.poly([(cx0 - 12, gy - 8), (cx0 + 6.5, gy - 8), (cx0 + 13, gy - 10), (cx0 + 8, gy - 15),
                    (cx0 - 7, gy - 14)]), [UMBER, UMBER, SIENNA], 1.2, n=4, rough=0.2, patch=0.6)
    p.wash(p.rough(p.poly([(cx0 - 6, gy + 2), (cx0 - 6, gy - 4), (cx0 - 3.4, gy - 4), (cx0 - 3.4, gy + 2)]), 0.15, 2),
           PAYNE, 1.0, rim=0.3)
    p.finish()
    return p


TERRA = "#D9967A"          # terracotta roof tile, muted; nowhere near the UI red
TERRA_M = "#C7998A"        # the harbor roofs, a more muted terracotta
SHADOW = "#9AA3C8"         # the cool violet-blue of shadows on white walls


def house_masks(p, x, base, w, h, depth, roof):
    """A white house as three masks: its lit front, its shaded side (to the right), its roof. roof: 'flat' or
    'tile'."""
    front = p.poly([(x, base), (x, base - h), (x + w, base - h), (x + w, base)])
    side = p.poly([(x + w, base), (x + w, base - h), (x + w + depth, base - h - depth * 0.35),
                   (x + w + depth, base - depth * 0.35)])
    if roof == "tile":
        r = p.poly([(x - 1.2, base - h), (x + w + depth + 0.8, base - h - depth * 0.35), (x + w * 0.6 + depth,
                     base - h - depth * 0.35 - w * 0.32), (x + w * 0.45, base - h - w * 0.3)])
    else:
        r = p.poly([(x - 0.6, base - h), (x + w, base - h), (x + w + depth, base - h - depth * 0.35),
                    (x + depth * 0.2, base - h - depth * 0.45)])
    return front, side, r


def hull_pts(bx, by, bw):
    """A curved hull: the sheer dips amidships and lifts to a higher bow on the right; the bottom is rounded."""
    us = np.linspace(0, 1, 24)
    sheer = [(bx + bw * u, by - bw * (0.035 + 0.07 * (1 - u) ** 3 + 0.16 * max(0.0, u - 0.62) ** 1.6 / 0.38 ** 1.6))
             for u in us]
    bottom = [(bx + bw * (0.06 + 0.86 * u), by + bw * (0.02 + 0.11 * math.sin(math.pi * u) ** 0.7))
              for u in us[::-1]]
    return sheer + bottom


def hull_mask(p, bx, by, bw):
    return p.poly(hull_pts(bx, by, bw))


def boat(p, bx, by, bw, hull, trim, mast=None, seed=0):
    """A wooden fishing boat seen side-on, painted loose: a curved sheer, the bow lifted, a painted trim band, a
    darker lower hull, a small cabin; a wobbly reflection below. Returns the boat's mask."""
    hb = hull_mask(p, bx, by, bw)
    p.loose(hb, [hull, hull, SHADOW], 1.0, n=5, rough=0.3, patch=0.45)
    top = hull_pts(bx, by, bw)[:24]
    band = p.poly(top + [(x, y + bw * 0.045) for x, y in top[::-1]]) * hb
    p.wash(p.rough(band, 0.2, 2), trim, 1.1, rim=1.0, flow=0.4)
    p.wash(hb * ramp_y(by + bw * 0.04, by + bw * 0.13, 0.0, 1.0), PAYNE, 0.8, rim=0.3, flow=0.4)
    cab = p.poly([(bx + bw * 0.42, by - bw * 0.02), (bx + bw * 0.66, by - bw * 0.02), (bx + bw * 0.64, by - bw * 0.2),
                  (bx + bw * 0.44, by - bw * 0.2)])
    p.loose(cab, [RAW, SHADOW], 0.45, n=3, rough=0.2, patch=0.6)
    p.wash(cab * ramp_x(bx + bw * 0.52, bx + bw * 0.66, 0.0, 1.0), SHADOW, 0.9, rim=0.6)
    p.wash(p.rough(p.poly([(bx + bw * 0.42, by - bw * 0.2), (bx + bw * 0.68, by - bw * 0.2),
                           (bx + bw * 0.68, by - bw * 0.225), (bx + bw * 0.42, by - bw * 0.225)]), 0.1, 1), UMBER, 1.1)
    p.wash(p.rough(p.poly([(bx + bw * 0.47, by - bw * 0.15), (bx + bw * 0.52, by - bw * 0.15),
                           (bx + bw * 0.52, by - bw * 0.1), (bx + bw * 0.47, by - bw * 0.1)]), 0.1, 1), PAYNE, 1.1)
    if mast:
        mx = bx + bw * 0.31
        p.wash(p.rough(p.stroke([(bx + bw * 0.3, by - bw * 0.04), (mx, by - mast)], 0.9, taper=False),
                       0.1, 2), UMBER, 1.2, rim=0.2)
        p.wash(p.rough(p.stroke([(mx - 2, by - mast + 2), (mx + 2.5, by - mast + 2)], 0.7, taper=False), 0.1, 1),
               UMBER, 1.2)                                                            # the masthead
        p.wash(p.rough(p.stroke([(mx, by - mast + 2), (bx + bw * 0.97, by - bw * 0.14)], 0.35, taper=False), 0.1, 2),
               UMBER, 0.8)                                                            # a stay to the bow
    refl = p.soften(p.rough(p.poly([(bx + bw * 0.12, by + bw * 0.1), (bx + bw * 0.92, by + bw * 0.09),
                                    (bx + bw * 0.8, by + bw * 0.34), (bx + bw * 0.2, by + bw * 0.36)]), 1.5, 4), 1.0)
    p.wash(refl, hull, 0.55, rim=0, flow=0.5, blotch=0.04)
    p.wash(refl * ramp_y(by + bw * 0.14, by + bw * 0.22, 1.0, 0.0), PAYNE, 0.45, rim=0)
    return hb


def harbor():
    """Small harbor, long season: two wooden fishing boats moored close in the foreground, the focal point; behind
    them the quay and a white village set back on an olive hillside to the right, built loose: walls of bare paper
    and warm glazes, cool shadow sides, terracotta roofs, a small campanile among them; cypresses; the water holding
    the boats' reflections and the colours of the village."""
    p = Paper(seed=21)
    rng = np.random.default_rng(21)
    plan = [  # (x, base, w, h, depth, roof), back to front: a village set back on the hill to the right
        (150, 222, 16, 12, 4, "tile"), (168, 216, 14, 15, 4, "flat"), (184, 212, 18, 12, 5, "tile"),
        (204, 208, 16, 14, 4, "tile"), (222, 206, 18, 12, 5, "flat"),
        (128, 240, 20, 13, 5, "tile"), (150, 236, 15, 17, 4, "flat"), (168, 238, 22, 12, 5, "tile"),
        (194, 232, 18, 16, 5, "tile"), (216, 230, 22, 13, 5, "flat"),
    ]
    rows = [(x, b, w, h, d, r, 0) for x, b, w, h, d, r in plan]
    raw_houses = [tuple(p.rough(m, 0.4, 3, fine=0.3) for m in house_masks(p, *r[:6])) for r in rows]
    solids = [np.clip(np.maximum(np.maximum(f, sd), rf), 0, 1) for f, sd, rf in raw_houses]
    houses = []
    for i, (f, sd, rf) in enumerate(raw_houses):
        front_of = [solids[j] for j in range(len(rows)) if rows[j][1] > rows[i][1] + 0.5]
        hide = 1 - np.clip(np.maximum.reduce(front_of), 0, 1) if front_of else 1
        houses.append((f * hide, sd * hide, rf * hide))
    bt_x, bt_top, bt_base = 214, 150, 206
    tower = p.rough(p.poly([(bt_x - 5, bt_base), (bt_x - 5, bt_top + 9), (bt_x + 5, bt_top + 9), (bt_x + 5, bt_base)]),
                    0.3, 3, fine=0.2) * (1 - np.clip(np.maximum.reduce(solids), 0, 1))
    roof_t = p.rough(p.poly([(bt_x - 6, bt_top + 9), (bt_x + 6, bt_top + 9), (bt_x, bt_top)]), 0.25, 2)
    built = np.clip(np.maximum.reduce(solids + [tower, roof_t]), 0, 1)
    around = 1 - built
    boats = [(16, 302, 74, CERUL, TERRA_M, 92), (110, 318, 60, RAW, CERUL, None)]
    # the water stops just inside each hull's edge, so it meets the boat with no paper rim
    hulls = np.clip((np.maximum.reduce([blur(hull_mask(p, bx, by, bw), 0.6 * S) for bx, by, bw, *_ in boats]) - 0.7)
                    * 6, 0, 1)
    # 1 sky over the whole cover, bright morning: cerulean deepening toward the top, a warm cream near the horizon,
    # soft clouds lifted out wet-in-wet; light enough that the title sits on it in dark blue
    full = np.ones((H, W), np.float32)
    p.wash(full * around, CERUL, 0.6, rim=1.2, flow=0.35, blotch=0.06, vary=ramp_y(0, 240, 0.9, 0.3))
    p.wash(full * around, ULTRA, 0.12, rim=0.4, flow=0.4, blotch=0.05, vary=ramp_y(0, 150, 1.0, 0.0))
    p.wash(p.soften(p.poly([(-20, 190), (260, 176), (260, 256), (-20, 256)]), 14) * around, RAW, 0.45, rim=0,
           flow=0.4, blotch=0.05)
    for x, y, rx, ry in [(40, 132, 44, 9), (150, 110, 38, 7), (90, 176, 50, 8), (200, 70, 30, 6)]:
        p.lift(p.soften(p.rough(p.ellipse(x, y, rx, ry), 3, 10, fine=0.8), 3) * around, 0.5)
    # 2 the hill: a far blue headland on the left, the olive hillside rising behind the village on the right
    p.wash(p.rough(p.poly([(-10, 253), (20, 244), (60, 240), (100, 246), (120, 254)]), 0.8, 5), ULTRA, 0.45,
           rim=1.4, flow=0.3, blotch=0.05)
    hill = p.rough(p.poly([(96, 252), (130, 230), (160, 208), (196, 190), (236, 180), (260, 178), (260, 254),
                           (96, 256)]), 1.4, 7, fine=0.6)
    p.loose(hill * around, [SAP, OLIVE, RAW, SAP], 0.8, n=10, rough=0.4, patch=0.3)
    p.wash(hill * around * ramp_y(180, 250, 0.2, 0.8), OLIVE, 0.35, rim=0, flow=0.4, blotch=0.05)
    for x, b0, hgt in [(122, 248, 18), (130, 246, 13), (240, 200, 16), (234, 202, 12)]:
        cyp = p.rough(p.poly([(x - 2.2, b0), (x - 1.4, b0 - hgt * 0.6), (x, b0 - hgt), (x + 1.4, b0 - hgt * 0.6),
                              (x + 2.2, b0)]), 0.4, 2, fine=0.3)
        p.wash(cyp * around, OLIVE, 1.3, rim=0.8, blotch=0.04)
        p.wash(cyp * around * ramp_x(x - 1, x + 2.5, 0, 1), PAYNE, 0.9, rim=0.2, blotch=0.03)
    # 3 houses, loose: walls a whisper of warm glaze, shadow sides cool, roofs terracotta in patches
    for (x, base, w, h, depth, roof, k), (front, side, r) in zip(rows, houses):
        p.wash(front, str(rng.choice([RAW, ROSE, RAW])), 0.14 + 0.06 * rng.random(), rim=1.0, flow=0.4, blotch=0.04)
        p.loose(side, [SHADOW, ULTRA, SHADOW], 0.7, n=3, rough=0.2, patch=0.7)
        if roof == "tile":
            p.loose(r, [TERRA_M, SIENNA, TERRA_M], 0.85, n=4, rough=0.2, patch=0.6)
        else:
            p.wash(r, SHADOW, 0.22, rim=0.8, blotch=0.03)
        eave = p.rough(p.poly([(x, base - h), (x + w, base - h), (x + w, base - h + 2.2), (x, base - h + 1.6)]),
                       0.3, 2, fine=0.2)
        p.wash(eave * front, SHADOW, 0.55, rim=0.2, blotch=0.03)
        if rng.random() < 0.6:
            wx = x + float(rng.uniform(2, max(2.5, w - 4)))
            wy = base - h + float(rng.uniform(4, max(4.5, h - 5)))
            p.wash(p.rough(p.poly([(wx, wy), (wx + 1.8, wy), (wx + 1.8, wy + 2.8), (wx, wy + 2.8)]), 0.15, 1)
                   * front, PAYNE, 0.85, rim=0.3, blotch=0.02)
    p.wash(p.soften(tower * ramp_x(bt_x - 1, bt_x + 5, 0.0, 1.0), 0.8), SHADOW, 0.7, rim=0.8)
    p.wash(p.rough(p.poly([(bt_x - 1.6, bt_top + 18), (bt_x - 1.6, bt_top + 13), (bt_x + 1.6, bt_top + 13),
                           (bt_x + 1.6, bt_top + 18)]), 0.15, 1) * tower, PAYNE, 1.1)
    p.loose(roof_t, [TERRA, SIENNA], 1.0, n=2, rough=0.15, patch=0.7)
    # 4 the quay under the village: a rough stroke, a dark band of shadow below it
    qpts = [(96, 258), (140, 256), (190, 256), (260, 254)]
    quay = p.rough(p.stroke(qpts, 5.0, taper=False), 0.7, 6, fine=0.4)
    p.loose(quay * around, [RAW, UMBER], 0.85, n=4, rough=0.2, patch=0.4)
    p.wash(p.rough(p.stroke([(x, y + 3.4) for x, y in qpts], 1.6, taper=False), 0.5, 6), PAYNE, 0.75, rim=0.3)
    # 5 the water: wet-in-wet, the village's colours dropped in under it, ripples lifted dry
    water = p.rough(p.poly([(-20, 249), (96, 252), (260, 252), (270, 360), (-20, 360)]), 0.4, 8) * (1 - hulls)
    p.wash(water * around, CERUL, 0.85, rim=0.8, flow=0.4, blotch=0.06, vary=ramp_y(254, 344, 0.7, 1.3))
    village_refl = p.soften(p.poly([(126, 262), (240, 262), (240, 296), (126, 292)]), 3.5)
    p.wash(village_refl * water, TERRA, 0.25, rim=0, flow=0.5, blotch=0.05)
    p.lift(village_refl * water, 0.2)
    p.wash(p.soften(p.poly([(-20, 300), (260, 296), (260, 360), (-20, 360)]), 10) * water, ULTRA, 0.5, rim=0,
           blotch=0.05, vary=ramp_y(296, 344, 0.3, 1.0))
    for i in range(10):
        x, y, w = float(rng.uniform(-10, 230)), float(rng.uniform(262, 340)), float(rng.uniform(6, 24))
        p.lift(p.rough(p.stroke([(x, y), (x + w, y - 0.4)], 1.2), 0.5, 4, fine=0.4) * water, 0.65, dry=0.7)
    # 6 the two boats, close, the focal point; masts stay below the name line
    for bx, by, bw, hull, trim, mast in boats:
        boat(p, bx, by, bw, hull, trim, mast=mast)
    # a mooring rope from the near boat to the quay
    p.wash(p.rough(p.stroke([(100, 290), (110, 282), (122, 268), (130, 260)], 0.5, taper=False), 0.2, 2), UMBER,
           0.9, rim=0)
    p.finish()
    return p


VIOLET = "#B4A9CC"          # far haze and shadows in the wood
GOLD = "#EBC27A"


def canopy(p, cx, cy, rx, ry, seed_n=8, rng=None):
    """A crown of leaves as a cluster of loose blobs, ragged at the edge like a dabbed brush."""
    m = np.zeros((p.img.shape[0], p.img.shape[1]), np.float32)
    for i in range(seed_n):
        ox, oy = rng.uniform(-rx * 0.7, rx * 0.7), rng.uniform(-ry * 0.6, ry * 0.6)
        m = np.maximum(m, p.ellipse(cx + ox, cy + oy, rx * rng.uniform(0.4, 0.7), ry * rng.uniform(0.4, 0.7)))
    return p.rough(m, 1.6, 4, fine=0.9)


def crown(p, cx, cy, rx, ry, cols, rng, n=9):
    """An autumn crown painted wet-in-wet: overlapping blobs, each dropped in its own colour so they bleed into
    each other, flowered and dark-rimmed where they dried; a few leaf dabs breaking the silhouette."""
    total = np.zeros((H, W), np.float32)
    for i in range(n):
        ox, oy = rng.uniform(-rx * 0.65, rx * 0.65), rng.uniform(-ry * 0.55, ry * 0.55)
        m = p.rough(p.ellipse(cx + ox, cy + oy, rx * rng.uniform(0.35, 0.6), ry * rng.uniform(0.35, 0.6)), 1.4, 3,
                    fine=0.8)
        total = np.maximum(total, m)
        p.wash(m, cols[i % len(cols)], rng.uniform(0.55, 0.9), rim=1.3, flow=0.6, blotch=0.12)
    for i in range(14):
        a = rng.uniform(0, 2 * math.pi)
        x, y = cx + math.cos(a) * rx * rng.uniform(0.8, 1.1), cy + math.sin(a) * ry * rng.uniform(0.8, 1.1)
        d = p.rough(p.ellipse(x, y, rng.uniform(1.0, 2.2), rng.uniform(0.7, 1.4)), 0.3, 1, fine=0.2)
        total = np.maximum(total, d)
        p.wash(d, cols[i % len(cols)], 0.9, rim=0.8, blotch=0.03)
    return total


PINE = "#5F7560"            # a dark fir among the golds: the picture's cool dark anchor
BARK = "#6E5A4C"


def limb(p, pts, w):
    """A branch as a tapered brush line: thick at its root, lifting to a point."""
    n = len(pts)
    m = np.zeros((H, W), np.float32)
    for i in range(n - 1):
        ww = w * (1 - i / n * 0.75)
        m = np.maximum(m, p.stroke([pts[i], pts[i + 1]], ww, taper=False))
    return p.rough(m, 0.25, 2, fine=0.2)


def tree(p, x, base, h, spread, cols, rng, lean=0.0, trunk_w=2.4, clumps=7, dark=SIENNA, size=0.22, fork_at=None, leaves=None):
    """An autumn tree built as a painter would: a tapering trunk that forks into curved limbs; the crown dabbed as
    separate clumps along and at the ends of the limbs with sky between them, each clump lit on its upper left and
    glazed darker on its lower right; the limbs show only in the gaps. Returns the crown mask (for reflections)."""
    top = base - h
    fork = base - h * (fork_at or rng.uniform(0.4, 0.48))
    fx = x + lean * h * 0.4
    tw = trunk_w
    wood = p.rough(p.poly([(x - tw * 1.3, base + 0.5), (x - tw * 0.8, base - 2), (fx - tw * 0.45, fork),
                           (fx + tw * 0.45, fork), (x + tw * 0.75, base - 2), (x + tw * 1.4, base + 0.5)]), 0.3, 3,
                   fine=0.25)
    cl = []
    k = min(5, max(3, clumps // 5))
    for i in range(k):
        a = math.pi * (1.15 + 0.7 * (i + rng.uniform(-0.15, 0.15)) / (k - 1))
        r = h * rng.uniform(0.3, 0.4)
        mx, my = fx + math.cos(a) * r * spread, fork + math.sin(a) * r
        wood = np.maximum(wood, limb(p, [(fx, fork + 1), (fx + (mx - fx) * 0.5, fork + (my - fork) * 0.6), (mx, my)],
                                     tw * 0.6))
        for da in (-0.35, 0.3):
            r2 = h * rng.uniform(0.18, 0.26)
            ex, ey = mx + math.cos(a + da) * r2 * spread * 1.3, my + math.sin(a + da) * r2
            wood = np.maximum(wood, limb(p, [(mx, my), (ex, ey)], tw * 0.32))
            cl.append((ex, ey))
        cl += [(mx, my), (fx + (mx - fx) * 0.5, fork + (my - fork) * 0.5 - h * 0.03)]
    cl.append((fx, fork - h * 0.04))
    while len(cl) < clumps:
        cl.append((fx + rng.uniform(-0.35, 0.35) * h * spread, top + h * rng.uniform(0.1, 0.3)))
    crown_m = np.zeros((H, W), np.float32)
    shade_m = np.zeros((H, W), np.float32)
    rs = []
    for i, (cx, cy) in enumerate(cl):
        rx = h * size * rng.uniform(0.75, 1.15)
        ry = rx * rng.uniform(0.62, 0.82)
        rs.append((rx, ry))
        m = p.rough(p.ellipse(cx, cy, rx, ry), rx * 0.2, max(2, rx * 0.45), fine=0.7)
        crown_m = np.maximum(crown_m, m)
        shade_m = np.maximum(shade_m, m * (1 - p.soften(p.ellipse(cx - rx * 0.3, cy - ry * 0.45, rx * 0.85,
                                                                   ry * 0.75), 1.0)))
    # the crown: a pale lit ground, colours dropped in wet-in-wet, then the shade glazed on the lower right
    p.wash(crown_m, cols[0], 0.6, rim=0.9, flow=0.6, blotch=0.12)
    for i, (cx, cy) in enumerate(cl):
        rx, ry = rs[i]
        d = p.rough(p.ellipse(cx + rng.uniform(-1, 2) * rx * 0.2, cy + rng.uniform(0, 1) * ry * 0.2, rx * 0.65,
                              ry * 0.6), rx * 0.15, 3, fine=0.6) * crown_m
        p.wash(d, cols[1 + i % (len(cols) - 1)], rng.uniform(0.5, 0.85), rim=0.5, flow=0.5, blotch=0.1)
    p.wash(shade_m, dark, 0.6, rim=0.5, flow=0.5, blotch=0.08)
    ys_, xs_ = np.nonzero(crown_m > 0.5)
    if len(xs_):                                   # the whole crown turns from the light: one glaze, lower right
        cx0, cx1, cy0, cy1 = xs_.min() / S, xs_.max() / S, ys_.min() / S, ys_.max() / S
        mass = np.clip(ramp_x(cx0, cx1, -0.3, 1.0) * 0.6 + ramp_y(cy0, cy1, -0.3, 1.0) * 0.6, 0, 1)
        p.wash(crown_m * mass, dark, 0.7, rim=0, flow=0.5, blotch=0.06)
        p.wash(crown_m * np.clip(mass - 0.55, 0, 1) * 2, UMBER, 0.6, rim=0, flow=0.5)
    # the wood: hidden inside the crown, only its gaps and a little of the shade let it through
    hide = np.clip(blur(crown_m, 0.8 * S) * 1.4, 0, 1)
    wood = wood * np.clip((Yw_() - (fork - h * 0.12)) / (h * 0.05), 0, 1)   # no limb pieces floating in the crown
    p.wash(wood * (1 - hide), BARK, 1.35, rim=0.5, blotch=0.04, gran=0.4)
    p.wash(wood * ramp_x(x - tw * 0.2, x + tw * 1.4, 0, 1) * (1 - hide), PAYNE, 0.7, rim=0.1)
    p.lift(wood * ramp_x(x - tw * 1.3, x - tw * 0.2, 1, 0) * (1 - hide) * (Yw_() > fork + 4), 0.3)
    # loose leaves breaking the outline
    for i in range(int(4 + clumps) if leaves is None else leaves):
        cx, cy = cl[rng.integers(len(cl))]
        rx, ry = rs[0]
        a = rng.uniform(math.pi * 0.9, math.pi * 2.1)
        lx, ly = cx + math.cos(a) * rx * rng.uniform(0.9, 1.15), cy + math.sin(a) * ry * rng.uniform(0.9, 1.15)
        p.wash(p.rough(p.ellipse(lx, ly, rng.uniform(0.8, 1.4), rng.uniform(0.6, 1.0)), 0.3, 1, fine=0.2),
               cols[i % len(cols)], 0.8, rim=0.8, blotch=0.03)
    return crown_m


def Yw_():
    from paint import YY as _YY
    return _YY / S


def spline(pts, n=12):
    """Catmull-Rom through the points: a smooth curve instead of a polyline's corners."""
    P = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(1, len(P) - 2):
        (x0, y0), (x1, y1), (x2, y2), (x3, y3) = P[i - 1], P[i], P[i + 1], P[i + 2]
        for t in np.linspace(0, 1, n, endpoint=False):
            t2, t3 = t * t, t * t * t
            out.append((0.5 * (2 * x1 + (x2 - x0) * t + (2 * x0 - 5 * x1 + 4 * x2 - x3) * t2 + (3 * x1 - x0 - 3 * x2 + x3) * t3),
                        0.5 * (2 * y1 + (y2 - y0) * t + (2 * y0 - 5 * y1 + 4 * y2 - y3) * t2 + (3 * y1 - y0 - 3 * y2 + y3) * t3)))
    return out + [pts[-1]]


def fir(p, x, base, h, w, rng):
    """A dark fir: ragged tiers wider toward the ground, painted in one go wet-in-wet, lit faintly on the left."""
    m = np.zeros((H, W), np.float32)
    n = 7
    for i in range(n):
        t = i / (n - 1)
        y = base - h + h * t * 0.92
        ww = w * (0.15 + 0.85 * t) * rng.uniform(0.85, 1.1)
        m = np.maximum(m, p.poly([(x, y - h * 0.16), (x + ww, y + h * 0.05), (x - ww, y + h * 0.06)]))
    m = np.maximum(m, p.poly([(x - 0.6, base - h - 2), (x + 0.6, base - h - 2), (x + 0.8, base), (x - 0.8, base)]))
    m = p.rough(m, 0.7, 2.0, fine=0.6)
    p.wash(m, PINE, 1.0, rim=1.2, flow=0.5, blotch=0.1)
    p.wash(m * ramp_x(x - w * 0.2, x + w, 0, 1), PAYNE, 0.7, rim=0.2, flow=0.4)
    p.wash(m * ramp_x(x - w, x - w * 0.2, 1, 0), RAW, 0.4, rim=0)
    return m


def autumn():
    """An autumn river at golden hour, the bridge its focal point. A golden haze over a violet wood; a humpbacked
    stone bridge spanning the river, its feet in the banks, its arch and its reflection closing a ring; a dark fir
    behind its left end as the cool anchor; the river winding toward us, gold where it holds the sky and cool where
    it holds the shade, with the trees' colours in vertical streaks; on the right one big oak rises into the sky and
    frames the scene; smaller trees on both banks, each forking into limbs with its crown dabbed in clumps."""
    p = Paper(seed=31)
    rng = np.random.default_rng(33)
    import paint
    Xw, Yw = paint.XX / S, paint.YY / S
    # 1 the sky: one golden haze, deeper at the top, pale where the light breaks through low behind the bridge
    full = p.soften(p.poly([(-20, -20), (260, -20), (260, 254), (-20, 254)]), 3)
    p.wash(full, GOLD, 0.75, rim=1.2, flow=0.2, blotch=0.03, vary=ramp_y(0, 250, 1.0, 0.5))
    p.wash(full, RAW, 0.35, rim=0.4, flow=0.2, blotch=0.03, vary=ramp_y(0, 160, 1.0, 0.0))
    p.wash(p.soften(p.poly([(-20, 160), (260, 150), (260, 240), (-20, 240)]), 16), ROSE, 0.3, rim=0, flow=0.5,
           blotch=0.05)
    p.lift(p.soften(p.ellipse(110, 222, 56, 18), 12), 0.4)
    # a soft rose cloud band low in the sky, below the title, and warmth gathering at the top
    for cx, cy, rx, ry in [(70, 196, 70, 5), (170, 186, 60, 4), (120, 206, 50, 3)]:
        p.wash(p.soften(p.rough(p.ellipse(cx, cy, rx, ry), 2, 10), 3), ROSE, 0.28, rim=0.1, flow=0.5, blotch=0.06)
    p.wash(full * ramp_y(0, 120, 1.0, 0.0), SIENNA, 0.35, rim=0, flow=0.3, blotch=0.03)
    # 2 the far wood: one violet band with an uneven top, warmer where the light is, then the paler middle trees
    far = np.zeros((H, W), np.float32)
    for i in range(22):
        far = np.maximum(far, p.ellipse(rng.uniform(-10, 246), rng.uniform(214, 230), rng.uniform(8, 18),
                                        rng.uniform(6, 12)))
    far = p.soften(np.maximum(far, p.poly([(-20, 228), (260, 224), (260, 256), (-20, 256)])), 2.0)
    p.wash(far, VIOLET, 0.7, rim=0.4, flow=0.5, blotch=0.08)
    p.wash(far * p.soften(p.ellipse(112, 230, 50, 14), 8), GOLD, 0.6, rim=0, flow=0.4)
    for x, y, rx, ry, cols in [(28, 228, 10, 8, [RAW, GOLD]), (60, 230, 8, 7, [GOLD, RAW]),
                               (162, 230, 9, 7, [GOLD, RAW]), (196, 226, 11, 9, [RAW, TERRA])]:
        crown(p, x, y, rx, ry, cols, rng, n=5)
    # 3 the river: it leaves the arch narrow and winds toward us, widening
    rl = [(101, 254), (96, 264), (104, 276), (116, 290), (110, 304), (84, 320), (46, 336), (6, 352)]
    rr = [(135, 254), (142, 264), (150, 276), (162, 290), (168, 304), (162, 320), (168, 336), (186, 352)]
    rl, rr = spline(rl), spline(rr)              # smooth curving banks, no jagged corners
    river = p.soften(p.rough(p.poly(rl + rr[::-1]), 0.35, 16, fine=0.0), 0.4)
    p.wash(river, GOLD, 0.6, rim=0.3, flow=0.4, blotch=0.04)                       # it holds the sky
    p.wash(river, SHADOW, 0.75, rim=0.2, flow=0.45, blotch=0.06, vary=ramp_y(262, 344, 0.15, 1.2))
    p.wash(river, ULTRA, 0.3, rim=0, flow=0.4, vary=ramp_y(300, 344, 0.0, 1.0))
    # 4 banks: raw sienna, warmer and deeper toward us; they overlap the water so no paper shows at the seam
    lbank = p.rough(p.poly([(-20, 252), (104, 252)] + rl[1:] + [(-20, 352)]), 0.35, 16, fine=0.0)
    rbank = p.rough(p.poly([(132, 252), (260, 250), (260, 352)] + rr[::-1][:-1]), 0.35, 16, fine=0.0)
    lbank = np.clip(blur(lbank, 1.0 * S) * 2.2, 0, 1)
    rbank = np.clip(blur(rbank, 1.0 * S) * 2.2, 0, 1)
    for bank in (lbank, rbank):
        p.wash(bank, RAW, 0.9, rim=0.6, flow=0.5, blotch=0.08, vary=ramp_y(250, 344, 0.75, 1.25))
        p.wash(bank * ramp_y(268, 344, 0.0, 1.0), SIENNA, 0.6, rim=0.2, flow=0.5, blotch=0.06)
        p.wash(bank * p.soften(p.rough(p.poly([(-20, 258), (260, 256), (260, 276), (-20, 282)]), 3, 12), 6), OLIVE, 0.4, rim=0,
               flow=0.6, blotch=0.1)
        p.wash(bank * p.soften(p.rough(p.poly([(-20, 296), (90, 292), (60, 352), (-20, 352)]), 6, 14), 8), UMBER,
               0.35, rim=0, flow=0.6)
    # the bank's own shade at the water's edge, and its dark line reflected just below it
    edge = np.clip(blur(river, 2.5 * S) * 1.6, 0, 1) * (1 - river) * np.maximum(lbank, rbank)
    p.wash(edge, UMBER, 0.25, rim=0, flow=0.4, blotch=0.04)
    ins = np.clip(blur(1 - river, 1.5 * S) * 1.6, 0, 1) * river
    p.wash(ins, PAYNE, 0.55, rim=0, flow=0.4)                          # darker water under the banks
    # 5 the fir behind the bridge's left end, the cool dark against the gold
    fir(p, 76, 252, 42, 8, rng)
    fir(p, 64, 252, 24, 5.5, rng)
    # 6 the bridge: lifted back to paper first (it stands in front of the wood), then built in stone
    bx, sy, br = 118, 254, 19                      # arch centre, spring line on the water, radius
    top = 227 + 15 * np.clip((Xw - bx) / 52, -1.0, 1.0) ** 2            # the humped parapet, ending at the piers
    body = ((Yw >= top) & (Yw <= 258) & (np.abs(Xw - bx) <= 52 + np.clip(Yw - 240, 0, 20) * 0.6)).astype(np.float32)
    hole = ((((Xw - bx) / br) ** 2 + ((Yw - sy) / (br * 0.98)) ** 2) < 1) & (Yw < sy + 1)
    body = p.rough(np.clip(body - hole, 0, 1), 0.35, 3, fine=0.3)
    p.lift(np.clip(blur(body, 0.5 * S) * 1.3, 0, 1), 0.92)
    p.loose(body, [RAW, GOLD, RAW, SIENNA], 1.0, n=10, rough=0.15, patch=0.12, ground=0.9)
    p.wash(body, SIENNA, 0.3, rim=0.8, flow=0.4, gran=0.5)
    p.wash(body * ramp_x(bx - 10, bx + 54, 0.0, 1.0), UMBER, 0.55, rim=0, flow=0.4, gran=0.5)   # turning from the light
    # stone courses and a few single stones, broken dry-brush so they read as masonry, not a grid
    for yy in np.arange(234, 257, 3.4):
        for seg in range(4):
            xa = bx - 54 + seg * 27 + rng.uniform(0, 8)
            p.wash(p.rough(p.stroke([(xa, yy + rng.uniform(-0.3, 0.3)), (xa + rng.uniform(10, 20), yy)], 0.45,
                                    taper=False), 0.15, 2) * body, UMBER, 0.55, rim=0, dry=0.55)
    for i in range(26):
        sx, sy2 = rng.uniform(bx - 52, bx + 50), rng.uniform(232, 255)
        st = p.rough(p.poly([(sx, sy2), (sx + 3.2, sy2), (sx + 3.2, sy2 + 2.4), (sx, sy2 + 2.4)]), 0.25, 1, fine=0.2)
        p.wash(st * body, str(rng.choice([SIENNA, UMBER, RAW])), rng.uniform(0.35, 0.7), rim=1.0, blotch=0.02)
    # the coping: a dark line under a lit lip, riding the hump
    cop = p.rough(((Yw - top > 1.0) & (Yw - top < 2.6) & (np.abs(Xw - bx) <= 54)).astype(np.float32), 0.2, 3)
    p.wash(cop, UMBER, 0.95, rim=0.3)
    # the voussoirs: a ring of wedge stones around the arch, each its own mark
    for a in np.linspace(math.pi * 1.04, math.pi * 1.96, 11):
        r0, r1 = br + 0.4, br + 4.2
        x0, y0 = bx + math.cos(a) * r0, sy + math.sin(a) * r0 * 0.98
        x1, y1 = bx + math.cos(a) * r1, sy + math.sin(a) * r1 * 0.98
        p.wash(p.rough(p.stroke([(x0, y0), (x1, y1)], 0.55, taper=False), 0.12, 1), UMBER, 0.9, rim=0, dry=0.25)
    ring = ((((Xw - bx) / (br + 4.2)) ** 2 + ((Yw - sy) / ((br + 4.2) * 0.98)) ** 2) < 1).astype(np.float32) * body
    p.wash(ring * (1 - ((((Xw - bx) / (br + 0.6)) ** 2 + ((Yw - sy) / (br * 0.98)) ** 2) < 1)), SIENNA, 0.35, rim=0.4)
    # under the arch: the shaded vault, dark at the top, a glimpse of lit water and far bank through it
    hole_m = np.clip(blur(hole.astype(np.float32), 0.6 * S) * 1.8, 0, 1)        # no paper rim at the arch
    p.lift(hole_m, 0.85)
    p.wash(hole_m, VIOLET, 0.8, rim=0, flow=0.4)
    p.wash(hole_m * ramp_y(sy - br, sy - 3, 1.0, 0.25), UMBER, 1.5, rim=0.2, flow=0.4, blotch=0.05)
    p.wash(hole_m * ramp_x(bx - br, bx + br, 0.2, 1.0), PAYNE, 0.6, rim=0)
    p.lift(hole_m * ramp_y(sy - 8, sy - 6, 0, 1), 0.6)
    p.wash(hole_m * ramp_y(sy - 8, sy, 0.3, 1), GOLD, 0.6, rim=0)
    p.wash(hole_m * ramp_y(sy - 8, sy, 0.0, 1), SHADOW, 0.5, rim=0)                         # light on the water beyond
    far_bank = p.rough(p.poly([(bx - br, sy - 10), (bx + br, sy - 9.5), (bx + br, sy - 7.5), (bx - br, sy - 8)]), 0.5, 3)
    p.wash(far_bank * hole_m, OLIVE, 0.9, rim=0.3, flow=0.5)                       # the far bank seen through it
    p.wash(hole_m * ramp_y(sy - br, sy - br * 0.4, 1.0, 0.0) * ramp_x(bx - br, bx + br, 0.5, 1.0), PAYNE, 0.6, rim=0)
    p.wash(p.soften(p.poly([(160, 257), (178, 252), (200, 258), (176, 262)]), 2) * rbank, UMBER, 0.5, rim=0)
    # the bridge's feet sink into the banks: bushes over both ends
    for cx, cy, rx, ry, cols in [(64, 255, 10, 6, [OLIVE, SIENNA, RAW]), (172, 255, 11, 6, [SIENNA, OLIVE, GOLD]),
                                 (94, 257, 6, 3.5, [OLIVE, SIENNA]), (144, 257, 6, 3.5, [SIENNA, OLIVE])]:
        crown(p, cx, cy, rx, ry, cols, rng, n=6)
    # the reflection: the arch's ring closed in the water, the bridge's underside a dark band, both broken by ripples
    rring = ((((Xw - bx) / (br + 4)) ** 2 + ((Yw - sy) / ((br + 4) * 0.98)) ** 2) < 1) & (Yw > sy)
    rhole = ((((Xw - bx) / br) ** 2 + ((Yw - sy) / (br * 0.98)) ** 2) < 1) & (Yw > sy)
    p.wash(p.soften(p.rough(rring.astype(np.float32) * (1 - rhole), 0.8, 3), 0.8) * river, SIENNA, 0.7, rim=0,
           vary=ramp_y(sy, sy + br + 4, 1.0, 0.4))
    p.wash(p.soften(p.rough(rhole.astype(np.float32), 0.8, 3), 1.0) * river, UMBER, 1.2, rim=0, flow=0.5,
           vary=ramp_y(sy, sy + br, 0.15, 1.0))
    p.wash(p.soften(p.rough(rhole.astype(np.float32), 0.8, 3), 1.0) * river, PAYNE, 0.5, rim=0,
           vary=ramp_x(bx - br, bx + br, 0.3, 1.0))
    p.wash(p.soften(p.poly([(96, 254), (140, 254), (140, 258), (96, 258)]), 0.8) * river, UMBER, 0.6, rim=0)
    for i, (dy, w) in enumerate([(3, 14), (7.5, 9), (10, 15), (15.5, 6)]):
        y = sy + dy
        p.lift(p.rough(p.stroke([(bx - w, y), (bx + w, y - 0.3)], 0.8), 0.6, 3) * river, 0.5, dry=0.5)
    # 7 trees on the banks, each its own shape; the left ones stay low, below the title
    for x, base, h, sp, tw, n, cols in [(18, 270, 50, 0.9, 2.8, 11, [GOLD, TERRA, SIENNA, RAW]),
                                        (44, 258, 28, 0.8, 1.6, 8, [RAW, GOLD, TERRA]),
                                        ]:
        tree(p, x, base, h, sp, cols, rng, lean=0.03, trunk_w=tw, clumps=n, size=0.2)
        p.wash(p.soften(p.rough(p.poly([(x - 3, base), (x + 3, base - 0.5), (x + h * 0.7, base + 3),
                                        (x + h * 0.6, base + 5)]), 0.8, 4), 1.5) * np.maximum(lbank, rbank),
               UMBER, 0.75, rim=0)                                         # its shadow thrown right
    # 8 the big oak on the right bank, framing: its trunk forks, its crown climbs into the sky in clumps
    big = tree(p, 206, 300, 178, 0.33, [GOLD, TERRA, RAW, SIENNA, GOLD], rng, lean=-0.02, trunk_w=6.5, clumps=30,
               dark=TERRA, size=0.095, fork_at=0.37, leaves=6)
    p.wash(p.soften(p.ellipse(214, 301, 22, 4), 2) * rbank, UMBER, 0.6, rim=0)           # it stands in its shadow
    # 9 the trees in the water: soft vertical streaks under each tree, and the shade under the right bank
    for x, w, col in [(22, 26, TERRA), (46, 14, GOLD), (74, 10, PINE), (186, 20, GOLD), (208, 30, TERRA)]:
        streak = p.soften(p.rough(p.poly([(x - w / 2, 262), (x + w / 2, 262), (x + w * 0.35, 312), (x - w * 0.3, 308)]),
                                  1.5, 4), 2.5)
        p.wash(streak * river, col, 0.5, rim=0, flow=0.4, blotch=0.04)
    p.wash(river * p.soften(p.rough(p.poly([(142, 262), (164, 262), (176, 336), (150, 336)]), 2, 6), 3), VIOLET, 0.55,
           rim=0)
    for i in range(3):
        x, y, w = rng.uniform(90, 140), rng.uniform(286, 326), rng.uniform(5, 14)
        p.lift(p.rough(p.poly([(x, y), (x + w, y - 0.3), (x + w, y + 0.6), (x, y + 0.8)]), 0.3, 3) * river, 0.35)
    # 10 the near plane: a warm bush low in each corner, the right one under the oak
    # the near corners deepen, warm on the left, the oak's ground on the right
    p.wash(p.soften(p.ellipse(-10, 352, 90, 46), 14) * lbank, UMBER, 0.8, rim=0, flow=0.5, blotch=0.05)
    p.wash(p.soften(p.ellipse(250, 352, 80, 40), 14) * rbank, UMBER, 0.75, rim=0, flow=0.5, blotch=0.05)
    p.finish()
    return p


def XX_lt(x):
    from paint import XX as _XX
    return (_XX / S < x).astype(np.float32)


def YY_lt(y):
    """A mask of everything above world y (for the dome's upper half)."""
    from paint import YY as _YY
    return (_YY / S < y).astype(np.float32)


SCENES = {"lighthouse": lighthouse, "harbor": harbor, "autumn": autumn}

if __name__ == "__main__":
    for name in sys.argv[1:] or SCENES:
        p = SCENES[name]()
        p.save(f"out/{name}-xl.png")
        p.save(f"out/{name}-sm.png", (352, 514))
