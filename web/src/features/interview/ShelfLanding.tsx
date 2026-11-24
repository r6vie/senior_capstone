import { type CSSProperties, useEffect, useLayoutEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { artFor, loadArt } from "../../ui/art/bookArt";
import { BookObject } from "../discovery/BookObject";
import "./ShelfLanding.css";

// The done screen's shelf: the member's book lands among other members' books and its cover arrives (board
// StartReveal, step 7, and its phone frame; Josef approved the motion). Only the shelf: the Librarian's line, the
// words and the buttons stay with the interview page.
//
// 1. Flight (about 1.6 s): the closed white book starts at `from`, turns to face the member and travels down to the
//    shelf, while its neighbours slide apart to open its gap. One soft ease-out, no bounce or overshoot; its dot
//    shadow comes as it touches the shelf. Transforms only (as BookReader), so it runs on the compositor.
// 2. Paint (about 4 s): the cover's quick clip plays exactly where the cover art sits, under the title and name.
//    Its last frame is the cover, so on `ended` the still cover takes its place with no jump.
// Reduced motion: a short crossfade to the finished shelf, with the still cover.

export type LandingBook = { id: string; design?: string | null; title: string; authorName: string };

// flight: travelling to the shelf, still white. white: on the shelf, still white, while the clip gets ready.
// paint: the clip plays. done: the still cover.
type Phase = "flight" | "white" | "paint" | "done";

const FLIGHT_MS = 1600;
// The neighbours make room first, so the gap is open before the book reaches it.
const PART_MS = 900;
// One soft ease-out, from the flight easing's family in BookReader.css: quick off the mark, long and soft into place.
const SETTLE = "cubic-bezier(0.25, 0, 0.1, 1)";
// The book turns to face the member about its spine early in its flight, on its own shorter curve.
const TURN_DEG = -18;
const TURN_MS = 640;
const TURN_EASE = "cubic-bezier(0.38, 0, 0.12, 1)";
// If the clip can't start in this long (slow connection, autoplay refused), the still cover comes instead.
const CLIP_WAIT_MS = 2500;

function reducedMotion(): boolean {
  return Boolean(window.matchMedia?.("(prefers-reduced-motion: reduce)").matches);
}

function canAnimate(element: Element | null | undefined): element is HTMLElement {
  return element instanceof HTMLElement && typeof element.animate === "function";
}

export function ShelfLanding({
  book,
  neighbours,
  from,
  onLanded,
}: {
  book: LandingBook;
  /** 4–6 other books for the row; half stand to the left of the member's book, the rest to the right. */
  neighbours: LandingBook[];
  /** Where the closed book starts, in viewport coordinates. Null: it is already on the shelf (no flight). */
  from: DOMRect | null;
  /** After the cover has painted in, or at once with reduced motion. */
  onLanded?: () => void;
}) {
  const art = artFor(book.id, book.design);
  const [reduced] = useState(reducedMotion);
  const [phase, setPhase] = useState<Phase>(() =>
    reduced || !art.anim ? "done" : from ? "flight" : "white",
  );
  // The member's book's cover, where the clip goes: inside it, under the type, exactly over the art.
  const [cover, setCover] = useState<HTMLElement | null>(null);
  const [inkDelay, setInkDelay] = useState<number | null>(null);
  // The clip never started, so the still cover fades in instead of appearing at once.
  const [fallback, setFallback] = useState(false);
  const mine = useRef<HTMLDivElement>(null);
  const left = useRef<HTMLDivElement>(null);
  const right = useRef<HTMLDivElement>(null);
  const video = useRef<HTMLVideoElement>(null);
  const landed = useRef(onLanded);
  landed.current = onLanded;
  const told = useRef(false);

  const leftBooks = neighbours.slice(0, Math.floor(neighbours.length / 2));
  const rightBooks = neighbours.slice(leftBooks.length);

  // A long title gets smaller type rather than a cut: the clamp in ShelfLanding.css is only the last resort, since
  // the member reads their own title here. Measured again once the display font has loaded.
  // biome-ignore lint/correctness/useExhaustiveDependencies: a new title is what calls for a new measure
  useLayoutEffect(() => {
    const title = mine.current?.querySelector<HTMLElement>(".book-title");
    if (!title) return;
    const shrink = () => {
      title.style.fontSize = "";
      const start = Number.parseFloat(getComputedStyle(title).fontSize);
      let size = start;
      // The display face's tight leading lets glyphs overhang a few pixels, so only a hidden half line counts as a cut.
      while (title.scrollHeight - title.clientHeight > size * 0.46 && size > start * 0.6) {
        size *= 0.92;
        title.style.fontSize = `${size}px`;
      }
    };
    shrink();
    document.fonts?.ready.then(shrink);
  }, [book.title]);

  // The still cover is fetched from the start, so it is ready the moment the clip ends (or instead of it).
  useEffect(() => {
    loadArt(art);
  }, [art]);

  useLayoutEffect(() => {
    setCover(mine.current?.querySelector<HTMLElement>(".book-cover") ?? null);
  }, []);

  // ---------- 1. Flight ----------
  useLayoutEffect(() => {
    if (phase !== "flight" || !from) return;
    const book = mine.current?.querySelector(".book");
    if (!canAnimate(book)) {
      setPhase("white");
      return;
    }
    const end = book.getBoundingClientRect();
    const scale = end.width ? from.width / end.width : 1;
    const dx = from.left - end.left;
    const dy = from.top - end.top;
    // One move from start to rest on one curve, so it slows all the way onto the shelf; the turn rides on top of it.
    const flight = book.animate(
      [{ transform: `translate(${dx}px, ${dy}px) scale(${scale})` }, { transform: "none" }],
      { duration: FLIGHT_MS, easing: SETTLE, fill: "backwards" },
    );
    const turn = book.animate([{ rotate: `y ${TURN_DEG}deg` }, { rotate: "y 0deg" }], {
      duration: TURN_MS,
      easing: TURN_EASE,
      fill: "backwards",
    });
    // The neighbours stand closed up where the gap will be, and slide apart to open it.
    const before = left.current?.lastElementChild?.getBoundingClientRect();
    const after = right.current?.firstElementChild?.getBoundingClientRect();
    const parts: Animation[] = [];
    if (before && after) {
      const shut = Math.max(0, (after.left - before.right) / 2 - 22);
      for (const [group, sign] of [
        [left.current, 1],
        [right.current, -1],
      ] as const) {
        if (canAnimate(group))
          parts.push(
            group.animate([{ transform: `translateX(${sign * shut}px)` }, { transform: "none" }], {
              duration: PART_MS,
              easing: SETTLE,
              fill: "backwards",
            }),
          );
      }
    }
    flight.finished.then(
      () => setPhase("white"),
      () => undefined,
    );
    return () => {
      flight.cancel();
      turn.cancel();
      for (const part of parts) part.cancel();
    };
  }, [phase, from]);

  // ---------- 2. Paint ----------
  // On the shelf and still white: start the clip once it can play, and count the paint from when it really
  // plays (the ink change is timed from then). If it can't start in time, the still cover comes instead.
  useEffect(() => {
    // The clip is put into the cover once the cover is known, a moment after the first render.
    if (phase !== "white" || !cover) return;
    const clip = video.current;
    const fail = () => {
      setFallback(true);
      setPhase("done");
    };
    if (!clip) return fail();
    const giveUp = window.setTimeout(fail, CLIP_WAIT_MS);
    const start = () => {
      const playing = clip.play?.();
      if (playing && typeof playing.catch === "function") playing.catch(fail);
    };
    const painting = () => {
      window.clearTimeout(giveUp);
      setPhase("paint");
    };
    clip.addEventListener("playing", painting);
    if (clip.readyState >= 3) start();
    else clip.addEventListener("canplay", start, { once: true });
    return () => {
      window.clearTimeout(giveUp);
      clip.removeEventListener("canplay", start);
      clip.removeEventListener("playing", painting);
    };
  }, [phase, cover]);

  useEffect(() => {
    if (phase !== "done" || told.current) return;
    told.current = true;
    landed.current?.();
  }, [phase]);

  const clip =
    cover && art.anim && phase !== "done"
      ? createPortal(
          <video
            ref={video}
            className="book-art sl-clip"
            muted
            playsInline
            preload="auto"
            disablePictureInPicture
            aria-hidden="true"
            tabIndex={-1}
            onLoadedMetadata={(event) => {
              // The title and name take the cover's own ink as the paint arrives under them.
              const length = event.currentTarget.duration;
              setInkDelay(Number.isFinite(length) ? Math.max(0, length - 1.6) : 2.4);
            }}
            onEnded={() => setPhase("done")}
            onError={() => {
              setFallback(true);
              setPhase("done");
            }}
          >
            <source src={art.anim.webm} type="video/webm" />
            <source src={art.anim.mp4} type="video/mp4" />
          </video>,
          cover,
        )
      : null;

  return (
    <div
      className="shelf-landing"
      data-phase={phase}
      data-reduced={reduced || undefined}
      data-fallback={fallback || undefined}
      style={inkDelay === null ? undefined : ({ "--sl-ink-delay": `${inkDelay}s` } as CSSProperties)}
    >
      <div className="sl-row">
        <div ref={left} className="sl-group sl-left">
          {leftBooks.map((neighbour) => (
            <div key={neighbour.id} className="sl-neighbour">
              <BookObject id={neighbour.id} book={neighbour} />
            </div>
          ))}
        </div>
        <div
          ref={mine}
          className="sl-mine"
          role="img"
          aria-label={`${book.title}, by ${book.authorName}, on the shelf`}
        >
          <BookObject id={book.id} book={book} size="lg" />
        </div>
        <div ref={right} className="sl-group sl-right">
          {rightBooks.map((neighbour) => (
            <div key={neighbour.id} className="sl-neighbour">
              <BookObject id={neighbour.id} book={neighbour} />
            </div>
          ))}
        </div>
      </div>
      <div className="ledge sl-ledge" />
      {clip}
    </div>
  );
}
