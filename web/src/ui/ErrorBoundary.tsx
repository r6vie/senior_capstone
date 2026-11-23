import { Component, type ErrorInfo, type ReactNode } from "react";

// A bug in one page shouldn't blank the whole app. Inside the shell this keeps the top bar and replaces only
// the page; around the whole app it is the last net. `resetKey` (the page's address) clears it on navigation.

type Props = {
  children: ReactNode;
  resetKey?: string;
  /** What to show instead of the page; gets a function that tries the page again. */
  fallback: (retry: () => void) => ReactNode;
};

export class ErrorBoundary extends Component<Props, { failed: boolean }> {
  state = { failed: false };

  static getDerivedStateFromError() {
    return { failed: true };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    // Kept in the console for whoever is debugging; the member sees a plain sentence.
    console.error(error, info.componentStack);
  }

  componentDidUpdate(previous: Props) {
    if (this.state.failed && previous.resetKey !== this.props.resetKey) this.setState({ failed: false });
  }

  retry = () => this.setState({ failed: false });

  render() {
    return this.state.failed ? this.props.fallback(this.retry) : this.props.children;
  }
}

/** The plain page shown when a page breaks: what happened, and two ways on. */
export function PageBroke({ retry, home }: { retry: () => void; home: ReactNode }) {
  return (
    <main className="shell-page">
      <div className="empty" role="alert">
        <h1 className="page-broke-title">Something went wrong on this page</h1>
        <p>It's not something you did. Try it again, or go back to the shelf.</p>
        <p className="page-broke-actions">
          <button type="button" className="button button-secondary" onClick={retry}>
            Try again
          </button>
          {home}
        </p>
      </div>
    </main>
  );
}
