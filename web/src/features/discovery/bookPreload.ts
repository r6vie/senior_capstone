import { api } from "../../api/client";
import type { components } from "../../api/schema";

// A book is fetched as soon as a reader shows interest in it (pointing at it on the shelf, or focusing it), so when
// it opens, its contents are already there: nothing on its pages appears or changes while it comes forward.
// Answers are kept briefly; an older one is fetched again.

type PublicBook = components["schemas"]["PublicBookResponse"];
type BookAnswer = Awaited<ReturnType<typeof fetchBook>>;

const FRESH_MS = 60_000;
const books = new Map<string, { at: number; answer: Promise<BookAnswer> }>();
const ready = new Map<string, PublicBook>();
let own: { at: number; answer: Promise<{ id: string | null } | null> } | null = null;
let ownReady: { id: string | null } | null = null;

function fetchBook(id: string) {
  return api.GET("/books/{book_id}", { params: { path: { book_id: id } } });
}

/** The book's answer, from an earlier preload when it is recent, else fetched now. `again` always fetches. */
export function loadBook(id: string, again = false): Promise<BookAnswer> {
  const kept = books.get(id);
  if (kept && !again && Date.now() - kept.at < FRESH_MS) return kept.answer;
  const answer = fetchBook(id).then((result) => {
    if (result.data) ready.set(id, result.data);
    else books.delete(id);
    return result;
  });
  answer.catch(() => books.delete(id));
  books.set(id, { at: Date.now(), answer });
  return answer;
}

/** The book if a recent preload already brought it, so a reader can open with it in hand. */
export function loadedBook(id: string): PublicBook | null {
  const kept = books.get(id);
  return kept && Date.now() - kept.at < FRESH_MS ? (ready.get(id) ?? null) : null;
}

/** Which book is the member's own (null id: none yet), to tell Ask to check out from My book. */
export function loadOwnBook(): Promise<{ id: string | null } | null> {
  if (own && Date.now() - own.at < FRESH_MS) return own.answer;
  const answer = api
    .GET("/books/me")
    .then(({ data, response }) => {
      const known = data || response.status === 404 ? { id: data?.id ?? null } : null;
      if (known) ownReady = known;
      else own = null;
      return known;
    })
    .catch(() => {
      own = null;
      return null;
    });
  own = { at: Date.now(), answer };
  return answer;
}

export function loadedOwnBook(): { id: string | null } | null {
  return own && Date.now() - own.at < FRESH_MS ? ownReady : null;
}

/** Forgets everything fetched, so each test starts from nothing. */
export function forgetLoadedBooks(): void {
  books.clear();
  ready.clear();
  own = null;
  ownReady = null;
}
