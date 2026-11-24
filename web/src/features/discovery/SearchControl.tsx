import { type FormEvent, type RefObject, useCallback, useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { api } from "../../api/client";
import { errorMessage } from "../../api/errors";
import type { components } from "../../api/schema";
import { artFor, loadArt } from "../../ui/art/bookArt";
import { Button } from "../../ui/Button";
import { BookObject } from "./BookObject";
import { type BookOrigin, BookReader } from "./BookReader";
import { loadBook } from "./bookPreload";
import "./SearchControl.css";

type SearchResult = components["schemas"]["SearchResult"];
type OpenedResult = { result: SearchResult; origin: BookOrigin };
const SEARCH_DELAY_MS = 200;

function Magnifier() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <circle cx="11" cy="11" r="7" />
      <path d="m20 20-3.5-3.5" />
    </svg>
  );
}

export function SearchControl({ triggerRef }: { triggerRef: RefObject<HTMLInputElement | null> }) {
  const dialog = useRef<HTMLDialogElement>(null);
  const field = useRef<HTMLInputElement>(null);
  const timer = useRef<ReturnType<typeof setTimeout>>(undefined);
  const generation = useRef(0);
  const restoreFocus = useRef(true);
  const suppressOpen = useRef(false);
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [busy, setBusy] = useState(false);
  const [searched, setSearched] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [opened, setOpened] = useState<OpenedResult | null>(null);

  const load = useCallback(async (value: string) => {
    const search = value.trim();
    const request = ++generation.current;
    if (search.length < 2) {
      setResults([]);
      setSearched(false);
      setBusy(false);
      setError(null);
      return;
    }
    setBusy(true);
    setResults([]);
    setError(null);
    try {
      const { data, error: failure } = await api.GET("/discovery/search", {
        params: { query: { q: search } },
      });
      if (request !== generation.current) return;
      if (!data) throw new Error(errorMessage(failure));
      setResults(data.results);
      setSearched(true);
    } catch (failure) {
      if (request === generation.current) {
        setError(failure instanceof Error ? failure.message : "Search isn't available right now.");
        setSearched(true);
      }
    } finally {
      if (request === generation.current) setBusy(false);
    }
  }, []);

  useEffect(() => {
    if (!open) return;
    clearTimeout(timer.current);
    if (query.trim().length < 2) {
      void load(query);
      return;
    }
    timer.current = setTimeout(() => void load(query), SEARCH_DELAY_MS);
    return () => clearTimeout(timer.current);
  }, [load, open, query]);

  useEffect(() => {
    if (!open) return;
    const element = dialog.current;
    const previousOverflow = document.documentElement.style.overflow;
    if (element && !element.open) element.showModal();
    document.documentElement.style.overflow = "hidden";
    field.current?.focus();
    return () => {
      document.documentElement.style.overflow = previousOverflow;
    };
  }, [open]);

  function show() {
    if (suppressOpen.current) {
      suppressOpen.current = false;
      return;
    }
    setOpen(true);
  }

  function close(shouldRestoreFocus = true) {
    clearTimeout(timer.current);
    generation.current += 1;
    restoreFocus.current = shouldRestoreFocus;
    setBusy(false);
    dialog.current?.close();
  }

  function submit(event: FormEvent) {
    event.preventDefault();
    clearTimeout(timer.current);
    void load(query);
  }

  function openBook(result: SearchResult, element: HTMLButtonElement) {
    const { x, y, width, height } = element.getBoundingClientRect();
    const origin = { x, y, width, height };
    loadBook(result.book.id);
    loadArt(artFor(result.book.id, result.book.design));
    setOpened({ result, origin });
  }

  function leaveReader() {
    setOpened(null);
    setOpen(false);
    setBusy(false);
    clearTimeout(timer.current);
    generation.current += 1;
    restoreFocus.current = false;
    dialog.current?.close();
  }

  const overlay = open ? (
    <dialog
      ref={dialog}
      className="search-overlay"
      aria-label="Search books"
      onCancel={(event) => {
        event.preventDefault();
        close();
      }}
      onClose={() => {
        setOpen(false);
        if (restoreFocus.current) {
          suppressOpen.current = true;
          triggerRef.current?.focus();
          queueMicrotask(() => {
            suppressOpen.current = false;
          });
        }
      }}
    >
      <button type="button" className="search-close" aria-label="Close search" onClick={() => close()}>
        <span aria-hidden="true">×</span>
      </button>
      <div className="search-overlay-inner">
        <form className="search-overlay-form" onSubmit={submit}>
          <label htmlFor="book-search">Search Trove</label>
          <div className="search-overlay-field">
            <Magnifier />
            <input
              ref={field}
              id="book-search"
              type="search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search stories, topics, and people"
              autoComplete="off"
            />
          </div>
          <Button type="submit" disabled={query.trim().length < 2 || busy}>
            Search
          </Button>
        </form>

        <section className="search-results" aria-live="polite" aria-busy={busy}>
          {query.trim().length < 2 && (
            <div className="search-intro">
              <h1>Find a story worth opening</h1>
              <p>Search experiences, questions, skills, chapters, or people.</p>
            </div>
          )}
          {query.trim().length >= 2 && busy && <p role="status">Searching the shelves…</p>}
          {error && (
            <div className="message message-error" role="alert">
              <p>{error}</p>
              <Button variant="secondary" onClick={() => void load(query)}>
                Try again
              </Button>
            </div>
          )}
          {!busy && !error && searched && results.length === 0 && (
            <div className="empty">
              <h2>No books found.</h2>
              <p>Try a broader topic, a different question, or an author's name.</p>
            </div>
          )}
          {!error && results.length > 0 && (
            <>
              <h1>Books</h1>
              <div className="search-results-grid">
                {results.map((result) => (
                  <article className="search-result" key={result.book.id}>
                    <BookObject
                      id={result.book.id}
                      book={{ title: result.book.title, authorName: result.book.author_name }}
                      out={opened?.result.book.id === result.book.id}
                      onOpen={(element) => openBook(result, element)}
                      onInterest={() => {
                        loadBook(result.book.id);
                        loadArt(artFor(result.book.id, result.book.design));
                      }}
                    />
                    <p>{result.excerpt}</p>
                  </article>
                ))}
              </div>
            </>
          )}
        </section>
      </div>
    </dialog>
  ) : null;

  return (
    <>
      <label className="search">
        <Magnifier />
        <input
          ref={triggerRef}
          type="search"
          value={query}
          readOnly
          placeholder="Search stories, topics, and people"
          aria-label="Search stories, topics, and people"
          aria-keyshortcuts="/"
          aria-haspopup="dialog"
          onFocus={show}
          onClick={show}
        />
        <span className="search-key" aria-hidden="true">
          /
        </span>
      </label>
      {typeof document === "undefined" ? null : createPortal(overlay, document.body)}
      {opened && (
        <BookReader
          bookId={opened.result.book.id}
          card={opened.result.book}
          origin={opened.origin}
          onDismiss={() => setOpened(null)}
          onNavigate={leaveReader}
        />
      )}
    </>
  );
}
