import { type ReactNode, useId, useState } from "react";
import { Link } from "react-router-dom";
import "./Auth.css";

// The signed-out pages (StartJoin, approved by Josef 2026-11-23): your unwritten book on one side and the form on the
// other. The left half is the dot ground with the Librarian's line in a caption box and a white book standing on a
// shelf; joining letters the member's name onto its cover as they type it. An invite is a library card behind the book.
// On a phone the book stands on a short dot band above the form.

export function AuthLayout({
  caption,
  title,
  voice,
  across,
  author,
  invitedBy,
  children,
}: {
  /** The short label above the title, e.g. "Sign in". */
  caption: string;
  title: string;
  /** The Librarian's line, in the caption box over the book. */
  voice: string;
  /** The one link to the other signed-out page, top right. */
  across: { to: string; label: string };
  /** The name on the white cover. Empty shows where it will go; leave it out for a book with no name yet. */
  author?: string;
  /** Who sent the invite link this member came from. */
  invitedBy?: string | null;
  children: ReactNode;
}) {
  return (
    <div className="auth">
      <header className="auth-top">
        <Link className="wordmark" to="/" aria-label="Trove home">
          Trove
        </Link>
        <Link className="auth-across" to={across.to}>
          {across.label}
        </Link>
      </header>
      <div className="auth-split">
        <section className="auth-l">
          <div className="auth-cap">
            <p>{voice}</p>
          </div>
          <div className="auth-stage">
            {invitedBy && (
              <p className="auth-card">
                <span className="auth-card-k">Invited by</span>
                <span className="auth-card-v">{invitedBy}</span>
                <span className="auth-card-r" aria-hidden="true" />
                <span className="auth-card-r" aria-hidden="true" />
              </p>
            )}
            <span className="auth-book" aria-hidden="true">
              <span className="auth-cover">
                <span className="auth-bar auth-bar-m" />
                <span className="auth-bar" />
                <span className="auth-bar auth-bar-s" />
                {author !== undefined && (
                  <span className="auth-author" data-ghost={author ? undefined : true}>
                    {author || "Your name"}
                  </span>
                )}
              </span>
            </span>
          </div>
          <span className="auth-shelf" aria-hidden="true" />
        </section>
        <main className="auth-r">
          <span className="caption">{caption}</span>
          <h1 className="auth-title">{title}</h1>
          {children}
        </main>
      </div>
    </div>
  );
}

/** A password field with a Show link inside it, so the member can check what they typed. */
export function PasswordField({
  value,
  onChange,
  autoComplete,
  hint,
}: {
  value: string;
  onChange: (value: string) => void;
  autoComplete: "new-password" | "current-password";
  hint?: string;
}) {
  const id = useId();
  const hintId = useId();
  const [shown, setShown] = useState(false);
  return (
    <div className="field">
      <label htmlFor={id}>Password</label>
      <span className="auth-pw">
        <input
          id={id}
          type={shown ? "text" : "password"}
          value={value}
          autoComplete={autoComplete}
          aria-describedby={hint ? hintId : undefined}
          onChange={(event) => onChange(event.target.value)}
        />
        <button
          type="button"
          className="auth-show"
          aria-label={shown ? "Hide password" : "Show password"}
          onClick={() => setShown((now) => !now)}
        >
          {shown ? "Hide" : "Show"}
        </button>
      </span>
      {hint && (
        <small id={hintId} className="muted">
          {hint}
        </small>
      )}
    </div>
  );
}

const DIGITS = 6;

/** The emailed code as six boxes, three and three. One real field sits over them, so typing, pasting and the
 *  phone's one-time-code suggestion all work as they would in a plain field. */
export function CodeField({ value, onChange }: { value: string; onChange: (value: string) => void }) {
  const id = useId();
  const [focused, setFocused] = useState(false);
  const at = Math.min(value.length, DIGITS - 1);
  return (
    <div className="field">
      <label htmlFor={id}>Code</label>
      <span className="auth-code">
        <input
          id={id}
          className="auth-code-input"
          value={value}
          inputMode="numeric"
          autoComplete="one-time-code"
          maxLength={DIGITS}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          onChange={(event) => onChange(event.target.value.replace(/\D/g, "").slice(0, DIGITS))}
        />
        <span className="auth-digits" aria-hidden="true">
          {Array.from({ length: DIGITS }, (_, index) => (
            <span
              // biome-ignore lint/suspicious/noArrayIndexKey: the code's six fixed places
              key={index}
              data-on={focused && index === at ? true : undefined}
              data-gap={index === DIGITS / 2 ? true : undefined}
            >
              {value[index] ?? ""}
            </span>
          ))}
        </span>
      </span>
    </div>
  );
}
