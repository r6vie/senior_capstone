"""Book screen B's title-page art for the three newer covers (covers_more.py). The inside follows the cover but is
not a zoom of it: like final.py's page() it opens the place up into a full scene, more planes, more features, weather
(cloud bands, mist), in the cover's inks and at the cover's slab size (a course is 4 world px on both).
World 570 x 684 = the title page; the text holds the upper left (to about x 480 above y 400), so the art climbs
highest on the right.

python3 pages_more.py [desert|coast|valley ...] -> out/page-{name}-title.png"""
import sys
sys.path.insert(0, ".")
from strata import Ridge, Blob, Water, Band, Mesa, Firs, River, trees, render
from covers_more import (TERRA_L, TERRA_D, ROSE, GOLD, HAZE_PEACH, HAZE_PEACH_D, NEAR_L, NEAR_D, SAND_CALM,
                         CHALK_L, CHALK_D, INDIGO_L, INDIGO_D, SEA, MOONGLINT, MOON, TURF, CALM,
                         VIOLET_L, VIOLET_D, RIVER, CREAM, H_GOLD, H_RUST, H_FOREST, POPLAR_L, POPLAR_D, dome)


class Arch(Mesa):
    """A rock arch: a mesa with an elliptical opening through its foot."""

    def __init__(self, *a, hole=(0, 0, 1, 1), **k):
        super().__init__(*a, **k)
        self.hole = hole

    def cover(self, x, y):
        cx, cy, rx, ry = self.hole
        return super().cover(x, y) & ~(((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2 <= 1)


def strip(x, y, w, h, inks):
    """A thin cloud or mist band: a few long flat ellipses."""
    return Blob([(x, y, w, h), (x - w * 0.45, y + h * 0.6, w * 0.55, h * 0.8), (x + w * 0.5, y + h * 0.4, w * 0.5, h * 0.7)],
                inks)


# ---- desert: a broad mesa at sunset, an arch, distant buttes, dunes ----
DUNE_L = ["#F2DDB6", "#EDD3A6", "#E7C997"]
DUNE_D = ["#D9B27E", "#C99D6B", "#B88A5B"]
FAR_BUTTE_L = ["#E19A78", "#D98D6B", "#CF8160"]
FAR_BUTTE_D = ["#A86450", "#985844", "#884D3B"]
SCRUB = ["#A3A17A", "#8E8F68", "#7A7B58"]


WASH = ["#D8B183", "#CBA273", "#BC9264"]


def desert():
    """A wide, low mesa and its bench at sunset, the sun sinking behind its right shoulder in a clear sky;
    the stepped haze cliff behind, a tier of misted buttes, a few stout pinnacles, an arch, a dry wash winding out of
    the plain between dunes, scrub along its banks, a low dark mesa framing the right foot."""
    sun = Blob([(524, 420, 36, 36)], GOLD, top_light=False)
    sun.ragged = 0
    tops = [480, 476, 480, 484, 480, 476, 472, 476, 480, 484, 480, 476, 480, 476, 472, 476, 480, 476, 480, 484, 480,
            476, 472]
    haze = [Mesa(-66 + 28 * i, t, 15, 19, 562, HAZE_PEACH, HAZE_PEACH_D, ledges=1, bed=8, seed=50 + i, wall_ledge=4,
                 wobble=0, speckle=0.3, ragged=0, flicker=0.01) for i, t in enumerate(tops)]
    far = [Mesa(cx, t, tw, bw, 548, FAR_BUTTE_L, FAR_BUTTE_D, ledges=2, bed=8, seed=70 + i, talus=True, wobble=0,
                speckle=0.3, flicker=0.01, lean=0.06)
           for i, (cx, t, tw, bw) in enumerate([(30, 494, 24, 36), (150, 506, 30, 42)])]
    # the hero: wide and flat-topped (about 1.6 : 1), the sun going down behind its right shoulder
    hero = Mesa(430, 448, 112, 146, 560, TERRA_L, TERRA_D, ledges=3, bed=8, seed=53, talus=True, top_tint=ROSE,
                shadow_slope=0.35, wobble=0, speckle=0.4, flicker=0.02, lean=0.05, flare=6,
                bedding=([484, 516], "#D9845A"))
    bench = Mesa(290, 508, 44, 64, 560, TERRA_L, TERRA_D, ledges=2, bed=8, seed=52, talus=True, top_tint=ROSE,
                 wobble=0, speckle=0.4, flicker=0.02, lean=0.05, shadow_steps=3)
    arch = Arch(96, 540, 46, 60, 622, NEAR_L, NEAR_D, ledges=2, bed=8, seed=57, top_tint=ROSE, wobble=0,
                speckle=0.4, flicker=0.02, shadow_steps=3, hole=(100, 622, 26, 54))
    near = Mesa(536, 572, 44, 66, 650, NEAR_L, NEAR_D, ledges=2, bed=8, seed=54, talus=True, top_tint=ROSE,
                wobble=0, speckle=0.4, flicker=0.02, lean=0.1, flare=3, shadow_steps=3)
    # a few stout pinnacles out on the plain
    hoodoos = [Mesa(cx, t, tw, bw, 600, NEAR_L, NEAR_D, ledges=1, bed=8, seed=80 + i, top_tint=ROSE, wall_ledge=3,
                    wobble=0, speckle=0.3, ragged=0, flicker=0.02, shadow_steps=2)
               for i, (cx, t, tw, bw) in enumerate([(200, 534, 7, 11), (234, 514, 8, 13), (266, 546, 6, 10)])]
    return [
        sun,
        *haze, *far,
        hero, bench,
        Band(-60, 640, 556, 700, SAND_CALM, seed=58, lens=0.0),
        *hoodoos,
        River(580, 700, 330, 34, 4, 70, WASH, DUNE_L, swings=1.3, phase=0.4, seed=47),
        arch,
        near,
        Ridge([(60, 612, 230, 200, 1.0)], 720, DUNE_L, DUNE_D, seed=59, rough=1, lean=0.5, smooth=True,
              flicker=0.02, round=True),
        Ridge([(480, 628, 210, 220, 1.0)], 720, DUNE_L, DUNE_D, seed=60, rough=1, lean=0.5, smooth=True,
              flicker=0.02, round=True),
        trees([270, 292, 308], 596, 9, SCRUB, seed=44, spread=0.6),
        trees([384, 408], 636, 10, SCRUB, seed=48, spread=0.6),
        trees([28, 60, 92], 620, 11, SCRUB, seed=49, spread=0.6),
    ]


# ---- coast: the chalk coast under the moon, stacks and an arch stepping out, a lighthouse ----
FAR_IND_L = ["#AEB6CE", "#A0A8C3", "#929AB7"]
FAR_IND_D = ["#8189A6", "#757D9A", "#69718E"]
NIGHT_CLOUD = ["#DCE2E6", "#CED6DC", "#BFC9D1"]
MIST = ["#E9EDEC", "#DFE5E5"]
ROCK_L = ["#5C6688", "#525C7C", "#475170"]
LAMP = ["#F6E7B8", "#F0DA9C"]


FAR_CHALK_L = ["#E3E3DE", "#D9DAD5", "#CFD0CB"]
FAR_CHALK_D = ["#B3B5B3", "#A6A8A7", "#999B9B"]
FOAM = ["#F3F5F2", "#E7EDEC", "#DCE5E5"]
SLATE = ["#4D5672", "#434B66"]


def coast():
    """The chalk coast under a low moon: the headland with its lighthouse and keeper's cottage, an arch and a broken
    line of stacks stepping out, a misted far stack, headlands receding to the left, foam at every foot, the moon's
    path down the sea, cloud banks to the right, dark rocks framing both corners of the foot."""
    head = Mesa(524, 384, 92, 132, 588, CHALK_L, CHALK_D, ledges=3, bed=9, seed=61, mist=(556, 588))
    arch = Arch(350, 470, 30, 44, 588, CHALK_L, CHALK_D, ledges=2, bed=8, seed=62, hole=(354, 588, 14, 50),
                mist=(560, 588))
    stacks = [Mesa(cx, t, tw, bw, 588, CHALK_L, CHALK_D, ledges=1, bed=8, seed=63 + i, mist=(570, 588))
              for i, (cx, t, tw, bw) in enumerate([(292, 504, 12, 18), (268, 526, 8, 13), (224, 572, 6, 9),
                                                   (186, 556, 5, 8)])]
    farstack = Mesa(412, 548, 16, 26, 588, FAR_CHALK_L, FAR_CHALK_D, ledges=1, bed=8, seed=68, mist=(560, 588))
    tower = Mesa(496, 340, 4, 5, 384, ["#F4F2EA", "#ECE9DE"], ["#B4AE9E", "#A39D8E"], ledges=1, bed=8, seed=69,
                 wobble=0, speckle=0, ragged=0, flicker=0)
    cottage = Mesa(516, 370, 9, 9, 384, ["#F4F2EA", "#ECE9DE"], ["#B4AE9E", "#A39D8E"], ledges=1, bed=8, seed=71,
                   wobble=0, speckle=0, ragged=0, flicker=0)
    sea = Water(582, 700, -40, 620, SEA, MOONGLINT, seed=64, mirror=[head, arch, farstack, *stacks], gaps=(0, 1),
                squash=0.5)
    sea.path = (300, 36)
    return [
        Blob([(300, 468, 24, 24)], MOON, top_light=False),
        strip(296, 484, 70, 5, NIGHT_CLOUD),
        strip(470, 322, 86, 7, NIGHT_CLOUD),
        strip(526, 344, 64, 6, NIGHT_CLOUD),
        strip(432, 366, 70, 6, NIGHT_CLOUD),
        Ridge([(-30, 520, 150, 160, 0.8), (130, 552, 90, 70, 0.9)], 586, FAR_IND_L, FAR_IND_D, seed=58, rough=2,
              ribs=0.5, mist=(572, 586), **CALM),
        Ridge([(190, 566, 50, 60, 1.0), (276, 572, 60, 50, 1.0)], 586, FAR_IND_L, FAR_IND_D, seed=57, rough=1,
              mist=(578, 586), **CALM),
        Ridge([(-40, 548, 120, 130, 0.9), (90, 566, 60, 50, 1.0)], 586, INDIGO_L, INDIGO_D, seed=60, rough=2,
              ribs=0.5, mist=(578, 586), **CALM),
        farstack, *stacks[::-1], arch, head,
        Band(448, 660, 376, 388, TURF, seed=65, lens=0.25),
        tower, cottage,
        Ridge([(516, 362, 12, 12, 1.0)], 370, SLATE, SLATE, seed=72, rough=0, smooth=True, flicker=0),
        Blob([(496, 336, 5, 4)], LAMP, top_light=False),
        sea,
        Band(170, 660, 584, 592, FOAM, seed=73, lens=0.15),
        Ridge([(-30, 624, 200, 190, 1.0)], 720, ROCK_L, INDIGO_D, seed=66, rough=2, lean=0.5, smooth=True,
              flicker=0.03, round=True),
        Ridge([(590, 646, 110, 90, 1.0)], 720, ROCK_L, INDIGO_D, seed=74, rough=2, lean=0.5, smooth=True,
              flicker=0.03, round=True),
    ]


# ---- autumn hills: rolling hills stepping back into mist, a grove, poplars, a river ----
H_OLIVE = (["#B7B56C", "#A6A55E", "#959651"], ["#727639", "#606531", "#4F5429"])
FAR_HILL = (VIOLET_L, VIOLET_D)
AUTUMN_TREES = ["#E7A453", "#D8883F", "#BE6E33", "#9E5729"]
CREAM_CLOUD = ["#FBF1DC", "#F6E6C6", "#EFD9B0"]
HILL_MIST = ["#F3ECDC", "#EDE4D0"]


PALE_LILAC = (["#DDDAE8", "#D3CFE1", "#C8C4D9"], ["#B0ABC5", "#A49FBA", "#9893AF"])
STUBBLE = (["#DDB463", "#D2A656", "#C6984B"], ["#B48841", "#A27A39", "#8F6C32"])
RUST_TREES = ["#C9763A", "#AE6230", "#8F4F28"]
DEEP_GREEN = (["#3F583B", "#354D32"], ["#1C2C22", "#132018"])
WOOD = ["#3F5A3C", "#344D33", "#2A402A"]


def valley():
    """Rolling autumn hills in five tiers: two tiers of lilac hills in mist, a big gold field striped with stubble
    beside a smaller gold hill, an olive slope with an orange grove, a river winding out between the rust hill and the
    forest, the poplar clump on the forest crest, a second line of poplars along the river, low clouds on both
    sides."""
    gold = Ridge([(500, 456, 280, 190, 1.0)], 700, H_GOLD[0], H_GOLD[1], seed=81, rough=1.5, ribs=0.2, lean=0.55,
                 smooth=True, flicker=0.02, round=True,
                 bands=[(492, 500, *STUBBLE), (524, 532, *STUBBLE), (556, 564, *STUBBLE), (588, 596, *STUBBLE)])
    return [
        # clouds kept low, on both sides, clear of the text
        strip(474, 380, 80, 7, CREAM_CLOUD),
        Blob([(530, 414, 40, 15), (502, 424, 28, 10), (558, 424, 26, 10)], CREAM_CLOUD),
        strip(380, 424, 46, 5, CREAM_CLOUD),
        strip(96, 440, 66, 6, CREAM_CLOUD),
        strip(206, 452, 46, 5, CREAM_CLOUD),
        dome([(400, 440, 170, 170, 1.0), (560, 452, 120, 120, 1.0)], 560, PALE_LILAC, 79, mist=(528, 560)),
        dome([(60, 486, 150, 140, 1.0), (250, 470, 130, 140, 1.0), (470, 470, 160, 150, 1.0)], 566, FAR_HILL, 80,
             mist=(536, 566)),
        gold,
        dome([(250, 520, 150, 130, 1.0)], 700, H_GOLD, 85),
        dome([(110, 540, 200, 170, 1.0)], 640, H_OLIVE, 84, mist=(616, 640)),
        trees([62, 96, 130], 592, 12, AUTUMN_TREES, seed=45, spread=0.7),
        River(596, 700, 200, 24, 4, 70, RIVER, CREAM, swings=1.4, phase=0.6, seed=46),
        Firs([(166, 640, 52, 5), (184, 642, 40, 4.5), (246, 644, 46, 5)], POPLAR_L, POPLAR_D, tiers=1),
        dome([(-40, 616, 250, 230, 1.0)], 700, H_RUST, 82),
        trees([30, 70, 104], 650, 11, RUST_TREES, seed=50, spread=0.7),
        dome([(470, 612, 280, 240, 1.0)], 700, H_FOREST, 83),
        Firs([(402, 624, 180, 11), (430, 620, 140, 10), (378, 628, 110, 9), (454, 624, 92, 8)], POPLAR_L, POPLAR_D,
             tiers=1),
        dome([(560, 652, 130, 110, 1.0)], 720, DEEP_GREEN, 86),
        trees([520, 552], 684, 11, WOOD, seed=51, spread=0.7),
    ]


SCENES = {"desert": desert, "coast": coast, "valley": valley}

if __name__ == "__main__":
    for name in sys.argv[1:] or list(SCENES):
        j = 0.017 if name == "desert" else 0.05
        render(SCENES[name](), (0, 0, 570, 684), (1140, 1368), 8, clean=True, jitter=j).save(f"out/page-{name}-title.png")
