"""A cover painting itself (Josef, 2026-11-23: "animate the art that we already have being drawn on ... one of the
colors starts slowly being drawn in, dropping in, like watercolor art would look like. And then in the end, just
like fades, and then a new cover comes to life"). For the blank book on the Getting started screens.

The cover's own scene function runs once with the engine's wash and lift recorded: every glaze is kept as the
absorbance it adds (or, for a lift, removes), in the order it was painted. Playback lays the glazes back down in that
order. Each one arrives as wet paint does: it lands where the brush first touches its shape and spreads out along an
uneven wet front across the shape, a little soft while wet; a big wash (the sky) spreads slowly, a small patch
quickly; the next one starts before the last has finished. When the picture is complete it rests, then washes back
to the paper, and the next cover begins. The loop's last frame is the clean paper the first frame starts from.

python3 paint_anim.py lake [--preview] -> out/anim-<scene>/frame_XXXX.png (472 x 688) and out/anim-<scene>-poster.png"""
import math
import os
import sys
import numpy as np
import cv2

sys.path.insert(0, ".")
import paint
from paint import Paper

OUT_W, OUT_H = 472, 688
FPS = 12
START_SPAN = 10.0         # every glaze has started by now (was ~19 s): more of them spread at once
PAINT_END = 13.5          # by now every glaze has landed (the last ends at ~12.3 s)
REST = 5.0                # the finished cover rests
FADE = 5.0                # it washes back to the paper
BLANK = 1.5               # a breath of clean paper before the next cover


def record(scene):
    """Run a scene with every wash and lift recorded as (absorbance delta at output size, the mask it was laid
    through, at output size)."""
    steps = []
    orig_wash, orig_lift = Paper.wash, Paper.lift

    def absorb(img):
        return -np.log(np.clip(img / paint.PAPER, 1e-4, 1))

    def shrink(a):
        return cv2.resize(a, (OUT_W, OUT_H), interpolation=cv2.INTER_AREA)

    def wrap(fn):
        def inner(self, mask, *a, **k):
            before = absorb(self.img)
            out = fn(self, mask, *a, **k)
            delta = absorb(self.img) - before
            m = np.asarray(mask, np.float32)
            if np.abs(delta).max() > 0.01:
                steps.append((shrink(delta).astype(np.float32), shrink(m)))
            return out
        return inner

    Paper.wash, Paper.lift = wrap(orig_wash), wrap(orig_lift)
    try:
        p = scene()
    finally:
        Paper.wash, Paper.lift = orig_wash, orig_lift
    blank = Paper(seed=1)
    blank.finish()
    paper = cv2.resize(blank.img.astype(np.float32), (OUT_W, OUT_H), interpolation=cv2.INTER_AREA)
    final = cv2.resize(p.img.astype(np.float32), (OUT_W, OUT_H), interpolation=cv2.INTER_AREA)
    return paper, final, steps


def fronts(steps, seed=3):
    """For each glaze: how far the wet front must travel to reach each pixel (0 where the brush lands, 1 at the far
    edge of its shape), warped so the front is ragged. The brush lands near the top of the shape, a little off
    centre, as a painter starts a wash at its top and lets it run down."""
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:OUT_H, 0:OUT_W].astype(np.float32)
    noise = cv2.GaussianBlur(cv2.resize(rng.random((OUT_H // 70 + 3, OUT_W // 70 + 3)).astype(np.float32),
                                        (OUT_W, OUT_H), interpolation=cv2.INTER_CUBIC), (0, 0), 6)   # broad lobes
    out = []
    for delta, m in steps:
        w = np.abs(delta).sum(axis=2) * (m > 0.02)
        tot = w.sum()
        if tot <= 0:
            out.append((np.zeros((OUT_H, OUT_W), np.float32), 0.0))
            continue
        cy = (yy * w).sum() / tot
        cx = (xx * w).sum() / tot
        ys = yy[w > w.max() * 0.2]
        top = np.percentile(ys, 15) if len(ys) else cy
        sx, sy = cx + rng.uniform(-0.15, 0.15) * OUT_W * 0.3, top * 0.6 + cy * 0.4
        d = np.sqrt((xx - sx) ** 2 + ((yy - sy) * 1.15) ** 2)
        reach = np.percentile(d[w > w.max() * 0.05], 98) if (w > w.max() * 0.05).any() else d.max()
        r = d / max(reach, 1) + 0.28 * (noise - 0.5)
        area = (m > 0.3).mean()
        out.append((r.astype(np.float32), float(area)))
    return out


def schedule(steps, fr):
    """Start time and spread time for each glaze (Josef, 2026-11-23: no empty gaps waiting their turn, "shorten the
    time between the individual ones so that more are running at the same time", the spreading speed unchanged).
    The big ground washes (the sky, the lake's ground, the far range) are pulled to the front, so no stretch of bare
    paper sits waiting for its first colour; everything else keeps its painting order, and the lifts stay after
    the paint they lift. Starts are packed into START_SPAN, so several glazes spread at once."""
    order = []
    for i, ((delta, _m), (_r, a)) in enumerate(zip(steps, fr)):
        is_lift = delta.sum() < 0
        big = a > 0.12 and not is_lift
        order.append((i * 0.25 if big else i, i))
    order.sort()
    weights = [0.6 + 3.0 * math.sqrt(fr[i][1]) for _k, i in order]
    total = sum(weights)
    out = [None] * len(steps)
    t = 0.3
    for (_k, i), w in zip(order, weights):
        dur = 1.6 + 5.0 * (w - 0.6) / 3.0                  # the same spreading speed as before
        out[i] = (t, dur)
        t += START_SPAN * w / total
    return out


def soft(x):
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def render(t, paper, steps, fr, sched):
    period = PAINT_END + REST + FADE + BLANK
    t = t % period
    total = np.zeros((OUT_H, OUT_W, 3), np.float32)
    for (delta, _m), (r, _a), (t0, dur) in zip(steps, fr, sched):
        if t < t0:
            continue
        u = (t - t0) / dur
        front = 1 - (1 - min(u, 1.0)) ** 2.2                   # quick at first, slowing as it spreads
        reveal = np.clip((front * 1.12 - r) / 0.05, 0, 1)
        wet = 1 - soft((t - t0 - dur) / 2.0)                    # still wet: slightly softer and paler
        a = delta * reveal[..., None]
        if wet > 0.01:
            a = a * (1 - 0.18 * wet)
        total += a
    fade = soft((t - PAINT_END - REST) / FADE)
    img = paper * np.exp(-np.maximum(total, 0) * (1 - fade))   # a lift never brightens paper it hasn't reached
    return (np.clip(img, 0, 1) * 255).astype(np.uint8)


if __name__ == "__main__":
    from PIL import Image
    name = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") else "lake"
    import abstract
    scenes = dict(abstract.SCENES)
    paper, final, steps = record(scenes[name])
    print("glazes recorded:", len(steps))
    fr = fronts(steps)
    sched = schedule(steps, fr)
    period = PAINT_END + REST + FADE + BLANK
    os.makedirs(f"out/anim-{name}", exist_ok=True)
    for f in os.listdir(f"out/anim-{name}"):
        os.remove(f"out/anim-{name}/{f}")
    n = int(period * FPS)
    step = 24 if "--preview" in sys.argv else 1
    for k in range(0, n, step):
        Image.fromarray(render(k / FPS, paper, steps, fr, sched)).save(f"out/anim-{name}/frame_{k:04d}.png")
    Image.fromarray(render(PAINT_END + 1.0, paper, steps, fr, sched)).save(f"out/anim-{name}-poster.png")
    full = (np.clip(final, 0, 1) * 255).astype(np.uint8)
    Image.fromarray(full).save(f"out/anim-{name}-target.png")
    print("period", period, "frames", n)
