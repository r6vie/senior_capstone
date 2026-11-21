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
TERRA_D = ["#8E4433", "#6E3329", "#5A2A20", "#6B2A1E"]
PLUM_L = ["#D3B2BC", "#C4A0AD", "#B38E9E"]
PLUM_D = ["#987080", "#83606F", "#6F515E"]
GOLD = ["#F7DCA0", "#F3CF8C", "#F0C27A"]   # pale gold, apart from the rock
ROSE = ["#EBA08C", "#E38E7E"]
DUSK = ["#F0D3BD", "#EAC6AC", "#E2B99C"]   # far mesas in warm haze, not purple
DUSK_D = ["#D6A78A", "#C9997D", "#BB8B70"]
SANDS = ["#F2DDB6", "#EBCE9E", "#E3C08A", "#C98A5E", "#A86A47"]


HAZE_PEACH = ["#EDC0A7", "#E8B49A", "#E1A88D"]
HAZE_PEACH_D = ["#E7B9A0", "#DDAA90", "#D19C82"]
MAROON = ["#5A2A24", "#4A2220", "#3A1C1C"]
UMBER = ["#6B3A2A", "#5E3324"]
NEAR_L = ["#B5583A", "#A94F33", "#9C482E"]
NEAR_D = ["#7A2E22", "#6B281E", "#5C221A"]
SAND_CALM = ["#F2DDB6", "#EDD3A6", "#E7C997", "#F2DDB6", "#EBCB98"]


def desert():
    """Back to the tilted butte (Josef preferred it to the sheer block): a talus skirt stepping out at the foot, the
    shade edge a stepped diagonal, and now a lean, so the cap sits right of its base; rose dusk light on the cap; the
    coral-gold sun behind the upper right shoulder; warm peach haze mesas behind (no purple); a smaller, nearer cliff
    in the right foreground in deeper terracotta, leaning the same way; calm sand over a dark umber base."""
    hero = Mesa(92, 178, 44, 70, 292, TERRA_L, TERRA_D, ledges=4, bed=8, seed=53, talus=True, top_tint=ROSE,
                shadow_slope=0.35, wobble=0, speckle=0.4, flicker=0.02, lean=0.12, flare=6,
                bedding=([204, 234, 262], "#D9845A"))
    near = Mesa(206, 262, 24, 40, 318, NEAR_L, NEAR_D, ledges=2, bed=8, seed=54, talus=True, top_tint=ROSE,
                wobble=0, speckle=0.4, flicker=0.02, lean=0.12, flare=3, shadow_steps=3)
    sun = Blob([(166, 197, 28, 28)], GOLD, top_light=False)
    sun.ragged = 0     # a clean disc
    return [
        sun,
        # the back cliff runs the full width as one line of flat tops at slightly different heights
        *[Mesa(cx, top, hw, hw + 4, 292, HAZE_PEACH, HAZE_PEACH_D, ledges=1, bed=8, seed=50 + i, wall_ledge=4, wobble=0,
               speckle=0.3, ragged=0, flicker=0.01)
          # a section every ~26 px, each one or two slabs (4 or 8 px) above or below its neighbour
          for i, (cx, top, hw) in enumerate([(-6, 240, 14), (20, 236, 14), (46, 240, 14), (72, 244, 14),
                                             (98, 240, 14), (124, 236, 14), (150, 240, 14), (176, 244, 14),
                                             (202, 240, 14), (228, 232, 14), (254, 236, 14)])],
        hero,
        Band(-60, 300, 288, 334, SAND_CALM, seed=58, lens=0.0),
        near,
        Band(-60, 300, 334, 360, UMBER, seed=59, lens=0.0),
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
        j = 0.017 if name == "desert" else 0.05    # the desert's faces are calm: a third of the usual jitter
        render(fn(), (0, 0, 236, 344), (472, 688), 8, paper=(255, 255, 255), clean=True, jitter=j).save(f"out/more-{name}-xl.png")
        render(fn(), (0, 0, 236, 344), (244, 356), 3, paper=(255, 255, 255), clean=True, jitter=j).save(f"out/more-{name}-sm.png")
