import { type ReactNode, useCallback, useEffect, useRef, useState } from "react";
import { useLocation, useNavigate, useNavigationType, useParams } from "react-router-dom";
import { artFor, loadArt } from "../../ui/art/bookArt";
import { Button } from "../../ui/Button";
import { PageLoading } from "../../ui/Loading";
import { BookObject } from "./BookObject";
import { type BookCard, type BookOrigin, BookReader } from "./BookReader";
import { loadBook, loadOwnBook } from "./bookPreload";
import { FrontDesk } from "./FrontDesk";
import { useShelf } from "./useShelf";
import "./ShelfPage.css";
import { useBookStepping } from "./useBookStepping";
import { type Recommendation, useRecommendation } from "./useRecommendation";

// These two sample groupings restore the earlier shelf preview; Recently added still contains
// every published book returned by the API. The final category decision remains open.

const SAMPLE_CATEGORY_SHELVES = [
  {
    name: "Changing course",
    titles: new Set([
      "Translating for My Parents",
      "The Quiet Founder",
      "Teaching Kids Who Hate Math",
      "From Pre-Med to Product",
      "The Accidental Data Scientist",
    ]),
  },
  {
    name: "Starting over",
    titles: new Set([
      "Lab Notebooks and Late Buses",
      "Small Town, Big Contracts",
      "The Second Language Classroom",
      "Growing Food in the City",
      "Fixing Old Buildings",
    ]),
  },
] as const;

function promotionFor(recommendation: Recommendation | null, failed: boolean, busy: boolean) {
  if (busy) {
    return {
      title: "The Librarian is looking",
      reason: "Reading the shelves for a story that belongs beside yours.",
      action: null,
      destination: null,
    };
  }
  if (failed || recommendation?.state === "unavailable") {
    return {
      title: "The Librarian is still looking",
      reason: "Your shelves are ready while the Librarian tries again.",
      action: "Try again",
      destination: null,
    };
  }
  if (recommendation?.state === "finish_book") {
    return {
      title: "Your story is almost ready",
      reason: "Finish your book so the Librarian can find the person whose story belongs beside yours.",
      action: "Finish your book",
      destination: "/my-book",
    };
  }
  if (recommendation?.state === "empty_shelf") {
    return {
      title: "The next story is coming",
      reason: "The Librarian will leave a recommendation here when another available book fits yours.",
      action: null,
      destination: null,
    };
  }
  return {
    title: "Your story belongs here",
    reason:
      "Create your book so the Librarian can introduce you to someone whose experience speaks to yours.",
    action: "Create your book",
    destination: "/interview",
  };
}

function Arrow({ back }: { back?: boolean }) {
  return (
    <svg
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2.6"
      aria-hidden="true"
    >
      <path d={back ? "M15 5l-7 7 7 7" : "M9 5l7 7-7 7"} />
    </svg>
  );
}

/** A shelf: its name and rule, arrows that move the row in place a book at a time, and the books on
 * one ink ledge. The next book peeks in at the edge. There is no separate "whole shelf" page. */
function ShelfRow({ name, children, busy }: { name: string; children: ReactNode; busy?: boolean }) {
  const row = useRef<HTMLDivElement>(null);
  useBookStepping(row);
  const [ends, setEnds] = useState({ start: true, end: true });

  const look = useCallback(() => {
    const element = row.current;
    if (!element) return;
    const max = element.scrollWidth - element.clientWidth;
    setEnds({ start: element.scrollLeft <= 1, end: element.scrollLeft >= max - 1 });
  }, []);

  useEffect(() => {
    const element = row.current;
    if (!element) return;
    look();
    element.addEventListener("scroll", look, { passive: true });
    const observer = typeof ResizeObserver === "undefined" ? null : new ResizeObserver(look);
    observer?.observe(element);
    return () => {
      element.removeEventListener("scroll", look);
      observer?.disconnect();
    };
  }, [look]);
  // Books arrive after the first look, so look again when they do.
  // biome-ignore lint/correctness/useExhaustiveDependencies: children changing is what calls for a new look
  useEffect(look, [children]);

  function step(direction: 1 | -1) {
    const element = row.current;
    if (!element) return;
    const padding = Number.parseFloat(getComputedStyle(element).paddingLeft) || 0;
    const left = element.getBoundingClientRect().left;
    const stops = [...element.children].map(
      (child) => child.getBoundingClientRect().left - left + element.scrollLeft - padding,
    );
    const at = element.scrollLeft;
    const target =
      direction > 0
        ? stops.find((stop) => stop > at + 1)
        : [...stops].reverse().find((stop) => stop < at - 1);
    const reduce = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
    element.scrollTo({
      left: Math.max(0, target ?? (direction > 0 ? at : 0)),
      behavior: reduce ? "auto" : "smooth",
    });
  }

  return (
    <section className="shelf-row" aria-label={name} aria-busy={busy}>
      <div className="shelf-head">
        <h2 className="shelf-name">{name}</h2>
        <div className="shelf-nav">
          <button
            type="button"
            aria-label={`Earlier books on ${name}`}
            disabled={ends.start}
            onClick={() => step(-1)}
          >
            <Arrow back />
          </button>
          <button
            type="button"
            aria-label={`More books on ${name}`}
            disabled={ends.end}
            onClick={() => step(1)}
          >
            <Arrow />
          </button>
        </div>
      </div>
      <div className="shelf-books" ref={row}>
        {children}
      </div>
      <div className="ledge" />
    </section>
  );
}

export function ShelfPage() {
  const shelf = useShelf();
  const librarian = useRecommendation();
  const { bookId } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const navigationType = useNavigationType();
  const selected = location.state as {
    card?: BookCard;
    origin?: BookOrigin;
    fromShelf?: boolean;
    /** Which copy was opened: a book can stand on more than one shelf, and only that copy leaves its place. */
    place?: string;
  } | null;
  // The copy that is out: the one opened, while its book is open (none for a book opened from a link).
  const outPlace = bookId && selected?.card?.id === bookId ? selected.place : undefined;
  const categoryShelves = SAMPLE_CATEGORY_SHELVES.map((category) => ({
    name: category.name,
    books: shelf.books.filter((book) => category.titles.has(book.title)),
  })).filter((category) => category.books.length > 0);
  const recommendation =
    librarian.recommendation?.state === "recommendation" ? librarian.recommendation : null;
  const featured = recommendation?.book;
  const promotion = promotionFor(librarian.recommendation, Boolean(librarian.error), librarian.busy);

  function bounds(element: HTMLButtonElement): BookOrigin {
    const { x, y, width, height } = element.getBoundingClientRect();
    return { x, y, width, height };
  }

  // Whether a book is the member's own decides its button, so it is known before any book opens.
  useEffect(() => {
    loadOwnBook();
  }, []);

  /** Pointed at or focused: fetch its contents and decode its art ahead of a likely opening. */
  function interest(id: string) {
    loadBook(id);
    loadArt(artFor(id));
  }

  function open(book: BookCard, element: HTMLButtonElement, place: string) {
    // On touch there was no pointing first: fetch now, while the book waits closed in its place.
    interest(book.id);
    navigate(`/books/${encodeURIComponent(book.id)}`, {
      state: { card: book, origin: bounds(element), fromShelf: true, place },
    });
  }

  function dismiss() {
    if (selected?.fromShelf) navigate(-1);
    else navigate("/", { replace: true });
  }

  return (
    <div className="shelf-page">
      <main>
        {/* The first shelf of books is what the page is for; the Librarian's pick fills its own band later. */}
        {shelf.busy && shelf.books.length === 0 && !shelf.error && <PageLoading />}
        <section className="feature surf dark" aria-labelledby="feature-title" aria-busy={librarian.busy}>
          <div className="burst" />
          <div className="feature-text">
            <span className="caption">The Librarian recommends</span>
            <h1 id="feature-title" className="page-title">
              {featured?.title ?? promotion.title}
            </h1>
            {featured && <p className="feature-author">by {featured.author_name}</p>}
            <p className="voice feature-reason">{recommendation?.reason ?? promotion.reason}</p>
            <div className="feature-action">
              {featured && (
                <Button
                  onClick={(event) => open(featured, event.currentTarget, `recommendation/${featured.id}`)}
                >
                  Ask to check out
                </Button>
              )}
              {!featured && promotion.action && (
                <Button
                  onClick={() =>
                    promotion.destination ? navigate(promotion.destination) : void librarian.retry()
                  }
                >
                  {promotion.action}
                </Button>
              )}
            </div>
          </div>
          <div className="feature-book">
            {featured ? (
              <BookObject
                id={featured.id}
                book={{ title: featured.title, authorName: featured.author_name }}
                size="lg"
                out={outPlace === `recommendation/${featured.id}`}
                onOpen={(element) => open(featured, element, `recommendation/${featured.id}`)}
                onInterest={() => interest(featured.id)}
              />
            ) : (
              <BookObject
                id="your-story-belongs-here"
                book={{ title: "Your story belongs here", authorName: "A book by you" }}
                size="lg"
              />
            )}
          </div>
        </section>

        <FrontDesk />

        <div className="shelves">
          {categoryShelves.map((category) => (
            <ShelfRow key={category.name} name={category.name}>
              {category.books.map((book) => (
                <BookObject
                  key={book.id}
                  id={book.id}
                  book={{ title: book.title, authorName: book.author_name }}
                  out={outPlace === `${category.name}/${book.id}`}
                  onOpen={(element) => open(book, element, `${category.name}/${book.id}`)}
                  onInterest={() => interest(book.id)}
                />
              ))}
            </ShelfRow>
          ))}

          <ShelfRow name="Recently added" busy={shelf.busy}>
            {shelf.books.map((book) => (
              <BookObject
                key={book.id}
                id={book.id}
                book={{ title: book.title, authorName: book.author_name }}
                out={outPlace === `recent/${book.id}`}
                onOpen={(element) => open(book, element, `recent/${book.id}`)}
                onInterest={() => interest(book.id)}
              />
            ))}
          </ShelfRow>
          <div className="shelf-feedback">
            {shelf.busy && <p role="status">Loading books…</p>}
            {shelf.error && (
              <div className="message message-error" role="alert">
                <p>{shelf.error}</p>
                <Button variant="secondary" onClick={shelf.loadMore} disabled={shelf.busy}>
                  Try again
                </Button>
              </div>
            )}
            {!shelf.busy && !shelf.error && !shelf.books.length && (
              <div className="empty">
                <h3>No books on the shelf yet.</h3>
                <p>Published books will appear here.</p>
                <Button variant="secondary" onClick={shelf.loadMore}>
                  Refresh shelf
                </Button>
              </div>
            )}
            {shelf.next && !shelf.error && (
              <Button
                variant="secondary"
                onClick={shelf.loadMore}
                disabled={shelf.busy}
                aria-busy={shelf.busy}
              >
                Load more books
              </Button>
            )}
          </div>
        </div>
      </main>
      {bookId && (
        <BookReader
          key={bookId}
          bookId={bookId}
          card={
            selected?.card?.id === bookId ? selected.card : shelf.books.find((book) => book.id === bookId)
          }
          origin={navigationType === "PUSH" ? selected?.origin : undefined}
          onDismiss={dismiss}
        />
      )}
    </div>
  );
}
