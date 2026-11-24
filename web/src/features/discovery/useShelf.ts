import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../../api/client";
import { errorMessage } from "../../api/errors";
import type { BookCard } from "./BookReader";

export function useShelf() {
  const [books, setBooks] = useState<BookCard[]>([]);
  const [next, setNext] = useState<string | null>(null);
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const generation = useRef(0);
  const pending = useRef(false);

  const load = useCallback(async (after?: string) => {
    if (pending.current) return;
    pending.current = true;
    const request = generation.current;
    setBusy(true);
    setError(null);
    try {
      const { data, error: failure } = await api.GET("/books", {
        params: { query: { limit: 20, ...(after ? { after } : {}) } },
      });
      if (request !== generation.current) return;
      if (!data) throw new Error(errorMessage(failure));
      setBooks((current) => {
        const combined = after ? [...current, ...data.books] : data.books;
        return [...new Map(combined.map((book) => [book.id, book])).values()];
      });
      setNext(data.next);
    } catch (failure) {
      if (request === generation.current) {
        setError(failure instanceof Error ? failure.message : "Couldn't load the shelf. Please try again.");
      }
    } finally {
      if (request === generation.current) {
        pending.current = false;
        setBusy(false);
      }
    }
  }, []);

  useEffect(() => {
    pending.current = false;
    void load();
    return () => {
      generation.current += 1;
    };
  }, [load]);

  return { books, next, busy, error, loadMore: () => load(next ?? undefined) };
}
