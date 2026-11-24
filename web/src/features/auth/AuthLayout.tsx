import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import "./Auth.css";

// The signed-out pages (sign in, join, confirm your email). The form side of the canvas's "Reference screen · Sign in"
// (docs/design/shelf/project/SysSignIn.dc.html), set as one centred card on a comic dot ground: the wordmark and one way
// across in a plain strip at the top, then a caption, a page title and one line in the Librarian's voice over the form.

export function AuthLayout({
  caption,
  title,
  voice,
  across,
  children,
}: {
  /** The short label above the title, e.g. "Sign in". */
  caption: string;
  title: string;
  /** One line in the Librarian's voice under the title. */
  voice?: string;
  /** The one link to the other signed-out page, top right. */
  across: { to: string; label: string };
  children: ReactNode;
}) {
  return (
    <div className="auth">
      <div className="auth-tone" aria-hidden="true" />
      <header className="auth-top">
        <Link className="wordmark" to="/" aria-label="Trove home">
          Trove
        </Link>
        <Link className="button button-quiet" to={across.to}>
          {across.label}
        </Link>
      </header>
      <main className="auth-card surf">
        <div className="auth-head">
          <span className="caption">{caption}</span>
          <h1 className="page-title">{title}</h1>
          {voice && <p className="voice auth-voice">{voice}</p>}
        </div>
        {children}
      </main>
    </div>
  );
}
