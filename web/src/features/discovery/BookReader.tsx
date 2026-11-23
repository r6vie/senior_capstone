import {
  type CSSProperties,
  type ReactNode,
  useCallback,
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
} from "react";
import { createPortal, flushSync } from "react-dom";
import { Link } from "react-router-dom";
import { errorMessage } from "../../api/errors";
import type { components } from "../../api/schema";
import { artFor, artReady, coverInk, loadArt } from "../../ui/art/bookArt";
import { Button } from "../../ui/Button";
import "./BookReader.css";
import { loadBook, loadedBook, loadedOwnBook, loadOwnBook } from "./bookPreload";

// Book screen B, "the book opens" (docs/design/system.md, "Handoff: the open book"). The book opens over the
// shelf, under the library's top bar, and everything for the book is inside it: Close and the page tabs at
// the heads of the pages, Ask to check out on the title page and under the contents. Each page is one flat
// plane carrying its own content, so a turn rotates a plane about the spine in 3D.

export type BookCard = components["schemas"]["BookCard"];
type PublicBook = components["schemas"]["PublicBookResponse"];
export type BookOrigin = { x: number; y: number; width: number; height: number };

// The book as drawn at 1440 wide; it scales down to fit, as one object.
const BOOK_W = 1180;
const BOOK_H = 724;
const TURN_MS = 700;
/** A jump of several spreads turns a leaf for each (up to MAX_LEAVES), each starting this much after the last. */
const LEAF_STAGGER_MS = 110;
const MAX_LEAVES = 4;

/** The spreads a turn passes through, ends included: every one for a short jump, evenly spaced for a long one. */
/** The text of `element` line by line, as the browser broke it (at spaces, hyphens or anywhere), or null where
 *  it can't say (tests). */
function linesOf(element: HTMLElement): string[] | null {
  const text = element.firstChild;
  if (!text || text.nodeType !== Node.TEXT_NODE || typeof document.createRange !== "function") return null;
  const content = text.textContent ?? "";
  const range = document.createRange();
  if (typeof range.getClientRects !== "function") return null;
  const lines: string[] = [];
  let line = "";
  let top: number | null = null;
  for (let index = 0; index < content.length; index++) {
    range.setStart(text, index);
    range.setEnd(text, index + 1);
    const box = range.getClientRects()[0];
    if (box?.width && top !== null && box.top > top + box.height / 2) {
      lines.push(line.trim());
      line = "";
    }
    if (box?.width && (top === null || box.top > top + box.height / 2)) top = box.top;
    line += content[index];
  }
  lines.push(line.trim());
  return lines;
}

function printLines(lines: string[]): ReactNode {
  return lines.map((line, index) => (
    // biome-ignore lint/suspicious/noArrayIndexKey: the lines of one fixed text, in order
    <span key={index} className="br-line">
      {line}
    </span>
  ));
}

/** Every animation running in `element` (none where the browser can't say, as in tests). */
function animationsIn(element: Element | null): Animation[] {
  return element?.getAnimations?.({ subtree: true }) ?? [];
}

function turnStops(from: number, to: number): number[] {
  const count = Math.min(Math.abs(to - from), MAX_LEAVES);
  return Array.from({ length: count + 1 }, (_, step) => from + Math.round((step * (to - from)) / count));
}
/** Closing's length (BookReader.css, "Closing"). */
const CLOSE_MS = 560;
/** The longest a book waits in its shelf place for its contents before it opens anyway. */
const HOLD_MS = 600;
const PAGE_W = 570;
/** The closed cover (.br-cover): 584 x 708, from the spine. */
const COVER_W = 584;
const COVER_H = 708;
/** The closed cover's outline (.br-cover-front border). */
const COVER_OUTLINE = 6;
/** How many hinged strips a turning page bends with. More bend more smoothly and cost more layers. */
const LEAF_STRIPS = 6;

type Side = "left" | "right";
interface Turn {
  from: number;
  to: number;
}

function reduced(): boolean {
  return Boolean(window.matchMedia?.("(prefers-reduced-motion: reduce)").matches);
}

function useNarrow(): boolean {
  const query = "(max-width: 719px)";
  const [narrow, setNarrow] = useState(() => Boolean(window.matchMedia?.(query).matches));
  useEffect(() => {
    const list = window.matchMedia?.(query);
    if (!list) return;
    const change = () => setNarrow(list.matches);
    list.addEventListener?.("change", change);
    return () => list.removeEventListener?.("change", change);
  }, []);
  return narrow;
}

export function BookReader({
  bookId,
  card,
  origin,
  example,
  onDismiss,
}: {
  bookId: string;
  card?: BookCard;
  origin?: BookOrigin;
  example?: PublicBook;
  onDismiss: () => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  const fit = useRef<HTMLDivElement>(null);
  const object = useRef<HTMLDivElement>(null);
  const [book, setBook] = useState<PublicBook | null>(() => example ?? loadedBook(bookId));
  // The same art as the book's cover on the shelf: its cover while it is closed, its title page once open.
  const art = artFor(bookId);
  // Its art decoded before it opens, so no picture comes in mid-flight (loaded ahead with the book on the shelf).
  const [artLoaded, setArtLoaded] = useState(() => artReady(art));
  useEffect(() => {
    let stale = false;
    loadArt(art).then(() => {
      if (!stale) setArtLoaded(true);
    });
    return () => {
      stale = true;
    };
  }, [art]);
  const [error, setError] = useState<string | null>(null);
  const [missing, setMissing] = useState(false);
  const [attempt, setAttempt] = useState(0);
  const [ownBook, setOwnBook] = useState<{ id: string | null } | null>(() => loadedOwnBook());
  // Spread 0 is the title page and the contents; spread n is chapter n facing the contents.
  const [spread, setSpread] = useState(0);
  const [turn, setTurn] = useState<Turn | null>(null);
  const [scale, setScale] = useState(1);
  // The closed cover's lines, exactly as the shelf book broke them (printCover), so its print never reflows.
  const [printed, setPrinted] = useState<{ title: string[]; name: string[] } | null>(null);
  const narrow = useNarrow();
  // On a phone, one page at a time: the title page, the contents, then each chapter.
  const [page, setPage] = useState(0);

  const title =
    book?.title ??
    card?.title ??
    (missing ? "Book unavailable" : error ? "Couldn't open this book" : "Opening book");
  const author = book?.author_name ?? card?.author_name;
  const chapters = book?.chapters ?? [];
  const last = chapters.length;

  // ---------- Size: the drawn book, scaled to the room under the top bar ----------
  // Fitted once the dialog is open (closed it has no size); the opening below does the first fit itself, so
  // it can measure the book at the size it will open to.
  const fitToRoom = useCallback(() => {
    const modal = dialog.current;
    const room = modal?.getBoundingClientRect();
    if (!modal || !room?.width) return null;
    const k = Math.min(1, (room.width - 48) / BOOK_W, (room.height - 48) / BOOK_H);
    fit.current?.style.setProperty("--k", String(k));
    setScale(k);
    return k;
  }, []);
  useEffect(() => {
    // The visible screen also changes when browser chrome shows or hides, which only the visual viewport reports.
    window.addEventListener("resize", fitToRoom);
    window.visualViewport?.addEventListener("resize", fitToRoom);
    return () => {
      window.removeEventListener("resize", fitToRoom);
      window.visualViewport?.removeEventListener("resize", fitToRoom);
    };
  }, [fitToRoom]);

  /** Points the opening (and the closing, which is the opening played backwards) at a book on the shelf: closed,
   *  the book is its right half (the cover over the page block), exactly where and as big as the shelf book. The
   *  move and the scale are about the spine, the book's centre. Measured at rest, so the old aim is cleared first. */
  function aim(element: HTMLElement, shelf: BookOrigin): boolean {
    for (const name of ["--reader-x", "--reader-y", "--reader-scale-x", "--reader-scale-y"])
      element.style.removeProperty(name);
    const target = element.getBoundingClientRect();
    if (!target.width || !target.height || !shelf.width) return false;
    // The closed cover is the board's right half: from the spine to 6px short of the edge, 8px in at head and
    // foot. It, not the whole half, lands on the shelf book, so the two match edge for edge.
    const k = target.width / BOOK_W;
    const scaleX = shelf.width / (COVER_W * k);
    const scaleY = shelf.height / (COVER_H * k);
    const spine = target.x + target.width / 2;
    element.style.setProperty(
      "--reader-x",
      `${shelf.x + shelf.width / 2 - (spine + (scaleX * COVER_W * k) / 2)}px`,
    );
    element.style.setProperty(
      "--reader-y",
      `${shelf.y + shelf.height / 2 - (target.y + target.height / 2)}px`,
    );
    element.style.setProperty("--reader-scale-x", String(scaleX));
    element.style.setProperty("--reader-scale-y", String(scaleY));
    const book = document.querySelector<HTMLElement>(".book[data-out]");
    if (book) printCover(element, book);
    return true;
  }

  /** Sets the closed cover's type, hinge and padding from the very book on the shelf, whatever its size: each
   *  measure times the move's start scale (across for sizes, so lines break as there; the type box is pressed
   *  to the down scale), so at the start the cover is that book's print, letter for letter. */
  function printCover(element: HTMLElement, book: HTMLElement) {
    const box = book.getBoundingClientRect();
    const cover = book.querySelector<HTMLElement>(".book-cover");
    const title = book.querySelector<HTMLElement>(".book-title");
    const name = book.querySelector<HTMLElement>(".book-author");
    if (!box.width || !cover || !title || !name) return;
    const across = COVER_W / box.width;
    const down = COVER_H / box.height;
    const titleBox = title.getBoundingClientRect();
    const nameBox = name.getBoundingClientRect();
    const hinge = getComputedStyle(cover, "::before");
    const outline = Number.parseFloat(getComputedStyle(cover).borderLeftWidth) || 0;
    const px = (value: number) => `${value}px`;
    const set = (property: string, value: string) => element.style.setProperty(property, value);
    set("--print-across", String(across));
    set("--print-squash", String(down / across));
    set("--print-left", px((titleBox.left - box.left) * across - COVER_OUTLINE));
    set("--print-top", px((titleBox.top - box.top) * down - COVER_OUTLINE));
    set("--print-width", px(titleBox.width * across));
    set("--print-title", px(Number.parseFloat(getComputedStyle(title).fontSize) * across));
    set("--print-name", px(Number.parseFloat(getComputedStyle(name).fontSize) * across));
    set("--print-gap", px((nameBox.top - titleBox.bottom) * across));
    set("--print-hinge", px((Number.parseFloat(hinge.left) + outline) * across - COVER_OUTLINE));
    set("--print-hinge-width", px(Number.parseFloat(hinge.width) * across));
    const lines = { title: linesOf(title), name: linesOf(name) };
    if (lines.title && lines.name) setPrinted({ title: lines.title, name: lines.name });
  }

  // Whole: the contents and the right button are known (or there is nothing more coming).
  const whole =
    artLoaded && (Boolean(example) || missing || Boolean(error) || (book !== null && ownBook !== null));
  const ready = useRef(whole);
  ready.current = whole;
  useEffect(() => {
    const go = () => {
      for (const animation of animationsIn(dialog.current))
        if (animation.playState === "paused") animation.play();
    };
    if (whole) {
      go();
      return;
    }
    // A slow answer never keeps the book on the shelf for long.
    const timer = setTimeout(go, HOLD_MS);
    return () => clearTimeout(timer);
  }, [whole]);

  // ---------- Closing: the opening backwards, so the book goes back to its place on the shelf and closes. ----------
  const leaving = useRef(false);
  function closeBook() {
    if (leaving.current) return;
    const modal = dialog.current;
    const element = object.current;
    // Where the book's place on the shelf is now (it kept its room, hidden, while the book was out).
    const shelfBook = document.querySelector<HTMLElement>(".book[data-out]");
    const place = shelfBook?.getBoundingClientRect() ?? origin;
    if (!modal || !element || !place?.width || narrow || reduced()) {
      onDismiss();
      return;
    }
    leaving.current = true;
    // A turn under way is settled first: the book closes on the spread it was turning to.
    if (turn) {
      clearTimeout(turnTimer.current ?? undefined);
      flushSync(() => {
        setSpread(turn.to);
        setTurn(null);
      });
    }
    // Its place's shadow dissolves back in while it flies home (ShelfPage.css).
    if (shelfBook) shelfBook.dataset.returning = "true";
    let done = false;
    const finish = () => {
      if (done) return;
      done = true;
      if (shelfBook) delete shelfBook.dataset.returning;
      onDismiss();
    };
    if (element.dataset.arrive) {
      // Still opening: play what has happened so far backwards, from where it is.
      for (const animation of animationsIn(modal)) animation.reverse();
    } else if (aim(element, place)) {
      modal.dataset.leave = "true";
    } else {
      finish();
      return;
    }
    element.addEventListener("animationend", (event) => {
      if (event.target === element && /^br-move/.test(event.animationName)) finish();
    });
    element.addEventListener("animationcancel", finish);
    // A hidden tab renders no frames, so no animation ends: close on time regardless.
    setTimeout(finish, CLOSE_MS + 150);
  }

  // ---------- Opening: one move. The book, a 3D object with a cover and a page block, travels from its place
  // on the shelf to the foreground, turning to show its depth as it comes, while its cover swings open. ----------
  // biome-ignore lint/correctness/useExhaustiveDependencies: it opens once; a later change of width doesn't replay it
  useLayoutEffect(() => {
    const modal = dialog.current;
    if (!modal) return;
    const opener = document.activeElement as HTMLElement | null;
    const root = document.documentElement;
    const before = { overflow: root.style.overflow, gutter: root.style.scrollbarGutter };
    // The shelf behind stops scrolling, keeping its scrollbar's room so nothing behind the book shifts.
    root.style.scrollbarGutter = "stable";
    root.style.overflow = "hidden";
    modal.showModal();
    if (!narrow) fitToRoom();
    const element = object.current;
    // A second run (React's development double-run) restarts the opening cleanly.
    if (element) delete element.dataset.arrive;
    if (element && origin && !narrow && aim(element, origin)) {
      element.dataset.arrive = "true";
      // Its pages must be whole before they show: until the book's contents (and whether it is the member's own)
      // are in, it waits closed in its place on the shelf, where it looks just like the book it replaced.
      if (!ready.current) for (const animation of animationsIn(modal)) animation.pause();
    }
    // Once it has arrived the opening is over: pages mounted later (a turn) must not replay its take-over.
    const arrived = (event: AnimationEvent) => {
      if (event.target === element && event.animationName === "br-move") delete element?.dataset.arrive;
    };
    element?.addEventListener("animationend", arrived);
    return () => {
      element?.removeEventListener("animationend", arrived);
      modal.close();
      root.style.overflow = before.overflow;
      root.style.scrollbarGutter = before.gutter;
      if (opener?.isConnected) opener.focus({ preventScroll: true });
    };
  }, [origin]);

  // A retry (attempt > 0) fetches again rather than reusing the failed answer.
  useEffect(() => {
    if (example) return;
    let stale = false;
    setError(null);
    setMissing(false);
    loadBook(bookId, attempt > 0)
      .then(({ data, error: failure, response }) => {
        if (stale) return;
        if (data) setBook(data);
        else if (response.status === 404) setMissing(true);
        else setError(errorMessage(failure));
      })
      .catch(() => {
        if (!stale) setError("Couldn't load this book. Please try again.");
      });
    return () => {
      stale = true;
    };
  }, [bookId, example, attempt]);

  useEffect(() => {
    if (example) return;
    let stale = false;
    // Only to tell the member's own book apart: its button is My book, not Ask to check out.
    loadOwnBook().then((known) => {
      if (!stale && known) setOwnBook(known);
    });
    return () => {
      stale = true;
    };
  }, [example]);

  // ---------- Turning ----------
  const turnTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  useEffect(() => () => clearTimeout(turnTimer.current ?? undefined), []);
  const focusHeading = useCallback(() => {
    requestAnimationFrame(() =>
      dialog.current
        ?.querySelector<HTMLElement>(".br-static [data-page-heading]")
        ?.focus({ preventScroll: true }),
    );
  }, []);

  const goTo = useCallback(
    (to: number) => {
      if (!book || turn) return;
      // A turn means the opening is over, even if its end was never seen (a hidden tab renders no frames).
      if (object.current) delete object.current.dataset.arrive;
      if (narrow) {
        const next = Math.max(0, Math.min(to, last + 1));
        if (next === page) return;
        setPage(next);
        focusHeading();
        return;
      }
      const next = Math.max(0, Math.min(to, last));
      if (next === spread) return;
      // Reduced motion: no turn, the spread just changes with a short fade.
      if (reduced()) {
        setSpread(next);
        focusHeading();
        return;
      }
      setTurn({ from: spread, to: next });
      turnTimer.current = setTimeout(
        () => {
          setSpread(next);
          setTurn(null);
          focusHeading();
        },
        TURN_MS + (turnStops(spread, next).length - 2) * LEAF_STAGGER_MS,
      );
    },
    [book, turn, narrow, last, page, spread, focusHeading],
  );

  // Where "forward" and "back" go: a spread at a time, or a page at a time on a phone.
  const at = narrow ? page : spread;
  const forward = () => goTo(at + 1);
  const back = () => goTo(at - 1);

  const swipe = useRef<{ x: number; y: number } | null>(null);

  // ---------- The pages ----------
  const isOwn = Boolean(book && ownBook?.id === book.id);
  const ask =
    example || !book || missing ? null : isOwn ? (
      <Link to="/my-book" className="button button-secondary">
        My book
      </Link>
    ) : (
      <Link to={`/checkouts/new/${encodeURIComponent(book.id)}`} className="button button-primary">
        Ask to check out
      </Link>
    );

  // Which tab is current: Contents for spread 0 (and the title page on a phone), else the chapter.
  const currentChapter = narrow ? (page >= 2 ? page - 1 : 0) : spread;

  const close = (
    <button type="button" className="br-close" onClick={closeBook}>
      <span aria-hidden="true">✕</span> <span className="br-close-words">Close the book</span>
    </button>
  );
  // Each page's tabs mark the spread that page belongs to, so the page turning in already shows where it goes.
  const tabs = (current: number) =>
    book &&
    !missing && (
      <nav className="br-tabs" aria-label="Pages of this book">
        <button
          type="button"
          aria-current={current === 0 ? "page" : undefined}
          onClick={() => goTo(narrow ? 1 : 0)}
        >
          Contents
        </button>
        {chapters.map((chapter, index) => (
          <button
            key={chapter.id}
            type="button"
            aria-label={`Chapter ${index + 1}: ${chapter.title}`}
            aria-current={current === index + 1 ? "page" : undefined}
            onClick={() => goTo(narrow ? index + 2 : index + 1)}
          >
            {index + 1}
          </button>
        ))}
      </nav>
    );

  const titlePage = (
    <>
      {example && <span className="caption br-caption">Example book</span>}
      <h1 className="br-title" data-page-heading={narrow ? true : undefined} tabIndex={-1}>
        {title}
      </h1>
      {author && <p className="byline br-byline">by {author}</p>}
      {book?.blurb && <p className="br-blurb">{book.blurb}</p>}
      {ask && <div className="br-ask">{ask}</div>}
    </>
  );

  const state = missing ? (
    <div className="empty" role="status">
      <p>This book isn't on the shelf anymore.</p>
    </div>
  ) : error ? (
    <div className="message message-error" role="alert">
      <p>{error}</p>
      <Button variant="secondary" onClick={() => setAttempt((value) => value + 1)}>
        Try again
      </Button>
    </div>
  ) : !book ? (
    <p role="status">Opening the book…</p>
  ) : null;

  const contents = (compact: boolean, current?: number) => (
    <>
      <h2 className="br-page-name" data-page-heading={!compact || undefined} tabIndex={-1}>
        Contents
      </h2>
      {state ?? (
        <ol className={compact ? "br-toc br-toc-compact" : "br-toc"}>
          {chapters.map((chapter, index) => (
            <li key={chapter.id} aria-current={current === index + 1 ? "page" : undefined}>
              <button
                type="button"
                aria-label={chapter.title}
                onClick={() => goTo(narrow ? index + 2 : index + 1)}
              >
                <b aria-hidden="true">{index + 1}</b>
                <span className="br-toc-title">{chapter.title}</span>
                <i aria-hidden="true">›</i>
                {!compact && chapter.summary && <span className="br-toc-summary">{chapter.summary}</span>}
              </button>
            </li>
          ))}
        </ol>
      )}
    </>
  );

  const chapterPage = (index: number) => {
    const chapter = chapters[index - 1];
    if (!chapter) return null;
    return (
      <article aria-label={chapter.title}>
        <span className="br-number" aria-hidden="true">
          {index}
        </span>
        <h2 className="br-chapter-title" data-page-heading tabIndex={-1}>
          {chapter.title}
        </h2>
        {chapter.summary && <p className="br-summary">{chapter.summary}</p>}
      </article>
    );
  };

  /** One page of a spread, with its head. Ask to check out goes under the contents, never under a chapter. */
  function pageOf(at: number, side: Side): ReactNode {
    if (side === "left") {
      return (
        <>
          {/* Every left page carries the book's art behind its text, the title page and each contents page. */}
          <img className="br-page-art" src={art.page} alt="" />
          <div className="br-head">{close}</div>
          {at === 0 ? (
            titlePage
          ) : (
            <>
              {contents(true, at)}
              {ask && <div className="br-ask br-ask-under">{ask}</div>}
            </>
          )}
          {at > 0 && (
            <button
              type="button"
              className="br-curl br-curl-back"
              aria-label="Turn back a page"
              onClick={back}
            />
          )}
        </>
      );
    }
    return (
      <>
        <div className="br-head br-head-right">{tabs(at)}</div>
        {at === 0 ? contents(false) : chapterPage(at)}
        {/* The turned-down corner is printed on the page, so it turns with it rather than coming and going. */}
        {book && !missing && at < last && (
          <button type="button" className="br-curl" aria-label="Turn the page" onClick={forward} />
        )}
      </>
    );
  }

  /** Strip `index` of the turning leaf (counted out from the spine) and, inside it, the rest. Its front shows its
   *  slice of the page turning away, its back the same slice of the page turning in. */
  function leafStrip(turn: { from: number; to: number }, ahead: boolean, index: number): ReactNode {
    if (index >= LEAF_STRIPS) return null;
    const width = PAGE_W / LEAF_STRIPS;
    // A right page's slice by the spine starts at its left edge; a left page's at its right edge.
    const near = index * width;
    const far = PAGE_W - (index + 1) * width;
    const front: Side = ahead ? "right" : "left";
    const back: Side = ahead ? "left" : "right";
    return (
      <div className="br-strip">
        <div className="br-face">
          <div className={`br-page br-${front}`} style={{ left: -(ahead ? near : far) }}>
            {pageOf(turn.from, front)}
          </div>
        </div>
        <div className="br-face br-face-back">
          <div className={`br-page br-${back}`} style={{ left: -(ahead ? far : near) }}>
            {pageOf(turn.to, back)}
          </div>
        </div>
        {leafStrip(turn, ahead, index + 1)}
      </div>
    );
  }

  function phonePage(at: number): ReactNode {
    return (
      <>
        <div className="br-head br-head-phone">
          {close}
          {tabs(currentChapter)}
        </div>
        {at === 0 ? titlePage : at === 1 ? contents(false) : chapterPage(at - 1)}
      </>
    );
  }

  // ---------- Layout ----------
  const turning = turn !== null;
  const ahead = turn && turn.to > turn.from;
  const staticLeft = turn ? (ahead ? turn.from : turn.to) : spread;
  const staticRight = turn ? (ahead ? turn.to : turn.from) : spread;

  return createPortal(
    <dialog
      ref={dialog}
      className="book-reader"
      aria-label={title}
      onCancel={(event) => {
        event.preventDefault();
        closeBook();
      }}
      onKeyDown={(event) => {
        if (event.target instanceof HTMLInputElement) return;
        if (event.key === "ArrowRight") {
          event.preventDefault();
          forward();
        } else if (event.key === "ArrowLeft") {
          event.preventDefault();
          back();
        }
      }}
    >
      <div className="br-dots" aria-hidden="true" />
      <div
        className="br-fit"
        ref={fit}
        style={{ "--k": narrow ? 1 : scale } as CSSProperties}
        onTouchStart={(event) => {
          const touch = event.touches[0];
          if (touch) swipe.current = { x: touch.clientX, y: touch.clientY };
        }}
        onTouchEnd={(event) => {
          const start = swipe.current;
          const touch = event.changedTouches[0];
          swipe.current = null;
          if (!start || !touch) return;
          const dx = touch.clientX - start.x;
          if (Math.abs(dx) > 50 && Math.abs(dx) > Math.abs(touch.clientY - start.y)) {
            if (dx < 0) forward();
            else back();
          }
        }}
      >
        <div
          className="br-book"
          ref={object}
          data-turning={turning || undefined}
          data-narrow={narrow || undefined}
        >
          {!narrow && (
            <>
              <div className="br-board" aria-hidden="true" />
              <div className="br-spine" aria-hidden="true" />
              <div className="br-edge" aria-hidden="true" />
              {/* The page block's own edges, so the closed book has depth. Edge-on, and thin, once open. */}
              <div className="br-block br-block-side" aria-hidden="true" />
              <div className="br-block br-block-spine" aria-hidden="true" />
              <div className="br-block br-block-head" aria-hidden="true" />
              <div className="br-block br-block-foot" aria-hidden="true" />
            </>
          )}
          {narrow ? (
            <section key={page} className="br-page br-phone br-static" aria-label="Page">
              {phonePage(page)}
              {page < last + 1 && book && !missing && (
                <button type="button" className="br-curl" aria-label="Turn the page" onClick={forward} />
              )}
            </section>
          ) : (
            <>
              <section
                key={`l${staticLeft}`}
                className="br-page br-left br-static"
                aria-label={staticLeft === 0 ? "Title page" : "Contents"}
              >
                {pageOf(staticLeft, "left")}
              </section>
              <section
                key={`r${staticRight}`}
                className="br-page br-right br-static"
                aria-label={staticRight === 0 ? "Contents" : "Chapter"}
                aria-busy={!book && !error && !missing}
              >
                {pageOf(staticRight, "right")}
              </section>
              {turn &&
                // The turning leaves, one per spread passed, each rotating about the spine: hinged strips, so
                // the paper bends as it turns. A leaf lies above the ones still to turn and, once over, above the
                // ones turned before it (--z-from, --z-to), so the stack keeps its order on both sides.
                turnStops(turn.from, turn.to)
                  .slice(1)
                  .map((stop, leaf, stops) => (
                    <div
                      key={stop}
                      className={`br-leaf ${ahead ? "br-leaf-forward" : "br-leaf-back"}`}
                      style={
                        {
                          "--delay": `${leaf * LEAF_STAGGER_MS}ms`,
                          "--z-from": `${(stops.length - leaf) * 0.5}px`,
                          "--z-to": `${(leaf + 1) * 0.5}px`,
                        } as CSSProperties
                      }
                      aria-hidden="true"
                      inert
                    >
                      {leafStrip(
                        { from: leaf === 0 ? turn.from : (stops[leaf - 1] ?? turn.from), to: stop },
                        Boolean(ahead),
                        0,
                      )}
                    </div>
                  ))}
              <div className="br-cover" aria-hidden="true">
                <div className="br-cover-rim br-cover-side" />
                <div className="br-cover-rim br-cover-spine" />
                <div className="br-cover-rim br-cover-head" />
                <div className="br-cover-rim br-cover-foot" />
                <div className="br-cover-front" style={coverInk(art)}>
                  <img className="br-cover-art" src={art.cover} alt="" />
                  <div className="br-cover-type">
                    <strong>{printed ? printLines(printed.title) : title}</strong>
                    <span>{printed ? printLines(printed.name) : author}</span>
                  </div>
                </div>
                {/* The cover's inside is the left of the spread: the board, the page edge and the title page,
                    so the book opens into itself rather than fading in. */}
                <div className="br-cover-back" inert>
                  <div className="br-cover-edge" />
                  <div className="br-page br-left br-cover-page">{pageOf(spread, "left")}</div>
                </div>
              </div>
            </>
          )}
        </div>
      </div>
    </dialog>,
    document.body,
  );
}
