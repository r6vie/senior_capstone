import { useCallback, useRef, useState } from "react";

// Screen readers hear each of the Librarian's lines once, as "Librarian: …". The handwriting itself is
// hidden from them (LIBRARIAN_SPEC.md §16).

export function useAnnouncer() {
  const [message, setMessage] = useState("");
  const said = useRef(new Set<string>());
  const say = useCallback((line: string) => {
    if (said.current.has(line)) return;
    said.current.add(line);
    setMessage((before) => (before ? `${before} ${line}` : line));
    // Cleared after a moment, so the next line is read on its own.
    setTimeout(() => setMessage((now) => (now.endsWith(line) ? "" : now)), 4000);
  }, []);
  const region = (
    <p className="iv-visually-hidden" aria-live="polite">
      {message}
    </p>
  );
  return { say, region };
}
