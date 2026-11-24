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


def schedule(slabs, course, plan, scene, scale, seed=5):
    """When each slab lands, following the terrain (Josef, 2026-11-23: "understand the terrain and the layout of the
    image"). plan gives each layer of the scene a start, a duration and how it grows:
      rise    land and things that stand on it build up from their foot, course by course, to their top
      sweep   a cloud drifts in from the left
      mirror  water reflecting a ridge: each row of the reflection lands just after the ridge row it mirrors, so
              the reflection grows down the lake as the mountain grows up; water that mirrors nothing spreads
              from the shoreline toward us
    Inside a course the slabs land a little out of step."""
    rng = random.Random(seed)
    rows = {}
    for k, rects in slabs:
        rows.setdefault(k, []).append(rects[0][1])
    lo = {k: min(v) for k, v in rows.items()}
    hi = {k: max(v) for k, v in rows.items()}

    def rise(k, y):
        st, du = plan[k][0], plan[k][1]
        return st + du * (1 - (y - lo[k]) / max(1, hi[k] - lo[k]))

    times = []
    for k, rects in slabs:
        st, du, mode = plan[k][:3]
        x0, y, x1, _y1, _c = rects[0]
        if mode == "rise":
            t = rise(k, y)
        elif mode == "sweep":
            t = st + du * ((x0 + x1) / 2) / scale[0]
        elif mode == "mirror":
            src = plan[k][3]
            w = scene[k]
            yw = (y + course / 2) / scale[1] * 344             # world units (the cover is 344 tall)
            my = 2 * w.y0 - yw + (yw - w.y0) * w.squash        # the ridge row this water row reflects
            myp = my / 344 * scale[1]
            if lo[src] <= myp <= hi[src]:
                t = rise(src, myp) + 0.35
            else:
                t = st + du * (y - lo[k]) / max(1, hi[k] - lo[k])
        else:
            t = st
        times.append(t + rng.uniform(-0.18, 0.18))
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
    """The strata covers with their choreography. Only the lake is wired up for the demo. The lake's layers
    (final.cover): 0 the coral sun, 1 the far haze ranges, 2 a cloud, 3 the teal massif, 4 the sage hill on the left,
    5 the lake (mirroring the massif), 6 the near shore, 7 its trees."""
    import final
    plan = {1: (0.3, 4.0, "rise"),                 # the horizon first: far haze rising from it
            3: (1.0, 7.5, "rise"),                 # the massif, from its foot to the stone cap
            5: (2.0, 8.0, "mirror", 3),            # the lake: the reflection grows down as the massif grows up
            4: (3.0, 4.0, "rise"),                 # the nearer sage hill
            0: (6.5, 2.8, "rise"),                 # the sun climbs up behind the peak once the mountain stands
            2: (8.0, 2.2, "sweep"),                # a cloud drifts in
            6: (8.6, 2.4, "rise"),                 # the near shore
            7: (9.6, 2.4, "rise")}                 # its trees grow up last
    return {"lake": (final.cover(), dict(viewport=(0, 0, 236, 344), size=(472, 688), course=8,
                                          paper=(255, 255, 255), clean=True), plan)}


if __name__ == "__main__":
    key = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "lake"
    scene, kw, plan = covers()[key]
    course, size, paper = kw["course"], kw["size"], kw.get("paper", strata.PAPER)
    slabs, final_img = record(scene, kw["viewport"], size, course,
                              **{a: b for a, b in kw.items() if a not in ("viewport", "size", "course")})
    times = schedule(slabs, course, plan, scene, size)
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
