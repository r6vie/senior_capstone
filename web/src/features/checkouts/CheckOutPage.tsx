import { type FormEvent, useCallback, useEffect, useId, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { api } from "../../api/client";
import { errorMessage, NO_CONNECTION } from "../../api/errors";
import type { components } from "../../api/schema";
import { Button } from "../../ui/Button";
import { PageLoading } from "../../ui/Loading";
import { BookObject } from "../discovery/BookObject";
import "./Checkouts.css";
import { usePageTitle } from "../../ui/usePageTitle";

// Checking out a book (plan item C1, docs/trove.md §6): one note to the author, one red button.
// The book page (D1) links here with the book's id.

type Book = components["schemas"]["PublicBookResponse"];
const MAX_NOTE = 1000;

export function CheckOutPage() {
  const { bookId = "" } = useParams();
  const navigate = useNavigate();
  const noteId = useId();
  const hintId = useId();
  const [book, setBook] = useState<Book | null>(null);
  usePageTitle(book ? `Check out ${book.title}` : "Check out a book");
  const [missing, setMissing] = useState(false);
  const [failed, setFailed] = useState(false);
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [needsOwnBook, setNeedsOwnBook] = useState(false);

  const load = useCallback(() => {
    let stale = false;
    setFailed(false);
    api
      .GET("/books/{book_id}", { params: { path: { book_id: bookId } } })
      .then(({ data, response }) => {
        if (stale) return;
        if (data) setBook(data);
        // Only a real "not found" means the book isn't there; anything else is worth another try.
        else if (response.status === 404) setMissing(true);
        else setFailed(true);
      })
      .catch(() => {
        if (!stale) setFailed(true);
      });
    return () => {
      stale = true;
    };
  }, [bookId]);

  useEffect(() => load(), [load]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!note.trim()) return setError("Write a short note to the author first.");
    setBusy(true);
    setError(null);
    const {
      data,
      error: failure,
      response,
    } = await api
      .POST("/checkouts", { body: { book_id: bookId, message: note.trim() } })
      .catch(() => ({ data: undefined, error: NO_CONNECTION, response: undefined }));
    setBusy(false);
    if (!data) {
      setNeedsOwnBook(response?.status === 403);
      return setError(errorMessage(failure));
    }
    navigate("/checkouts", { state: { checkedOut: data.book_title, answerBy: data.expires_at } });
  }

  if (failed && !book) {
    return (
      <main className="shell-page checkouts-page">
        <h1 className="page-title">Check out a book</h1>
        <p role="alert" className="message message-error">
          <span>!</span>
          <span>
            We couldn't load this book.{" "}
            <Button variant="quiet" onClick={() => load()}>
              Try again
            </Button>
          </span>
        </p>
      </main>
    );
  }
  if (missing) {
    return (
      <main className="shell-page checkouts-page">
        <h1 className="page-title">Check out a book</h1>
        <div className="empty">
          <h3>This book isn't available right now.</h3>
          <p>
            <Link to="/">Back to the shelf</Link>
          </p>
        </div>
      </main>
    );
  }

  if (!book) {
    return (
      <main className="shell-page checkouts-page" aria-busy="true">
        <PageLoading />
      </main>
    );
  }

  return (
    <main className="shell-page page-rail checkouts-page">
      {/* On a wide screen the head holds the left rail, with the book itself under it (docs/design/system.md
          Additions, "Wide pages"). */}
      <header className="page-rail-head">
        <span className="caption">Check out</span>
        <h1 className="page-title checkout-book-title">{book.title}</h1>
        <p className="checkout-byline">by {book.author_name}</p>
        {book.blurb && <p className="voice checkout-blurb">{book.blurb}</p>}
        <div className="checkout-book">
          <BookObject
            id={book.id}
            design={book.design}
            book={{ title: book.title, authorName: book.author_name }}
          />
        </div>
      </header>

      <form onSubmit={submit} className="stack checkout-form">
        <div className="field" data-invalid={error && !needsOwnBook ? "true" : undefined}>
          <label htmlFor={noteId}>Your note to {book.author_name}</label>
          <textarea
            id={noteId}
            value={note}
            maxLength={MAX_NOTE}
            aria-describedby={error && !needsOwnBook ? hintId : undefined}
            onChange={(event) => {
              setNote(event.target.value);
              setError(null);
              setNeedsOwnBook(false);
            }}
          />
          {error && !needsOwnBook && (
            <span id={hintId} className="hint" role="alert">
              {error}
            </span>
          )}
        </div>
        {needsOwnBook && (
          <p role="alert" className="message message-error">
            <span>!</span>
            <span>
              {error} <Link to="/my-book">Go to my book</Link>
            </span>
          </p>
        )}
        <div className="checkout-submit">
          <Button type="submit" disabled={busy} aria-busy={busy}>
            Ask to check out
          </Button>
        </div>
      </form>
    </main>
  );
}
