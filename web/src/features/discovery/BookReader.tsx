import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { Link } from "react-router-dom";
import { api } from "../../api/client";
import { errorMessage } from "../../api/errors";
import type { components } from "../../api/schema";
import { Button } from "../../ui/Button";
import { SparkButton } from "../book/SparkButton";
import { ContentsPage } from "./ContentsPage";
import "./BookReader.css";

export type BookCard = components["schemas"]["BookCard"];
type PublicBook = components["schemas"]["PublicBookResponse"];
export type BookOrigin = { x: number; y: number; width: number; height: number };

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
  const spread = useRef<HTMLDivElement>(null);
  const heading = useRef<HTMLHeadingElement>(null);
  const [book, setBook] = useState<PublicBook | null>(example ?? null);
  const [error, setError] = useState<string | null>(null);
  const [missing, setMissing] = useState(false);
  const [attempt, setAttempt] = useState(0);
  const [active, setActive] = useState<number | null>(null);
  const [turn, setTurn] = useState(0);
  const [turning, setTurning] = useState(false);
  const [ownBook, setOwnBook] = useState<{ id: string | null } | null>(null);
  const [sparks, setSparks] = useState<components["schemas"]["SparkResponse"][] | null>(null);
  const title =
    book?.title ??
    card?.title ??
    (missing ? "Book unavailable" : error ? "Couldn't open this book" : "Opening book");
  const author = book?.author_name ?? card?.author_name;

  useLayoutEffect(() => {
    const modal = dialog.current;
    const object = spread.current;
    if (!modal || !object) return;
    const opener = document.activeElement as HTMLElement | null;
    const overflow = document.body.style.overflow;
    modal.showModal();
    document.body.style.overflow = "hidden";
    const target = object.getBoundingClientRect();
    if (origin && target.width && target.height) {
      // Before the cover swings left, the closed book occupies the spread's right half.
      object.style.setProperty(
        "--reader-x",
        `${origin.x + origin.width / 2 - (target.x + target.width * 0.75)}px`,
      );
      object.style.setProperty(
        "--reader-y",
        `${origin.y + origin.height / 2 - (target.y + target.height / 2)}px`,
      );
      object.style.setProperty("--reader-scale-x", String(origin.width / (target.width / 2)));
      object.style.setProperty("--reader-scale-y", String(origin.height / target.height));
      object.dataset.arrive = "true";
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
    // These are optional enhancements. Their failure must not stop a public book from opening.
    api
      .GET("/books/me")
      .then(({ data, response }) => {
        if (!stale && (data || response.status === 404)) setOwnBook({ id: data?.id ?? null });
      })
      .catch(() => undefined);
    api
      .GET("/interview/sparks")
      .then(({ data }) => {
        if (!stale && data) setSparks(data);
      })
      .catch(() => undefined);
    return () => {
      stale = true;
    };
  }, [example]);

  useEffect(() => {
    if (turn > 0) heading.current?.focus({ preventScroll: true });
  }, [turn]);

  function turnPage() {
    setTurn((value) => value + 1);
    setTurning(true);
  }

  const chapter = active === null ? null : book?.chapters[active];
  return createPortal(
    <dialog
      ref={dialog}
      className="book-reader"
      aria-labelledby="reader-title"
      onCancel={(event) => {
        event.preventDefault();
        onDismiss();
      }}
    >
      <div className="reader-toolbar">
        <Button variant="quiet" onClick={onDismiss}>
          Back to shelf
        </Button>
        <span>Press Esc to close</span>
      </div>
      <div className="reader-stage">
        <div className="reader-spread" ref={spread}>
          <section className="reader-page reader-left" aria-label="Title page">
            <span className="caption">{example ? "Example book" : "Trove"}</span>
            <div className="reader-title-block">
              <h1 id="reader-title">{title}</h1>
              {author && <p className="reader-author">by {author}</p>}
            </div>
            <div className="reader-left-footer">
              {example ? (
                <p className="muted">The Librarian's example. Real books appear on the shelf below.</p>
              ) : (
                book &&
                !missing &&
                (ownBook?.id === book.id ? (
                  <Link to="/my-book" className="button button-secondary">
                    My book
                  </Link>
                ) : (
                  <Link
                    to={`/checkouts/new/${encodeURIComponent(book.id)}`}
                    className="button button-primary"
                  >
                    Ask to check out
                  </Link>
                ))
              )}
              {!example && book && <p className="muted">A conversation with the author.</p>}
            </div>
          </section>
          <section
            className="reader-page reader-right"
            aria-label="Reading page"
            aria-busy={!book && !error && !missing}
          >
            <header className="reader-page-heading">
              <span className="caption">{chapter ? `Chapter ${(active ?? 0) + 1}` : "Inside the book"}</span>
              <h2 ref={heading} tabIndex={-1}>
                {chapter?.title ?? "Contents"}
              </h2>
            </header>
            {missing ? (
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
            ) : (
              <>
                <div className="reader-contents-view" hidden={active !== null}>
                  <ContentsPage
                    chapters={book.chapters}
                    onTurn={turnPage}
                    onSelect={(index) => {
                      setActive(index);
                      turnPage();
                    }}
                  />
                </div>
                {book.chapters.map((item, index) => (
                  <article
                    key={item.id}
                    className="reader-chapter"
                    hidden={active !== index}
                    aria-label={item.title}
                  >
                    <div className="reader-summary">
                      <p>
                        {item.summary ||
                          (example
                            ? "This example includes chapter titles only."
                            : "No summary is available for this chapter yet.")}
                      </p>
                      {!example && ownBook && ownBook.id !== book.id && sparks && (
                        <SparkButton
                          bookId={book.id}
                          chapterId={item.id}
                          chapterTitle={item.title}
                          hasBook={ownBook.id !== null}
                          sparkId={
                            sparks.find((spark) => spark.book_id === book.id && spark.chapter_id === item.id)
                              ?.id
                          }
                        />
                      )}
                    </div>
                    <Button
                      variant="quiet"
                      onClick={() => {
                        setActive(null);
                        turnPage();
                      }}
                    >
                      Back to contents
                    </Button>
                  </article>
                ))}
              </>
            )}
          </section>
          <div className="reader-cover" aria-hidden="true">
            <div className="reader-cover-front">
              <strong>{title}</strong>
              <span>{author}</span>
            </div>
            <div className="reader-cover-back" />
          </div>
          {turning && (
            <div
              key={turn}
              className="reader-turn-sheet"
              aria-hidden="true"
              onAnimationEnd={() => setTurning(false)}
            />
          )}
        </div>
      </div>
    </dialog>,
    document.body,
  );
}
