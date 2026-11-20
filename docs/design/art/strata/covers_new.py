"""Four new strata covers in the final style (Josef, 2026-11-20: "two completely new sceneries", then all four, cover
only for now). Same rules as covers_more.py: laid clean, title and name set left at the top (to about y 100 of the
236 x 344 cover), the art filling the rest and running off the foot, one focal point, every cover ink taken from
the art and never the UI red.

1 karst: rounded limestone towers stepping back into river mist, one tall tower as the focus, a boat on the river
2 aurora: a winter night, snow peaks under green and teal aurora bands, dark firs, a frozen lake, one lit window
3 terraces: hillsides cut into flooded rice terraces that mirror a rose-and-gold dawn, mist in the valley
4 lagoon: a green volcanic cone with a thin plume over a turquoise lagoon, reef foam, a sandbar and palms

python3 covers_new.py [karst|aurora|terraces|lagoon ...] -> out/new-{name}-{xl,sm}.png"""
import sys
sys.path.insert(0, ".")
from strata import Ridge, Blob, Water, Band, Mesa, Terraces, Firs, Grove, Trunks, trees, grove, render

CALM = dict(smooth=True, flicker=0.04)


def disc(cx, cy, r, inks):
    b = Blob([(cx, cy, r, r)], inks, top_light=False)
    b.ragged = 0
    return b


def tower(peaks, base, lit, dark, seed, mist=None, rough=1.5, ribs=0.35):
    """A karst tower: a round-topped dome with steep sides (power < 1 squares the shoulders)."""
    return Ridge(peaks, base, lit, dark, seed=seed, rough=rough, ribs=ribs, lean=0.18, mist=mist, smooth=True,
                 flicker=0.03, round=True)


def palms(posts, ground, inks, trunk, thick=1.1):
    """Palms: a thin leaning trunk and a crown of long drooping fronds (flat ellipses either side of the top)."""
    out, e = [], []
    for x, h, s in posts:
        top = ground - h
        out.append((x, top, ground, thick))
        # fronds arch up from the crown and droop at their tips
        e += [(x - s * 0.7, top - s * 0.05, s * 0.85, s * 0.34), (x + s * 0.7, top - s * 0.05, s * 0.85, s * 0.34),
              (x - s * 1.45, top + s * 0.4, s * 0.55, s * 0.32), (x + s * 1.45, top + s * 0.4, s * 0.55, s * 0.32),
              (x - s * 1.9, top + s * 0.85, s * 0.3, s * 0.3), (x + s * 1.9, top + s * 0.85, s * 0.3, s * 0.3),
              (x, top - s * 0.3, s * 0.5, s * 0.36)]
    t = Trunks(out, trunk)
    t.min_run = 0.5      # a trunk is narrower than a slab and a half
    return [t, Grove(e, inks)]


# ---- 1 karst river in mist ----
K_FAR = (["#CDD8D0", "#C6D2C9"], ["#A2B5A9", "#9AAEA1"])
K_MID = (["#A9BCAB", "#A0B4A3"], ["#728979", "#6A8171"])
K_NEAR = (["#7E9A7E", "#6E8C70", "#5F7E62"], ["#3F5847", "#344C3D", "#2A4033"])
K_HERO = (["#8FAA8A", "#7F9C7B", "#6F8D6C", "#627F60"], ["#3A5242", "#2F4637", "#253A2D"])
K_WATER = ["#C3D3CB", "#AFC4BB", "#9AB4AA", "#86A399"]
K_GLINT = ["#F1F4EE", "#E6EDE6"]
K_SUN = ["#F4E8C6", "#F0E0B4"]
K_BAMBOO = ["#8FAE6A", "#7C9D5A", "#6A8B4B", "#56763D", "#44602F"]
K_BOAT = ["#33322C", "#2B2A25"]
K_SAGE = ["#A3B494", "#97A988", "#8B9E7D"]
K_MISTS = ["#EEF2EE", "#E7ECE7", "#DFE6E0"]


def mist_strip(x, y, w, h, inks):
    return Blob([(x, y, w, h), (x - w * 0.5, y + h * 0.5, w * 0.5, h * 0.8), (x + w * 0.55, y + h * 0.4, w * 0.45, h * 0.7)],
                 inks, top_light=False)


def karst():
    hero = tower([(168, 128, 30, 34, 0.35)], 300, *K_HERO, seed=71, mist=(270, 300))
    river = Water(296, 352, -20, 260, K_WATER, K_GLINT, seed=75, mirror=[hero], gaps=(0, 0), squash=0.55)
    river.brick = (5.0, 16.0)      # fewer, longer slabs: a calm river
    return [
        disc(84, 168, 15, K_SUN),
        # distance is told by value alone, plane by plane: no random pale bricks inside a tower
        tower([(36, 214, 22, 20, 0.45), (92, 200, 18, 20, 0.4), (226, 206, 24, 22, 0.5)], 286, *K_FAR, seed=72,
              ribs=0, rough=0.8),
        tower([(-6, 232, 26, 24, 0.4), (60, 222, 16, 18, 0.35), (122, 238, 14, 16, 0.4)], 296, *K_MID, seed=73,
              ribs=0, rough=0.8),
        mist_strip(70, 284, 70, 4, K_MISTS),
        hero,
        tower([(234, 196, 22, 30, 0.4)], 300, *K_NEAR, seed=74, mist=(276, 300)),
        river,
        Band(70, 170, 316, 328, K_GLINT, seed=78, lens=0.0),          # calm pale water round the boat
        Band(-60, 40, 340, 352, K_SAGE, seed=76, lens=0.4),
        # a sampan: a long low hull and its small arched cover
        Mesa(118, 318, 19, 15, 322, K_BOAT, K_BOAT, ledges=1, bed=8, seed=79, wobble=0, speckle=0, ragged=0),
        Blob([(112, 315, 7, 4)], ["#6B5A44", "#5C4C39"], top_light=True),
    ]


# ---- 2 winter night, aurora ----
NIGHT = ["#3B4170", "#424879", "#4A5082", "#535A8C"]   # darkest overhead, a little lighter toward the peaks
AURORA = ["#4E8F98", "#5FAFA6", "#7CC9A3", "#A6E0BC"]   # a curtain: teal above, bright green along its lower hem
SNOW = (["#F3F5F8", "#E9EDF3", "#DEE4EE"], ["#9AA4C4", "#8892B6", "#7680A8"])
SNOW_FAR = (["#B4BBD6", "#A8B0CE", "#9CA5C6"], ["#727CA2", "#687298", "#5E688E"])
F_LIT = ["#2F4A48", "#294240"]
F_DARK = ["#172827", "#122120"]
ICE = ["#AFBAD6", "#A8B3D1", "#A1ACCB"]
ICE_G = ["#B8C2DC", "#B3BDD8"]
CABIN = (["#86695A", "#7A5F51"], ["#3B302C", "#30272A"])
ROOF = (["#3A2F2B", "#33292A"], ["#2A2224", "#231C1E"])
LAMP = ["#F7DC93", "#F2CC72"]


class Sky:
    """A night sky laid as slabs from y0 down to y1, dissolving into paper across its top `soft` px: slabs pale toward
    paper and drop out in ragged patches (mist by leaving bricks out, never a gradient)."""

    brick = (2.0, 8.0)

    def __init__(self, y0, y1, soft, inks, seed=1):
        from strata import hexrgb
        self.y0, self.y1, self.soft, self.seed = y0, y1, soft, seed
        self.c = [hexrgb(c) for c in inks]

    def _f(self, y):
        return min(1, max(0, (y - self.y0) / self.soft))

    def cover(self, x, y):
        import numpy as np
        from strata import vnoise
        if not (self.y0 <= y <= self.y1):
            return np.zeros_like(x, dtype=bool)
        f = self._f(y)
        if f >= 1:
            return np.ones_like(x, dtype=bool)
        n = np.array([vnoise(xx, y, 26, self.seed) for xx in x])
        return n < f * 1.25

    def colour(self, x, y, rng):
        from strata import mix
        t = min(0.999, max(0, (y - self.y0) / (self.y1 - self.y0) + rng.uniform(-0.1, 0.1)))
        c = self.c[int(t * len(self.c))]
        f = self._f(y)
        return mix(c, (255, 255, 255), (1 - f) * 0.55)


def curtain(x0, x1, y0, amp, waves, depth, inks, n=26):
    """An aurora curtain: a ribbon of tall ellipses following a slow wave, lighter along its lower hem."""
    import math
    e = []
    for i in range(n):
        t = i / (n - 1)
        x = x0 + (x1 - x0) * t
        y = y0 + amp * math.sin(t * math.pi * waves) - t * 18
        e.append((x, y, (x1 - x0) / n * 1.4, depth * (0.7 + 0.3 * math.sin(t * 9))))
    return Blob(e, inks, top_light=True)


class NightBelow:
    """The night sky cut off at the aurora: it starts at the curtain's upper edge (paper above), runs edge to edge and
    down behind the peaks. Darkest overhead."""

    brick = (2.0, 8.0)

    def __init__(self, aur, base, inks):
        import numpy as np
        from strata import hexrgb
        self.base, self.c = base, [hexrgb(c) for c in inks]
        xs = np.linspace(-40, 280, 641)
        top = np.full_like(xs, np.inf)
        for cx, cy, rx, ry in aur.e:
            d = np.clip(1 - ((xs - cx) / rx) ** 2, 0, None)
            top = np.where(d > 0, np.minimum(top, cy - ry * np.sqrt(d)), top)
        # past the curtain's ends the sky holds the line of its last slab
        ok = np.isfinite(top)
        top[~ok] = np.interp(xs[~ok], xs[ok], top[ok])
        self.xs, self.top_y, self.y0 = xs, top, float(top.min())

    def cover(self, x, y):
        import numpy as np
        return (y >= np.interp(x, self.xs, self.top_y)) & (y <= self.base)

    def colour(self, x, y, rng):
        t = min(0.999, max(0, (y - self.y0) / (self.base - self.y0) + rng.uniform(-0.08, 0.08)))
        return self.c[int(t * len(self.c))]


def aurora():
    peaks = Ridge([(58, 222, 50, 54, 1.0), (166, 146, 66, 72, 1.1)], 276, *SNOW, seed=82, rough=2.5, ribs=0.5,
                  lean=0.3, smooth=True, flicker=0.04)
    lake = Water(284, 310, -20, 260, ICE, ICE_G, seed=84, gaps=(0, 0), squash=0.5)
    lake.brick = (6.0, 20.0)    # one flat sheet of ice
    # the curtain thickens toward the right and steps in tiers, with short drops hanging into the dark beneath it
    aur = Blob(curtain(-10, 250, 152, 7, 1.4, 9, AURORA).e + curtain(110, 250, 128, 6, 1.0, 10, AURORA).e,
               AURORA, top_light=True)
    drops = Blob([(150, 166, 3, 10), (176, 160, 3, 13), (200, 150, 3.5, 14), (222, 144, 3, 12), (86, 172, 3, 8)],
                 ["#7CC9A3", "#5FAFA6", "#4E8F98"], top_light=True)
    return [
        NightBelow(aur, 290, NIGHT),
        aur,
        Ridge([(10, 212, 44, 40, 1.0), (236, 204, 40, 50, 1.0)], 280, *SNOW_FAR, seed=81, rough=2, ribs=0.3,
              smooth=True, flicker=0.03),
        peaks,
        Band(-60, 300, 270, 288, SNOW[0], seed=83, lens=0.0),
        lake,
        Band(40, 170, 296, 300, ["#A6D8BC", "#9CCFB2"], seed=88, lens=0.0),    # the aurora's one green sliver
        Band(-60, 300, 308, 360, SNOW[0], seed=85, lens=0.0),
        # the cabin on the near shore, its window the one warm light
        Mesa(124, 300, 20, 20, 322, *CABIN, ledges=1, bed=8, seed=86, wobble=0, speckle=0, ragged=0),
        Ridge([(124, 282, 29, 29, 1.0)], 301, *ROOF, seed=87, rough=0, smooth=True, flicker=0),
        Blob([(116, 311, 5, 4)], LAMP, top_light=False),
        Firs([(16, 338, 62, 12), (40, 342, 44, 9), (-2, 344, 42, 9), (204, 336, 68, 13), (228, 342, 52, 10),
              (184, 344, 36, 7)], F_LIT, F_DARK, tiers=2),
    ]


# ---- 3 rice terraces at dawn (rethought, Josef 2026-11-20: the striped ridge was rejected) ----
# Each terrace is a shelf seen from the front: a thin flooded pool on top holding the dawn sky, a green bank below.
# Shelves stack up a hillside, each shorter than the one under it, their ends drooping like contour lines on a round
# hill. The low sun repeats as a column of glints down every pool beneath it.
DAWN_SUN = ["#F6C7A2", "#F2B98F", "#EDAB7E"]
SKY_POOL = [["#F3CDC4", "#F0C6BC"], ["#F5D3C2", "#F2CCBA"], ["#F6DAC0", "#F3D3B7"], ["#F6E0BE", "#F3D9B3"],
            ["#F5E4C2", "#F1DCB6"]]      # the sky in the water: rose high up, gold low down
SUN_GLINT = ["#FBEBD7", "#F8E2C4"]
RISER = (["#6F9650", "#638A47", "#577E3F"], ["#3F6232", "#36572B", "#2E4C25"])   # thin dark banks
RISER_FAR = (["#C9C2B8", "#C0B8AE"], ["#A99FA6", "#9F959C"])     # the far hill's banks in the morning haze
POOL_FAR = [["#F8E9E3", "#F5E2DB"]]
T_FAR = (["#E6CDD3", "#DDC1C8", "#D3B5BD"], ["#C3A6B0", "#B79AA5", "#AB8F9A"])
T_MISTS = ["#FBF3EF", "#F6EBE6", "#F1E3DD"]
T_TREE = ["#6E9455", "#5E8448", "#4E733B", "#3F6130"]


class Shelves:
    """Terraced hill: shelves (cx, y, half width) from the top down. A shelf's edge droops `bow` px at its ends; it
    covers from that edge down to the hill's base (the shelves below lie over it). The top `pool` px is water, the
    rest is bank, lit left of a line leaning down from the crest and shaded right of it."""

    brick = (1.8, 7.0)

    def __init__(self, shelves, base, bank, water, glint, sun_x=None, bow=10, pool_h=4.5, seed=1, lean=0.25,
                 wave=0.0):
        from strata import hexrgb
        self.s, self.base, self.pool_h, self.bow, self.seed, self.lean = shelves, base, pool_h, bow, seed, lean
        self.lit, self.dark = [hexrgb(c) for c in bank[0]], [hexrgb(c) for c in bank[1]]
        self.w = [[hexrgb(c) for c in p] for p in water]
        self.g = [hexrgb(c) for c in glint]
        self.sun_x, self.wave = sun_x, wave
        self.crest = min(sh[1] for sh in shelves)
        self.cx0 = shelves[0][0]

    def _edge(self, sh, x):
        import numpy as np
        cx, y, hw = sh
        d = (x - cx) / hw
        # the wall follows the hill's spurs and gullies: a slow wave along it, the same on every shelf so they nest
        wave = self.wave * np.sin((x - cx * 0.3) / 19.0)
        return np.where(np.abs(d) <= 1, y + self.bow * d ** 2 + wave, np.inf)

    def cover(self, x, y):
        import numpy as np
        m = np.zeros_like(x, dtype=bool)
        for sh in self.s:
            m |= (y >= self._edge(sh, x)) & (y <= self.base)
        return m

    def colour(self, x, y, rng):
        import numpy as np
        from strata import vnoise
        xa = np.array([x])
        # the nearest shelf that covers this point is the lowest one whose edge is above it
        own = None
        for sh in self.s:
            e = self._edge(sh, xa)[0]
            if e <= y:
                own = (sh, e)
        if own is None:      # a slab centre just above the top shelf's edge
            sh = self.s[0]
            e = y
        else:
            sh, e = own
        if y - e < self.pool_h:
            if self.sun_x is not None and abs(x - self.sun_x) < 9 and rng.random() < 0.85:
                return self.g[int(rng.random() * len(self.g))]
            # each pool holds the sky top to bottom: rose along its far edge, gold toward its near edge
            t = (y - e) / self.pool_h + rng.uniform(-0.12, 0.12)
            pal = self.w[int(min(len(self.w) - 1, max(0, t * len(self.w))))]
            c = pal[int(rng.random() * len(pal))]
            if x > self.cx0 + 20 + (y - self.crest) * self.lean:
                from strata import shade, mix
                c = shade(mix(c, (170, 150, 160), 0.18), -0.06)      # the shaded side: a greyed rose
            return c
        shadow = x > self.cx0 + (y - self.crest) * self.lean
        pal = self.dark if shadow else self.lit
        k = (y - e - self.pool_h) / 9 + rng.uniform(-0.25, 0.25)
        return pal[int(min(len(pal) - 1, max(0, k * len(pal))))]


T_DEEP = (["#4E6E45", "#45643D", "#3C5A36"], ["#2C4429", "#243A23", "#1D301D"])    # the near slope, the dark base


def rice():
    # six big shelves 26 px apart, each wider than the one above; the lower ones run off both edges; banks one slab
    near = [(150 - i * 4, 170 + i * 26, 44 + i * 48) for i in range(7)]
    return [
        disc(58, 184, 17, DAWN_SUN),
        # a pale lavender ridge the full width behind the terraces
        Ridge([(-10, 222, 80, 70, 1.0), (120, 232, 60, 70, 1.0), (240, 216, 60, 60, 1.0)], 290, *T_FAR, seed=90,
              rough=2, smooth=True, flicker=0.02, round=True, mist=(262, 290)),
        mist_strip(80, 272, 70, 5, T_MISTS),
        Shelves(near, 360, RISER, SKY_POOL, SUN_GLINT, sun_x=58, bow=26, pool_h=17, seed=97, lean=0.2, wave=6),
        *grove([150], 172, 9, T_TREE, trunk="#4A3828", seed=98, spread=0.4, trunk_h=0.9),
        Ridge([(10, 316, 150, 110, 1.0)], 360, *T_DEEP, seed=99, rough=1.5, smooth=True, flicker=0.02, round=True,
              lean=0.5),
    ]


# ---- 4 volcanic lagoon ----
V_CONE = (["#7FA067", "#6E9259", "#5E834C", "#4F7340"], ["#3E5B36", "#33502E", "#2A4426"])
V_ASH = (["#A79C8E", "#988D80"], ["#6F665D", "#61594F"])
V_FAR = (["#9DBBA6", "#93B29C"], ["#6F917C", "#658771"])
PLUME = ["#F2F1EE", "#E6E5E1", "#D9D8D3"]
LAGOON = ["#8CC6BF", "#76B3AF", "#629F9E", "#538C8E", "#457A7F"]
LAG_G = ["#E6F6F2", "#CDEDE7"]
FOAM = ["#F4F7F5", "#E7F0EE", "#D4ECE8"]
SANDBAR = ["#F4E6C3", "#EEDCB0", "#E6CF9C"]
L_PALM = ["#5E9A4E", "#4E8A42", "#3F7836", "#31652B"]
JUNGLE = ["#5C8E4A", "#4C7E3F", "#3E6D34", "#305B2A"]


def lagoon():
    cone = Ridge([(150, 140, 98, 104, 1.25)], 286, *V_CONE, seed=100, rough=2, ribs=0.55, lean=0.28,
                 bands=[(140, 166, *V_ASH)], smooth=True, flicker=0.04)
    return [
        # the plume rises from the crater and leans downwind
        Blob([(152, 132, 9, 7), (164, 123, 11, 6), (182, 117, 12, 5), (200, 115, 10, 4)], PLUME, top_light=True),
        Ridge([(-4, 240, 40, 46, 1.0)], 284, *V_FAR, seed=101, rough=1, smooth=True, flicker=0.02),
        cone,
        trees([112, 138, 164, 190, 216, 240], 288, 8, JUNGLE, seed=102, spread=1.1),
        Water(282, 352, -20, 260, LAGOON, LAG_G, seed=103, mirror=[cone], gaps=(0, 1), squash=0.5),
        Band(96, 176, 300, 305, SANDBAR, seed=104, lens=0.0),     # a sandbar out in the lagoon
        Band(-80, 150, 314, 352, SANDBAR, seed=105, lens=0.75),
        *palms([(24, 80, 14), (60, 62, 12)], 330, L_PALM, "#5E4630", thick=2.6),
    ]


SCENES = {"karst": karst, "aurora": aurora, "terraces": rice, "lagoon": lagoon}

if __name__ == "__main__":
    for name in sys.argv[1:] or SCENES:
        fn = SCENES[name]
        render(fn(), (0, 0, 236, 344), (472, 688), 8, paper=(255, 255, 255), clean=True, jitter=0.04).save(
            f"out/new-{name}-xl.png")
        render(fn(), (0, 0, 236, 344), (244, 356), 3, paper=(255, 255, 255), clean=True, jitter=0.04).save(
            f"out/new-{name}-sm.png")
