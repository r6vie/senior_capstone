import { type RefObject, useEffect } from "react";

// A shelf row moves a book at a time. Native scrolling coasts as far as the flick sends it, so a small
// flick could pass three books; snap points stop it, but each settle is slow and a second flick waits
// for it. Here a slow drag can reach only the next book, a flick moves exactly one, a hard fling two,
// and a new flick starts from where the last was heading, so quick flicks chain without waiting.

const FLICK = 0.25; // px per ms: faster than this is a flick, not a drag
const FLING = 3.2; // px per ms: only a hard fling goes two books; an ordinary quick flick goes one
const SETTLE_MS = 220;
const GESTURE_GAP_MS = 140; // wheel events further apart than this start a new gesture
const WHEEL_START = 8; // px of horizontal travel before a trackpad swipe counts

function positions(row: HTMLElement): number[] {
  const padding = Number.parseFloat(getComputedStyle(row).paddingLeft) || 0;
  const rowLeft = row.getBoundingClientRect().left;
  const max = row.scrollWidth - row.clientWidth;
  const stops = [...row.children].map((child) => {
    const left = (child as HTMLElement).getBoundingClientRect().left - rowLeft + row.scrollLeft - padding;
    return Math.min(Math.max(0, left), max);
  });
  // Books near the end share the last reachable stop; keep one of each.
  return stops.filter((stop, index) => index === 0 || stop > (stops[index - 1] as number) + 1);
}

function nearest(stops: number[], at: number): number {
  let best = 0;
  stops.forEach((stop, index) => {
    if (Math.abs(stop - at) < Math.abs((stops[best] as number) - at)) best = index;
  });
  return best;
}

export function useBookStepping(ref: RefObject<HTMLElement | null>) {
  useEffect(() => {
    const row = ref.current;
    if (!row) return;
    const reduceMotion = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;

    let frame = 0;
    // Where the row is heading, so the next gesture counts from there rather than from mid-glide. Only
    // while that glide could still be running: after it, the row's own position is the truth.
    let heading: number | null = null;
    let headingSince = 0;

    function stop() {
      cancelAnimationFrame(frame);
      frame = 0;
    }

    function glide(index: number, stops: number[]) {
      stop();
      const clamped = Math.min(Math.max(0, index), stops.length - 1);
      heading = clamped;
      headingSince = performance.now();
      const to = stops[clamped] as number;
      const from = (row as HTMLElement).scrollLeft;
      if (reduceMotion || Math.abs(to - from) < 1) {
        (row as HTMLElement).scrollLeft = to;
        heading = null;
        return;
      }
      const started = performance.now();
      const tick = (now: number) => {
        const t = Math.min(1, (now - started) / SETTLE_MS);
        const eased = 1 - (1 - t) ** 3;
        (row as HTMLElement).scrollLeft = from + (to - from) * eased;
        if (t < 1) frame = requestAnimationFrame(tick);
        else {
          frame = 0;
          heading = null;
        }
      };
      frame = requestAnimationFrame(tick);
    }

    function origin(stops: number[]): number {
      const fresh = heading !== null && performance.now() - headingSince < SETTLE_MS + 60;
      return fresh && heading !== null ? heading : nearest(stops, (row as HTMLElement).scrollLeft);
    }

    // ---------- Touch: the row follows the finger for about a book, then resists ----------
    let touch: {
      x: number;
      y: number;
      left: number;
      index: number;
      stops: number[];
      samples: [number, number][];
    } | null = null;
    let horizontal: boolean | null = null;

    function onTouchStart(event: TouchEvent) {
      const point = event.touches[0];
      if (!point || event.touches.length > 1) return;
      const stops = positions(row as HTMLElement);
      const index = origin(stops);
      stop();
      touch = {
        x: point.clientX,
        y: point.clientY,
        left: (row as HTMLElement).scrollLeft,
        index,
        stops,
        samples: [[performance.now(), point.clientX]],
      };
      horizontal = null;
    }

    function onTouchMove(event: TouchEvent) {
      const point = event.touches[0];
      if (!touch || !point) return;
      const dx = point.clientX - touch.x;
      const dy = point.clientY - touch.y;
      if (horizontal === null) {
        if (Math.abs(dx) < 6 && Math.abs(dy) < 6) return;
        horizontal = Math.abs(dx) > Math.abs(dy);
      }
      if (!horizontal) return; // the page scrolls as usual
      event.preventDefault();
      touch.samples.push([performance.now(), point.clientX]);
      if (touch.samples.length > 6) touch.samples.shift();
      // One book's width follows the finger; past that the row gives way less and less.
      const { stops, index } = touch;
      const step =
        Math.abs(((stops[index + 1] ?? stops[index - 1]) as number) - (stops[index] as number)) || 120;
      const travel = -dx;
      const eased =
        Math.abs(travel) <= step
          ? travel
          : Math.sign(travel) * (step + Math.sqrt(Math.abs(travel) - step) * 4);
      (row as HTMLElement).scrollLeft = touch.left + eased;
    }

    function onTouchEnd() {
      if (!touch) return;
      const { stops, index, samples } = touch;
      touch = null;
      if (!horizontal) {
        heading = null;
        return;
      }
      const [first, last] = [samples[0], samples[samples.length - 1]];
      const elapsed = first && last ? last[0] - first[0] : 0;
      const velocity = first && last && elapsed > 0 ? (first[1] - last[1]) / elapsed : 0; // + is towards later books
      const speed = Math.abs(velocity);
      let target: number;
      if (speed > FLICK) {
        target = index + Math.sign(velocity) * (speed > FLING ? 2 : 1);
      } else {
        // A slow drag settles on whichever of this book or its neighbours is nearest.
        target = Math.min(Math.max(nearest(stops, (row as HTMLElement).scrollLeft), index - 1), index + 1);
      }
      glide(target, stops);
    }

    // ---------- Wheel and trackpad: one book per swipe, however long the swipe's momentum lasts ----------
    let lastWheel = 0;
    let travel = 0;
    let stepped = false;
    let lastDelta = 0;
    let peak = 0;

    function onWheel(event: WheelEvent) {
      const dx = event.deltaX || (event.shiftKey ? event.deltaY : 0);
      if (Math.abs(dx) <= Math.abs(event.deltaY) && !event.shiftKey) return; // vertical: the page scrolls
      event.preventDefault();
      const now = performance.now();
      // A mouse wheel's notch: big, and spaced apart. Trackpad momentum comes every frame, and a fast
      // swipe's deltas can be big too, so size alone would count it twice.
      const notch = event.deltaMode !== 0 || (Math.abs(dx) >= 100 && now - lastWheel >= 30);
      // A new swipe: a pause, or speed picking up again after the last swipe's momentum had faded. A
      // swipe's own ramp-up at the start isn't one: its speed hasn't fallen yet.
      const size = Math.abs(dx);
      const fading = Math.abs(lastDelta) < peak * 0.6;
      const fresh =
        now - lastWheel > GESTURE_GAP_MS ||
        Math.sign(dx) !== Math.sign(lastDelta) ||
        (stepped && fading && size > Math.abs(lastDelta) * 1.6 && size > 4);
      lastWheel = now;
      lastDelta = dx;
      if (fresh) {
        travel = 0;
        stepped = false;
        peak = 0;
      }
      peak = Math.max(peak, size);
      if (stepped && !notch) return;
      travel += dx;
      if (notch || Math.abs(travel) >= WHEEL_START) {
        const stops = positions(row as HTMLElement);
        glide(origin(stops) + Math.sign(travel), stops);
        stepped = true;
        travel = 0;
      }
    }

    row.addEventListener("touchstart", onTouchStart, { passive: true });
    row.addEventListener("touchmove", onTouchMove, { passive: false });
    row.addEventListener("touchend", onTouchEnd);
    row.addEventListener("touchcancel", onTouchEnd);
    row.addEventListener("wheel", onWheel, { passive: false });
    return () => {
      stop();
      row.removeEventListener("touchstart", onTouchStart);
      row.removeEventListener("touchmove", onTouchMove);
      row.removeEventListener("touchend", onTouchEnd);
      row.removeEventListener("touchcancel", onTouchEnd);
      row.removeEventListener("wheel", onWheel);
    };
  }, [ref]);
}
