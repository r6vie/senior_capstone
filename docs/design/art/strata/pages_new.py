"""Book screen B's title-page art for the covers in covers_new.py. As in pages_more.py, the page is not a zoom of the
cover: it opens the place up into a full scene, more planes, more features, weather, in the cover's inks and at the
cover's slab size. World 570 x 684 = the title page; the text holds the upper left (to about x 480 above y 400), so
the art climbs highest on the right.

python3 pages_new.py [karst ...] -> out/page-{name}-title.png"""
import sys
sys.path.insert(0, ".")
from strata import Ridge, Blob, Water, Band, River, trees, grove, render
from covers_new import (tower, disc, mist_strip, Blocks, K_FAR, K_MID, K_NEAR, K_HERO, K_WATER, K_GLINT, K_SUN,
                        K_BAMBOO, K_BOAT, K_MISTS, K_SAGE)

K_HAZE = (["#E2E9E3", "#DCE4DD"], ["#C7D3CA", "#C0CDC3"])        # the furthest towers, nearly lost in the haze
K_FIELD = ["#B9C99A", "#AFC18E", "#A4B783"]                      # paddies on the flats by the river
K_FIELD_D = ["#93A876", "#899F6C"]
ROOF = ["#4A403A", "#3F3631"]
ROOF_D = ["#2F2824", "#28221F"]
WALL = ["#D9CDB4", "#CFC2A8"]
WALL_D = ["#A99B82", "#9C8E76"]
POST = ["#5A4434", "#4E3B2D"]
HAT = ["#C9B27E", "#B9A16D"]
FIGURE = ["#3A3A3A", "#2F2F2F"]


def ptower(peaks, base, lit, dark, seed, mist=None, ribs=0.35, rough=1.5):
    """A karst tower for the page: as the cover's, but the shade line falls nearly straight, so the right side stays
    in shadow all the way down to the water."""
    return Ridge(peaks, base, lit, dark, seed=seed, rough=rough, ribs=ribs, lean=0.04, mist=mist, smooth=True,
                 flicker=0.03, round=True)


def cloud(x, y, w):
    """A thin cloud of a few stepped slabs, ends uneven, as on the coast page."""
    return Blob([(x, y, w, 4), (x + w * 0.35, y - 5, w * 0.55, 3.6), (x - w * 0.45, y + 4.5, w * 0.45, 3.4)],
                K_MISTS, top_light=False)


PAV_PILLAR = ["#6B3F2E", "#5E372A"]
PAV_WALL = ["#E3D8C0", "#DAD0B6"]
PAV_WALL_D = ["#B3A58B", "#A8997F"]


def pavilion(x, base):
    """A riverside pavilion, about 75 px wide: a lit left face and a shaded right, dark pillars, and a two-tier roof
    whose eaves step out and turn up at the tips, each tier lit left of the centre and inked right."""
    m = x + 36
    b = [(x + 6, base - 16, m, base, PAV_WALL), (m, base - 16, x + 66, base, PAV_WALL_D),
         (x + 4, base - 16, x + 8, base, PAV_PILLAR), (x + 34, base - 16, x + 38, base, PAV_PILLAR),
         (x + 64, base - 16, x + 68, base, PAV_PILLAR),
         (x + 20, base - 12, x + 28, base - 4, ["#3A332E", "#332D29"])]                 # a dark doorway
    # lower roof tier: a wide eave, its tips turned up
    b += [(x - 8, base - 20, m, base - 16, ROOF), (m, base - 20, x + 80, base - 16, ROOF_D),
          (x - 12, base - 24, x - 4, base - 20, ROOF), (x + 76, base - 24, x + 84, base - 20, ROOF_D),
          (x, base - 24, m, base - 20, ROOF), (m, base - 24, x + 72, base - 20, ROOF_D)]
    # upper tier: a short wall, then a smaller roof with its own turned-up tips
    b += [(x + 16, base - 28, m, base - 24, PAV_WALL), (m, base - 28, x + 56, base - 24, PAV_WALL_D),
          (x + 8, base - 32, m, base - 28, ROOF), (m, base - 32, x + 64, base - 28, ROOF_D),
          (x + 4, base - 36, x + 12, base - 32, ROOF), (x + 60, base - 36, x + 68, base - 32, ROOF_D),
          (x + 16, base - 36, m, base - 32, ROOF), (m, base - 36, x + 56, base - 32, ROOF_D),
          (x + 28, base - 40, x + 44, base - 36, ROOF_D)]
    return Blocks(b)


CANOPY = ["#8C7A5C", "#806F53"]
CANOPY_D = ["#5C4E3B", "#524534"]


def sampan(x, y):
    """A sampan: a long low hull with raised ends, an arched cane canopy lit on its left, and a boatman in a conical
    hat leaning on his pole."""
    b = [(x - 30, y - 4, x + 34, y, K_BOAT), (x - 36, y - 8, x - 26, y - 4, K_BOAT), (x + 30, y - 8, x + 40, y - 4, K_BOAT),
         (x - 26, y - 8, x - 16, y - 4, ["#57534A", "#4D4941"]),
         (x - 12, y - 12, x + 2, y - 4, CANOPY), (x + 2, y - 12, x + 16, y - 4, CANOPY_D),
         (x - 8, y - 16, x + 4, y - 12, CANOPY), (x + 4, y - 16, x + 12, y - 12, CANOPY_D),
         (x + 22, y - 16, x + 26, y - 4, FIGURE), (x + 18, y - 20, x + 30, y - 16, HAT), (x + 22, y - 24, x + 26, y - 20, HAT),
         (x + 30, y - 32, x + 32, y + 4, POST)]
    return Blocks(b)


K_REFL = ["#5F7A66", "#566F5C", "#4D6553"]        # the tall towers' shade, broken on the water
PADDY_A = ["#B9C99A", "#B1C392"]
PADDY_B = ["#C7D4AB", "#BFCEA2"]
PADDY_EDGE = ["#8FA571", "#869C69"]
STALK = ["#6E8C4C", "#628043"]


def karst():
    """A river valley among karst towers: towers in five planes, the furthest nearly lost in haze, mist and thin
    cloud lying between them; three tall towers on the right rising highest beside the text, each a step darker
    than the one behind; the low sun behind the haze; the water wide and calm with the towers mirrored and their
    shade broken on it; stepped paddies on the flats, a two-tier pavilion on the left bank, bamboo along both banks
    and in the near corner, a sampan with its boatman in front."""
    # the text holds the upper left to about x 480 above y 400: the tall towers stand right of that line
    left = ptower([(438, 402, 26, 28, 0.38)], 560, *K_MID, seed=173, mist=(530, 560))
    hero = ptower([(524, 170, 38, 40, 0.35)], 560, *K_HERO, seed=171, mist=(532, 560))
    twin = ptower([(572, 262, 24, 34, 0.4)], 560, *K_NEAR, seed=172, mist=(536, 560))
    near = ptower([(34, 436, 34, 40, 0.4), (84, 486, 18, 22, 0.4)], 590, *K_NEAR, seed=188, mist=(570, 590))
    pool = Water(560, 684, -40, 610, K_WATER, K_GLINT, seed=175, mirror=[hero, twin, left, near], gaps=(0, 0),
                 squash=0.5)
    pool.brick = (5.0, 16.0)
    shade = Water(566, 626, 400, 600, K_REFL, K_REFL, seed=191, gaps=(2, 4))
    shade.brick = (2.0, 6.0)
    return [
        disc(318, 434, 22, K_SUN),
        # the valley floor in haze, behind every tower, so no paper shows between their feet
        Band(-60, 640, 488, 562, K_HAZE[0], seed=199, lens=0.0),
        # plane 5: haze towers, heights varied; every plane's foot runs down behind the paddies, so no paper shows
        ptower([(20, 418, 22, 22, 0.45), (84, 444, 18, 20, 0.4), (150, 406, 22, 20, 0.5), (226, 450, 16, 18, 0.4),
                (290, 428, 22, 24, 0.45), (356, 446, 18, 20, 0.4), (430, 402, 24, 22, 0.5), (548, 392, 24, 26, 0.45)],
               562, *K_HAZE, seed=176, ribs=0, rough=0.8),
        cloud(250, 470, 90),
        # plane 4: far towers
        ptower([(40, 452, 22, 20, 0.45), (118, 430, 18, 20, 0.4), (196, 466, 20, 22, 0.45), (262, 440, 16, 18, 0.4),
                (334, 474, 20, 22, 0.4)], 562, *K_FAR, seed=177, ribs=0, rough=0.8),
        cloud(110, 500, 70),
        # plane 3: mid towers
        ptower([(-10, 432, 30, 26, 0.4), (64, 470, 18, 20, 0.35), (150, 486, 20, 22, 0.4), (232, 462, 16, 18, 0.4),
                (318, 494, 18, 20, 0.4)], 562, *K_MID, seed=178, ribs=0, rough=0.8),
        cloud(380, 524, 80),
        # the tall towers on the right, back to front
        left, hero, twin,
        ptower([(480, 446, 20, 22, 0.4)], 560, *K_HERO, seed=179, mist=(536, 560)),
        cloud(548, 330, 30),
        cloud(530, 452, 46),
        # the flats: stepped paddies either side of the river
        Band(-60, 300, 532, 540, PADDY_B, seed=180, lens=0.0),
        Band(-60, 300, 540, 544, PADDY_EDGE, seed=192, lens=0.0),
        Band(-60, 300, 544, 552, PADDY_A, seed=193, lens=0.0),
        Band(-60, 300, 552, 556, PADDY_EDGE, seed=194, lens=0.0),
        Band(-60, 300, 556, 562, PADDY_B, seed=195, lens=0.0),
        Band(330, 640, 544, 552, PADDY_A, seed=181, lens=0.0),
        Band(330, 640, 552, 556, PADDY_EDGE, seed=196, lens=0.0),
        Band(330, 640, 556, 562, PADDY_B, seed=197, lens=0.0),
        pool,
        shade,
        pavilion(150, 554),
        trees([136, 256, 276], 552, 7, K_BAMBOO, seed=183, spread=0.8),
        # a far boat, small, out on the flat water
        Blocks([(214, 584, 240, 588, K_BOAT), (222, 580, 232, 584, CANOPY)]),
        # the near tower on the left, standing in the water, its foot in bamboo
        near,
        Band(-60, 130, 588, 604, K_SAGE, seed=189, lens=0.3),
        trees([0, 26, 54, 86, 112], 600, 9, K_BAMBOO, seed=190, spread=0.8),
        trees([360, 384, 520, 548], 556, 7, K_BAMBOO, seed=184, spread=0.8),
        # the near bank at the lower left: bamboo stalks rising out of a sage bank
        Band(-60, 150, 646, 690, K_SAGE, seed=185, lens=0.5),
        Blocks([(x, 612 + (i % 3) * 6, x + 2, 652, STALK) for i, x in enumerate([8, 20, 34, 46, 62, 78, 94])]),
        trees([12, 40, 70, 96], 630, 7, K_BAMBOO, seed=198, spread=0.9),
        Band(470, 640, 660, 690, K_SAGE, seed=186, lens=0.5),
        trees([500, 530, 560], 672, 9, K_BAMBOO, seed=187, spread=0.8),
        sampan(300, 632),
    ]


# ---- winter night, aurora ----
from covers_new import (AuroraSky, NIGHT, CURTAIN, SNOW, SNOW_FAR, F_LIT, F_DARK, ICE, ICE_G, Firs)
STAR = ["#EFE3B0", "#E8DAA2"]
SNOW_MID = (["#D3D9E8", "#CBD2E3", "#C3CBDE"], ["#8E97B8", "#848DAF", "#7A84A6"])
F_FAR = (["#3F5A63", "#38525B"], ["#24363D", "#1E2F35"])       # far firs along the shore, a step paler


def winter_hem(x):
    import numpy as np
    # one smooth curve: low and nearly level under the text, rising gently on the right, no gaps
    xa = np.asarray(x, dtype=float)
    return 500 - 0.03 * xa - np.clip(xa - 430, 0, None) * 0.25     # only a slight lift on the right, no spike


class EvenAurora(AuroraSky):
    """The page's aurora: one even depth from edge to edge (the cover's curtain thins toward its left end; this one
    does not)."""

    def _taper(self, x):
        import numpy as np
        return np.ones_like(np.asarray(x, dtype=float))


FJORD = ["#5F6A98", "#58628F", "#515B87", "#4A547F"]        # dark water holding the night
FJORD_G = ["#9FD8BF", "#B6C0DC"]                          # the aurora and the snow caught on it
CLIFF = (["#C9CFE0", "#BEC5D9", "#B3BBD2"], ["#6E78A0", "#646E96", "#5A648C"])   # the fjord's steep walls


def winter():
    """A winter night over a fjord: the aurora as one smooth curtain lying low under the text and rising gently on
    the right, dissolving upward into paper; the night beneath it with a few pale stars; soft, uneven snow hills
    behind; the fjord running back between steep snow walls to the far hills, narrow in the distance and widening
    toward us, the aurora caught on its dark water; far firs on the shores, dark groves in both lower corners."""
    hills = Ridge([(470, 452, 90, 80, 0.7), (360, 486, 90, 70, 0.65), (250, 500, 60, 60, 0.8),
                   (150, 488, 100, 76, 0.65), (40, 500, 84, 70, 0.7), (560, 470, 70, 60, 0.7)], 600, *SNOW, seed=200,
                  rough=5, ribs=0.9, lean=0.4, smooth=True, flicker=0.04)
    far = Ridge([(250, 480, 110, 90, 0.7), (110, 484, 100, 80, 0.7), (420, 470, 80, 70, 0.75)], 600, *SNOW_FAR,
                seed=201, rough=3, ribs=0.3, smooth=True, flicker=0.03)
    stars = Blocks([(x, y, x + 2.5, y + 4, STAR) for x, y in
                    [(222, 492), (300, 488), (372, 490), (430, 470), (486, 430), (540, 400), (520, 446)]])
    # the fjord's walls: a steep snow headland on each side, shaded on the side facing away from the light
    left_wall = Ridge([(70, 580, 120, 170, 0.5)], 700, *CLIFF, seed=208, rough=4, ribs=0.7, lean=0.5, smooth=True,
                      flicker=0.04)
    right_wall = Ridge([(540, 572, 200, 120, 0.5)], 700, *CLIFF, seed=209, rough=4, ribs=0.7, lean=0.2, smooth=True,
                       flicker=0.04)
    # the lake: dark night ice between the hills, the hills behind mirrored in it
    lake = Water(566, 676, -40, 610, ["#7E89B2", "#7680AA", "#6E78A2"], ["#9AA4C8", "#A8B1D2"], seed=210,
                 mirror=[hills], gaps=(0, 0), squash=0.5)
    lake.brick = (6.0, 20.0)
    return [
        EvenAurora(winter_hem, 610, 14, 96, NIGHT, CURTAIN, seed=203),       # a tall, slow dissolve into paper
        far,
        hills,
        Band(-60, 640, 556, 568, ["#E8ECF4", "#E2E7F1", "#DCE2EE"], seed=211, lens=0.0),     # the far shore
        lake,
        # the aurora faint in the ice
        Blocks([(x + dx, y, x + dx + 10, y + 4, ["#9FD8BF", "#94CFB5"]) for x, y in [(150, 590), (250, 604), (360, 596),
                                                                                       (300, 630)] for dx in (0, 16)]),
        # the snow hills in front, either side of the lake, and the near shore
        left_wall, right_wall,
        Band(-60, 640, 672, 700, ["#E8ECF4", "#E2E7F1", "#DCE2EE"], seed=212, lens=0.3),
        Firs([(x, y, h, w) for x, y, h, w in [(60, 566, 26, 6), (76, 568, 32, 7), (92, 570, 24, 6),
                                              (520, 560, 28, 6), (536, 562, 34, 7), (552, 564, 26, 6)]],
             *F_FAR, tiers=2),
        # dark groves in both lower corners
        Firs([(10, 676, 96, 16), (40, 680, 74, 13), (70, 684, 56, 11), (-10, 684, 80, 14), (98, 686, 40, 9)],
             F_LIT, F_DARK, tiers=3),
        Firs([(480, 680, 90, 15), (510, 676, 110, 17), (540, 680, 96, 16), (566, 684, 84, 14), (454, 686, 50, 10)],
             F_LIT, F_DARK, tiers=3),
    ]


def cloud_band(x, y, w):
    """A low bank of mist over the ice: long stepped slabs, ends uneven."""
    return Blob([(x, y, w, 4), (x - w * 0.5, y + 3, w * 0.45, 3.5), (x + w * 0.45, y - 2, w * 0.4, 3.5)],
                ["#EEF1F8", "#E6EAF4", "#DDE2EF"], top_light=False)


# ---- rice terraces at dawn ----
from covers_new import block_palms, P_LIT, P_DARK, P_TRUNK
from covers_new import (Paddies, PADDY_LEFT, PADDY_RIGHT, SEEDLING, BUTTER, FAR_1, FAR_2, DEEP_LAKE, LAKE_GLINT,
                        TREE_DARK, THATCH, STILT, PLANTER, BUSH_SHADE, BUSH_LIT, Mesa)
FAR_3 = (["#C4C0D6", "#BDB9D0"], ["#A9A4C0", "#A29DB9"])     # the furthest ridge, palest
EGRET = ["#F7F7F2", "#EEEEE8"]
STEP = ["#B9A77A", "#AD9B6E"]


class ContourHill(Ridge):
    """A round hill cut into terraces that follow its own shape: each bank runs parallel to the hill's skyline, so the
    lines bend with the hill. Terraces widen down the slope (they come nearer); a slow wave lets them swell and pinch.
    Between the banks the flooded pools take the hill's lit or shaded ink."""

    def __init__(self, peaks, base, pool, bank, spacing, grow=0.012, bank_frac=0.3, wave=3.0, **kw):
        kw.setdefault("round", True)
        super().__init__(peaks, base, pool[0], pool[1], smooth=True, **kw)
        from strata import hexrgb
        self.bank = ([hexrgb(c) for c in bank[0]], [hexrgb(c) for c in bank[1]])
        self.spacing, self.grow, self.bank_frac, self.wave = spacing, grow, bank_frac, wave

    def colour(self, x, y, rng):
        import math
        import numpy as np
        top = self.top(np.array([x]))[0]
        d = y - top + self.wave * math.sin(x / 17.0 + self.seed)
        u = math.log1p(self.grow * max(0.0, d)) / math.log1p(self.grow * self.spacing)
        if d > 5 and (u % 1) < self.bank_frac:
            px, ty = self.peaks[0][0], self.peaks[0][1]
            pal = self.bank[1] if x > px + (y - ty) * self.lean else self.bank[0]
            return pal[int(rng.random() * len(pal))]
        return super().colour(x, y, rng)


HILL_GOLD = (["#F1D9A4", "#EDCF93", "#E8C584"], ["#C7A672", "#BB9A67", "#AE8E5C"])
HILL_PEACH = (["#EFC3A6", "#EAB797", "#E4AB88"], ["#B58C7C", "#AA8172", "#9F7768"])
HILL_LILAC = (["#C9C3DA", "#C1BBD3", "#B9B3CC"], ["#9993B2", "#8F89A9", "#857FA0"])
BANK_OLIVE = (["#8D9A55", "#82904D"], ["#55623A", "#4C5934"])
BANK_MOSS = (["#5E7446", "#54693F"], ["#33452D", "#2C3D27"])
BANK_FAINT = (["#ADA6C4", "#A69FBE"], ["#8A84A4", "#837D9D"])
ROCK = (["#B7AE9C", "#ADA492", "#A39A88"], ["#7A7266", "#70685C", "#665F54"])
FALL = ["#EAF2F4", "#DCE9EE", "#CFE0E8"]
FOREST = ["#4E7442", "#46693B", "#3C5A33", "#304A29"]


def terraces():
    """A whole terraced country at dawn, lower and wider than the cover: plain violet ridges far off with the sun
    half behind them; small hills in the middle distance, each finely terraced along its own curve; a still lake
    holding the sun; on the left a big terraced hill broken by a forested gully and a rock outcrop; on the right a
    hill of large, wide terraces with the stilted hut on top; broad flat
    paddies across the foreground with shade trees on the banks and bushes."""
    lake = Water(540, 652, -40, 610, DEEP_LAKE, LAKE_GLINT, seed=330, gaps=(0, 0))
    lake.path = (300, 8)
    lake.brick = (4.0, 12.0)
    big_left = ContourHill([(60, 470, 202, 148, 2.2)], 660, HILL_PEACH, BANK_MOSS, spacing=12, bank_frac=0.42,
                           seed=331, rough=2, lean=0.5, flicker=0.02, wave=4)
    big_right = ContourHill([(530, 404, 162, 148, 2.2)], 660, HILL_GOLD, BANK_OLIVE, spacing=20, bank_frac=0.34,
                            seed=332, rough=2, lean=0.5, flicker=0.02, wave=3)
    paddy_rows = []
    for i, (y, h) in enumerate([(652, 16), (668, 32)]):
        paddy_rows.append(Band(-60, 640, y, y + h - 4, PADDY_RIGHT["pool"] if i % 2 else ["#E9C77A", "#E3A57E"],
                               seed=340 + i, lens=0.0))
        paddy_rows.append(Band(-60, 640, y + h - 4, y + h, ["#5A5A36", "#525231"], seed=350 + i, lens=0.0))
    return [
        Ridge([(380, 448, 170, 160, 1.0), (120, 460, 140, 120, 1.0)], 540, *FAR_3, seed=300, rough=2, smooth=True,
              flicker=0.02),
        disc(300, 476, 22, BUTTER),
        Ridge([(220, 480, 120, 100, 1.0), (420, 470, 110, 120, 1.0)], 540, *FAR_1, seed=301, rough=2, smooth=True,
              flicker=0.02),
        ContourHill([(180, 500, 94, 81, 2.2)], 560, HILL_LILAC, BANK_FAINT, spacing=7, bank_frac=0.4, seed=333,
                    rough=1, lean=0.5, flicker=0.02),
        ContourHill([(400, 494, 108, 94, 2.2)], 560, HILL_GOLD, BANK_OLIVE, spacing=8, bank_frac=0.36, seed=334,
                    rough=1, lean=0.5, flicker=0.02),
        lake,
        # smaller terraced hills between, overlapping, each its own ink
        ContourHill([(150, 532, 94, 81, 2.2)], 640, (["#B8C48A", "#AEBB80"], ["#8A9765", "#808D5C"]), BANK_MOSS,
                    spacing=9, bank_frac=0.4, seed=342, rough=1.5, lean=0.5, flicker=0.02, wave=0),
        ContourHill([(330, 556, 103, 86, 2.2)], 650, HILL_GOLD, (["#7A6A3C", "#706136"], ["#55492A", "#4D4226"]),
                    spacing=10, bank_frac=0.4, seed=343, rough=1.5, lean=0.5, flicker=0.02, wave=0),
        ContourHill([(470, 540, 94, 81, 2.2)], 650, HILL_PEACH, BANK_OLIVE, spacing=9, bank_frac=0.4, seed=344,
                    rough=1.5, lean=0.5, flicker=0.02, wave=0),
        big_left,
        # the gully: a forested cleft running down the big left hill, and a rock outcrop beside it
        trees([150, 166, 178, 192], 560, 11, FOREST, seed=335, spread=0.6),
        trees([170, 188, 204], 600, 12, FOREST, seed=336, spread=0.6),
        big_right,
        Mesa(530, 390, 13, 13, 408, *THATCH, ledges=1, bed=8, seed=313, wobble=0, speckle=0, ragged=0),
        Ridge([(530, 372, 22, 22, 1.0)], 391, *THATCH, seed=314, rough=0, smooth=True, flicker=0),
        Blocks([(526, 396, 533, 408, PLANTER)]),
        trees([566, 584], 414, 12, TREE_DARK, seed=315, spread=0.5),
        trees([380, 404], 560, 9, BUSH_LIT, seed=338, spread=0.6),
        *paddy_rows,
        # broad shade trees on the paddy banks, crowns held up on dark trunks
        *grove([60, 300, 520], 664, 18, FOREST, trunk="#3E2E22", seed=345, spread=0.8, trunk_h=1.6),
        trees([150, 176], 670, 9, BUSH_SHADE, seed=339, spread=0.6),
        trees([430], 668, 8, BUSH_LIT, seed=341, spread=0.6),
    ]


# ---- volcanic lagoon ----
from covers_new import (V_CONE, V_ASH, V_BASALT, V_SHOULDER, V_FAR, PLUME, LAGOON, LAG_G, SANDBAR, P_LIT, P_DARK,
                        P_TRUNK, JUNGLE, block_palms)
REEF = ["#3E8A94", "#357C86", "#2F6F79"]           # the deep water past the reef
FOAM_L = ["#F4F8F6", "#E6F0EE"]
CORAL = ["#4C9A97", "#438E8B"]                     # darker heads of coral in the shallows
CANOE = ["#6B4A32", "#5E412C"]
OUTRIG = ["#8A6A48", "#7C5F40"]
CLOUD_W = ["#F4F4F2", "#ECECE8", "#E2E2DE"]


def lagoon_page():
    """An atoll's lagoon, wide and low: a lower volcano on the right, its dark summit and glowing vent, a short plume;
    misty far islands on the horizon and a low jungle island in the middle distance; deep water outside the reef,
    surf breaking along it, the turquoise lagoon inside with coral heads; two sandy motu on the reef, each with a
    cluster of palms; in front, a beach under a dense palm forest, an outrigger canoe drawn up on the sand."""
    import random
    cone = Ridge([(500, 388, 112, 90, 0.75), (420, 452, 50, 40, 0.85), (586, 430, 40, 60, 0.85)], 524, *V_CONE,
                 seed=400, rough=5, ribs=0.85, lean=0.3,
                 bands=[(384, 400, *V_ASH), (400, 424, *V_BASALT)], smooth=True, flicker=0.05)
    far = Ridge([(60, 498, 60, 50, 0.8), (190, 506, 40, 36, 0.9), (300, 500, 50, 40, 0.85)], 520,
                ["#C3D4C8", "#BCCEC1"], ["#A9BEB0", "#A2B8A9"], seed=401, rough=2, smooth=True, flicker=0.02,
                mist=(508, 520))
    mid = Ridge([(250, 492, 120, 100, 0.8)], 530, *V_FAR, seed=402, rough=3, ribs=0.4, smooth=True, flicker=0.03)
    # the water rows run well past both edges and leave no open gaps, so no paper shows through the lagoon
    lagoon = Water(566, 700, -120, 720, ["#9DD0C9", "#8CC7C0", "#7DBBB5", "#6FAFAA"], LAG_G, seed=403, gaps=(0, 0))
    r = random.Random(7)
    # the forest: palms crowded along the near beach in two loose rows, uneven gaps, every one its own height, crown
    # and lean, so nothing lines up
    back, front, x = [], [], -14
    while x < 300:
        x += r.uniform(12, 30)
        row = back if r.random() < 0.55 else front
        row.append((round(x), int(r.uniform(50, 116)), int(r.uniform(15, 30)), int(r.uniform(-12, 12))))
    return [
        Blob([(500, 376, 9, 7), (508, 366, 12, 7), (522, 358, 14, 6), (540, 354, 12, 5)], PLUME, top_light=True),
        Blob([(380, 440, 50, 4), (340, 444, 26, 3.5)], CLOUD_W, top_light=False),
        Blob([(160, 456, 60, 4), (210, 460, 30, 3.5)], CLOUD_W, top_light=False),
        far,
        mid,
        trees([170, 200, 230, 260, 290, 320], 530, 9, JUNGLE, seed=404, spread=1.0),
        Ridge([(586, 470, 40, 60, 1.1)], 524, *V_SHOULDER, seed=405, rough=2, ribs=0.6, lean=0.3, smooth=True,
              flicker=0.04),
        cone,
        Blob([(500, 392, 7, 3)], ["#E3A061", "#D98E4E"], top_light=False),          # the vent's glow
        trees([400, 430, 460, 490, 520, 550, 580], 526, 10, JUNGLE, seed=406, spread=1.0),
        Water(524, 556, -120, 720, REEF, LAG_G, seed=407, gaps=(0, 0)),
        Water(552, 566, -120, 720, FOAM_L, FOAM_L, seed=408, gaps=(2, 4)),         # the surf breaking on the reef
        lagoon,
        Blob([(120, 612, 30, 4), (420, 640, 40, 4), (520, 600, 26, 4)], CORAL, top_light=False),
        # the reef closing the lagoon: an arc of sand and surf curving round from the volcano's foot
        Blob([(x, 566 + (x - 300) ** 2 / 3000, 22, 3.6) for x in range(300, 640, 30)],
             ["#EFE3C2", "#F7F1E0", "#FFFFFF"], top_light=False),
        Blob([(500, 660, 60, 8), (560, 650, 40, 6)], ["#BFE0D6", "#B4D9CE"], top_light=False),   # a sand shoal
        # two motu on the reef, sand and a cluster of palms each
        Band(320, 400, 556, 566, SANDBAR, seed=409, lens=0.6),
        block_palms([(340, 40, 14, 4), (360, 50, 16, 6), (380, 36, 13, -2)], 560, P_LIT, P_DARK, P_TRUNK),
        Band(450, 540, 584, 594, SANDBAR, seed=410, lens=0.6),
        block_palms([(466, 48, 15, 5), (490, 38, 12, -3), (514, 54, 16, 6), (530, 34, 12, -4)], 588, P_LIT, P_DARK,
                    P_TRUNK),
        # the near beach and its forest
        trees([0, 40, 80, 120, 160, 200, 240], 650, 14, JUNGLE, seed=411, spread=0.9),
        Band(-80, 360, 640, 700, SANDBAR, seed=412, lens=0.5),
        Band(-80, 350, 638, 644, ["#D9C49A", "#D1BB8F"], seed=413, lens=0.5),
        *[block_palms([p], 650 + r.choice((0, 4, 8)), P_LIT, P_DARK, P_TRUNK) for p in back],
        trees([20, 90, 170, 230], 664, 9, JUNGLE, seed=414, spread=1.2),
        *[block_palms([p], 666 + r.choice((0, 4, 8, 12)), P_LIT, P_DARK, P_TRUNK) for p in front],
        Blocks([(250, 668, 330, 676, CANOE), (244, 664, 254, 668, CANOE), (326, 664, 336, 668, CANOE),
                (258, 656, 322, 660, OUTRIG), (266, 660, 270, 668, OUTRIG), (310, 660, 314, 668, OUTRIG)]),
    ]


SCENES = {"karst": karst, "winter": winter, "terraces": terraces, "lagoon": lagoon_page}

if __name__ == "__main__":
    for name in sys.argv[1:] or list(SCENES):
        render(SCENES[name](), (0, 0, 570, 684), (1140, 1368), 8, clean=True, jitter=0.04).save(
            f"out/page-{name}-title.png")
