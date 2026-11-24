"""A strata cover laying itself (Josef, 2026-11-23: the strata covers animate too, in the design studio and when they
are one of your picks, "so it's all nice and unified", the timing matching the watercolours, in a way "cool and
appropriate for that art style").

Watercolour arrives as wet paint spreading; strata is built, so it arrives the way it is made: slab by slab. The
renderer runs once with every slab recorded (its rectangles). Playback lays them back in one sweep from the foot of
the cover to the top, racing at first and slowing as it climbs; each slab appears a little above its course and
drifts down into place, the top ones settling slowest. The schedule is written on the watercolours' clock
(paint_anim.py, settled by ~11.7 s, the cover at 13.5 s) and played at QUICK (0.3) of it: about 4 s, the same as the
watercolours' quick version. The last frame is the cover, pixel for pixel.

python3 strata_anim.py [key ...] [--preview] -> out/anim-<key>/quick_XXXX.png (24 fps, about 4 s): the only version.
Josef, 2026-11-23: strata plays fast everywhere it appears (the reveal, the picks, the studio), never slow."""
import math
import os
import random
import sys
import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, ".")
import strata

PAINT_END, QUICK = 13.5, 0.3                         # the watercolours' clock (art/watercolor/paint_anim.py)
QUICK_FPS = 24
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
    """The ten strata set 1 covers, by their set keys: (scene, render arguments), exactly as each script renders its
    472 x 688 cover (set-1/covers/<key>.webp)."""
    import final
    import covers_more
    import covers_new
    import covers_us
    import fields
    base = dict(viewport=(0, 0, 236, 344), size=(472, 688), course=8, paper=(255, 255, 255), clean=True)
    return {
        "lake": (final.cover(), base),
        "desert": (covers_more.desert(), dict(base, jitter=0.017)),
        "coast": (covers_more.coast(), dict(base, jitter=0.05)),
        "valley": (covers_more.valley(), dict(base, jitter=0.05)),
        "karst": (covers_new.karst(), dict(base, jitter=0.04)),
        "winter": (covers_new.aurora(), dict(base, jitter=0.04)),
        "lagoon": (covers_new.lagoon(), dict(base, jitter=0.04)),
        "city": (covers_us.city(), dict(base, jitter=0.04)),
        "forest": (covers_us.forest(), dict(base, jitter=0.04)),
        "fields": (fields.cover(), dict(base, jitter=0.04)),
    }


if __name__ == "__main__":
    # Josef, 2026-11-23: strata never plays slow (the slow timing is only watercolour's, on the sign-in intro); the
    # book reveal, the picks and the design studio all use this quick build
    keys = [a for a in sys.argv[1:] if not a.startswith("-")] or list(covers())
    allc = covers()
    for key in keys:
        scene, kw = allc[key]
        course, size, paper = kw["course"], kw["size"], kw.get("paper", strata.PAPER)
        slabs, final_img = record(scene, kw["viewport"], size, course,
                                  **{a: b for a, b in kw.items() if a not in ("viewport", "size", "course")})
        times = schedule(slabs)
        d = f"out/anim-{key}"
        os.makedirs(d, exist_ok=True)
        for f in os.listdir(d):
            os.remove(f"{d}/{f}")
        step = 12 if "--preview" in sys.argv else 1
        for n in range(0, int(PAINT_END * QUICK * QUICK_FPS) + 1, step):
            Image.fromarray(frame(n / QUICK_FPS, slabs, times, size, paper, course, k=QUICK)).save(f"{d}/quick_{n:04d}.png")
        done = frame(PAINT_END, slabs, times, size, paper, course)
        ref = np.asarray(Image.open(f"set-1/covers/{key}.webp").convert("RGB")).astype(int)
        print(key, "slabs", len(slabs), "settled by", round(QUICK * max(t0 + st for t0, st in times), 2), "s;",
              "finished frame vs set-1 cover: max diff", int(np.abs(done.astype(int) - ref).max()), flush=True)
