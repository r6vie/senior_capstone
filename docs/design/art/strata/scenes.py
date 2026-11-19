from strata import Ridge, Blob, Water, Band, trees

# Shared inks, refined from the reference: fewer, cleaner families.
COBALT = ["#A9C7E4", "#7FAAD6", "#5389C4", "#3369AC", "#1F4E8E"]
GLINT = ["#F1F1EE", "#E1E5E8", "#C9D4DE"]
TEAL_LIT = ["#6E9CB0", "#4F8399", "#3D6E7E", "#2F5C62"]
TEAL_DARK = ["#28463F", "#1C3631", "#132722", "#0E1D1A"]
SAGE_LIT = ["#A8B4A7", "#8E9C8E", "#76877A"]
SAGE_DARK = ["#56675D", "#40524A", "#2E3E37"]
CORAL = ["#F2A48C", "#EE8A6E", "#E87457"]
RUST = ["#9A4A35", "#7E3A2A", "#5F2A1F"]
CLOUD = ["#F1EEE7", "#E4DFD5", "#D3CDC1", "#BFB8AB", "#A69F92"]
STONE_LIT = ["#EEEBE4", "#E2DED4", "#D4CFC3"]
STONE_DARK = ["#B9B2A5", "#9E978A", "#837C70"]
LEAF = ["#93B47A", "#6F9A5A", "#4F7D45", "#3A6337", "#284A2B", "#1B3520"]
SHORE = ["#B5C192", "#9EAF7D", "#8A9E6C", "#A8B886"]


# The hero book's cover is a window onto its landscape: on the book page the cover sits at COVER
# (world px) and shows exactly the land behind it.
LAKE_COVER = (128, 64, 364, 408)


def lake():
    """World 1440 x 620. A tall teal peak and the sun inside the cover window; low hills and the lake
    under the text column; a coral and a sage peak on the right; groves on both shores."""
    return [
        Blob([(300, 236, 42, 42)], CORAL, top_light=False),
        Ridge([(1290, 238, 240, 260, 1.25), (1010, 352, 200, 230, 1.1)], 436, STONE_LIT, STONE_DARK, seed=11, rough=4),
        Ridge([(1342, 196, 170, 230, 1.2)], 436, CORAL, RUST, seed=12),
        Blob([(1250, 104, 150, 22), (1350, 86, 110, 18), (1150, 120, 90, 14), (1440, 112, 120, 18)], CLOUD),
        Blob([(-40, 160, 110, 18), (10, 178, 80, 14)], CLOUD),
        Ridge([(252, 186, 230, 330, 1.45), (-20, 290, 150, 200, 1.1), (560, 388, 160, 200, 1.0)], 452,
              TEAL_LIT, TEAL_DARK, seed=13, rough=6),
        Ridge([(1170, 262, 210, 260, 1.3)], 448, SAGE_LIT, SAGE_DARK, seed=14, rough=6),
        Blob([(760, 420, 170, 16), (900, 428, 140, 12), (1010, 418, 110, 14)], CLOUD),
        Water(440, 532, -40, 1500, COBALT, GLINT, seed=21),
        Band(-60, 440, 512, 548, SHORE, seed=31, lens=0.8),
        trees([10, 70, 135, 195, 255, 320, 380], 524, 17, LEAF, seed=41),
        Band(1060, 1500, 520, 556, SHORE, seed=32, lens=0.8),
        trees([1110, 1175, 1240, 1300, 1365, 1430], 532, 16, LEAF, seed=42),
        Water(556, 600, 420, 1080, COBALT, GLINT, seed=22, taper=0.6),
    ]


# ---------- cover-only scenes: world 236 x 344, title on paper above y~118, name on paper below y~300 ----------
COVER_W, COVER_H = 236, 344
BLUE_LIT = ["#9DBBD6", "#7CA2C8", "#5C88B6", "#456FA0"]
BLUE_DARK = ["#3A5B86", "#2C4A72", "#1F395C", "#152A46"]
OCHRE_LIT = ["#E6CB97", "#DAB477", "#C99C5A"]
OCHRE_DARK = ["#A07A45", "#83613A", "#634829"]


def coast():
    return [
        Blob([(184, 168, 20, 20)], CORAL, top_light=False),
        Blob([(150, 128, 70, 9), (100, 138, 50, 7)], CLOUD),
        Ridge([(40, 140, 120, 150, 1.0)], 252, CORAL, RUST, seed=51, rough=3, lean=0.2),
        Ridge([(-30, 200, 90, 120, 0.8)], 262, STONE_LIT, STONE_DARK, seed=52, rough=3),
        Water(236, 300, 40, 280, COBALT, GLINT, seed=53, taper=0.3),
    ]


def ranges():
    return [
        Ridge([(150, 150, 140, 150, 1.1), (20, 175, 90, 110, 1.0)], 250, BLUE_LIT, BLUE_DARK, seed=61, rough=3),
        Ridge([(70, 176, 110, 120, 1.15), (200, 190, 90, 100, 1.1)], 262, STONE_LIT, STONE_DARK, seed=62, rough=3),
        Ridge([(130, 222, 120, 140, 1.0)], 272, CORAL, RUST, seed=63, rough=2),
        Band(-20, 260, 266, 292, SHORE, seed=64, lens=0.4),
        trees([10, 52, 96, 140, 186, 226], 278, 11, LEAF, seed=65),
    ]


def islands():
    return [
        Blob([(60, 170, 26, 26)], CORAL, top_light=False),
        Blob([(160, 132, 80, 10), (200, 146, 60, 8), (110, 150, 40, 6)], CLOUD),
        Water(206, 296, -20, 260, COBALT, GLINT, seed=71),
        Band(20, 140, 214, 236, SHORE, seed=72, lens=0.7),
        trees([40, 70, 100, 124], 222, 11, LEAF, seed=73),
        Band(140, 260, 252, 272, SHORE, seed=74, lens=0.7),
        trees([160, 190, 222], 260, 10, LEAF, seed=75),
    ]


def twins():
    return [
        Ridge([(170, 140, 120, 110, 1.3)], 262, SAGE_LIT, SAGE_DARK, seed=81, rough=3),
        Blob([(120, 214, 90, 9), (190, 224, 60, 7), (40, 222, 50, 6)], CLOUD),
        Ridge([(60, 166, 110, 120, 1.3)], 272, TEAL_LIT, TEAL_DARK, seed=82, rough=3),
        Water(268, 296, -20, 260, COBALT, GLINT, seed=83, taper=0.5),
    ]


def summit():
    return [
        Blob([(60, 150, 70, 9), (30, 162, 50, 7)], CLOUD),
        Ridge([(190, 150, 110, 120, 1.1), (20, 180, 80, 90, 1.0)], 240, BLUE_LIT, BLUE_DARK, seed=90, rough=3),
        Ridge([(120, 132, 110, 130, 1.25)], 270, STONE_LIT, STONE_DARK, seed=91, rough=3),
        Ridge([(220, 212, 70, 60, 1.0)], 276, CORAL, RUST, seed=92, rough=2),
        Blob([(110, 244, 100, 9), (190, 250, 60, 7)], CLOUD),
        Band(-20, 150, 270, 292, SHORE, seed=93, lens=0.5),
        trees([0, 34, 70, 104], 280, 10, LEAF, seed=94),
    ]


def terraces():
    """A river valley: two hills lean in, groves on the near slopes, the river between them."""
    return [
        Blob([(118, 176, 26, 26)], CORAL, top_light=False),
        Ridge([(10, 150, 120, 190, 1.0)], 262, SAGE_LIT, SAGE_DARK, seed=101, rough=3),
        Ridge([(236, 168, 180, 100, 1.0)], 268, TEAL_LIT, TEAL_DARK, seed=102, rough=3),
        Water(244, 300, 70, 170, COBALT, GLINT, seed=105, taper=-0.6),
        trees([0, 30, 58], 254, 11, LEAF, seed=104),
        trees([186, 214, 240], 262, 11, LEAF, seed=106),
    ]


def dusk():
    return [
        Blob([(70, 150, 24, 24)], STONE_LIT, top_light=False),
        Ridge([(160, 150, 130, 120, 1.2), (30, 190, 80, 90, 1.0)], 262, OCHRE_LIT, OCHRE_DARK, seed=111, rough=3),
        Blob([(100, 236, 110, 9), (40, 246, 60, 7)], CLOUD),
        Ridge([(200, 220, 90, 80, 1.0)], 276, TEAL_LIT, TEAL_DARK, seed=112, rough=2),
        Water(262, 298, -20, 260, COBALT, GLINT, seed=113, taper=0.4),
    ]


COVER_SCENES = {
    "coast": coast, "ranges": ranges, "islands": islands, "twins": twins,
    "summit": summit, "terraces": terraces, "dusk": dusk,
}
