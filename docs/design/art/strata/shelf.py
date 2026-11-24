import sys
sys.path.insert(0, ".")
from strata import render
from scenes import COVER_SCENES
for name, fn in COVER_SCENES.items():
    for size, ((w, h), course) in {"md": ((244, 356), 3), "sm": ((184, 272), 3)}.items():
        k = h / 344
        render(fn(), (0, 0, 236, 344), (w, h), course, fade=[("y", 262 * k, 300 * k)], seed=sum(map(ord, name)),
               paper=(255, 255, 255), brick=(1.4, 5.5)).save(f"out/{name}-{size}.png")
