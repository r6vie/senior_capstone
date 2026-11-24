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
SETTLE = 0.45                                       # a slab's drop and fade into place


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


def schedule(slabs, course, seed=5):
    """When each slab lands. Layers start far to near across START_SPAN, a bigger layer given longer to build;
    within a layer, courses go up from its foot, and the slabs of one course land a little out of step."""
    rng = random.Random(seed)
    layers = sorted({k for k, _r in slabs})
    area = {k: 0 for k in layers}
    rows = {k: [] for k in layers}
    for k, rects in slabs:
        x0, y0, x1, y1, _c = rects[0]
        area[k] += (x1 - x0 + 1) * course
        rows[k].append(y0)
    tot = sum(area.values())
    weights = {k: 0.6 + 3.0 * math.sqrt(area[k] / tot) for k in layers}
    t, start, dur = 0.3, {}, {}
    wsum = sum(weights.values())
    for k in layers:
        start[k] = t
        dur[k] = 1.6 + 5.0 * (weights[k] - 0.6) / 3.0
        t += START_SPAN * weights[k] / wsum
    lo = {k: min(rows[k]) for k in layers}
    hi = {k: max(rows[k]) for k in layers}
    times = []
    for k, rects in slabs:
        y = rects[0][1]
        up = 1 - (y - lo[k]) / max(1, hi[k] - lo[k])          # 0 at the layer's foot, 1 at its top
        times.append(start[k] + dur[k] * (0.85 * up + 0.15 * rng.random()))
    return times


def ease(x):
    x = min(max(x, 0.0), 1.0)
    return 1 - (1 - x) ** 3


def frame(t, slabs, times, size, paper, course, k=1.0):
    W, H = size
    img = np.empty((H, W, 3), np.float32)
    img[:] = paper
    t = t / k
    settle = SETTLE
    for (layer, rects), t0 in zip(slabs, times):
        u = (t - t0) / settle
        if u <= 0:
            continue
        a = ease(u)
        dy = int(round(-course * 0.9 * (1 - a)))             # it drops the last part of a course into place
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
    """The ten strata set 1 covers: (scene, render arguments). Only the lake is wired up for the demo."""
    import final
    return {"lake": (final.cover(), dict(viewport=(0, 0, 236, 344), size=(472, 688), course=8,
                                          paper=(255, 255, 255), clean=True))}


if __name__ == "__main__":
    key = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "lake"
    scene, kw = covers()[key]
    course, size, paper = kw["course"], kw["size"], kw.get("paper", strata.PAPER)
    slabs, final_img = record(scene, kw["viewport"], size, course,
                              **{a: b for a, b in kw.items() if a not in ("viewport", "size", "course")})
    times = schedule(slabs, course)
    print(key, "slabs:", len(slabs), "last lands at", round(max(times) + SETTLE, 2), "s")
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
