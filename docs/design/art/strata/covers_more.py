"""Three more strata covers in the final style: laid clean (render(clean=True)), the title and name set left at the
top (to about y 100 of the 236 x 344 cover), the art filling the rest and running off the foot. Each has its own
terrain and palette; each cover ink is taken from its art, never the UI red.

1 desert: stepped mesas and buttes at dusk, a low gold sun, dunes in front
2 coast: a grassy headland and two sea stacks by moonlight, the moon's path on the sea
3 valley: a terraced hill and a wooded hill in autumn, a river winding back to violet hills

python3 covers_more.py -> out/more-{desert,coast,valley}-{xl,sm}.png"""
import sys
sys.path.insert(0, ".")
from strata import Ridge, Blob, Water, Band, Mesa, Terraces, River, Firs, trees, grove, render

CALM = dict(smooth=True, flicker=0.05)

# ---- 1 desert ----
SAND_L = ["#F2DDB6", "#EBCE9E", "#E1BD85"]
SAND_D = ["#C99B69", "#B08254", "#946A42"]
TERRA_L = ["#E7A174", "#DD8A60", "#CE744D"]
TERRA_D = ["#8E4433", "#6E3329", "#4C2422", "#2F1A20"]
PLUM_L = ["#D3B2BC", "#C4A0AD", "#B38E9E"]
PLUM_D = ["#987080", "#83606F", "#6F515E"]
GOLD = ["#F29A6C", "#EC8556", "#E27043"]   # a saturated coral-orange sun
ROSE = ["#EBA08C", "#E38E7E"]
DUSK = ["#B49AB4", "#A688A6", "#977898"]
DUSK_D = ["#7E6280", "#6B526D", "#59445B"]
SANDS = ["#F2DDB6", "#EBCE9E", "#E3C08A", "#C98A5E", "#A86A47"]


def desert():
    """The critic's round: one flat-capped butte about 45% of the width, sheer walls then a talus skirt, its shade
    side a stepped diagonal down to near-black aubergine; the coral sun behind its upper right shoulder; a long low
    dusty-violet mesa line behind; sand only in the bottom fifth, in broken courses with thin rust shadows."""
    hero = Mesa(98, 168, 52, 84, 296, TERRA_L, TERRA_D, ledges=3, bed=8, seed=53, talus=True, top_tint=ROSE,
                shadow_slope=0.35, flicker=0.03)
    sand = Water(290, 352, -40, 280, SANDS, ["#F7EAD0", "#F1E1C2"], seed=57, gaps=(1, 2), squash=0.5)
    return [
        Blob([(168, 176, 28, 28)], GOLD, top_light=False),
        Mesa(70, 246, 76, 92, 292, DUSK, DUSK_D, ledges=1, bed=6, seed=50, mist=(278, 292), flicker=0.03),
        Mesa(200, 262, 16, 26, 292, TERRA_L, TERRA_D, ledges=1, bed=7, seed=52, talus=True, shadow_slope=0.3,
             flicker=0.03),
        hero,
        sand,
    ]


# ---- 2 coast ----
CHALK_L = ["#E4E0D4", "#D6D1C3", "#C6C0B0"]
CHALK_D = ["#9A9484", "#837E70", "#6C685C"]
INDIGO_L = ["#7C88AE", "#6C789D", "#5C688C"]
INDIGO_D = ["#4A557A", "#3E4867", "#323B56"]
SEA = ["#6E9DA6", "#5B8C97", "#4A7B87", "#3B6A77", "#2E5967"]
MOONGLINT = ["#EEF1EC", "#DFE6E3", "#CCD8D6"]
MOON = ["#EEDFB4", "#E6D19C", "#DCC286"]
TURF = ["#8FA66E", "#7C955C", "#6A844C"]


def coast():
    head = Mesa(206, 156, 54, 92, 268, CHALK_L, CHALK_D, ledges=3, bed=9, seed=61)
    stack1 = Mesa(104, 196, 12, 18, 268, CHALK_L, CHALK_D, ledges=1, bed=8, seed=62)
    stack2 = Mesa(66, 222, 8, 13, 268, CHALK_L, CHALK_D, ledges=1, bed=8, seed=63)
    sea = Water(262, 352, -20, 260, SEA, MOONGLINT, seed=64, mirror=[head, stack1, stack2], gaps=(0, 1), squash=0.5)
    sea.path = (110, 10)
    return [
        Blob([(118, 150, 20, 20)], MOON, top_light=False),
        Ridge([(-10, 230, 80, 90, 0.9), (60, 244, 50, 60, 1.0)], 266, INDIGO_L, INDIGO_D, seed=60, rough=2,
              ribs=0.5, mist=(252, 266), **CALM),
        stack2, stack1, head,
        Band(150, 262, 150, 160, TURF, seed=65, lens=0.25),
        sea,
    ]


# ---- 3 valley ----
GOLD_L = ["#EBCB78", "#E0B65F", "#D2A049"]
OLIVE = ["#A3AA61", "#8D964F", "#78823F"]
RUSTT = ["#D27845", "#BC6236", "#9E4E2A", "#7F3D21"]
VIOLET_L = ["#C4C1D8", "#B4B0CB", "#A39FBC"]
VIOLET_D = ["#8F8AA8", "#7F7A97", "#6E6A86"]
FOREST_L = ["#7E8E52", "#6C7C45", "#5A6A39"]
FOREST_D = ["#465331", "#3A4529", "#2E3721"]
RIVER = ["#A9C3CF", "#91B0C0", "#7A9CAF", "#668AA0"]
CREAM = ["#FBEFD5", "#F6E3BD", "#F0D6A4"]


# ---- 3 autumn hills (critic round: no disc; three round domes on a value ladder; a poplar clump as the focus) ----
H_GOLD = (["#F4DA97", "#EFCD80", "#E8C06B"], ["#D6A95A", "#C2964D", "#AD8341"])
H_RUST = (["#DA845A", "#CD7049", "#BD5F3B"], ["#9A4A2E", "#803D27", "#663220"])
H_FOREST = (["#56714F", "#4A6545", "#3F583B"], ["#263A2D", "#1C2C22", "#132018"])
POPLAR_L = ["#46634A", "#3E5A42"]
POPLAR_D = ["#152219", "#101A13"]


def dome(peaks, base, inks, seed, mist=None):
    return Ridge(peaks, base, inks[0], inks[1], seed=seed, rough=1.5, ribs=0.2, lean=0.55, mist=mist, smooth=True,
                 flicker=0.02, round=True)


def valley():
    """Rolling autumn hills, no disc: three rounded domes on one value ladder, the pale gold hill at the back
    (the lightest and warmest, the source of glow, its crest at half the cover's height), rust in the middle running
    off the left edge, deep forest in front; on the forest crest at 60-75% across, a clump of dark poplars, the
    tallest reaching the 45% line."""
    return [
        dome([(150, 172, 150, 140, 1.0)], 300, H_GOLD, 81),
        dome([(-50, 214, 230, 210, 1.0)], 352, H_RUST, 82),
        dome([(196, 262, 176, 160, 1.0)], 352, H_FOREST, 83),
        Firs([(152, 272, 114, 8), (172, 270, 88, 7), (134, 276, 70, 6), (190, 274, 58, 5.5)], POPLAR_L, POPLAR_D,
             tiers=1),
    ]


SCENES = {"desert": desert, "coast": coast, "valley": valley}

if __name__ == "__main__":
    for name, fn in SCENES.items():
        render(fn(), (0, 0, 236, 344), (472, 688), 8, paper=(255, 255, 255), clean=True).save(f"out/more-{name}-xl.png")
        render(fn(), (0, 0, 236, 344), (244, 356), 3, paper=(255, 255, 255), clean=True).save(f"out/more-{name}-sm.png")
