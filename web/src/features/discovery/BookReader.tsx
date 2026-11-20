import {
  type CSSProperties,
  type ReactNode,
  useCallback,
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
} from "react";
import { createPortal } from "react-dom";
import { Link } from "react-router-dom";
import { api } from "../../api/client";
import { errorMessage } from "../../api/errors";
import type { components } from "../../api/schema";
import { Button } from "../../ui/Button";
import "./BookReader.css";

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
  const [book, setBook] = useState<PublicBook | null>(example ?? null);
  const [error, setError] = useState<string | null>(null);
  const [missing, setMissing] = useState(false);
  const [attempt, setAttempt] = useState(0);
  const [ownBook, setOwnBook] = useState<{ id: string | null } | null>(null);
  // Spread 0 is the title page and the contents; spread n is chapter n facing the contents.
  const [spread, setSpread] = useState(0);
  const [turn, setTurn] = useState<Turn | null>(null);
  const [scale, setScale] = useState(1);
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
  useLayoutEffect(() => {
    const measure = () => {
      const room = dialog.current?.getBoundingClientRect();
      if (!room || !room.width) return;
      setScale(Math.min(1, (room.width - 48) / BOOK_W, (room.height - 48) / BOOK_H));
    };
    measure();
    window.addEventListener("resize", measure);
    return () => window.removeEventListener("resize", measure);
  }, []);

  // ---------- Opening: the book grows from its place on the shelf, and the cover swings open ----------
  // biome-ignore lint/correctness/useExhaustiveDependencies: it opens once; a later change of width doesn't replay it
  useLayoutEffect(() => {
    const modal = dialog.current;
    if (!modal) return;
    const opener = document.activeElement as HTMLElement | null;
    const overflow = document.body.style.overflow;
    modal.showModal();
    document.body.style.overflow = "hidden";
    const element = object.current;
    const target = element?.getBoundingClientRect();
    const k = fit.current ? fit.current.getBoundingClientRect().width / BOOK_W || 1 : 1;
    if (element && target && origin && target.width && target.height && !narrow) {
      // Before the cover swings left, the closed book is the right half. Offsets are in the book's own
      // (unscaled) space, because the move happens inside the scaled frame.
      element.style.setProperty(
        "--reader-x",
        `${(origin.x + origin.width / 2 - (target.x + target.width * 0.75)) / k}px`,
      );
      element.style.setProperty(
        "--reader-y",
        `${(origin.y + origin.height / 2 - (target.y + target.height / 2)) / k}px`,
      );
      element.style.setProperty("--reader-scale-x", String(origin.width / (target.width / 2)));
      element.style.setProperty("--reader-scale-y", String(origin.height / target.height));
      element.dataset.arrive = "true";
    }
    return () => {
      modal.close();
      document.body.style.overflow = overflow;
      if (opener?.isConnected) opener.focus({ preventScroll: true });
    };
  }, [origin]);

  // biome-ignore lint/correctness/useExhaustiveDependencies: incrementing attempt explicitly retries the same book request.
  useEffect(() => {
    if (example) return;
    let stale = false;
    setError(null);
    setMissing(false);
    api
      .GET("/books/{book_id}", { params: { path: { book_id: bookId } } })
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
    api
      .GET("/books/me")
      .then(({ data, response }) => {
        if (!stale && (data || response.status === 404)) setOwnBook({ id: data?.id ?? null });
      })
      .catch(() => undefined);
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
      turnTimer.current = setTimeout(() => {
        setSpread(next);
        setTurn(null);
        focusHeading();
      }, TURN_MS);
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
    <button type="button" className="br-close" onClick={onDismiss}>
      <span aria-hidden="true">✕</span> <span className="br-close-words">Close the book</span>
    </button>
  );
  const tabs = book && !missing && (
    <nav className="br-tabs" aria-label="Pages of this book">
      <button
        type="button"
        aria-current={currentChapter === 0 ? "page" : undefined}
        onClick={() => goTo(narrow ? 1 : 0)}
      >
        Contents
      </button>
      {chapters.map((chapter, index) => (
        <button
          key={chapter.id}
          type="button"
          aria-label={`Chapter ${index + 1}: ${chapter.title}`}
          aria-current={currentChapter === index + 1 ? "page" : undefined}
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
          <div className="br-head">{close}</div>
          {at === 0 ? (
            titlePage
          ) : (
            <>
              {contents(true, at)}
              {ask && <div className="br-ask br-ask-under">{ask}</div>}
            </>
          )}
        </>
      );
    }
    return (
      <>
        <div className="br-head br-head-right">{tabs}</div>
        {at === 0 ? contents(false) : chapterPage(at)}
      </>
    );
  }

  function phonePage(at: number): ReactNode {
    return (
      <>
        <div className="br-head br-head-phone">
          {close}
          {tabs}
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
  const canForward = book && !missing && at < (narrow ? last + 1 : last);

  return createPortal(
    <dialog
      ref={dialog}
      className="book-reader"
      aria-label={title}
      onCancel={(event) => {
        event.preventDefault();
        onDismiss();
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
              <div className="br-edge" aria-hidden="true" />
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
                {canForward && !turning && (
                  <button type="button" className="br-curl" aria-label="Turn the page" onClick={forward} />
                )}
              </section>
              {turn && (
                // The turning leaf: a plane with a page on each face, rotating about the spine.
                <div
                  className={`br-leaf ${ahead ? "br-leaf-forward" : "br-leaf-back"}`}
                  aria-hidden="true"
                  inert
                >
                  <div className="br-face br-page">{pageOf(turn.from, ahead ? "right" : "left")}</div>
                  <div className="br-face br-face-back br-page">
                    {pageOf(turn.to, ahead ? "left" : "right")}
                  </div>
                </div>
              )}
              <div className="br-gutter" aria-hidden="true" />
              <div className="br-cover" aria-hidden="true">
                <div className="br-cover-front">
                  <strong>{title}</strong>
                  <span>{author}</span>
                </div>
                {/* The cover's inside is the left of the spread: the board, the page edge and the title page,
                    so the book opens into itself rather than fading in. */}
                <div className="br-cover-back" inert>
                  <div className="br-cover-edge" />
                  <div className="br-page br-left br-cover-page">{pageOf(0, "left")}</div>
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
