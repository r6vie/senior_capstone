"""Three more strata covers, chosen to be relatable for American members (Josef, 2026-11-20): a lakefront city at
dusk, a prairie farm at harvest, a bay bridge at sunset. Same style and rules as covers_new.py (see CRITIC.md):
236 x 344 world, title and name on paper at the top, art below y ~180 left of x ~200 (the shelf-size name line),
light from the left, no UI red.

python3 covers_us.py [city|prairie|bay ...] -> out/us-{name}-{xl,sm}.png"""
import sys
sys.path.insert(0, ".")
from strata import Ridge, Blob, Water, Band, Mesa, River, Firs, trees, render
from covers_new import Blocks, disc

# ---- 1 lakefront city at dusk ----
DUSK_SUN = ["#F4C79A", "#F0B988", "#EBAB78"]
TOWER_L = ["#C9A79A", "#BF9C8F", "#B49184"]          # faces catching the last warm light
TOWER_D = ["#5E6A86", "#55607C", "#4C5672"]          # faces in shade, slate blue
TOWER_FAR = (["#D9CCD0", "#D2C4C9"], ["#A9AABD", "#A1A2B6"])
WINDOW = ["#F2D58E", "#EBCB7E"]
LAKE = ["#7C8BA8", "#72809D", "#687592", "#5F6B87"]
LAKE_G = ["#D9B7A6", "#C9AFA8"]
PIER = (["#8C8478", "#80786D"], ["#4E4A46", "#45413E"])
LIGHT_W = ["#F1EEE8", "#E7E3DC"]
LIGHT_D = ["#4A4448", "#403B3F"]
CLOUD_P = ["#F2DCD6", "#EBD2CC", "#E4C8C3"]


def tower(cx, top, hw, base, seed, lit=TOWER_L, dark=TOWER_D):
    return Mesa(cx, top, hw, hw, base, lit, dark, ledges=1, bed=8, seed=seed, wobble=0, speckle=0, ragged=0,
                flicker=0.0)


def city():
    """The skyline across the lake at dusk: one dominant tower with a setback crown on the right (the only thing above
    the name line), five more of uneven height and width with gaps between them; a continuous pale far skyline behind
    with the sun half set into it on the left; faces lit warm on the left, slate in shade on the right, a few lit
    windows clustered on two towers; the lake below with a warm reflection under the main tower; a short breakwater
    stepping out to a small lighthouse, and a dark rocky shore in the lower left as the near anchor."""
    # the main tower wholly right of the name column (its left edge past x 202); the rest broken up unevenly: a
    # stepped block with a shoulder, a stub, a slim one, a low one
    towers = [tower(219, 150, 14, 280, 1), tower(219, 138, 9, 152, 11), tower(219, 126, 2, 140, 12),
              tower(172, 216, 12, 280, 3), tower(190, 232, 6, 280, 8), tower(146, 268, 6, 280, 4),
              tower(124, 226, 7, 280, 6), tower(100, 252, 6, 280, 7)]
    # the far skyline: one continuous pale band of low blocks, no paper between them
    far = [tower(x, t, 13, 280, 20 + i, *TOWER_FAR) for i, (x, t) in
           enumerate([(-6, 256), (20, 250), (46, 258), (72, 248), (98, 254), (124, 246), (150, 252), (176, 244),
                      (202, 250), (228, 246), (254, 252)])]
    windows = Blocks([(x, y, x + 2.5, y + 4, WINDOW) for x, y in
                      [(208, 176), (212, 214)]])
    lake = Water(280, 352, -120, 720, LAKE, ["#9AA6BE", "#A4AFC6"], seed=30, mirror=towers, gaps=(0, 0), squash=0.5)
    lake.brick = (5.0, 14.0)
    return [
        disc(54, 250, 18, DUSK_SUN),
        *far,
        *towers,
        windows,
        Band(-60, 300, 276, 282, ["#4E5268", "#474B60"], seed=31, lens=0.0),       # the shoreline under the city
        lake,
        # the main tower's warm reflection
        Blob([(219, 292, 8, 4), (217, 304, 6, 4), (220, 316, 5, 3.5)], ["#E5BFA4", "#DDB49A"], top_light=False),
        # one solid dark shore wedge in the lower left, the near anchor
        Ridge([(-30, 298, 30, 118, 0.85)], 352, ["#3A4058", "#353B52"], ["#2A3048", "#252A40"], seed=34, rough=3,
              ribs=0.3, smooth=True, flicker=0.02),
    ]


# ---- 2 prairie farm at harvest ----
SUN_G = ["#F5DDA0", "#F1D18A", "#ECC57A"]
WHEAT = ["#E9CC86", "#E2C177", "#DBB66A"]
WHEAT_D = ["#C9A25A", "#BD9750"]
CORN = ["#9DAA62", "#909E57", "#83924D"]
PLOW = ["#A8805C", "#9C7552", "#906A49"]
ROAD = ["#D9C8A8", "#CFBD9C", "#C4B290"]
BARN_L = ["#9A5A3C", "#8E5236"]                    # weathered barn: rust brown, never the UI red
BARN_D = ["#5E3426", "#552F22"]
BARN_ROOF = ["#5C5650", "#524D48"]
BARN_TRIM = ["#E8E0D2", "#DED5C6"]
SILO_L = ["#C9C4BA", "#BFB9AE"]
SILO_D = ["#8C877E", "#837E75"]
WINDBREAK = ["#5E7445", "#526840", "#465C37", "#3A4F2E"]
FAR_FIELD = ["#D8CFA8", "#D1C79E"]


class Furrows:
    """Fields in perspective: crop rows fanning out from a vanishing point at the farmstead, alternating wheat and
    darker stubble, so the field leads the eye to the barn instead of lying in stripes."""

    brick = (1.6, 6.0)

    def __init__(self, y0, vx, vy, inks_a, inks_b, rows=22, seed=1):
        from strata import hexrgb
        self.y0, self.vx, self.vy, self.rows, self.seed = y0, vx, vy, rows, seed
        self.a, self.b = [hexrgb(c) for c in inks_a], [hexrgb(c) for c in inks_b]

    def cover(self, x, y):
        import numpy as np
        return np.full(len(x), y >= self.y0, dtype=bool)

    def colour(self, x, y, rng):
        import math
        ang = math.atan2(x - self.vx, max(1.0, y - self.vy))
        pal = self.a if int(math.floor(ang * self.rows / math.pi * 2)) % 2 else self.b
        return pal[int(rng.random() * len(pal))]


def prairie():
    """Harvest on the plains: a flat horizon with the low gold sun on the left, half behind a windbreak in three
    irregular groups; the farmstead in the middle distance, a gambrel barn (lit gable, shaded side, one door) with a
    domed silo close beside it, both throwing shadow right; crop rows fanning out toward the barn; the farm road
    curving in from the lower left; a cluster of fence posts in the near corner as the dark anchor."""
    vx, vy = 165, 258
    LIT, SHADE, ROOFD = ["#8A4A32", "#80442E"], ["#5E3326", "#552E22"], ["#3E3936", "#36322F"]
    # the gambrel gable end facing us: straight walls, then steep lower roof flanks, then a shallow cap; a dark roof
    # edge traces the outline; the side wall goes back to the right in shade under its own roof plane
    # the gambrel gable end facing us, larger so its details read: straight walls, steep lower roof flanks, a shallow
    # cap; a bold pale trim traces the roof; the side wall goes back to the right in shade under its roof plane
    rows = [(y, 124, 174) for y in range(262, 232, -4)] + \
           [(232, 125, 173), (228, 127, 171), (224, 131, 167), (220, 137, 161), (216, 143, 155), (212, 147, 151)]
    WALLS = 7                          # rows of straight wall before the roof begins
    gable = [(l, y - 4, r, y, LIT) for y, l, r in rows]
    # the roof edge and its cream trim run continuously: each piece spans from this row's edge back to the one below
    roof_rows = rows[WALLS - 1:]
    edge, eave_trim = [], []
    for (yb, lb, rb), (y, l, r) in zip(roof_rows, roof_rows[1:]):
        edge += [(min(l, lb) - 3, y - 4, l, y, ROOFD), (r, y - 4, max(r, rb) + 3, y, ROOFD)]
    for (yb, lb, rb), (y, l, r) in zip(roof_rows, roof_rows[1:]):
        eave_trim += [(min(l, lb), y - 4, l + 2, y, ["#EDE6D8", "#E3DACB"]),
                      (r - 2, y - 4, max(r, rb), y, ["#EDE6D8", "#E3DACB"])]
    side = [(174, 234, 198, 262, SHADE)]
    roof_side = [(r + 1, y - 4, r + 24, y, ROOFD) for y, l, r in rows[WALLS - 1:]]
    TRIM = ["#EDE6D8", "#E3DACB"]
    BOARD = ["#7A4029", "#723C27"]
    boards = [(x, 234, x + 1.5, 262, BOARD) for x in (130, 137, 161, 168)]
    # a plain cream frame round one double door, a single dark seam down its middle; a small framed hayloft
    door = [(138, 240, 160, 262, TRIM), (141, 243, 157, 262, SHADE), (148, 243, 150, 262, ["#3A2A22"])]
    loft = [(146, 222, 156, 230, TRIM), (148, 224, 154, 230, SHADE)]
    windows = [(178, 242, 185, 250, ["#3A2A22"]), (188, 242, 195, 250, ["#3A2A22"]),
               (177, 240, 186, 242, TRIM), (187, 240, 196, 242, TRIM)]
    cupola = []
    barn = Blocks(gable + boards + side + roof_side + edge + eave_trim + door + loft + windows + cupola)
    SILO_LB, SILO_DB = ["#9A9890", "#928F88"], ["#6E6C68", "#666461"]
    silo = Blocks([(202, 196, 209, 262, SILO_LB), (209, 196, 216, 262, SILO_DB),
                   (203, 192, 215, 196, SILO_LB), (205, 188, 213, 192, SILO_LB), (207, 185, 211, 188, SILO_DB)])
    dome = Blocks([])
    road = River(262, 344, 140, -40, 4, 60, ROAD, ROAD, swings=0.6, phase=0.0, seed=40)
    # a fence in perspective from the near corner back toward the road: posts shrinking and closing up with distance
    # (ground line, height, width), two continuous rails along them
    # a near fence along the lower left, receding gently: the posts and both rails read as separate pieces
    pts = [(6, 344, 28, 4), (38, 336, 23, 3.5), (66, 329, 19, 3), (90, 323, 15, 3)]
    POST, RAIL = ["#4A3A2C", "#40322A"], ["#5A4030", "#523A2B"]
    rails = []
    for frac in (0.3, 0.65):
        for (xa, ga, ha, wa), (xb, gb, hb, wb) in zip(pts, pts[1:]):
            ya, yb = ga - ha * (1 - frac), gb - hb * (1 - frac)
            th = 2.5
            for k in range(int(xa), int(xb), 2):
                t = (k - xa) / (xb - xa)
                y0 = ya + (yb - ya) * t
                y1 = ya + (yb - ya) * min(1, t + 2 / (xb - xa))
                rails.append((k, min(y0, y1) - th / 2, k + 2.5, max(y0, y1) + th / 2, RAIL))
    posts = Blocks(rails + [(x, g - h, x + w, g, POST) for x, g, h, w in pts])
    return [
        disc(58, 236, 20, SUN_G),
        # the far fields: an uneven low strip, darker under the trees
        Ridge([(10, 250, 50, 40, 1.0), (90, 254, 50, 50, 1.0), (170, 251, 40, 50, 1.0), (240, 252, 50, 40, 1.0)],
              262, ["#C9B98A", "#BFAF80"], ["#B5A576", "#AC9C6E"], seed=41, rough=2, smooth=True, flicker=0.02),
        trees([18, 34, 52], 256, 10, WINDBREAK, seed=42, spread=0.8),
        trees([96, 108], 258, 6, WINDBREAK, seed=43, spread=0.8),
        trees([226, 238], 256, 9, WINDBREAK, seed=48, spread=0.8),
        Furrows(262, vx, vy, WHEAT, ["#B38E52", "#A8844A"], rows=13, seed=45),
        # darker furrow lines converging on the farmstead, and the near field deepening toward us
        Blocks([(vx + (xb - vx) * (y - vy) / (344 - vy), y, vx + (xb - vx) * (y - vy) / (344 - vy) + 2 + (y - vy) / 16,
                 y + 4, ["#A88440", "#9E7B3B"]) for xb in (-60, 30, 120, 220, 300, 380) for y in range(266, 344, 4)]),
        Blob([(118, 344, 160, 18)], ["#9C7A3A", "#94733A", "#8C6C36"], top_light=False),
        road,
        # shadows thrown right by the barn and silo
        Blob([(214, 266, 30, 4)], ["#B9985E", "#AE8E56"], top_light=False),
        barn, silo, dome,
        posts,
    ]


# ---- 3 bay bridge at sunset ----
SUN_S = ["#F3C29A", "#EFB487", "#E9A676"]
HILL_FAR = (["#C8BFD3", "#C0B7CC"], ["#A39CB6", "#9B94AE"])
HILL_MID = (["#A9A3B8", "#A09AAF"], ["#7E7896", "#76708E"])
BRIDGE = ["#9B5A3E", "#8F5238"]                  # muted rust, never the UI red
BRIDGE_D = ["#6A3A28", "#5F3424"]
BAY = ["#8C9CB6", "#8292AC", "#7787A1", "#6C7C96"]
BAY_G = ["#EAC6AE", "#E2BBA3"]
SAIL = ["#F4F1EC", "#E9E5DE"]
HEADLAND = (["#7E8C5E", "#738255", "#68774C"], ["#465436", "#3E4B30", "#36422A"])
CYPRESS = ["#3F5236", "#36482F", "#2E3E28"]


def bay():
    """A suspension bridge across the bay at sunset, seen at an angle: the near tower tall on the right (the only
    thing above the name line), two legs and three crossbars, its left leg lit; the far tower smaller and paler toward
    the middle; a solid deck with a dark underside running off to the left; the main cable a clean catenary two slabs
    thick; the sun low in the haze between the towers, clear of every cable, its warm reflection beneath; soft hills
    behind, a step darker so the deck separates; a headland with cypresses in the lower left as the near anchor."""
    import math
    # a level deck with a dark underside; two towers (the near one tall on the right, the far one smaller); one
    # continuous main cable: up from a shore anchor to the far tower's top, sagging below the sun, up to the near
    # tower's top where it stops; hangers at even spacing between cable and deck
    DECK_T, DECK_B = 240, 246
    TF = (121, 194)                    # far tower top (centre)
    TN = (220, 124)                    # near tower top (centre)
    LOW = (156, 230)                   # the cable's lowest point, below the sun

    def cable_y(x):
        if x <= TF[0]:                                     # from the anchor at the deck's far end up to the far tower
            return DECK_T + (TF[1] - DECK_T) * (x - 0) / (TF[0] - 0)
        if x <= LOW[0]:
            return LOW[1] - (LOW[1] - TF[1]) * ((LOW[0] - x) / (LOW[0] - TF[0])) ** 2
        # a gentler rise that starts sooner and only meets the tower at its top
        return LOW[1] - (LOW[1] - TN[1]) * ((x - LOW[0]) / (208 - LOW[0])) ** 1.45

    # each cable piece spans its own slope, so the steep run up to the tower stays one line
    cable = [(x, min(cable_y(x), cable_y(x + 2)) - 2.5, x + 3, max(cable_y(x), cable_y(x + 2)) + 2.5, BRIDGE_D)
             for x in range(0, 206, 2)]
    hangers = [(x, cable_y(x + 1) + 2, x + 2, DECK_T, ["#7A4630"]) for x in range(TF[0] + 12, 204, 10)]
    deck = [(-20, DECK_T, 260, DECK_T + 3, BRIDGE), (-20, DECK_T + 3, 260, DECK_B, ["#4A2A1E", "#43261B"])]
    far = [(114, 194, 119, 250, ["#B88A72", "#AE8068"]), (124, 194, 129, 250, ["#9C6E58", "#93664F"]),
           (114, 204, 129, 208, ["#9C6E58"]), (114, 222, 129, 226, ["#9C6E58"]), (113, 190, 130, 194, ["#9C6E58"])]
    near = [(208, 124, 216, 256, BRIDGE), (226, 124, 234, 256, BRIDGE_D), (206, 118, 236, 124, BRIDGE_D),
            (208, 146, 234, 152, BRIDGE_D), (208, 182, 234, 188, BRIDGE_D), (208, 216, 234, 222, BRIDGE_D)]
    bridge = Blocks(cable + hangers + deck + far + near)
    # one low continuous far shore just above the deck, no loose bumps
    hills = Ridge([(40, 232, 160, 140, 0.6), (190, 230, 110, 100, 0.6)], 258, ["#6E6A85", "#68647F"],
                  ["#5A5672", "#54506B"], seed=50, rough=2, smooth=True, flicker=0.02)
    bay_w = Water(256, 352, -120, 720, BAY, ["#9DACC4", "#A7B5CB"], seed=51, mirror=[hills], gaps=(0, 0),
                  squash=0.5)
    bay_w.brick = (5.0, 14.0)
    return [
        disc(150, 198, 14, SUN_S),
        hills,
        Band(-60, 300, 254, 260, ["#5E5A72", "#56526A"], seed=53, lens=0.0),
        bay_w,
        Blob([(150, 270, 9, 3.5), (149, 284, 7, 3.5), (151, 298, 5, 3)], ["#EDC4A6", "#E5B999"], top_light=False),
        bridge,
        # the headland in the lower left, lit on its left shoulder, and its cypresses
        # one low, uneven dark bluff spreading off the lower-left edge
        Ridge([(-30, 304, 110, 120, 0.7), (56, 322, 36, 50, 0.9)], 352, ["#3E4C36", "#38452F"],
              ["#2E3A2A", "#283324"], seed=54, rough=4, ribs=0.4, smooth=True, flicker=0.03),
    ]


SCENES = {"city": city, "prairie": prairie, "bay": bay}

if __name__ == "__main__":
    for name in sys.argv[1:] or SCENES:
        fn = SCENES[name]
        render(fn(), (0, 0, 236, 344), (472, 688), 8, paper=(255, 255, 255), clean=True, jitter=0.04).save(
            f"out/us-{name}-xl.png")
        render(fn(), (0, 0, 236, 344), (244, 356), 3, paper=(255, 255, 255), clean=True, jitter=0.04).save(
            f"out/us-{name}-sm.png")
