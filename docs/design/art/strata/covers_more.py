"""Three more strata covers in the final style: laid clean (render(clean=True)), the title and name set left at the
top (to about y 100 of the 236 x 344 cover), the art filling the rest and running off the foot. Each has its own
terrain and palette; each cover ink is taken from its art, never the UI red.

1 desert: stepped mesas and buttes at dusk, a low gold sun, dunes in front
2 coast: a grassy headland and two sea stacks by moonlight, the moon's path on the sea
3 valley: a terraced hill and a wooded hill in autumn, a river winding back to violet hills

python3 covers_more.py -> out/more-{desert,coast,valley}-{xl,sm}.png"""
import sys
sys.path.insert(0, ".")
from strata import Ridge, Blob, Water, Band, Mesa, Terraces, trees, render

CALM = dict(smooth=True, flicker=0.05)

# ---- 1 desert ----
SAND_L = ["#F2DDB6", "#EBCE9E", "#E1BD85"]
SAND_D = ["#C99B69", "#B08254", "#946A42"]
TERRA_L = ["#E7A174", "#DD8A60", "#CE744D"]
TERRA_D = ["#A2533A", "#86432F", "#6A3525"]
PLUM_L = ["#D3B2BC", "#C4A0AD", "#B38E9E"]
PLUM_D = ["#987080", "#83606F", "#6F515E"]
GOLD = ["#F7DC97", "#F3CB79", "#EEBA5E"]


def desert():
    return [
        Blob([(176, 196, 30, 30)], GOLD, top_light=False),
        Ridge([(30, 244, 70, 60, 0.35), (200, 240, 60, 70, 0.4)], 272, PLUM_L, PLUM_D, seed=51, rough=2, ribs=0.3,
              mist=(256, 272), **CALM),
        Mesa(204, 214, 24, 40, 276, TERRA_L, TERRA_D, ledges=2, bed=6, seed=52, mist=(262, 276)),
        Mesa(92, 150, 46, 104, 290, TERRA_L, TERRA_D, ledges=3, bed=8, seed=53, mist=(276, 290)),
        Band(-40, 280, 276, 352, SAND_L, seed=56, lens=0.0),
        Ridge([(40, 284, 120, 110, 0.9), (190, 296, 110, 120, 0.85)], 352, SAND_L, SAND_D, seed=54, rough=3,
              ribs=0.4, lean=0.5, **CALM),
        Ridge([(150, 318, 140, 130, 0.8)], 352, SAND_L, SAND_D, seed=55, rough=3, ribs=0.4, lean=0.5, **CALM),
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


def valley():
    river = Band(30, 250, 262, 352, RIVER, seed=75, lens=0.97)   # narrow in the distance, wide at the foot
    return [
        Blob([(186, 168, 18, 18)], CREAM, top_light=False),
        Ridge([(60, 222, 90, 90, 1.0), (180, 210, 90, 100, 1.05)], 262, VIOLET_L, VIOLET_D, seed=71, rough=3,
              ribs=0.5, mist=(244, 262), **CALM),
        Ridge([(220, 200, 100, 70, 1.15)], 300, FOREST_L, FOREST_D, seed=72, rough=4, ribs=0.8, mist=(284, 300), **CALM),
        Terraces([(-6, 182, 150, 160, 0.95)], 352, GOLD_L, OLIVE, bed=12, seed=74, rough=2, **CALM),
        river,
        trees([188, 206, 224, 240], 340, 12, RUSTT, seed=76),
    ]


SCENES = {"desert": desert, "coast": coast, "valley": valley}

if __name__ == "__main__":
    for name, fn in SCENES.items():
        render(fn(), (0, 0, 236, 344), (472, 688), 8, paper=(255, 255, 255), clean=True).save(f"out/more-{name}-xl.png")
        render(fn(), (0, 0, 236, 344), (244, 356), 3, paper=(255, 255, 255), clean=True).save(f"out/more-{name}-sm.png")
