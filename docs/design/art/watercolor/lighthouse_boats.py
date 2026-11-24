"""A new version of the daytime lighthouse (Josef, 2026-11-23: "a new version of the day lighthouse that takes
the boats from harbor and put the cover next to the existing ones (not replace)"). Round 1's lighthouse, as it was,
with the round 1 harbor's two wooden fishing boats in its foreground water.

python3 lighthouse_boats.py -> out/lighthouse-boats-xl.png and out/lighthouse-boats-sm.png"""
import math
import sys
import numpy as np
sys.path.insert(0, ".")
from paint import Paper, ramp_y, ramp_x, blur, S
from covers import (ULTRA, CERUL, PAYNE, SIENNA, RAW, ROSE, SAP, OLIVE, UMBER, TERRA, SHADOW, GOLD, hull_mask, boat,
                    house_masks)


def lighthouse_boats():
    """The round 1 lighthouse (commit 5813d6b, unchanged) with the harbor's two fishing boats moored in the open
    water on the left, the hulls kept out of the sea's glazes so they read clean against it.

    Keeping the light: a white lighthouse on a grassy headland on the right, the only thing above the name
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
    # the harbor's two boats at the harbor's size and colours (Josef preferred these to a smaller, recoloured pass)
    boats = [(8, 300, 92, CERUL, TERRA, 104), (104, 318, 74, RAW, CERUL, None)]
    hulls = np.clip((np.maximum.reduce([blur(hull_mask(p, bx, by, bw), 0.6 * S) for bx, by, bw, *_ in boats]) - 0.7)
                    * 6, 0, 1)
    around = (1 - np.maximum(land, keep_white)) * (1 - hulls)
    # 1 sky: pale cerulean wet-in-wet, clouds as bare paper, rose low on the left, one backrun
    sky = p.soften(p.poly([(-20, 184), (150, 178), (190, 140), (260, 130), (260, 252), (-20, 252)]), 5)
    clouds = np.maximum.reduce([p.soften(p.ellipse(x, y, rx, ry), 6) for x, y, rx, ry in
                                [(40, 200, 34, 8), (126, 196, 30, 7), (180, 160, 22, 8), (90, 216, 24, 4)]])
    p.wash(sky * (1 - clouds * 0.95) * around, CERUL, 0.6, rim=1.4, flow=0.35, blotch=0.06,
           vary=ramp_y(150, 250, 1.0, 0.6) * ramp_x(0, 150, 0.6, 1.0))
    p.wash(p.soften(p.poly([(-20, 220), (110, 226), (140, 252), (-20, 252)]), 8) * around, ROSE, 0.5, rim=0,
           flow=0.3, blotch=0.04)
    p.wash(p.soften(p.poly([(150, 140), (260, 128), (260, 186), (170, 192)]), 7) * around, ULTRA, 0.25, rim=0,
           flow=0.4, blotch=0.06)
    # 2 far headland
    p.wash(p.rough(p.poly([(-6, 251), (6, 245), (22, 241), (40, 242), (58, 247), (74, 251)]), 0.8, 5),
           ULTRA, 0.5, rim=1.4, flow=0.25, blotch=0.05)
    # 3 the sea
    sea = p.rough(p.poly([(-20, 251), (260, 251), (260, 360), (-20, 360)]), 0.3, 8)
    p.wash(sea * around, CERUL, 0.75, rim=1.0, flow=0.3, blotch=0.06, vary=ramp_y(251, 344, 0.7, 1.2))
    p.wash(p.soften(p.poly([(-20, 290), (260, 286), (260, 360), (-20, 360)]), 10) * around, ULTRA, 0.45, rim=0,
           flow=0.35, blotch=0.06, vary=ramp_y(286, 344, 0.3, 1.0))
    for i, (x, y, w) in enumerate([(14, 258, 30), (52, 262, 6), (20, 268, 14), (66, 256, 18)]):
        p.lift(p.rough(p.poly([(x, y), (x + w, y - 0.4), (x + w, y + 0.9), (x, y + 1.2)]), 0.5, 3, fine=0.4) * around,
               0.6)
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
    # 5 three rock groups at the waterline, two values each; the surf lifted as broad, broken paper round them
    for i, (x, y, rx, ry) in enumerate([(176, 282, 12, 4), (124, 279, 5, 2.2), (92, 270, 2.6, 1.2)]):
        r = p.rough(p.ellipse(x, y, rx, ry), rx * 0.15, 2, fine=0.4)
        p.wash(r, UMBER, 1.0, rim=1.0, gran=0.4, blotch=0.05)
        p.wash(r * ramp_y(y - ry * 0.2, y + ry, 0.0, 1.0), PAYNE, 1.1, rim=0.4, blotch=0.04)
    for i, (pts, w) in enumerate([([(84, 272), (110, 280), (146, 285), (176, 290), (210, 290), (250, 292)], 4.5),
                                  ([(150, 296), (190, 300), (230, 302)], 2.6)]):
        p.lift(p.rough(p.stroke(pts, w), 1.4, 6, fine=0.9) * (1 - face), 0.8, dry=0.55)
    # 6 the lighthouse: a tapered tower, its left face bare paper, the right face a soft cool shadow built loose,
    # two faint bands, the lantern one warm glaze under a dark cap; the cottage a cream block standing on the grass
    shade = p.soften(p.poly([(tx + 0.5, tb), (tx + 0.5, ty + 16), (tx + 7.5, ty + 16), (tx + 10, tb)]), 2.0)
    p.loose(shade * np.clip(tower * 1.15, 0, 1), [ULTRA, SHADOW, ULTRA], 0.55, n=5, rough=0.2, patch=0.5,
            vary=ramp_x(tx - 2, tx + 9, 0.2, 1.0))
    p.wash(shade * np.clip(tower * 1.15, 0, 1), SIENNA, 0.12, rim=0.4)
    for yb in (ty + 46, ty + 76):
        p.wash(p.rough(p.poly([(tx - 9, yb), (tx + 9, yb), (tx + 9, yb + 4), (tx - 9, yb + 4)]), 0.3, 3) * tower,
               SHADOW, 0.3, rim=0.8, flow=0.4)
    p.wash(p.rough(p.poly([(tx - 10, ty + 18), (tx + 10, ty + 18), (tx + 10, ty + 15), (tx - 10, ty + 15)]), 0.25, 2),
           PAYNE, 1.2, rim=0.5)                                                # the gallery
    p.wash(p.rough(p.poly([(tx - 5, ty + 15), (tx + 5, ty + 15), (tx + 5, ty + 7), (tx - 5, ty + 7)]), 0.25, 2),
           GOLD if "GOLD" in globals() else RAW, 1.0, rim=1.2, flow=0.4)     # the lamp room, one warm glaze
    p.wash(p.rough(p.poly([(tx - 7, ty + 7.5), (tx + 7, ty + 7.5), (tx, ty - 1)]), 0.25, 2), PAYNE, 1.4, rim=0.6)
    p.wash(p.rough(p.poly([(tx - 2.6, tb - 1), (tx - 2.6, tb - 6), (tx - 0.2, tb - 6), (tx - 0.2, tb - 1)]), 0.2, 2),
           PAYNE, 0.8, rim=0.4)
    cx0 = 184
    gy = 254 - (cx0 - 104) * 0.29                                                # the grass line under the cottage
    # the keeper's cottage, painted like the harbor's houses (Josef: "more like the harbor houses"): the lit front a
    # whisper of warm glaze on paper, the side cool, a terracotta tile roof in patches, an eave shadow, small windows
    hx, hb, hw, hh, hd = cx0 - 11, gy + 2, 17, 11, 5
    front, side, roof = (p.rough(m, 0.4, 3, fine=0.3) for m in house_masks(p, hx, hb, hw, hh, hd, "tile"))
    p.lift(np.clip(blur(np.maximum.reduce([front, side, roof]), 0.3 * S) * 1.4, 0, 1), 0.9)
    p.wash(front, RAW, 0.16, rim=1.0, flow=0.4, blotch=0.04)
    p.loose(side, [SHADOW, ULTRA, SHADOW], 0.7, n=3, rough=0.2, patch=0.7)
    p.loose(roof, [TERRA, SIENNA, TERRA], 0.95, n=4, rough=0.2, patch=0.6)
    eave = p.rough(p.poly([(hx, hb - hh), (hx + hw, hb - hh), (hx + hw, hb - hh + 2.2), (hx, hb - hh + 1.6)]), 0.3, 2,
                   fine=0.2)
    p.wash(eave * front, SHADOW, 0.55, rim=0.2, blotch=0.03)
    for wx, wy in [(hx + 3, hb - 7), (hx + 11, hb - 7.5)]:
        p.wash(p.rough(p.poly([(wx, wy), (wx + 1.8, wy), (wx + 1.8, wy + 2.8), (wx, wy + 2.8)]), 0.15, 1) * front,
               PAYNE, 0.85, rim=0.3, blotch=0.02)
    p.wash(p.rough(p.poly([(hx + 7, hb), (hx + 7, hb - 4.5), (hx + 9.2, hb - 4.5), (hx + 9.2, hb)]), 0.15, 1) * front,
           UMBER, 0.9, rim=0.3)                                                  # the door
    # 7 the two boats, moored in the open water left of the headland; masts stay below the name line
    for bx, by, bw, hull, trim, mast in boats:
        boat(p, bx, by, bw, hull, trim, mast=mast)
    # 8 two gulls
    for i, (x, y, k) in enumerate([(60, 196, 4.2), (80, 204, 3.2)]):
        left = [(x - k + k * u, y - k * 0.55 * math.sin(math.pi * u) * (1.2 - u)) for u in np.linspace(0, 1, 8)]
        right = [(x + k * u, y - k * 0.55 * math.sin(math.pi * u) * (0.2 + u)) for u in np.linspace(0, 1, 8)]
        g = np.maximum(p.stroke(left, 0.7), p.stroke(right, 0.7))
        p.wash(g, PAYNE, 1.4, rim=0, gran=0)
    p.fade_top(176, 196, right=(178, 200, 136), keep=keep_white)
    p.finish()
    return p


if __name__ == "__main__":
    p = lighthouse_boats()
    p.save("out/lighthouse-boats-xl.png")
    p.save("out/lighthouse-boats-sm.png", (352, 514))
