"""Cover design 1, "the lake": world 236 x 344. Title on paper above y 118, full name on paper below y 300."""
import sys
sys.path.insert(0, ".")
from PIL import Image
from strata import Ridge, Blob, Water, Band, grove, render
from scenes import COBALT, GLINT, TEAL_LIT, TEAL_DARK, CORAL, RUST, CLOUD, STONE_LIT, STONE_DARK, LEAF, SHORE

BLUE_LIT = ["#7FA6CC", "#5F8DBE", "#4A79AD", "#3B679A"]
BLUE_DARK = ["#33598A", "#284A77", "#1E3B62", "#162E4E"]


def scene():
    teal = Ridge([(70, 124, 88, 118, 1.35), (-14, 186, 56, 76, 1.1)], 238, TEAL_LIT, TEAL_DARK, seed=13, rough=2)
    coral = Ridge([(198, 148, 72, 88, 1.25)], 238, CORAL, RUST, seed=12, rough=2,
                  bands=[(196, 202, STONE_LIT, STONE_DARK), (218, 222, STONE_LIT, STONE_DARK)])
    far = Ridge([(134, 170, 66, 76, 1.1), (240, 180, 60, 70, 1.0)], 236, BLUE_LIT, BLUE_DARK, seed=11, rough=2)
    pale = Ridge([(18, 162, 50, 60, 1.1), (110, 182, 40, 50, 1.0)], 236, STONE_LIT, STONE_DARK, seed=19, rough=2)
    return [
        Blob([(170, 158, 22, 22)], CORAL, top_light=False),
        pale,
        Blob([(28, 150, 26, 4), (52, 144, 16, 3)], CLOUD),
        far,
        coral,
        teal,
        Blob([(132, 206, 40, 6), (176, 212, 36, 5), (100, 214, 24, 4)], CLOUD),
        Water(238, 288, -20, 260, COBALT, GLINT, seed=21, mirror=[pale, far, coral, teal]),
        Band(-20, 84, 262, 278, SHORE, seed=31, lens=0.7),
        *grove([4, 22, 40, 58, 74], 270, 8, LEAF, seed=41),
        Band(168, 260, 272, 288, SHORE, seed=32, lens=0.7),
        *grove([182, 202, 222, 240], 280, 7, LEAF, seed=42),
    ]


SIZES = {"lg": ((472, 688), 4), "md": ((244, 356), 3), "sm": ((184, 272), 3)}
if __name__ == "__main__":
    for name, ((w, h), course) in SIZES.items():
        k = h / 344
        img = render(scene(), (0, 0, 236, 344), (w, h), course, fade=[("y", 284 * k, 312 * k)], seed=5, brick=(1.4, 5.5),
                     paper=(255, 255, 255))
        img.save(f"out/lake-{name}.png")
    Image.open("out/lake-lg.png").resize((944, 1376), Image.NEAREST).crop((0, 400, 944, 1200)).save("out/lake-zoom.png")
