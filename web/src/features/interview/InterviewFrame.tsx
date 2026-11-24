import { createContext, type ReactNode, useContext, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { Button } from "../../ui/Button";
import { useAuth } from "../auth/AuthProvider";
import type { Phase } from "./interviewClient";
import { LeftoverWords } from "./LeftoverWords";
import { reducedMotion } from "./librarian/pen";
import "./InterviewPage.css";

// The Librarian's line and its top bar, shared by every interview screen: the first interview, adding to
// a book, proposed changes and the reading question.

const PHASES: { id: Phase; label: string }[] = [
  { id: "sweep", label: "First look" },
  { id: "dig", label: "Deeper" },
  { id: "shape", label: "Check" },
];

/** Arriving on a screen starts the keyboard at the Librarian's words. */
export function focusLine() {
  document.querySelector<HTMLElement>(".iv-say")?.focus({ preventScroll: true });
}

// A wait this long gets one calm line.
const SLOW_AFTER_MS = 10_000;
/** A wait shorter than this shows nothing new: what was there stays, so a quick reply never flashes a line. */
export const WAIT_SHOWS_AFTER_MS = 300;

/** A line that starts with "The Librarian" needs no label saying who speaks. Today every such line is a
 * wait; this keeps the rule for any that isn't. */
function namesLibrarian(say: ReactNode): boolean {
  return typeof say === "string" && say.startsWith("The Librarian");
}

export function Frame({
  phase,
  say,
  busy,
  canLeave = true,
  quiet = false,
  eyebrow,
  children,
}: {
  phase?: Phase;
  canLeave?: boolean;
  /** The line steps back, on a screen where something below it is the focus. */
  quiet?: boolean;
  /** A small caption above the Librarian's words. */
  eyebrow?: string;
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
  // The label steps aside with the line: only once the waiting line shows (Waiting), never for a quick reply.
  const [waitShows, setWaitShows] = useState(false);
  useEffect(() => {
    setWaitShows(false);
    if (!busy) return;
    const timer = setTimeout(() => setWaitShows(true), WAIT_SHOWS_AFTER_MS);
    return () => clearTimeout(timer);
  }, [busy]);

  return (
    <div className="interview">
      <header className="iv-top">
        <Link className="wordmark" to="/" aria-label="Trove home">
          Trove
        </Link>
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
      {/* No band (StartReveal): the Librarian's line runs across the top of the page, under a small label
          unless the line already names it. On a wait the label is hidden but keeps its place, so the line
          doesn't move when the wait starts or ends. */}
      <section className="iv-line">
        {(eyebrow || !namesLibrarian(say)) && (
          <span
            className="iv-eyebrow"
            data-hidden={waitShows || undefined}
            aria-hidden={waitShows || undefined}
          >
            {eyebrow ?? "The Librarian"}
          </span>
        )}
        <h1 className="iv-say" data-quiet={quiet || undefined} tabIndex={-1} aria-live="polite">
          {say}
        </h1>
        {slow && (
          <p className="iv-still" role="status">
            Still working. Your answers are saved.
          </p>
        )}
      </section>
      {/* Outside the part that goes inert during a wait: these words have to stay selectable. */}
      <LeftoverWords />
      <main className="iv-act" tabIndex={-1} inert={busy} aria-busy={busy}>
        {children}
      </main>
    </div>
  );
}

/** The plain top bar of the question screens and the intro book: the wordmark, Leave for now, the avatar. */
export function IvTop() {
  const { user } = useAuth();
  return (
    <header className="iv-top iv-top-plain">
      <Link className="wordmark" to="/" aria-label="Trove home">
        Trove
      </Link>
      <span className="iv-grow" />
      <Link to="/my-book" className="button button-quiet">
        Leave<span className="iv-wide-only"> for now</span>
      </Link>
      {user && (
        <Link to="/settings" className="avatar" aria-label="Settings">
          {user.first_name.charAt(0)}
          {user.last_name?.charAt(0)}
        </Link>
      )}
    </header>
  );
}

/** The question screen with the Librarian (LibDesktop, LibPhone): a plain header, the question as words
 * on the page, the answer card under it, and the Librarian's notebook beside them. */
export function AskFrame({
  eyebrow,
  question,
  typing = false,
  busy,
  aside,
  children,
}: {
  /** "Question", or "Adding to your book" in a round on a shelved book. */
  eyebrow: string;
  question: ReactNode;
  /** The question is typing in (StartOpen): its place keeps two lines, so the cards under it hold still. */
  typing?: boolean;
  busy?: boolean;
  /** The notebook. */
  aside?: ReactNode;
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
    <div className="interview iv-ask">
      <IvTop />
      {/* Outside the part that goes inert during a wait: these words have to stay selectable. */}
      <LeftoverWords />
      <main className="iv-act" tabIndex={-1} inert={busy} aria-busy={busy}>
        {/* The question runs the full width; the answer and the notebook start level under it (StartOpen). */}
        <div className="iv-question">
          <p className="iv-qeye">{eyebrow}</p>
          <h1 className="iv-say iv-q" data-typing={typing || undefined} tabIndex={-1} aria-live="polite">
            {question}
          </h1>
          {slow && (
            <p className="iv-still" role="status">
              Still working. Your answers are saved.
            </p>
          )}
        </div>
        <div className="lib-cols">
          <div className="lib-main">{children}</div>
          {aside}
        </div>
      </main>
    </div>
  );
}

// One letter of the first question every this many milliseconds: quick, but readable as typing.
const TYPE_MS = 28;

/** The first question typing in at the top (StartOpen), letter by letter, once `after` milliseconds
 * have passed. */
export function TypedQuestion({ text, after, onDone }: { text: string; after: number; onDone: () => void }) {
  // With reduced motion the question is simply there, whole.
  const [still] = useState(reducedMotion);
  const [count, setCount] = useState(still ? text.length : 0);
  const done = useRef(onDone);
  done.current = onDone;
  useEffect(() => {
    if (still) return;
    let timer: ReturnType<typeof setTimeout>;
    let typed = 0;
    const tick = () => {
      typed += 1;
      setCount(typed);
      if (typed < text.length) timer = setTimeout(tick, TYPE_MS);
      else done.current();
    };
    timer = setTimeout(tick, after);
    return () => clearTimeout(timer);
  }, [text, after, still]);
  // The whole question sits invisibly under the typed letters, so its place is its final size from the
  // first letter and nothing under it moves as it wraps. Screen readers read that whole question, once.
  return (
    <span className="iv-typed">
      <span className="iv-typed-full">{text}</span>
      <span className="iv-typed-now" aria-hidden="true">
        {text.slice(0, count)}
        {count < text.length && <span className="iv-caret" />}
      </span>
    </span>
  );
}

export function Waiting({ children, holding }: { children: ReactNode; holding?: ReactNode }) {
  // For a moment the line stays as it was; a reply that quick never shows a waiting line at all.
  const [shown, setShown] = useState(!holding);
  useEffect(() => {
    if (shown) return;
    const timer = setTimeout(() => setShown(true), WAIT_SHOWS_AFTER_MS);
    return () => clearTimeout(timer);
  }, [shown]);
  if (!shown) return <>{holding}</>;
  // The line keeps the height of what it held, so the page doesn't jump while the Librarian thinks.
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
