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
from strata import Ridge, Blob, Water, Band, Mesa, Terraces, Firs, Grove, Trunks, River, trees, grove, render

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


class Blocks:
    """A crafted object drawn as a few level blocks, the way the approved pages draw the lighthouse and the cottage:
    each block (x0, y0, x1, y1, inks) is one flat piece; later blocks lie over earlier ones."""

    brick = (1.2, 4.0)
    ragged = 0
    min_run = 0.5

    def __init__(self, blocks):
        from strata import hexrgb
        self.b = [(x0, y0, x1, y1, [hexrgb(c) for c in inks]) for x0, y0, x1, y1, inks in blocks]

    def cover(self, x, y):
        import numpy as np
        m = np.zeros_like(x, dtype=bool)
        for x0, y0, x1, y1, _ in self.b:
            if y0 <= y < y1:
                m |= (x >= x0) & (x < x1)
        return m

    def colour(self, x, y, rng):
        inks, best = None, 1e9
        for x0, y0, x1, y1, c in self.b:
            if y0 <= y < y1:
                d = 0 if x0 <= x < x1 else min(abs(x - x0), abs(x - x1))
                if d <= best:          # inside wins; the last (nearest) block wins ties
                    inks, best = c, d
        return inks[int(rng.random() * len(inks))]


def block_palms(posts, ground, lit, dark, trunk):
    """Abstract palms in the strata manner: a trunk of single slabs stepping sideways as it climbs, a crown of three
    level courses (narrow, wide, then two drooping tips), lit on the left of the trunk line, inked on the right."""
    b = []
    for x, h, s, lean in posts:
        top = ground - h
        n = int(h // 4)
        for i in range(n):
            tx = x + round(lean * i / max(1, n - 1) / 2) * 2   # steps sideways a slab at a time
            b.append((tx - 2.6, ground - (i + 1) * 4, tx + 2.6, ground - i * 4, trunk))
        cx = x + lean
        for (dx0, dx1, dy) in [(-0.3, 0.3, -12), (-0.8, 0.8, -8), (-1.3, 1.3, -4), (-1.65, -0.55, 0),
                               (0.55, 1.65, 0), (-1.9, -1.3, 4), (1.3, 1.9, 4)]:
            x0, x1 = cx + dx0 * s, cx + dx1 * s
            if x0 < cx < x1:
                b.append((x0, top + dy, cx, top + dy + 4, lit))
                b.append((cx, top + dy, x1, top + dy + 4, dark))
            else:
                b.append((x0, top + dy, x1, top + dy + 4, lit if x1 <= cx else dark))
    return Blocks(b)


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
NIGHT = ["#474D7C", "#4F5585", "#585E8E", "#626898"]   # darkest overhead, a little lighter toward the peaks
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


class AuroraSky:
    """The winter sky as one smooth curve: the aurora's hem sweeps up to the right; below it the night, darkest
    just under the glow; above it the curtain, green at the hem and teal higher, dissolving into paper (its slabs pale
    and drop out, never a gradient)."""

    brick = (2.2, 9.0)

    def __init__(self, hem, base, band, soft, night, curtain, seed=1):
        from strata import hexrgb
        self.hem, self.base, self.band, self.soft, self.seed = hem, base, band, soft, seed
        self.night = [hexrgb(c) for c in night]
        self.cur = [hexrgb(c) for c in curtain]

    def _taper(self, x):
        import numpy as np
        return np.clip((np.asarray(x, dtype=float) + 6) / 70.0, 0.15, 1.0)   # the curtain thins out toward the left

    def cover(self, x, y):
        import numpy as np
        from strata import vnoise
        h = self.hem(x)
        top = h - (self.band + self.soft) * self._taper(x)
        m = (y >= top) & (y <= self.base)
        f = (y - top) / (self.soft * self._taper(x))   # 0 at the top of the dissolve, 1 at the curtain proper
        # the blend into paper is made of gaps: long horizontal openings in each course, more of them higher up,
        # so the curtain frays into separate slabs and spaces rather than fading as a smear
        n = np.array([vnoise(xx * 0.35, y * 2.0, 6, self.seed) for xx in np.atleast_1d(x)])
        return m & ((f >= 1) | (n < f * 1.05 - 0.05))

    def colour(self, x, y, rng):
        from strata import mix
        h = float(self.hem(x))
        d = h - y                            # height above the hem
        if d > 0:
            t = min(0.999, max(0, d / (self.band + self.soft) + rng.uniform(-0.08, 0.08)))
            c = self.cur[int(t * len(self.cur))]
            f = d / (self.band + self.soft)
            return mix(c, (255, 255, 255), max(0, min(1, f)) ** 1.5 * 0.6)
        t = min(0.999, max(0, -d / (self.base - h) + rng.uniform(-0.08, 0.08)))
        c = self.night[int(t * len(self.night))]
        if -d < 7 and rng.random() < 0.55:
            return mix(c, self.cur[0], 0.35)          # the glow just under the hem
        return c


def hem(x):
    import numpy as np
    return 220 - 0.2 * x - 6 * np.sin(x / 46.0)


CURTAIN = ["#A9E2BF", "#8ED3AC", "#72C3A3", "#5CAEA6", "#5297A0"]   # bright green hem, teal above
CAB_LOG = ["#A8876D", "#9C7C63"]
CAB_SIDE = ["#4A3A32", "#41332C"]
CAB_ROOF_SNOW = ["#F3F5F8", "#E9EDF3"]
CAB_ROOF_SHADE = ["#8E97B8", "#848DAF"]
CAB_EAVE = ["#2E2524", "#28201F"]
CAB_ROOF_LIT = ["#5E4B42", "#55433B"]
CAB_ROOF_DARK = ["#33282A", "#2D2325"]
CAB_GOLD = ["#F7DC93", "#F2CC72"]


LOG_A = ["#A8876D", "#A0805F"]          # the lit gable wall, laid in logs of two tones
LOG_B = ["#7E5F48", "#765942"]
SIDE_A = ["#5A473C", "#524035"]         # the side wall in shade
SIDE_B = ["#4A3A31", "#43342C"]
STONE_L = ["#A9A6A2", "#9F9C97"]
STONE_D = ["#6F6C69", "#666360"]
SNOW_LIT = ["#F7F8FB", "#EEF1F6"]
SNOW_SHD = ["#B9C0D6", "#AEB6CE"]
FASCIA = ["#3A2E29", "#332824"]
GLOW = ["#F8DE96", "#F3CF78"]
FRAME = ["#3A2E29", "#332824"]
WOOD_END = ["#E2C49C", "#D8B98F"]
SMOKE = ["#A9AEC0", "#9DA3B6", "#9298AC"]


CAB_WALL = (["#A8876D", "#9C7C63", "#93735A"], ["#5A473C", "#4E3E34", "#45372F"])
CAB_ROOF = (["#5E4636", "#553F31"], ["#33271F", "#2C221B"])
CAB_SNOW = (["#F7F8FB", "#EEF1F6"], ["#BCC3D8", "#B0B8CF"])


def cabin(x, base):
    """A log cabin built from a few solid forms, so it reads whole: log walls (a lit left face, a shaded right, the
    logs as alternating beds), one gable roof lit left and dark right with deep snow on its upper half, a stone
    chimney with a snow cap and smoke, a lit window, a door, a woodpile, drifts at the foot. x is the centre."""
    walls = Mesa(x, base - 24, 30, 30, base, *CAB_WALL, ledges=1, bed=4, seed=86, wobble=0, speckle=0, ragged=0,
                 flicker=0)
    roof = Ridge([(x, base - 52, 40, 40, 1.0)], base - 22, *CAB_ROOF, seed=87, rough=0, smooth=True, flicker=0,
                 lean=0.0, cap=(5, *CAB_SNOW))     # only a thin line of snow: the dark roof must read against the snow
    details = Blocks([
        (x + 16, base - 52, x + 20, base - 38, STONE_L), (x + 20, base - 52, x + 24, base - 38, STONE_D),   # chimney
        (x + 14, base - 56, x + 26, base - 52, CAB_SNOW[0]),
        (x - 22, base - 18, x - 10, base - 8, GLOW),                                                     # window
        (x - 3, base - 18, x + 7, base, FRAME),                                                           # door
        (x + 14, base - 18, x + 24, base - 8, ["#C9A75E", "#BE9B55"]),                                  # second window
    ] + [(x + 32 + c * 5 + r * 2.5, base - 4 - r * 4, x + 36 + c * 5 + r * 2.5, base - r * 4, WOOD_END)
         for r in range(3) for c in range(3 - r)])                                                       # woodpile
    return [walls, roof, details,
            Blob([(x + 22, base - 64, 4, 3.5), (x + 27, base - 72, 5, 3.5), (x + 34, base - 79, 6, 3.5)], SMOKE,
                 top_light=True),
            Blob([(x - 18, base + 3, 30, 4), (x + 30, base + 3, 30, 4)], SNOW_LIT, top_light=True)]


def aurora():
    # low snow hills, soft-shouldered but uneven: a long main hill with a second summit on its shoulder, a smaller
    # hill to the left, each side a different length
    peaks = Ridge([(44, 230, 58, 44, 0.8), (84, 244, 26, 34, 0.9), (150, 222, 70, 50, 0.8), (178, 230, 40, 40, 0.85),
                   (218, 232, 36, 44, 0.9)],
                  280, *SNOW, seed=82, rough=3.5, ribs=0.4, lean=0.4, smooth=True, flicker=0.04)
    lake = Water(284, 310, -20, 260, ICE, ICE_G, seed=84, gaps=(0, 0), squash=0.5)
    lake.brick = (6.0, 20.0)    # one flat sheet of ice
    return [
        AuroraSky(hem, 290, 12, 56, NIGHT, CURTAIN, seed=80),
        Ridge([(-6, 238, 50, 40, 0.85), (112, 246, 40, 30, 0.9), (244, 228, 50, 60, 0.8)], 282, *SNOW_FAR, seed=81,
              rough=3, ribs=0.3, smooth=True, flicker=0.03),
        peaks,
        Band(-60, 300, 272, 288, SNOW[0], seed=83, lens=0.0),
        lake,
        Band(-60, 300, 308, 360, SNOW[0], seed=85, lens=0.0),
        # a stand of firs behind the cabin, so its snowy roof reads against dark
        Firs([(50, 304, 52, 15), (68, 300, 60, 16), (142, 300, 62, 16), (160, 304, 52, 14)], F_LIT, F_DARK,
             tiers=2),
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

    def _shadow(self, x, y, pad):
        # a hill is shaded right of its crest line; a valley (shade_left) on its left slope, which faces away from the
        # light
        if getattr(self, "shade_left", False):
            return x < self.cx0 - pad
        return x > self.cx0 + pad + (y - self.crest) * self.lean

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
            if self.sun_x is not None and abs(x - self.sun_x) < getattr(self, 'sun_w', 9) and rng.random() < 0.85:
                return self.g[int(rng.random() * len(self.g))]
            # each pool holds the sky top to bottom: rose along its far edge, gold toward its near edge
            t = (y - e) / self.pool_h + rng.uniform(-0.12, 0.12)
            pal = self.w[int(min(len(self.w) - 1, max(0, t * len(self.w))))]
            c = pal[int(rng.random() * len(pal))]
            if self._shadow(x, y, 20):
                from strata import shade, mix
                c = shade(mix(c, (170, 150, 160), 0.18), -0.06)      # the shaded side: a greyed rose
            return c
        shadow = self._shadow(x, y, 0)
        pal = self.dark if shadow else self.lit
        k = (y - e - self.pool_h) / 9 + rng.uniform(-0.25, 0.25)
        return pal[int(min(len(pal) - 1, max(0, k * len(pal))))]


V_POOL = [["#F4D2C8", "#F0C8BD"], ["#F5D8C3", "#F1D0B8"], ["#F6DEBF", "#F2D6B3"], ["#F5E3C3", "#F1DBB6"]]
V_BANK = (["#7FA35E", "#749853"], ["#4F7140", "#466638"])
V_GLINT = ["#FFF4E2", "#FCEBD3"]
T_VFAR = (["#E7DAE3", "#E0D2DC"], ["#C7B6C4", "#BEADBB"])
HUT_W = (["#C9A574", "#BC9866"], ["#8E6A43", "#7E5D3A"])
R_TREES = ["#5E8448", "#4E733B", "#3F6130", "#33532A"]


class Paddies:
    """A terraced valley seen head on, built from level courses as strata is. Each slope steps down toward the middle
    in terraces of its own rhythm until the two meet and the foreground is all paddies. A terrace reads top to bottom
    as a flooded pool, a dark lip (1 course) and an earth riser (2), each pool deeper than the one above as the
    terraces come nearer, and every terrace bows down toward the middle like a contour line. Light from the left: the
    left slope faces away (violet-grey water, moss risers), the right is lit (butter and peach water, olive risers).
    The nearest pools carry rows of seedlings."""

    brick = (2.0, 7.0)

    def __init__(self, y0, left, right, inks_left, inks_right, seedling, cx=118, dip=6, seed=1):
        self.seed, self.cx, self.dip = seed, cx, dip
        self.sides = []
        for steps, sign, inks in ((left, 1, inks_left), (right, -1, inks_right)):
            rows, y = [], y0
            for i, (pool, edge) in enumerate(steps):
                h = (pool + 3) * 4
                rows.append((y, y + h, pool * 4, edge, i, len(steps)))
                y += h
            self.sides.append((rows, sign, {k: [hexrgb(c) for c in v] for k, v in inks.items()}))
        self.seedling = [hexrgb(c) for c in seedling]

    def _bow(self, x):
        return self.dip * max(0.0, 1 - abs(x - self.cx) / 120)

    def _row(self, side, x, y):
        yy = y - self._bow(x)
        for r in side[0]:
            if r[0] <= yy < r[1]:
                return r, yy
        return None, yy

    def _edge_at(self, side, y):
        # the slope's inner edge runs as one smooth diagonal through the terraces' edges, course by course, so the
        # profile of the V does not step terrace by terrace
        import numpy as np
        rows = side[0]
        ys = [r[0] for r in rows] + [rows[-1][1]]
        es = [r[3] for r in rows] + [rows[-1][3]]
        return float(np.interp(y, ys, es))

    def _inside(self, side, r, x, y=None):
        e = self._edge_at(side, y) if y is not None else r[3]
        return (x <= e) if side[1] > 0 else (x >= e)

    def cover(self, x, y):
        import numpy as np
        out = np.zeros(len(x), dtype=bool)
        for j, xx in enumerate(x):
            for side in self.sides:
                r, _ = self._row(side, xx, y)
                if r and self._inside(side, r, xx, y) and (side[1] > 0) == (xx <= self.cx):
                    out[j] = True
        return out

    def colour(self, x, y, rng):
        side = self.sides[0] if x <= self.cx else self.sides[1]
        r, yy = self._row(side, x, y)
        if r is None:
            side = self.sides[1] if side is self.sides[0] else self.sides[0]
            r, yy = self._row(side, x, y)
        y0, y1, pool_h, edge, i, n = r
        inks = side[2]
        d = yy - y0
        if d >= pool_h + 4:
            pal = inks["riser"]
        elif d >= pool_h:
            # on the page the lips break every so often, so they read as banks, not ruled lines
            if getattr(self, "lip_breaks", False) and int((x + i * 53) // 70) % 4 == 0:
                pal = inks["pool"]
            else:
                pal = inks["lip"]
        else:
            pal = inks["pool"]
        return pal[int(rng.random() * len(pal))]


from strata import hexrgb

PADDY_LEFT = dict(riser=["#4E5E3A", "#47563A"], lip=["#24332F", "#1F2D29"], pool=["#8E8AA8", "#8682A1", "#9894B0"])
PADDY_RIGHT = dict(riser=["#9A8F4E", "#A39858"], lip=["#24332F", "#1F2D29"],
                   pool=["#E9C77A", "#E6BF70", "#E3A57E", "#E8B888"])
SEEDLING = ["#3F5A36", "#45623B"]
BUTTER = ["#F3DCA0", "#F0D493", "#E6C47E"]
FAR_1 = (["#A7A3BF", "#A09CB9"], ["#8F8AAA", "#8883A4"])
FAR_2 = (["#7F7AA0", "#77729A"], ["#666189", "#5F5A82"])
DEEP_LAKE = ["#34505C", "#2E4954", "#2B434D"]
LAKE_GLINT = ["#E9CF94", "#E2C483"]
TREE_DARK = ["#2F4030", "#273626", "#1F2A22", "#1A241D"]
BUSH_SHADE = ["#7E9A63", "#6B8754", "#587347", "#455E39"]     # bushes on the shaded slope
BUSH_LIT = ["#6F9550", "#5F8445", "#4F733B", "#3F6131"]       # and on the lit one, olive
THATCH = (["#A8844A", "#9C7942"], ["#6B5130", "#5E472A"])
STILT = ["#3A2C20", "#33271C"]
PLANTER = ["#2B2A33", "#25242C"]
HAT = ["#D9B46A", "#CDA75E"]


def rice():
    """The rice country of the book page, kept minimal: two terraced hills, bell-shaped so they spread into the
    ground, their terraces following each hill's curve, a peach hill on the left and a taller gold one on the right
    with the stilted hut on its crest; between them the sun sits between violet ridges over a small dark lake; wavy
    fields across the foot. At shelf size a three-line title and a one-line name reach world y ~171 in the left
    column, so everything left of x ~200 stays below y 180; only the right hill and the hut rise higher."""
    from pages_new import (ContourHill, FieldRows, HILL_GOLD, HILL_PEACH, BANK_MOSS, BANK_OLIVE, FAR_1, FAR_3,
                           BUTTER, DEEP_LAKE, LAKE_GLINT, THATCH, PLANTER, TREE_DARK, PADDY_RIGHT)
    lake = Water(236, 300, -20, 260, DEEP_LAKE, LAKE_GLINT, seed=120, gaps=(0, 0))
    lake.path = (106, 5)
    lake.brick = (4.0, 12.0)
    return [
        Ridge([(150, 206, 110, 100, 1.0), (30, 216, 80, 70, 1.0)], 260, *FAR_3, seed=121, rough=2, smooth=True,
              flicker=0.02),
        disc(106, 224, 13, BUTTER),
        Ridge([(60, 226, 70, 60, 1.0), (170, 214, 70, 80, 1.0)], 262, *FAR_1, seed=122, rough=2, smooth=True,
              flicker=0.02),
        lake,
        ContourHill([(10, 200, 100, 84, 2.2)], 320, HILL_PEACH, BANK_MOSS, spacing=10, bank_frac=0.42, seed=123,
                    rough=1.5, lean=0.5, flicker=0.02, wave=0),
        ContourHill([(212, 168, 96, 100, 2.2)], 330, HILL_GOLD, BANK_OLIVE, spacing=13, bank_frac=0.38, seed=124,
                    rough=1.5, lean=0.5, flicker=0.02, wave=0),
        Mesa(212, 156, 8, 8, 168, *THATCH, ledges=1, bed=8, seed=125, wobble=0, speckle=0, ragged=0),
        Ridge([(212, 144, 14, 14, 1.0)], 157, *THATCH, seed=126, rough=0, smooth=True, flicker=0),
        Blocks([(209, 160, 214, 168, PLANTER)]),
        trees([16, 32], 212, 8, TREE_DARK, seed=127, spread=0.6),
        FieldRows(300, [14, 18, 22], [["#E9C77A", "#E3A57E"], PADDY_RIGHT["pool"], ["#EDCB86", "#E6B48C"]],
                  ["#5A5A36", "#525231"], seed=128),
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


V_BASALT = (["#5E5A55", "#544F4A"], ["#3A3633", "#312E2B"])      # old lava, darker beds across the flank
V_SHOULDER = (["#7F9C66", "#728F5A", "#66834F"], ["#45613B", "#3C5634", "#334B2D"])
P_LIT = ["#5F9A4C", "#548E43"]
P_DARK = ["#2F5A2C", "#284E26"]
P_TRUNK = ["#6B5236", "#5E4630"]


def lagoon():
    """A steeper, broken cone: concave flanks rising to a notched crater, ravines down the faces, two dark beds of
    old lava and an ash cap; a smaller parasitic cone on its right shoulder; a tall plume leaning downwind."""
    # lower and broken up: a blunt summit on bulging slopes (power < 1), a long lumpy shoulder down the left and a
    # higher, steeper one on the right, so the outline steps in and out instead of running straight like a pyramid
    # kept below the name line: at shelf size a three-line title and a one-line name reach y ~171 left of x ~200
    cone = Ridge([(132, 182, 84, 72, 0.72), (52, 236, 42, 30, 0.85), (210, 212, 30, 44, 0.85)],
                 286, *V_CONE, seed=100, rough=4, ribs=0.85, lean=0.3,
                 bands=[(178, 192, *V_ASH), (192, 212, *V_BASALT)], smooth=True, flicker=0.05)
    return [
        # the plume: a column out of the crater, billowing and bending right, its top clear of the title
        Blob([(140, 180, 6, 3.5), (152, 177, 9, 3.5), (170, 173, 12, 4), (192, 170, 14, 4), (214, 168, 12, 3.5)],
             PLUME, top_light=True),
        Ridge([(-4, 240, 40, 46, 1.0)], 284, *V_FAR, seed=101, rough=1, smooth=True, flicker=0.02),
        Ridge([(236, 226, 30, 40, 1.2)], 286, *V_SHOULDER, seed=106, rough=2, ribs=0.6, lean=0.3,
              bands=[(218, 226, *V_ASH)], smooth=True, flicker=0.04),
        cone,
        Blob([(132, 186, 5, 2.5)], ["#E3A061", "#D98E4E"], top_light=False),   # the vent's glow
        trees([100, 126, 150, 176, 202, 228, 250], 288, 7, JUNGLE, seed=102, spread=1.1),
        Water(282, 352, -20, 260, LAGOON, LAG_G, seed=103, mirror=[cone], gaps=(0, 1), squash=0.5),
        Band(96, 176, 300, 305, SANDBAR, seed=104, lens=0.0),     # a sandbar out in the lagoon
        Band(-80, 150, 314, 352, SANDBAR, seed=105, lens=0.75),
        block_palms([(20, 72, 17, 8), (58, 56, 14, 6)], 332, P_LIT, P_DARK, P_TRUNK),
    ]


SCENES = {"karst": karst, "aurora": aurora, "terraces": rice, "lagoon": lagoon}

if __name__ == "__main__":
    for name in sys.argv[1:] or SCENES:
        fn = SCENES[name]
        render(fn(), (0, 0, 236, 344), (472, 688), 8, paper=(255, 255, 255), clean=True, jitter=0.04).save(
            f"out/new-{name}-xl.png")
        render(fn(), (0, 0, 236, 344), (244, 356), 3, paper=(255, 255, 255), clean=True, jitter=0.04).save(
            f"out/new-{name}-sm.png")
