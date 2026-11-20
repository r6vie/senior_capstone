"""Book screen B's page art for the three newer covers (covers_more.py): the inside follows the cover. Each page scene
is the cover's place seen wider, laid out like final.py's page(): world 570 x 684 at the cover's slab size (a course
is 4 world px on both), the text holding the upper left, the cover's hero on the right third, lower land framing the
left, the foreground running off the foot. The contents page shows the same place from further back.

python3 pages_more.py -> out/page-{desert,coast,valley}-{title,contents}.png"""
import sys
sys.path.insert(0, ".")
from strata import Ridge, Blob, Water, Band, Mesa, Firs, render
from covers_more import (TERRA_L, TERRA_D, ROSE, GOLD, HAZE_PEACH, HAZE_PEACH_D, NEAR_L, NEAR_D, SAND_CALM, UMBER,
                         CHALK_L, CHALK_D, INDIGO_L, INDIGO_D, SEA, MOONGLINT, MOON, TURF, CALM,
                         H_GOLD, H_RUST, H_FOREST, POPLAR_L, POPLAR_D, dome)


def desert():
    """The leaning butte on the right third with the pale sun behind its upper right shoulder, the smaller near cliff
    off the right edge, the stepped peach haze cliff across the whole width, calm sand over umber."""
    hero = Mesa(410, 360, 58, 96, 612, TERRA_L, TERRA_D, ledges=4, bed=8, seed=53, talus=True, top_tint=ROSE,
                shadow_slope=0.35, wobble=0, speckle=0.4, flicker=0.02, lean=0.12, flare=8,
                bedding=([430, 492, 552], "#D9845A"))
    near = Mesa(522, 580, 28, 46, 646, NEAR_L, NEAR_D, ledges=2, bed=8, seed=54, talus=True, top_tint=ROSE,
                wobble=0, speckle=0.4, flicker=0.02, lean=0.12, flare=4, shadow_steps=3)
    sun = Blob([(494, 446, 34, 34)], GOLD, top_light=False)
    sun.ragged = 0
    # the back cliff: a section every ~28 px, each one or two slabs above or below its neighbour
    tops = [548, 552, 552, 548, 552, 556, 552, 548, 544, 548, 552, 556, 552, 548, 552, 548, 544, 548, 552, 548, 552, 556, 552,
            548, 544]
    haze = [Mesa(-66 + 28 * i, t, 15, 19, 612, HAZE_PEACH, HAZE_PEACH_D, ledges=1, bed=8, seed=50 + i, wall_ledge=4,
                 wobble=0, speckle=0.3, ragged=0, flicker=0.01) for i, t in enumerate(tops)]
    left = Mesa(20, 540, 50, 70, 612, NEAR_L, NEAR_D, ledges=2, bed=8, seed=55, talus=True, top_tint=ROSE,
                wobble=0, speckle=0.4, flicker=0.02, lean=-0.08, flare=3, shadow_steps=3)
    return [sun, *haze, left, hero,
            Band(-60, 640, 608, 660, SAND_CALM, seed=58, lens=0.0),
            near,
            Band(-60, 640, 660, 700, UMBER, seed=59, lens=0.0)]


def coast():
    """The chalk headland on the right third running off the edge, turf on its top, the two stacks stepping out to the
    left, the moon over them with its path on the sea, a low indigo headland far off on the left."""
    head = Mesa(520, 380, 90, 130, 588, CHALK_L, CHALK_D, ledges=3, bed=9, seed=61)
    stack1 = Mesa(360, 470, 21, 31, 588, CHALK_L, CHALK_D, ledges=1, bed=8, seed=62)
    stack2 = Mesa(300, 510, 14, 22, 588, CHALK_L, CHALK_D, ledges=1, bed=8, seed=63)
    sea = Water(582, 700, -40, 620, SEA, MOONGLINT, seed=64, mirror=[head, stack1, stack2], gaps=(0, 1), squash=0.5)
    sea.path = (318, 14)
    return [
        Blob([(318, 420, 26, 26)], MOON, top_light=False),
        Ridge([(-20, 522, 170, 180, 0.8), (150, 550, 100, 110, 0.9)], 586, INDIGO_L, INDIGO_D, seed=60, rough=2,
              ribs=0.5, mist=(570, 586), **CALM),
        stack2, stack1, head,
        Band(434, 660, 372, 384, TURF, seed=65, lens=0.25),
        sea,
        Band(-60, 180, 652, 700, INDIGO_D, seed=66, lens=0.5),
    ]


def valley():
    """The gold hill at the back right, rust running off the left, deep forest in front with the poplar clump on its
    crest at the right third."""
    return [
        dome([(470, 450, 340, 190, 1.0)], 700, H_GOLD, 81),
        dome([(-20, 548, 330, 300, 1.0)], 700, H_RUST, 82),
        dome([(450, 596, 280, 240, 1.0)], 700, H_FOREST, 83),
        Firs([(402, 610, 180, 11), (430, 606, 140, 10), (378, 614, 110, 9), (454, 610, 92, 8)], POPLAR_L, POPLAR_D,
             tiers=1),
    ]


SCENES = {"desert": desert, "coast": coast, "valley": valley}

if __name__ == "__main__":
    only = sys.argv[1:] or list(SCENES)
    for name in only:
        j = 0.017 if name == "desert" else 0.05
        s = SCENES[name]()
        render(s, (0, 0, 570, 684), (1140, 1368), 8, clean=True, jitter=j).save(f"out/page-{name}-title.png")
        render(s, (-50, 260, 620, 684), (1140, 722), 8, clean=True, jitter=j).save(f"out/page-{name}-contents.png")
