import { useCallback, useEffect, useRef, useState } from "react";
import { api } from "../../api/client";
import { errorMessage } from "../../api/errors";
import type { components } from "../../api/schema";

export type Recommendation = components["schemas"]["LibrarianRecommendation"];

export function useRecommendation() {
  const [recommendation, setRecommendation] = useState<Recommendation | null>(null);
  const [busy, setBusy] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const generation = useRef(0);

  const load = useCallback(async () => {
    const request = generation.current;
    setBusy(true);
    setError(null);
    try {
      const { data, error: failure } = await api.GET("/discovery/recommendation");
      if (request !== generation.current) return;
      if (!data) throw new Error(errorMessage(failure));
      setRecommendation(data);
    } catch (failure) {
      if (request === generation.current) {
        setError(failure instanceof Error ? failure.message : "The Librarian couldn't choose a book.");
      }
    } finally {
      if (request === generation.current) setBusy(false);
    }
  }, []);

  useEffect(() => {
    void load();
    return () => {
      generation.current += 1;
    };
  }, [load]);

  return { recommendation, busy, error, retry: load };
}
