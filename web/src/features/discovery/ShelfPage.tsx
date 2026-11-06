import { Button } from "../../ui/Button";
import { useAuth } from "../auth/AuthProvider";
import { type SampleBook, sampleBooks, sampleFeatured, sampleShelves } from "./sampleBooks";
import "./ShelfPage.css";

// A static preview of the shelf (reference screen manga B2, docs/design/system.md). Books, the nav,
// "See all" and "Ask to check out" are drawn but not wired yet: nothing here has a handler or a route.

const booksById = new Map(sampleBooks.map((book) => [book.id, book]));

function bookById(id: string): SampleBook {
  const book = booksById.get(id);
  if (!book) throw new Error(`Sample book ${id} is missing.`);
  return book;
}

function Book({ book, size }: { book: SampleBook; size?: "lg" }) {
  return (
    <button
      type="button"
      className={size === "lg" ? "book book-lg" : "book"}
      aria-label={`${book.title}, by ${book.firstName}`}
    >
      <span className="book-cover">
        <span className="book-title">{book.title}</span>
        <span className="book-author">{book.firstName}</span>
      </span>
    </button>
  );
}

const NAV_ITEMS = ["Shelf", "My book", "Checkouts", "Past meets"];

export function ShelfPage() {
  const { user } = useAuth();
  const featured = bookById(sampleFeatured.bookId);

  return (
    <div className="shelf-page">
      <header className="top-bar">
        <span className="wordmark">Trove</span>
        <nav className="nav" aria-label="Main">
          {NAV_ITEMS.map((item) => (
            // biome-ignore lint/a11y/useValidAnchor: inert in this static preview; the routes don't exist yet
            <a key={item} aria-current={item === "Shelf" ? "page" : undefined}>
              {item}
            </a>
          ))}
        </nav>
        <div className="top-bar-end">
          <label className="search">
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <circle cx="11" cy="11" r="7" />
              <path d="m20 20-3.5-3.5" />
            </svg>
            <input type="search" placeholder="Search by topic" aria-label="Search by topic" />
          </label>
          <span className="avatar" aria-hidden="true">
            {user?.first_name.charAt(0)}
          </span>
        </div>
      </header>

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
              <p className="feature-author">by {featured.firstName}</p>
              <p className="voice feature-reason">{sampleFeatured.reason}</p>
            </div>
            <div className="feature-book">
              <div className="halo" />
              <Book book={featured} size="lg" />
            </div>
            <div className="feature-action">
              <Button>Ask to check out</Button>
              <span className="feature-note">A thirty-minute video call</span>
            </div>
          </div>
          <div className="feature-rule" />
        </section>

        {sampleShelves.map((shelf) => (
          <section key={shelf.name} className="shelf-row" aria-label={shelf.name}>
            <div className="shelf-head">
              <h2 className="shelf-name">{shelf.name}</h2>
              {/* biome-ignore lint/a11y/useValidAnchor: inert in this static preview */}
              <a>See all</a>
            </div>
            <div className="shelf-books">
              {shelf.bookIds.map((id) => (
                <Book key={id} book={bookById(id)} />
              ))}
            </div>
            <div className="ledge" />
          </section>
        ))}
      </main>
    </div>
  );
}
