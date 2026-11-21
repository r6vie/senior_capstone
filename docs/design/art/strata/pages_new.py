"""Book screen B's title-page art for the covers in covers_new.py. As in pages_more.py, the page is not a zoom of the
cover: it opens the place up into a full scene, more planes, more features, weather, in the cover's inks and at the
cover's slab size. World 570 x 684 = the title page; the text holds the upper left (to about x 480 above y 400), so
the art climbs highest on the right.

python3 pages_new.py [karst ...] -> out/page-{name}-title.png"""
import sys
sys.path.insert(0, ".")
from strata import Ridge, Blob, Water, Band, trees, render
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
    # the aurora lies low and nearly level under the text, then sweeps up steeply beside it on the right
    return 490 - 0.04 * x - np.clip(np.asarray(x, dtype=float) - 440, 0, None) * 1.75


class CurtainSky(AuroraSky):
    """The page's aurora: the curtain split into separate hanging curtains by gaps where slabs are left out."""

    gaps = [(98, 122), (196, 216), (300, 318), (400, 414)]

    def cover(self, x, y):
        import numpy as np
        m = super().cover(x, y)
        h = np.asarray(self.hem(x), dtype=float)
        xa = np.asarray(x, dtype=float)
        above = y < h
        for a, b in self.gaps:
            m &= ~(above & (xa >= a) & (xa <= b))
        return m


def winter():
    """A winter night in a wide snow valley: the aurora sweeping up the right of the page, its curtain dissolving into
    paper through gaps; the night sky under it with a few stars; a tall snow peak on the right and a long range of
    lower, uneven snow hills to the left; a frozen lake with the peaks mirrored in its ice and a bank of mist; far
    firs along the shore, and dark groves of firs in both lower corners on deep snow."""
    peaks = Ridge([(520, 300, 92, 84, 0.95), (446, 468, 66, 54, 0.7), (334, 500, 96, 70, 0.65), (276, 514, 40, 50, 0.8),
                   (180, 492, 100, 76, 0.65), (58, 506, 84, 70, 0.7)], 600, *SNOW, seed=200, rough=5, ribs=0.9,
                  lean=0.4, smooth=True, flicker=0.04)
    far = Ridge([(250, 476, 110, 90, 0.7), (110, 480, 100, 80, 0.7), (400, 456, 80, 70, 0.75)], 600, *SNOW_FAR,
                seed=201, rough=3, ribs=0.3, smooth=True, flicker=0.03)
    lake = Water(598, 640, -40, 610, ["#7E89B2", "#7680AA", "#6E78A2"], ["#9AA4C8", "#A8B1D2"], seed=202,
                 mirror=[peaks], gaps=(0, 0), squash=0.5)
    lake.brick = (6.0, 20.0)
    stars = Blocks([(x, y, x + 2.5, y + 4, STAR) for x, y in
                    [(222, 488), (286, 484), (372, 486), (420, 480), (452, 448), (552, 286), (500, 360), (560, 340)]])
    return [
        CurtainSky(winter_hem, 610, 14, 70, NIGHT, CURTAIN, seed=203),
        stars,
        far,
        peaks,
        Ridge([(560, 520, 60, 50, 0.85), (380, 540, 70, 60, 0.8)], 600, *SNOW_MID, seed=204, rough=3, ribs=0.3,
              smooth=True, flicker=0.03),
        Band(-60, 640, 592, 602, SNOW[0], seed=205, lens=0.0),
        Firs([(x, 602, h, w) for x, h, w in [(140, 30, 6), (156, 38, 7), (172, 28, 6), (292, 34, 7), (308, 26, 6),
                                             (414, 32, 6), (430, 40, 8), (446, 28, 6)]], *F_FAR, tiers=2),
        lake,
        # the aurora caught faintly in the ice under its curtains, and two pale cracks
        Blocks([(x + dx, y, x + dx + 10, y + 4, ["#9FD8BF", "#94CFB5"]) for x, y in [(60, 608), (170, 616), (270, 610),
                                                                                       (360, 620)] for dx in (0, 16)]),
        Blocks([(120, 626, 150, 630, ["#8C90B8"]), (330, 612, 360, 616, ["#8C90B8"])]),
        cloud_band(300, 604, 150),
        Band(-60, 640, 638, 700, SNOW[0], seed=206, lens=0.0),
        Band(-60, 640, 664, 700, SNOW[0][1:] + SNOW[1][:1], seed=207, lens=0.2),
        # dark groves in both lower corners
        Firs([(10, 676, 96, 16), (40, 680, 74, 13), (70, 684, 56, 11), (-10, 684, 80, 14), (98, 686, 40, 9)],
             F_LIT, F_DARK, tiers=3),
        Firs([(470, 680, 90, 15), (500, 676, 118, 18), (532, 680, 100, 16), (560, 684, 84, 14), (444, 686, 50, 10)],
             F_LIT, F_DARK, tiers=3),
    ]


def cloud_band(x, y, w):
    """A low bank of mist over the ice: long stepped slabs, ends uneven."""
    return Blob([(x, y, w, 4), (x - w * 0.5, y + 3, w * 0.45, 3.5), (x + w * 0.45, y - 2, w * 0.4, 3.5)],
                ["#EEF1F8", "#E6EAF4", "#DDE2EF"], top_light=False)


# ---- rice terraces at dawn ----
from covers_new import (Paddies, PADDY_LEFT, PADDY_RIGHT, SEEDLING, BUTTER, FAR_1, FAR_2, DEEP_LAKE, LAKE_GLINT,
                        TREE_DARK, THATCH, STILT, PLANTER, BUSH_SHADE, BUSH_LIT, Mesa)
FAR_3 = (["#C4C0D6", "#BDB9D0"], ["#A9A4C0", "#A29DB9"])     # the furthest ridge, palest
EGRET = ["#F7F7F2", "#EEEEE8"]
STEP = ["#B9A77A", "#AD9B6E"]


def terraces():
    """The terraced valley opened up: the left slope stays low beneath the text and steps down to the right; the right
    slope climbs high beside it; between them the valley runs back through three violet ridges to the butter sun in
    the notch, over a deep lake with the sun's path on it. The terraces bow like contour lines, the shaded left in
    violet-grey water on moss, the lit right in butter and peach on olive. Bushes and dark trees stand on the
    terraces, a stilted hut on the right, a stone stair climbing the right slope, egrets in the near pools."""
    cx = 330
    lake = Water(486, 600, -40, 610, DEEP_LAKE, LAKE_GLINT, seed=310, gaps=(0, 0))
    lake.path = (cx, 9)
    lake.brick = (4.0, 12.0)
    # left slope: low, from the left edge stepping down to the meeting point; right slope: high, from the edge down
    left = [(2, 70), (3, 120), (2, 160), (3, 200), (3, 236), (3, 268), (4, 300), (4, 380), (5, 380), (5, 380),
            (5, 380)]
    # the right slope keeps right of the text (about x 470 above y 350) and climbs to the hut
    right = [(2, 560), (3, 520), (2, 500), (3, 486), (3, 472), (3, 456), (3, 440), (3, 424), (3, 408), (3, 392),
             (3, 376), (4, 360), (4, 344), (4, 338), (4, 326), (5, 342), (5, 330)]   # the meeting steps, never a ruled line
    soft_left = dict(PADDY_LEFT, lip=["#4C5A43", "#45523D"])
    soft_right = dict(PADDY_RIGHT, lip=["#5A5A36", "#525231"])
    lp = Paddies(420, left, [(1, 10000)], soft_left, soft_right, SEEDLING, cx=10000, dip=8, seed=311)
    rp = Paddies(244, [(1, -10000)], right, soft_left, soft_right, SEEDLING, cx=cx, dip=8, seed=312)
    lp.lip_breaks = rp.lip_breaks = True
    return [
        Ridge([(400, 450, 120, 140, 1.0)], 520, (["#DCD8E8", "#D6D2E3"], ["#C8C3DC", "#C2BDD6"]), seed=299,
              rough=2, smooth=True, flicker=0.02) if False else Ridge([(400, 450, 120, 140, 1.0)], 520,
              ["#DCD8E8", "#D6D2E3"], ["#C8C3DC", "#C2BDD6"], seed=299, rough=2, smooth=True, flicker=0.02),
        Ridge([(380, 440, 160, 150, 1.0)], 520, *FAR_3, seed=300, rough=2, smooth=True, flicker=0.02),
        disc(cx, 470, 26, BUTTER),
        Ridge([(250, 466, 120, 100, 1.0), (430, 456, 110, 120, 1.0)], 520, *FAR_1, seed=301, rough=2, smooth=True,
              flicker=0.02),
        Ridge([(220, 484, 110, 90, 1.0), (450, 480, 90, 110, 1.0)], 530, *FAR_2, seed=302, rough=2, smooth=True,
              flicker=0.02),
        lake,
        Blob([(120, 500, 80, 4), (60, 504, 40, 3.5), (190, 498, 40, 3.5)], ["#F4F2F6", "#ECE9F0"], top_light=False),
        lp, rp,
        # the stilted hut high on the right
        Blocks([(526, 252, 529, 268, STILT), (546, 252, 549, 268, STILT)]),
        Mesa(538, 234, 13, 13, 252, *THATCH, ledges=1, bed=8, seed=313, wobble=0, speckle=0, ragged=0),
        Ridge([(538, 216, 22, 22, 1.0)], 235, *THATCH, seed=314, rough=0, smooth=True, flicker=0),
        Blocks([(534, 240, 541, 252, PLANTER)]),
        trees([566, 580], 252, 12, TREE_DARK, seed=315, spread=0.5),
        # bushes and trees on the terraces
        trees([30, 52, 74], 440, 12, BUSH_SHADE, seed=316, spread=0.7),
        trees([146], 482, 9, BUSH_SHADE, seed=317, spread=0.6),
        trees([20, 40], 548, 10, TREE_DARK, seed=318, spread=0.6),
        trees([226, 250], 520, 8, BUSH_SHADE, seed=319, spread=0.6),
        trees([492], 330, 9, BUSH_LIT, seed=320, spread=0.6),
        trees([540, 560], 380, 10, BUSH_LIT, seed=321, spread=0.6),
        trees([420, 446], 470, 9, BUSH_LIT, seed=322, spread=0.6),
        trees([520], 560, 11, BUSH_LIT, seed=323, spread=0.6),
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
    """The island from the lagoon: the volcano on the right rising highest beside the text, a dark barren summit over
    green skirts, its vent glowing, the plume rising and leaning away; a second, older island low on the left; the
    lagoon in bands, deep blue past the reef, a line of breaking foam, turquoise shallows with darker coral heads;
    a sandbar island with palms and an outrigger canoe drawn up on it in front; jungle along the volcano's foot."""
    # kept right of the text (about x 470 above y 350): a steep left flank, a shoulder low on the left below the text
    cone = Ridge([(510, 210, 96, 100, 0.72), (420, 400, 70, 50, 0.85), (590, 300, 40, 70, 0.85)], 520, *V_CONE,
                 seed=400, rough=5, ribs=0.85, lean=0.3,
                 bands=[(206, 226, *V_ASH), (226, 262, *V_BASALT)], smooth=True, flicker=0.05)
    old = Ridge([(70, 470, 110, 90, 0.8), (190, 490, 60, 50, 0.9)], 528, *V_FAR, seed=401, rough=3, ribs=0.4,
                smooth=True, flicker=0.03)
    lagoon = Water(560, 700, -40, 610, ["#9DD0C9", "#8CC7C0", "#7DBBB5", "#6FAFAA"], LAG_G, seed=402, gaps=(0, 1))
    return [
        # the plume, rising from the vent and leaning away to the right, clear of the text
        Blob([(510, 196, 10, 8), (518, 184, 13, 8), (532, 172, 16, 8), (550, 162, 16, 7), (566, 156, 14, 6)], PLUME,
             top_light=True),
        Blob([(548, 300, 26, 5), (530, 306, 16, 4)], CLOUD_W, top_light=False),
        old,
        # a smaller island far out in the haze, and two cloud strips in the open middle
        Ridge([(300, 500, 50, 44, 0.85)], 528, ["#BCCDC0", "#B4C6B8"], ["#A2B5A7", "#9AAE9F"], seed=411, rough=2,
              smooth=True, flicker=0.02, mist=(512, 528)),
        Blob([(300, 432, 70, 4), (250, 436, 30, 3.5)], ["#DFE3E6", "#D6DADE"], top_light=False),
        Blob([(380, 452, 60, 4), (424, 456, 30, 3.5)], ["#DFE3E6", "#D6DADE"], top_light=False),
        Ridge([(560, 360, 50, 60, 1.1)], 520, *V_SHOULDER, seed=403, rough=2, ribs=0.6, lean=0.3, smooth=True,
              flicker=0.04),
        cone,
        Blob([(510, 214, 8, 3)], ["#E3A061", "#D98E4E"], top_light=False),         # the vent's glow
        trees([300, 330, 362, 396, 430, 466, 500, 536, 566], 522, 11, JUNGLE, seed=404, spread=1.0),
        trees([40, 76, 110, 150, 190], 530, 8, JUNGLE, seed=405, spread=1.0),
        Water(522, 560, -40, 610, REEF, LAG_G, seed=406, gaps=(0, 1)),
        Water(552, 564, -40, 610, FOAM_L, FOAM_L, seed=407, gaps=(2, 4)),          # the surf breaking on the reef
        lagoon,
        Blob([(90, 604, 30, 4), (380, 630, 40, 4), (520, 612, 26, 4)], CORAL, top_light=False),
        # the sandbar island in front, palms, a canoe drawn up
        Band(-80, 300, 620, 700, SANDBAR, seed=410, lens=0.6),
        Band(-80, 290, 618, 624, ["#D9C49A", "#D1BB8F"], seed=412, lens=0.6),          # the wet sand at the edge
        block_palms([(40, 72, 30, 14), (96, 62, 26, 12), (150, 52, 22, 9)], 680, P_LIT, P_DARK, P_TRUNK),
        Blocks([(186, 660, 286, 668, CANOE), (180, 656, 190, 660, CANOE), (282, 656, 292, 660, CANOE),
                (196, 648, 276, 652, OUTRIG), (206, 652, 210, 660, OUTRIG), (262, 652, 266, 660, OUTRIG)]),
    ]


SCENES = {"karst": karst, "winter": winter, "terraces": terraces, "lagoon": lagoon_page}

if __name__ == "__main__":
    for name in sys.argv[1:] or list(SCENES):
        render(SCENES[name](), (0, 0, 570, 684), (1140, 1368), 8, clean=True, jitter=0.04).save(
            f"out/page-{name}-title.png")
