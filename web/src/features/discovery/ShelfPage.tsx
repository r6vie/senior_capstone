import { type ReactNode, useCallback, useEffect, useRef, useState } from "react";
import { useLocation, useNavigate, useNavigationType, useParams } from "react-router-dom";
import { Button } from "../../ui/Button";
import { type BookCard, type BookOrigin, BookReader } from "./BookReader";
import { FrontDesk } from "./FrontDesk";
import { type SampleBook, sampleBooks, sampleFeatured } from "./sampleBooks";
import { useShelf } from "./useShelf";
import "./ShelfPage.css";
import { useBookStepping } from "./useBookStepping";

// The Librarian remains a hardcoded example until D3. These two sample groupings restore the
// earlier shelf preview; Recently added still contains every published book returned by the API.

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

const booksById = new Map(sampleBooks.map((book) => [book.id, book]));

function bookById(id: string): SampleBook {
  const book = booksById.get(id);
  if (!book) throw new Error(`Sample book ${id} is missing.`);
  return book;
}

function Book({
  book,
  size,
  onOpen,
}: {
  book: Pick<SampleBook, "title" | "authorName">;
  size?: "lg";
  onOpen: (element: HTMLButtonElement) => void;
}) {
  return (
    <button
      type="button"
      className={size === "lg" ? "book book-lg" : "book"}
      aria-label={`${book.title}, by ${book.authorName}`}
      onClick={(event) => onOpen(event.currentTarget)}
    >
      <span className="book-cover">
        <span className="book-title">{book.title}</span>
        <span className="book-author">{book.authorName}</span>
      </span>
    </button>
  );
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
  const featured = bookById(sampleFeatured.bookId);
  const shelf = useShelf();
  const { bookId } = useParams();
  const navigate = useNavigate();
  const location = useLocation();
  const navigationType = useNavigationType();
  const [preview, setPreview] = useState<BookOrigin | null>(null);
  const selected = location.state as { card?: BookCard; origin?: BookOrigin; fromShelf?: boolean } | null;
  const categoryShelves = SAMPLE_CATEGORY_SHELVES.map((category) => ({
    name: category.name,
    books: shelf.books.filter((book) => category.titles.has(book.title)),
  })).filter((category) => category.books.length > 0);

  function bounds(element: HTMLButtonElement): BookOrigin {
    const { x, y, width, height } = element.getBoundingClientRect();
    return { x, y, width, height };
  }

  function open(book: BookCard, element: HTMLButtonElement) {
    navigate(`/books/${encodeURIComponent(book.id)}`, {
      state: { card: book, origin: bounds(element), fromShelf: true },
    });
  }

  function dismiss() {
    if (selected?.fromShelf) navigate(-1);
    else navigate("/", { replace: true });
  }

  return (
    <div className="shelf-page">
      <main>
        <section className="feature surf dark" aria-labelledby="feature-title">
          <div className="burst" />
          <div className="feature-text">
            <span className="caption">The Librarian recommends</span>
            <h1 id="feature-title" className="page-title">
              {featured.title}
            </h1>
            <p className="feature-author">by {featured.authorName}</p>
            <p className="voice feature-reason">{sampleFeatured.reason}</p>
            <div className="feature-action">
              <Button onClick={(event) => setPreview(bounds(event.currentTarget))}>Ask to check out</Button>
              <span className="feature-note">A thirty-minute video call</span>
            </div>
          </div>
          <div className="feature-book">
            <Book book={featured} size="lg" onOpen={(element) => setPreview(bounds(element))} />
          </div>
        </section>

        <FrontDesk />

        <div className="shelves">
          {categoryShelves.map((category) => (
            <ShelfRow key={category.name} name={category.name}>
              {category.books.map((book) => (
                <Book
                  key={book.id}
                  book={{ title: book.title, authorName: book.author_name }}
                  onOpen={(element) => open(book, element)}
                />
              ))}
            </ShelfRow>
          ))}

          <ShelfRow name="Recently added" busy={shelf.busy}>
            {shelf.books.map((book) => (
              <Book
                key={book.id}
                book={{ title: book.title, authorName: book.author_name }}
                onOpen={(element) => open(book, element)}
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
      {preview && (
        <BookReader
          bookId={featured.id}
          origin={preview}
          onDismiss={() => setPreview(null)}
          example={{
            id: featured.id,
            title: featured.title,
            author_name: featured.authorName,
            cover_style: "cover-1",
            blurb: null,
            chapters: featured.chapters.map((title, index) => ({
              id: `example-${index}`,
              title,
              summary: "",
            })),
          }}
        />
      )}
    </div>
  );
}
