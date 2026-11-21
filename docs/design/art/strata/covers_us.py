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
    rows = [(240, 140, 176)] * 0 + [(y, 140, 176) for y in range(262, 240, -4)] + \
           [(240, 141, 175), (236, 142, 174), (232, 144, 172), (228, 148, 168), (224, 153, 163), (220, 156, 160)]
    gable = [(l, y - 4, r, y, LIT) for y, l, r in rows]
    edge = [(l - 2, y - 4, l + 1, y, ROOFD) for y, l, r in rows[5:]] + [(r - 1, y - 4, r + 2, y, ROOFD)
                                                                         for y, l, r in rows[5:]]
    side = [(176, 240, 194, 262, SHADE)]
    roof_side = [(r, y - 4, r + 18, y, ROOFD) for y, l, r in rows[5:]]
    door = [(152, 248, 164, 262, SHADE)]
    barn = Blocks(gable + side + roof_side + edge + door)
    SILO_LB, SILO_DB = ["#9A9890", "#928F88"], ["#6E6C68", "#666461"]
    silo = Blocks([(198, 196, 205, 262, SILO_LB), (205, 196, 212, 262, SILO_DB),
                   (199, 192, 211, 196, SILO_LB), (201, 188, 209, 192, SILO_LB), (203, 185, 207, 188, SILO_DB)])
    dome = Blocks([])
    road = River(262, 344, 140, -40, 4, 60, ROAD, ROAD, swings=0.6, phase=0.0, seed=40)
    # fence posts at uneven intervals, their rails drooping a little between them
    pts = [(10, 300, 4, 44), (29, 308, 4, 36), (60, 316, 3, 28), (75, 322, 3, 22)]
    rails = []
    for (xa, ya, wa, _), (xb, yb, _, _) in zip(pts, pts[1:]):
        for k in range(int(xa), int(xb), 6):
            t = (k - xa) / max(1, xb - xa)
            sag = 3 * (1 - (2 * t - 1) ** 2)
            for off in (12, 26):
                yy = ya + (yb - ya) * t + off + sag
                rails.append((k, yy, k + 6, yy + 3, ["#5C4A38", "#54442F"]))
    posts = Blocks(rails + [(x, y, x + w, y + h, ["#4A3A2C", "#40322A"]) for x, y, w, h in pts])
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
        Blob([(206, 266, 28, 4)], ["#B9985E", "#AE8E56"], top_light=False),
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
    deck_y = lambda x: 242 + (x - 60) * 0.06
    near = [(208, 124, 216, 256, BRIDGE), (226, 124, 234, 256, BRIDGE_D), (208, 140, 234, 146, BRIDGE_D),
            (208, 176, 234, 182, BRIDGE_D), (208, 214, 234, 220, BRIDGE_D)]
    far = [(114, 196, 119, 250, ["#B88A72", "#AE8068"]), (127, 196, 132, 250, ["#9C6E58", "#93664F"]),
           (114, 204, 132, 208, ["#9C6E58"]), (114, 222, 132, 226, ["#9C6E58"])]

    def cable_y(x):
        # a catenary sagging lowest at x 165, below the sun, rising to the near tower's top; never above y 180 left
        # of x 200
        if x < 123:
            return 197 + (123 - x) * 0.45
        if x < 165:
            return 232 - 0.0208 * (x - 165) ** 2
        if x < 221:
            return 232 - 0.0344 * (x - 165) ** 2
        return 124 + (x - 221) * 1.1

    cable = [(x, cable_y(x + 2) - 3, x + 4, cable_y(x + 2) + 3, BRIDGE_D) for x in range(30, 244, 2)]
    deck = [(x, deck_y(x), x + 6, deck_y(x) + 4, BRIDGE) for x in range(-10, 250, 6)]
    under = [(x, deck_y(x) + 4, x + 6, deck_y(x) + 8, ["#4A2A1E"]) for x in range(-10, 250, 6)]
    hangers = [(x, cable_y(x) + 4, x + 1.5, deck_y(x), BRIDGE_D) for x in range(134, 210, 12)]
    bridge = Blocks(cable + under + deck + hangers + far + near)
    hills = Ridge([(30, 222, 90, 80, 0.8), (88, 232, 40, 30, 0.9), (150, 230, 80, 70, 0.85), (196, 240, 40, 40, 0.9)],
                  258, ["#7A7490", "#726C88"], ["#5E5874", "#57516C"], seed=50, rough=4, smooth=True, flicker=0.02)
    bay_w = Water(256, 352, -120, 720, BAY, ["#9DACC4", "#A7B5CB"], seed=51, mirror=[hills], gaps=(0, 0),
                  squash=0.5)
    bay_w.brick = (5.0, 14.0)
    return [
        disc(160, 200, 14, SUN_S),
        hills,
        Ridge([(206, 236, 60, 50, 0.85)], 258, *HILL_MID, seed=52, rough=3, smooth=True, flicker=0.02),
        Band(-60, 300, 254, 260, ["#5E5A72", "#56526A"], seed=53, lens=0.0),
        bay_w,
        Blob([(160, 270, 9, 3.5), (159, 284, 7, 3.5), (161, 298, 5, 3)], ["#EDC4A6", "#E5B999"], top_light=False),
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
