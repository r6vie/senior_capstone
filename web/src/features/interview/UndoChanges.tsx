import { useEffect, useRef, useState } from "react";

// Undoing takes approved chapters off the shelf, and they won't be suggested again, so it asks in place
// first. A second press while one is running does nothing.

export function UndoChanges({ onUndo, onDone }: { onUndo: () => Promise<void>; onDone: () => void }) {
  const [asking, setAsking] = useState(false);
  const [working, setWorking] = useState(false);
  const [failed, setFailed] = useState(false);
  const running = useRef(false);
  // Focus goes to the safe answer, so a second Enter can't undo by accident.
  const keep = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (asking) keep.current?.focus();
  }, [asking]);

  async function undo() {
    if (running.current) return;
    running.current = true;
    setWorking(true);
    setFailed(false);
    try {
      await onUndo();
      onDone();
    } catch {
      setFailed(true);
    } finally {
      running.current = false;
      setWorking(false);
    }
  }

  if (!asking) {
    return (
      <button type="button" className="button button-quiet" onClick={() => setAsking(true)}>
        Undo these changes
      </button>
    );
  }
  return (
    <div className="iv-undo">
      <p>Undo these changes? Your book goes back to how it was.</p>
      {failed && (
        <p className="message" role="alert">
          That didn't go through. Your book hasn't changed. Try again.
        </p>
      )}
      <div className="iv-row">
        <button
          type="button"
          className="button button-quiet iv-sm"
          aria-busy={working}
          disabled={working}
          onClick={undo}
        >
          Undo
        </button>
        <button
          type="button"
          ref={keep}
          className="button button-quiet iv-sm"
          onClick={() => setAsking(false)}
        >
          Keep them
        </button>
      </div>
    </div>
  );
}
