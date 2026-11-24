import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../../api/client";
import type { components } from "../../api/schema";

// Under the Librarian's cover: the one request waiting on the member, with its bookmark, and their own
// book (Folio front page, docs/design/system.md, Additions). Never a count: one request, by name.

type MyCheckouts = components["schemas"]["MyCheckouts"];
type MyBook = components["schemas"]["MyBookResponse"];

interface Desk {
  waiting: { readerName: string } | null;
  book: { title: string; authorName: string } | null | undefined;
}

function useDesk(): Desk {
  const [desk, setDesk] = useState<Desk>({ waiting: null, book: undefined });
  useEffect(() => {
    let live = true;
    // Each block reads on its own and simply stays away if its read fails: the shelf is the page.
    api
      .GET("/checkouts")
      .then(({ data }) => {
        const lending = (data as MyCheckouts | undefined)?.lending;
        if (!live || !Array.isArray(lending)) return;
        const first = lending
          .filter((checkout) => checkout.status === "waiting")
          .sort((a, b) => a.created_at.localeCompare(b.created_at))[0];
        setDesk((now) => ({ ...now, waiting: first ? { readerName: first.reader_name } : null }));
      })
      .catch(() => undefined);
    api
      .GET("/books/me")
      .then(({ data, response }) => {
        if (!live) return;
        const book = data as MyBook | undefined;
        // A failed read isn't "no book": the card stays away rather than say "Not written yet" to an author.
        if (response?.status !== 404 && !response?.ok) return;
        if (response?.status === 404 || !book?.title) setDesk((now) => ({ ...now, book: null }));
        else setDesk((now) => ({ ...now, book: { title: book.title, authorName: book.author_name } }));
      })
      .catch(() => undefined);
    return () => {
      live = false;
    };
  }, []);
  return desk;
}

/** `underway`: the member is mid-interview with no book yet (the shelf's recommendation says so); undefined
 *  until that is known, so the card never says "Not written yet" and then changes its mind. */
export function FrontDesk({ underway }: { underway?: boolean }) {
  const desk = useDesk();
  const { waiting } = desk;
  const book = desk.book === null && underway === undefined ? undefined : desk.book;
  if (!waiting && book === undefined) return null;
  return (
    <div className="front-desk">
      {waiting && (
        <section className="surf surf-spine desk-block desk-waiting" aria-label="Waiting on you">
          <span className="desk-ribbon" aria-hidden="true" />
          <p>
            <span className="desk-eyebrow">Waiting on you</span>
            <b>{waiting.readerName}</b> asked to check out your book.
          </p>
          <Link to="/checkouts" className="button button-secondary">
            Review request
          </Link>
        </section>
      )}
      {book !== undefined && (
        <section className="surf desk-block desk-book" aria-label="Your book">
          {book && (
            <span className="book book-xs" aria-hidden="true">
              <span className="book-cover">
                <span className="book-title">{book.title}</span>
                <span className="book-author">{book.authorName}</span>
              </span>
            </span>
          )}
          <p>
            <span className="desk-eyebrow">Your book</span>
            <b>{book ? book.title : underway ? "In progress" : "Not written yet"}</b>
          </p>
          {!book && underway ? (
            <Link to="/interview" className="button button-secondary">
              Continue
            </Link>
          ) : (
            <Link to="/my-book" className="button button-secondary">
              Open
            </Link>
          )}
        </section>
      )}
    </div>
  );
}
