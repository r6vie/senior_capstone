import { createContext, type ReactNode, useContext, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { Button } from "../../ui/Button";
import type { Phase } from "./interviewClient";
import "./InterviewPage.css";

// The question band and its top bar, shared by every interview screen: the first interview, adding to
// a book, proposed changes and the reading question.

const PHASES: { id: Phase; label: string }[] = [
  { id: "sweep", label: "First look" },
  { id: "dig", label: "Deeper" },
  { id: "shape", label: "Check" },
];

// A wait this long gets one calm line.
const SLOW_AFTER_MS = 15_000;

export function Frame({
  phase,
  say,
  busy,
  canLeave = true,
  quiet = false,
  children,
}: {
  phase?: Phase;
  canLeave?: boolean;
  /** The band steps back, on a screen where something below it is the focus. */
  quiet?: boolean;
  say: ReactNode;
  /** While the Librarian works, the member's side holds still rather than greying out. */
  busy?: boolean;
  children?: ReactNode;
}) {
  const [slow, setSlow] = useState(false);
  useEffect(() => {
    setSlow(false);
    if (!busy) return;
    const timer = setTimeout(() => setSlow(true), SLOW_AFTER_MS);
    return () => clearTimeout(timer);
  }, [busy]);

  return (
    <div className="interview">
      <header className="iv-top">
        <span className="wordmark">Trove</span>
        {phase && (
          <ol className="iv-phases" aria-label="Where we are">
            {PHASES.map((item) => (
              <li key={item.id} aria-current={item.id === phase ? "step" : undefined}>
                {item.label}
              </li>
            ))}
          </ol>
        )}
        {canLeave && (
          <Link to="/my-book" className="button button-quiet">
            Leave for now
          </Link>
        )}
      </header>
      <section className="iv-band dark">
        <span className="halo" />
        <h1 className="iv-say" data-quiet={quiet || undefined} tabIndex={-1} aria-live="polite">
          {say}
        </h1>
        {slow && (
          <p className="iv-still" role="status">
            Still working. Your answers are saved.
          </p>
        )}
      </section>
      <main className="iv-act" tabIndex={-1} inert={busy} aria-busy={busy}>
        {children}
      </main>
    </div>
  );
}

export function Waiting({ children, holding }: { children: ReactNode; holding?: ReactNode }) {
  // The band keeps the height of what it held, so the page doesn't jump while the Librarian thinks.
  return (
    <>
      {holding && (
        <span className="iv-holding" aria-hidden="true">
          {holding}
        </span>
      )}
      <span className="iv-waiting" data-over={Boolean(holding)}>
        {children}
      </span>
    </>
  );
}

// Set when the last call failed in a way that is safe to repeat (the Librarian couldn't answer).
export const RetryContext = createContext<(() => void) | null>(null);

export function ErrorMessage({ message }: { message: string | null }) {
  const retry = useContext(RetryContext);
  const box = useRef<HTMLDivElement>(null);
  // On a phone the member can be several chapters away from where the error appears.
  useEffect(() => {
    if (message) box.current?.scrollIntoView?.({ block: "nearest" });
  }, [message]);
  if (!message) return null;
  return (
    <div className="iv-error" ref={box}>
      <div className="message message-error" role="alert">
        <span>{message}</span>
      </div>
      {retry && (
        <Button variant="secondary" className="iv-sm" onClick={retry}>
          Try again
        </Button>
      )}
    </div>
  );
}

export function SmallBook({ title, author }: { title: string; author: string }) {
  return (
    // The title and name are printed beside it, so a screen reader shouldn't hear them twice.
    <span className="book book-sm" aria-hidden="true">
      <span className="book-cover">
        <span className="book-title">{title}</span>
        <span className="book-author">{author}</span>
      </span>
    </span>
  );
}
