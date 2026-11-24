import { type FormEvent, useCallback, useEffect, useId, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../../api/client";
import { errorMessage } from "../../api/errors";
import type { components } from "../../api/schema";
import { Button } from "../../ui/Button";
import { PageLoading } from "../../ui/Loading";
import "./MessagesPage.css";
import { usePageTitle } from "../../ui/usePageTitle";

// The conversation inside an accepted checkout (plan item C3, docs/trove.md §6, §9.8). Small on purpose:
// no live updates, read receipts or typing indicators. The page checks for new messages every so often
// while it's open, and tells the API only what it has actually shown.

type Thread = components["schemas"]["Thread"];
type Message = components["schemas"]["Message"];

const MAX_MESSAGE = 2000;
const CHECK_EVERY_MS = 20_000;

const timeFormat = new Intl.DateTimeFormat(undefined, {
  weekday: "short",
  month: "short",
  day: "numeric",
  hour: "numeric",
  minute: "2-digit",
});
const when = (iso: string) => timeFormat.format(new Date(iso));

function MessageItem({ message, otherName }: { message: Message; otherName: string }) {
  if (message.kind === "note") {
    // From the app, such as a confirmed meeting time: a plain line, not someone's words.
    return (
      <li className="thread-note">
        <span>{message.text}</span> <time dateTime={message.sent_at}>{when(message.sent_at)}</time>
      </li>
    );
  }
  const who = message.from_me ? "You" : message.sender_name || otherName;
  return (
    <li className={message.from_me ? "thread-message thread-mine" : "thread-message"}>
      <p className="thread-meta">
        <strong>{message.kind === "checkout_note" ? `${who}, checking out` : who}</strong>{" "}
        <time dateTime={message.sent_at}>{when(message.sent_at)}</time>
      </p>
      <div className="bubble thread-bubble">{message.text}</div>
    </li>
  );
}

export function MessagesPage() {
  const { checkoutId = "" } = useParams();
  const [thread, setThread] = useState<Thread | null>(null);
  usePageTitle(thread ? `Messages with ${thread.other_name}` : "Messages");
  const [missing, setMissing] = useState(false);
  // A failed check (the server restarting, a dropped connection) never hides a conversation already shown.
  const [loadFailed, setLoadFailed] = useState(false);
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const textId = useId();
  const hintId = useId();
  // Only the newest load may update the page; an older, slower answer must not replace a newer one.
  const latest = useRef(0);
  // The newest message already reported as seen, so a check every 20 seconds doesn't repeat itself.
  const reported = useRef<string | null>(null);
  // A second click or Enter before the first send answers must not post the message twice.
  const sending = useRef(false);

  const load = useCallback(async () => {
    const request = ++latest.current;
    let data: Thread | undefined;
    let notFound = false;
    try {
      const result = await api.GET("/messages/{checkout_id}", {
        params: { path: { checkout_id: checkoutId } },
      });
      data = result.data;
      notFound = result.response.status === 404;
    } catch {
      // A dropped connection: treated like any other failed check below.
    }
    if (request !== latest.current) return;
    if (!data) {
      // Only a real "not found" means there is no conversation; anything else is worth another try.
      if (notFound) setMissing(true);
      else setLoadFailed(true);
      return;
    }
    setLoadFailed(false);
    setThread(data);
    const newest = data.messages.at(-1)?.sent_at;
    // Only what is on screen counts as read, and only while someone can see the page.
    if (newest && newest !== reported.current && document.visibilityState === "visible") {
      try {
        const { response } = await api.POST("/messages/{checkout_id}/read", {
          params: { path: { checkout_id: checkoutId } },
          body: { seen_up_to: newest },
        });
        // Remembered only once it worked, so a failed attempt is tried again on the next check.
        if (response.ok) reported.current = newest;
      } catch {
        // Tried again on the next check.
      }
    }
  }, [checkoutId]);

  useEffect(() => {
    load();
    const timer = window.setInterval(() => {
      if (document.visibilityState === "visible") load();
    }, CHECK_EVERY_MS);
    const onVisible = () => {
      if (document.visibilityState === "visible") load();
    };
    document.addEventListener("visibilitychange", onVisible);
    return () => {
      window.clearInterval(timer);
      document.removeEventListener("visibilitychange", onVisible);
      latest.current += 1;
    };
  }, [load]);

  async function send(event: FormEvent) {
    event.preventDefault();
    if (sending.current) return;
    if (!text.trim()) return setError("Write something first.");
    sending.current = true;
    setBusy(true);
    setError(null);
    let failure: unknown = null;
    try {
      ({ error: failure } = await api.POST("/messages/{checkout_id}", {
        params: { path: { checkout_id: checkoutId } },
        body: { text: text.trim() },
      }));
    } catch {
      failure = { detail: "We couldn't send that. Check your connection and try again." };
    }
    sending.current = false;
    setBusy(false);
    if (failure) return setError(errorMessage(failure));
    setText("");
    // Reload rather than add it by hand, so anything the other person sent meanwhile shows too.
    await load();
  }

  if (missing) {
    return (
      <main className="shell-page messages-page">
        <h1 className="page-title">Messages</h1>
        <div className="empty">
          <h3>This conversation isn't available.</h3>
          <p>
            A conversation opens once the author says yes. <Link to="/checkouts">Back to Checkouts</Link>
          </p>
        </div>
      </main>
    );
  }

  if (!thread && loadFailed) {
    return (
      <main className="shell-page messages-page">
        <h1 className="page-title">Messages</h1>
        <p role="alert" className="message message-error">
          <span>!</span>
          <span>
            We couldn't load this conversation.{" "}
            <Button variant="quiet" onClick={() => load()}>
              Try again
            </Button>
          </span>
        </p>
      </main>
    );
  }

  if (!thread) {
    return (
      <main className="shell-page messages-page" aria-busy="true">
        <PageLoading />
      </main>
    );
  }

  return (
    <main className="shell-page messages-page">
      <p>
        <Link to="/checkouts">Back to Checkouts</Link>
      </p>
      <span className="caption">{thread.book_title}</span>
      <h1 className="page-title">Messages with {thread.other_name}</h1>

      {loadFailed && (
        <p role="status" className="muted">
          Couldn't check for new messages just now. We'll keep trying.
        </p>
      )}
      <ol className="thread" aria-label={`Conversation with ${thread.other_name}`}>
        {thread.messages.map((message) => (
          <MessageItem key={message.id} message={message} otherName={thread.other_name} />
        ))}
      </ol>

      {thread.can_write ? (
        <form onSubmit={send} className="stack thread-form">
          <div className="field" data-invalid={error ? "true" : undefined}>
            <label htmlFor={textId}>Write to {thread.other_name}</label>
            <textarea
              id={textId}
              value={text}
              maxLength={MAX_MESSAGE}
              aria-describedby={hintId}
              onChange={(event) => {
                setText(event.target.value);
                setError(null);
              }}
            />
            <span id={hintId} className="hint" role={error ? "alert" : undefined}>
              {error ?? "Up to 2,000 characters. New messages show up here on their own."}
            </span>
          </div>
          <div>
            <Button type="submit" disabled={busy} aria-busy={busy}>
              Send
            </Button>
          </div>
        </form>
      ) : (
        <p className="muted">This conversation is closed. You can still read it.</p>
      )}
    </main>
  );
}
