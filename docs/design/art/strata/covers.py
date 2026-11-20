import sys; sys.path.insert(0,'.')
from strata import render
from scenes import COVER_SCENES, COVER_W, COVER_H, lake, LAKE_COVER
from PIL import Image

SIZES = {"lg": ((472, 688), 8), "md": ((244, 356), 4), "sm": ((184, 272), 4)}

def go(name, scene, vp, fade_from, fade_to):
    for size, ((w, h), course) in SIZES.items():
        k = h / (vp[3] - vp[1])
        fade = [("y", fade_from * k, fade_to * k)]
        render(scene, vp, (w, h), course, fade=fade, seed=sum(map(ord, name)), paper=(255, 255, 255)).save(f"out/{name}-{size}.png")

for name, fn in COVER_SCENES.items():
    go(name, fn(), (0, 0, COVER_W, COVER_H), 256, 300)
# the lake book: same place as its hero, drawn for each size (lg comes from hero.py, aligned)
for size in ("md", "sm"):
    (w, h), course = SIZES[size]
    k = h / 344
    render(lake(), LAKE_COVER, (w, h), course, fade=[("y", 256 * k, 300 * k)], seed=3, paper=(255, 255, 255)).save(f"out/lake-{size}.png")

# contact sheet
names = ["lake"] + list(COVER_SCENES)
sheet = Image.new("RGB", (len(names) * 260 + 20, 700), (230, 230, 225))
for i, n in enumerate(names):
    src = f"out/{n}-md.png"
    sheet.paste(Image.open(src), (20 + i * 260, 20))
    sheet.paste(Image.open(f"out/{n}-sm.png"), (20 + i * 260, 400))
sheet.save("out/sheet.png")
