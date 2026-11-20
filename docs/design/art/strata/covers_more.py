"""Three more strata covers in the final style: laid clean (render(clean=True)), the title and name set left at the
top (to about y 100 of the 236 x 344 cover), the art filling the rest and running off the foot. Each has its own
terrain and palette; each cover ink is taken from its art, never the UI red.

1 desert: stepped mesas and buttes at dusk, a low gold sun, dunes in front
2 coast: a grassy headland and two sea stacks by moonlight, the moon's path on the sea
3 valley: a terraced hill and a wooded hill in autumn, a river winding back to violet hills

python3 covers_more.py -> out/more-{desert,coast,valley}-{xl,sm}.png"""
import sys
sys.path.insert(0, ".")
from strata import Ridge, Blob, Water, Band, Mesa, Terraces, River, trees, grove, render

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


TERR_BEDS = [["#7B8443", "#727B3C"], ["#9C9A4C", "#918F45"], ["#C9A24A", "#BF9742"], ["#DB963F", "#D08A38"],
             ["#C8693A", "#BC5F34"], ["#A9522D", "#9C4A29"]]
LIP = ["#F3E7C6", "#EEDFB6"]
PINE_L = ["#4E6A4E", "#445F45", "#3A543C"]
PINE_D = ["#24372B", "#1B2B22", "#121E18"]
AMBER = ["#F4B04F", "#EFA03E", "#E68E31"]


def valley():
    """The critic's rethink: the terraces are the hero, a big stepped hillside rising from the bottom left to about
    half the art's height, each terrace one solid colour from deep olive at the top through ochre and amber to rust
    at the foot, a pale lip on each; a dark pine ridge behind on the right with a near-black shadow flank; an amber
    sun partly behind its shoulder; a river along the foot in broken blue courses. No lilac hills."""
    pine = Ridge([(200, 178, 110, 80, 1.1)], 312, PINE_L, PINE_D, seed=72, rough=3, ribs=0.8, lean=0.15,
                 mist=(296, 312), **CALM)
    hill = Terraces([(-20, 184, 30, 250, 0.7)], 320, GOLD_L, OLIVE, bed=16, beds=TERR_BEDS, lip=LIP, seed=74,
                    rough=2, smooth=True, flicker=0.0)
    river = Water(320, 352, -20, 280, RIVER, ["#F4F3EE", "#E4ECEF"], seed=75, gaps=(1, 2), squash=0.5, taper=0.2)
    return [
        Blob([(170, 200, 24, 24)], AMBER, top_light=False),
        pine,
        hill,
        river,
    ]


SCENES = {"desert": desert, "coast": coast, "valley": valley}

if __name__ == "__main__":
    for name, fn in SCENES.items():
        render(fn(), (0, 0, 236, 344), (472, 688), 8, paper=(255, 255, 255), clean=True).save(f"out/more-{name}-xl.png")
        render(fn(), (0, 0, 236, 344), (244, 356), 3, paper=(255, 255, 255), clean=True).save(f"out/more-{name}-sm.png")
