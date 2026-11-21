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


SCENES = {"karst": karst}

if __name__ == "__main__":
    for name in sys.argv[1:] or list(SCENES):
        render(SCENES[name](), (0, 0, 570, 684), (1140, 1368), 8, clean=True, jitter=0.04).save(
            f"out/page-{name}-title.png")
