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


def autumn():
    """An autumn river: golden trees on both banks, wet-in-wet, their colours bleeding; a stone arch bridge in the
    middle distance, its arch and its reflection closing a full circle; the river widening toward us, holding
    vertical streaks of the trees, with lifted ripples; a violet haze of far trees; on the right bank one big tree
    rises above the name line, its crown in the top right; reeds and fallen leaves on the near banks."""
    p = Paper(seed=31)
    rng = np.random.default_rng(32)
    GOLDS = [GOLD, RAW, TERRA, SIENNA]
    # 1 warm light and the far wood, wet-in-wet
    # the whole sky in a golden haze, deeper and warmer toward the top, pale where the light breaks through
    # behind the bridge; light enough that the title sits on it in deep umber
    full = p.soften(p.poly([(-20, -20), (260, -20), (260, 252), (-20, 252)]), 3)   # the sky ends at the far bank
    p.wash(full, GOLD, 0.75, rim=1.2, flow=0.2, blotch=0.03, vary=ramp_y(0, 250, 1.0, 0.55))
    p.wash(full, RAW, 0.35, rim=0.4, flow=0.2, blotch=0.03, vary=ramp_y(0, 160, 1.0, 0.0))
    p.wash(p.soften(p.poly([(-20, 150), (260, 140), (260, 240), (-20, 240)]), 16), ROSE, 0.35, rim=0, flow=0.5,
           blotch=0.05)
    p.lift(p.soften(p.ellipse(118, 230, 46, 22), 10), 0.45)
    far = np.zeros((H, W), np.float32)
    for i in range(16):
        far = np.maximum(far, p.ellipse(rng.uniform(-10, 246), rng.uniform(208, 232), rng.uniform(12, 22),
                                        rng.uniform(8, 13)))
    far = p.soften(np.maximum(far, p.poly([(-20, 226), (260, 222), (260, 246), (-20, 248)])), 2.5)
    p.wash(far, VIOLET, 0.75, rim=0.3, flow=0.5, blotch=0.07)
    p.wash(far * p.soften(p.ellipse(60, 222, 30, 10), 5), GOLD, 0.5, rim=0, flow=0.4)
    # a row of smaller crowns in the middle distance, paler, behind the bridge
    for x, y, rx, ry, cols in [(40, 226, 12, 9, [GOLD, RAW]), (84, 228, 10, 8, [TERRA, GOLD]),
                               (150, 226, 11, 9, [RAW, GOLD]), (190, 224, 12, 9, [GOLD, TERRA]),
                               (226, 222, 13, 10, [SIENNA, GOLD])]:
        crown(p, x, y, rx, ry, cols, rng, n=5)
    # 2 the river: narrow under the bridge, meandering toward us in an S; it holds the sky (ochre and grey-blue),
    # darkest along its banks
    rl = [(100, 252), (94, 262), (104, 274), (118, 288), (114, 302), (88, 318), (56, 334), (30, 350)]
    rr = [(136, 252), (142, 262), (148, 274), (162, 288), (170, 302), (160, 318), (150, 334), (150, 350)]
    river = p.rough(p.poly(rl + rr[::-1]), 0.8, 6, fine=0.4)
    p.wash(river, GOLD, 0.45, rim=1.2, flow=0.4, blotch=0.04)
    p.wash(river, SHADOW, 0.7, rim=1.0, flow=0.45, blotch=0.05, vary=ramp_y(250, 344, 0.6, 1.2))
    edge = np.clip(river - blur(river, 3 * S) * 1.1, 0, 1) * 2
    p.wash(np.clip(edge, 0, 1) * river, UMBER, 0.45, rim=0, flow=0.4)
    p.lift(river * p.soften(p.ellipse(120, 262, 18, 10), 5), 0.4)                 # the light in the water
    # 3 banks, loose, overlapping the river's edge; pale ochre far, burnt sienna near
    lbank = p.rough(p.poly([(-20, 248), (102, 248)] + rl[1:] + [(-20, 350)]), 1.0, 5, fine=0.5)
    rbank = p.rough(p.poly([(134, 248), (260, 246), (260, 350)] + rr[::-1][:-1]), 1.0, 5, fine=0.5)
    lbank = np.clip(blur(lbank, 1.2 * S) * 2.2, 0, 1)        # the banks overlap the water's edge, no paper seam
    rbank = np.clip(blur(rbank, 1.2 * S) * 2.2, 0, 1)
    for bank in (lbank, rbank):
        p.wash(bank, RAW, 0.9, rim=1.0, flow=0.5, blotch=0.07, vary=ramp_y(248, 344, 0.7, 1.2))
        for i in range(34):                       # grass in horizontal dry-brush strokes, longer toward us
            y0 = float(rng.uniform(250, 344))
            x0 = float(rng.uniform(-20, 250))
            ln = 6 + (y0 - 250) * 0.25
            p.wash(p.rough(p.stroke([(x0, y0), (x0 + ln * 0.5, y0 - 0.6), (x0 + ln, y0 - 0.2)], 1.0 + (y0 - 250) / 60),
                           0.5, 4) * bank, str(rng.choice([SIENNA, GOLD, UMBER])), 0.6, rim=0.6, dry=0.6, blotch=0.03)
        p.wash(bank * ramp_y(270, 344, 0.0, 1.0), SIENNA, 0.6, rim=0.3, flow=0.5, blotch=0.06)
    for corner in (p.soften(p.ellipse(-10, 350, 90, 50), 16) * lbank, p.soften(p.ellipse(250, 350, 90, 54), 16) * rbank):
        p.wash(corner, SIENNA, 0.6, rim=0, flow=0.3, blotch=0.03)                 # the bottom corners anchor it
    # 4 the bridge: loose stone with a lit face and a curved top; the arch opening a deep warm umber; its
    # reflection broken by the water
    bx, by, br = 118, 254, 21
    Xw = __import__("paint").XX / S
    Yw = __import__("paint").YY / S
    hump = 228 - 6 * np.exp(-((Xw - bx) / 30) ** 2)
    deck = p.rough(((Yw >= hump) & (Yw <= 255) & (Xw >= 80) & (Xw <= 156)).astype(np.float32), 0.5, 3, fine=0.4)
    hole = p.ellipse(bx, by, br, br * 0.95) * YY_lt(by + 0.01)
    stone = np.clip(deck - hole, 0, 1)
    p.loose(stone, [RAW, GOLD, SIENNA, RAW], 0.9, n=8, rough=0.2, patch=0.3)
    p.wash(stone * ramp_x(100, 156, 0.0, 1.0), UMBER, 0.5, rim=0.4, flow=0.4, gran=0.5)
    coping = p.rough(((np.abs(Yw - hump - 1.0) < 1.4) & (Xw >= 78) & (Xw <= 158)).astype(np.float32), 0.3, 3)
    p.wash(coping, UMBER, 0.75, rim=0.4)
    for a in np.linspace(math.pi * 1.06, math.pi * 1.94, 8):
        x0, y0 = bx + math.cos(a) * (br + 0.5), by + math.sin(a) * (br * 0.95 + 0.5)
        x1, y1 = bx + math.cos(a) * (br + 3.6), by + math.sin(a) * (br * 0.95 + 3.6)
        p.wash(p.rough(p.stroke([(x0, y0), (x1, y1)], 0.7, taper=False), 0.15, 1) * stone, UMBER, 0.8, rim=0, dry=0.3)
    p.loose(hole, [UMBER, SIENNA, UMBER], 1.3, n=3, rough=0.2, patch=0.6)
    p.wash(hole * ramp_y(by - br, by - br * 0.3, 1.0, 0.0), PAYNE, 0.7, rim=0)       # the shaded underside
    rhole = p.ellipse(bx, by, br, br * 0.95) * (1 - YY_lt(by))
    p.wash(p.soften(p.rough(rhole, 1.2, 3), 1.5) * river, UMBER, 0.6, rim=0, flow=0.5, blotch=0.04,
           vary=ramp_y(by, by + br, 1.0, 0.3))                          # the arch's reflection, soft and fading
    for i in range(3):
        y = by + 4 + i * 4
        p.lift(p.rough(p.stroke([(bx - br + 4, y), (bx + br - 4, y - 0.3)], 0.9), 0.5, 3) * rhole, 0.45, dry=0.6)
    p.wash(p.soften(p.rough(p.poly([(80, 254), (156, 254), (156, 262), (80, 262)]) * (1 - rhole), 0.6, 3), 1) * river,
           RAW, 0.45, rim=0.1, blotch=0.03)
    # 5 trees on the banks, crowns wet-in-wet; left ones kept below the name line
    for x, base, tw, th, rx, ry, cols in [(14, 262, 3.0, 24, 22, 18, [TERRA, GOLD, SIENNA]),
                                          (56, 248, 2.0, 16, 13, 11, [GOLD, RAW, TERRA]),
                                          (78, 252, 1.6, 12, 9, 8, [RAW, GOLD]),
                                          (170, 250, 2.2, 18, 14, 12, [GOLD, SIENNA, RAW])]:
        trunk = p.rough(p.poly([(x - tw, base), (x - tw * 0.5, base - th), (x + tw * 0.5, base - th),
                                (x + tw, base)]), 0.3, 2)
        p.wash(trunk, UMBER, 1.2, rim=0.5, blotch=0.04)
        crown(p, x, base - th - ry * 0.5, rx, ry, cols, rng)
    # reflections of the crowns: soft vertical streaks in the water
    for x, w, col in [(16, 26, TERRA), (52, 18, GOLD), (182, 16, GOLD), (210, 30, GOLD)]:
        streak = p.soften(p.rough(p.poly([(x - w / 2, 262), (x + w / 2, 262), (x + w * 0.4, 304), (x - w * 0.3, 300)]),
                                  1.5, 4), 2.2)
        p.wash(streak * river, col, 0.5, rim=0, flow=0.4, blotch=0.04)
    for i in range(4):
        x, y, w = rng.uniform(90, 150), rng.uniform(266, 336), rng.uniform(6, 14)
        p.lift(p.rough(p.poly([(x, y), (x + w, y - 0.3), (x + w, y + 0.7), (x, y + 0.9)]), 0.3, 3) * river, 0.35)
    # 6 the big tree on the right bank
    tx = 224
    trunk = p.rough(p.poly([(tx - 7, 292), (tx - 4, 270), (tx - 4.2, 236), (tx - 1.6, 200), (tx - 0.4, 160),
                            (tx + 4.2, 160), (tx + 3.6, 200), (tx + 2.2, 236), (tx + 3.4, 270), (tx + 7.5, 292)]),
                    0.6, 4, fine=0.4)
    limbs = p.rough(p.stroke([(tx + 1, 176), (232, 160), (240, 150)], 2.0), 0.4, 3)
    t = np.maximum(trunk, limbs)
    p.wash(t, UMBER, 1.3, rim=0.6, blotch=0.05, gran=0.4)
    p.wash(t * ramp_x(tx - 3, tx + 9, 0, 1), PAYNE, 0.9, rim=0.2, blotch=0.04)
    p.lift(p.rough(p.stroke([(tx - 5, 290), (tx - 4, 220), (tx - 2.6, 160)], 1.1), 0.3, 3) * t, 0.45)
    crown(p, 230, 150, 26, 28, [GOLD, TERRA, RAW, SIENNA], rng, n=14)
    crown(p, 216, 178, 10, 9, [GOLD, RAW], rng, n=6)
    p.wash(p.soften(p.poly([(-20, 300), (260, 296), (260, 360), (-20, 360)]), 10) * river, ULTRA, 0.45, rim=0,
           blotch=0.05, vary=ramp_y(296, 344, 0.3, 1.0))
    p.wash(river * p.soften(p.rough(p.poly([(140, 262), (160, 262), (190, 330), (160, 330)]), 2, 6), 3), VIOLET, 0.5,
           rim=0)                                                                  # the bank's shadow on the water
    for bank in (lbank, rbank):
        for i in range(26):
            x0 = float(rng.uniform(-10, 240))
            y0 = float(rng.uniform(252, 344))
            p.wash(p.rough(p.stroke([(x0, y0), (x0 + rng.uniform(3, 8), y0 - rng.uniform(0, 1.5))],
                                    rng.uniform(0.8, 1.4)), 0.3, 2) * bank, UMBER, 0.6, rim=0.3, dry=0.6, blotch=0.03)
    # warm bushes framing the bottom corners, the nearest plane
    crown(p, 238, 334, 20, 16, [GOLD, SIENNA, TERRA], rng, n=7)
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
