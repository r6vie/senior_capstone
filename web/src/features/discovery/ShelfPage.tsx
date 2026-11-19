import { type ReactNode, useRef, useState } from "react";
import { useLocation, useNavigate, useNavigationType, useParams } from "react-router-dom";
import { Button } from "../../ui/Button";
import { type BookCard, type BookOrigin, BookReader } from "./BookReader";
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

function ShelfBooks({ children }: { children: ReactNode }) {
  const row = useRef<HTMLDivElement>(null);
  useBookStepping(row);
  return (
    <div className="shelf-books" ref={row}>
      {children}
    </div>
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
        <section className="feature" aria-labelledby="feature-title">
          <div className="band dark">
            <div className="burst" />
            <div className="feature-fade" />
            <div className="feature-text">
              <span className="caption">The Librarian recommends</span>
              <h1 id="feature-title" className="page-title">
                {featured.title}
              </h1>
              <p className="feature-author">by {featured.authorName}</p>
              <p className="voice feature-reason">{sampleFeatured.reason}</p>
            </div>
            <div className="feature-book">
              <div className="halo" />
              <Book book={featured} size="lg" onOpen={(element) => setPreview(bounds(element))} />
            </div>
            <div className="feature-action">
              <Button onClick={(event) => setPreview(bounds(event.currentTarget))}>Ask to check out</Button>
              <span className="feature-note">A thirty-minute video call</span>
            </div>
          </div>
          <div className="feature-rule" />
        </section>

        {categoryShelves.map((category) => (
          <section key={category.name} className="shelf-row" aria-label={category.name}>
            <div className="shelf-head">
              <h2 className="shelf-name">{category.name}</h2>
            </div>
            <ShelfBooks>
              {category.books.map((book) => (
                <Book
                  key={book.id}
                  book={{ title: book.title, authorName: book.author_name }}
                  onOpen={(element) => open(book, element)}
                />
              ))}
            </ShelfBooks>
            <div className="ledge" />
          </section>
        ))}

        <section className="shelf-row" aria-label="Recently added" aria-busy={shelf.busy}>
          <div className="shelf-head">
            <h2 className="shelf-name">Recently added</h2>
          </div>
          <ShelfBooks>
            {shelf.books.map((book) => (
              <Book
                key={book.id}
                book={{ title: book.title, authorName: book.author_name }}
                onOpen={(element) => open(book, element)}
              />
            ))}
          </ShelfBooks>
          <div className="ledge" />
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
        </section>
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
