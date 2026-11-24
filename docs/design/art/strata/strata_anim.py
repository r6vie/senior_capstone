"""A strata cover laying itself (Josef, 2026-11-23: the strata covers animate too, in the design studio and when they
are one of your picks, "so it's all nice and unified", the timing matching the watercolours, in a way "cool and
appropriate for that art style").

Watercolour arrives as wet paint spreading; strata is built, so it arrives the way it is made: slab by slab. The
renderer runs once with every slab recorded (its rectangles and which layer of the scene it belongs to). Playback
lays the scene's layers far to near, in the renderer's own order, each one built up from its bottom course to its
top, like masonry or settling sediment; inside a course the slabs land a little out of step. Each slab drops a
little way into its course and settles, fading in as it does. The clock is the watercolours' (paint_anim.py): every
layer has started by 10 s, everything has landed by about 12.5 s, the reveal ends on the finished cover at 13.5 s,
and the design studio's quick version is the same build at 0.3 of the time.

python3 strata_anim.py lake [--preview] -> out/anim-<key>/reveal_XXXX.png (12 fps), quick_XXXX.png (24 fps),
out/anim-<key>-poster.png"""
import math
import os
import random
import sys
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, ".")
import strata

START_SPAN, PAINT_END, QUICK = 10.0, 13.5, 0.3       # the watercolours' clock (art/watercolor/paint_anim.py)
FPS, QUICK_FPS = 12, 24
SWEEP, EASE = 9.0, 2.4                              # the front reaches the top at 9 s, racing first, slowing last
SETTLE_FAST, SETTLE_SLOW = 0.8, 2.2                 # a slab's drift into place: quick at the foot, slow at the top
DROP = 1.6                                          # how far above its course it appears, in courses


def record(scene, viewport, size, course, **kw):
    """Render with every rectangle recorded: [(layer index, [(x0, y0, x1, y1, rgb), ...]), ...] per slab, in the
    order they were laid, and the finished image."""
    slabs = []
    current = {"depth": 0}
    wrapped = []
    for k, layer in enumerate(scene):
        orig = layer.colour

        def colour(*a, _orig=orig, _k=k, **kk):
            # the water asks the mountain it mirrors for its colour: only the outermost call starts a slab
            if current["depth"] == 0:
                slabs.append((_k, []))
            current["depth"] += 1
            try:
                return _orig(*a, **kk)
            finally:
                current["depth"] -= 1
        layer.colour = colour
        wrapped.append((layer, orig))
    orig_rect = ImageDraw.ImageDraw.rectangle

    def rect(self, xy, fill=None, **kk):
        if slabs and fill is not None:
            (x0, y0), (x1, y1) = (xy[0], xy[1]) if len(xy) == 2 else ((xy[0], xy[1]), (xy[2], xy[3]))
            slabs[-1][1].append((int(x0), int(y0), int(x1), int(y1), fill))
        return orig_rect(self, xy, fill=fill, **kk)

    ImageDraw.ImageDraw.rectangle = rect
    try:
        img = strata.render(scene, viewport, size, course, **kw)
    finally:
        ImageDraw.ImageDraw.rectangle = orig_rect
        for layer, orig in wrapped:
            layer.colour = orig
    return [s for s in slabs if s[1]], img


def schedule(slabs, seed=5):
    """When each slab lands and how long it takes to settle (Josef, 2026-11-23: bottom to top, "nice and smooth";
    then: "at first it's a faster spread, so more blocks appear at the beginning and then it slows down and the
    last one settle in more slower", lasting as long as the watercolours). The front races up the lower cover and
    slows toward the top (an ease-out over SWEEP seconds), and each slab's settle lengthens from SETTLE_FAST at the
    foot to SETTLE_SLOW at the top, so the build pushes in and then calms down. The slabs of a course land a little
    out of step, so the front is soft, not a ruled line. Returns (start, settle) per slab."""
    rng = random.Random(seed)
    ys = [rects[0][1] for _k, rects in slabs]
    top, bottom = min(ys), max(ys)
    out = []
    for y in ys:
        r = (bottom - y) / max(1, bottom - top)                 # 0 at the foot, 1 at the top
        x = 1 - (1 - r) ** (1 / EASE)                           # the inverse of an ease-out: high rows come late
        settle = SETTLE_FAST + (SETTLE_SLOW - SETTLE_FAST) * r
        out.append((0.3 + SWEEP * x + rng.uniform(-0.25, 0.25) * (0.4 + r), settle))
    return out


def ease(x):
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3


def frame(t, slabs, times, size, paper, course, k=1.0):
    """A slab appears a little above its course (DROP courses), fading in over the first third of its settle while
    it drifts down, and slows into place (an ease-out), so the cover seems to settle rather than pop."""
    W, H = size
    img = np.empty((H, W, 3), np.float32)
    img[:] = paper
    t = t / k
    for (layer, rects), (t0, settle) in zip(slabs, times):
        u = (t - t0) / settle
        if u <= 0:
            continue
        a = min(1.0, u / 0.35)
        a = a * a * (3 - 2 * a)
        dy = int(round(-course * DROP * (1 - ease(u))))
        for x0, y0, x1, y1, c in rects:
            ya, yb = max(0, y0 + dy), min(H, y1 + 1 + dy)
            if yb <= ya:
                continue
            reg = img[ya:yb, x0:x1 + 1]
            if a >= 1:
                reg[:] = c
            else:
                reg[:] = reg * (1 - a) + np.array(c, np.float32) * a
    return np.clip(img, 0, 255).astype(np.uint8)


def covers():
    """The strata set 1 covers and how each is rendered. Only the lake is wired up for the demo."""
    import final
    return {"lake": (final.cover(), dict(viewport=(0, 0, 236, 344), size=(472, 688), course=8,
                                          paper=(255, 255, 255), clean=True))}


if __name__ == "__main__":
    key = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "lake"
    scene, kw = covers()[key]
    course, size, paper = kw["course"], kw["size"], kw.get("paper", strata.PAPER)
    slabs, final_img = record(scene, kw["viewport"], size, course,
                              **{a: b for a, b in kw.items() if a not in ("viewport", "size", "course")})
    times = schedule(slabs)
    print(key, "slabs:", len(slabs), "last settles at", round(max(t0 + st for t0, st in times), 2), "s")
    d = f"out/anim-{key}"
    os.makedirs(d, exist_ok=True)
    for f in os.listdir(d):
        os.remove(f"{d}/{f}")
    step = 12 if "--preview" in sys.argv else 1
    for n in range(0, int(PAINT_END * FPS) + 1, step):
        Image.fromarray(frame(n / FPS, slabs, times, size, paper, course)).save(f"{d}/reveal_{n:04d}.png")
    for n in range(0, int(PAINT_END * QUICK * QUICK_FPS) + 1, step):
        Image.fromarray(frame(n / QUICK_FPS, slabs, times, size, paper, course, k=QUICK)).save(f"{d}/quick_{n:04d}.png")
    done = frame(PAINT_END, slabs, times, size, paper, course)
    Image.fromarray(done).save(f"out/anim-{key}-poster.png")
    ref = np.asarray(final_img.convert("RGB")).astype(int)
    print(key, "finished frame vs the cover: max diff", int(np.abs(done.astype(int) - ref).max()))
