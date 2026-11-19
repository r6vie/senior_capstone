import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { api } from "../../api/client";
import { errorMessage } from "../../api/errors";
import type { components } from "../../api/schema";
import { Button } from "../../ui/Button";
import { ContactDetails } from "./ContactDetails";
import { DidYouMeet } from "./DidYouMeet";
import { formatDay } from "./dates";
import "./Checkouts.css";

// Checkouts (plan item C1, docs/trove.md §6): requests for your book first, since they wait on you,
// then the books you've checked out. No counts anywhere, and no red: nothing here is the one next step
// for every member (docs/design/system.md).

type Mine = components["schemas"]["MyCheckouts"];
type Lending = components["schemas"]["LendingCheckout"];
type Reading = components["schemas"]["ReadingCheckout"];
type Act = (path: "accept" | "decline" | "cancel", id: string) => Promise<string | null>;
// After a Yes or No to "Did you meet?": the checkout closes, so the page says so before it reloads.
type Answered = (name: string, final: boolean) => Promise<void>;

function Note({ text }: { text: string }) {
  return <blockquote className="checkout-note">{text}</blockquote>;
}

// After a yes: the conversation (C3) and arranging the meeting (M1). "New message" is private to you and
// never a count (docs/trove.md §6).
function AcceptedActions({ id, newMessages }: { id: string; newMessages: boolean }) {
  return (
    <div className="checkout-actions">
      <Link className="button button-secondary" to={`/checkouts/${id}/messages`}>
        Messages
      </Link>
      {newMessages && <span className="caption checkout-new">New message</span>}
      <Link className="button button-secondary" to={`/checkouts/${id}/meeting`}>
        Arrange the reading
      </Link>
    </div>
  );
}

function ItemError({ text }: { text: string | null }) {
  if (!text) return null;
  return (
    <p role="alert" className="message message-error">
      <span>!</span>
      <span>{text}</span>
    </p>
  );
}

function LendingItem({ item, act, answered }: { item: Lending; act: Act; answered: Answered }) {
  const [busy, setBusy] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function run(path: "accept" | "decline") {
    setBusy(true);
    setError(await act(path, item.id));
    setBusy(false);
  }

  return (
    <li className="checkout">
      <h3 className="checkout-name">{item.reader_name}</h3>
      {item.reader_book && <p className="muted">Author of "{item.reader_book.title}"</p>}
      <Note text={item.message} />
      {item.status === "accepted" ? (
        <>
          <p>You said yes.</p>
          {item.did_you_meet && (
            <DidYouMeet
              checkoutId={item.id}
              name={item.reader_name}
              view={item.did_you_meet}
              onAnswered={(answer) => answered(item.reader_name, answer !== "not_yet")}
            />
          )}
          {item.reader_contact && <ContactDetails name={item.reader_name} contact={item.reader_contact} />}
          <AcceptedActions id={item.id} newMessages={item.new_messages ?? false} />
        </>
      ) : confirming ? (
        <div className="checkout-actions">
          <span>Decline {item.reader_name}'s checkout? They'll see the book isn't available right now.</span>
          <Button variant="secondary" disabled={busy} aria-busy={busy} onClick={() => run("decline")}>
            Decline
          </Button>
          <Button variant="quiet" disabled={busy} onClick={() => setConfirming(false)}>
            Keep it
          </Button>
        </div>
      ) : (
        <>
          {item.expires_at && (
            <p className="muted">
              If you don't answer by {formatDay(item.expires_at)}, it closes on its own.
            </p>
          )}
          <div className="checkout-actions">
            <Button variant="secondary" disabled={busy} aria-busy={busy} onClick={() => run("accept")}>
              Accept
            </Button>
            <Button variant="quiet" disabled={busy} onClick={() => setConfirming(true)}>
              Decline
            </Button>
          </div>
        </>
      )}
      <ItemError text={error} />
    </li>
  );
}

function readingStatus(item: Reading): string {
  switch (item.status) {
    case "waiting":
      return item.expires_at
        ? `Waiting for an answer. If there's none by ${formatDay(item.expires_at)}, it closes on its own.`
        : "Waiting for an answer.";
    case "accepted":
      return "Accepted.";
    case "cancelled":
      return "You cancelled this checkout.";
    case "returned":
      return "Returned.";
    default:
      return "This book isn't available right now.";
  }
}

function ReadingItem({ item, act, answered }: { item: Reading; act: Act; answered: Answered }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function cancel() {
    setBusy(true);
    setError(await act("cancel", item.id));
    setBusy(false);
  }

  return (
    <li className="checkout">
      <h3 className="checkout-book">{item.book_title}</h3>
      <p className="muted">by {item.author_name}</p>
      <Note text={item.message} />
      <p>{readingStatus(item)}</p>
      {item.did_you_meet && (
        <DidYouMeet
          checkoutId={item.id}
          name={item.author_name}
          view={item.did_you_meet}
          returned={item.status === "returned"}
          onAnswered={(answer) => answered(item.author_name, answer !== "not_yet")}
        />
      )}
      {/* Contacts on a returned checkout mean it's a Past meet, where they and the conversation now live. */}
      {item.status === "returned" && item.author_contact && (
        <p>
          <Link to="/past-meets">See {item.author_name} in Past meets</Link>
        </p>
      )}
      {item.status === "accepted" && item.author_contact && (
        <ContactDetails name={item.author_name} contact={item.author_contact} />
      )}
      {item.status === "accepted" && (
        <AcceptedActions id={item.id} newMessages={item.new_messages ?? false} />
      )}
      {item.status === "waiting" && (
        <div className="checkout-actions">
          <Button variant="quiet" disabled={busy} aria-busy={busy} onClick={cancel}>
            Cancel checkout
          </Button>
        </div>
      )}
      <ItemError text={error} />
    </li>
  );
}

export function CheckoutsPage() {
  const location = useLocation();
  const navigate = useNavigate();
  // Shown once: clear it from the history entry, so a refresh doesn't repeat it.
  const [justCheckedOut] = useState(
    location.state as { checkedOut?: string; answerBy?: string | null } | null,
  );
  const checkedOut = justCheckedOut?.checkedOut;
  const [mine, setMine] = useState<Mine | null>(null);
  const [loadFailed, setLoadFailed] = useState(false);
  const [closed, setClosed] = useState<string | null>(null);

  // Only the newest load may update the page, and none after leaving it: an older, slower response
  // must not overwrite a newer one.
  const latest = useRef(0);
  const load = useCallback(async () => {
    const request = ++latest.current;
    const { data } = await api.GET("/checkouts");
    if (request !== latest.current) return;
    if (data) setMine(data);
    setLoadFailed(!data);
  }, []);

  useEffect(() => {
    load();
    return () => {
      latest.current += 1;
    };
  }, [load]);

  useEffect(() => {
    if (checkedOut) navigate(".", { replace: true, state: null });
  }, [checkedOut, navigate]);

  const act: Act = useCallback(
    async (path, id) => {
      const { error } = await api.POST(`/checkouts/{checkout_id}/${path}`, {
        params: { path: { checkout_id: id } },
      });
      if (error) return errorMessage(error);
      await load();
      return null;
    },
    [load],
  );

  const answered: Answered = useCallback(
    async (name, final) => {
      if (final) setClosed(name);
      await load();
    },
    [load],
  );

  return (
    <main className="shell-page checkouts-page">
      <h1 className="page-title">Checkouts</h1>
      {checkedOut && (
        <p role="status" className="message">
          <span>✓</span>
          <span>
            You asked to check out "{checkedOut}".
            {justCheckedOut?.answerBy &&
              ` If the author hasn't answered by ${formatDay(justCheckedOut.answerBy)}, it closes on its own.`}
          </span>
        </p>
      )}
      {closed && (
        <p role="status" className="message">
          <span>✓</span>
          <span>Thanks for answering. Your checkout with {closed} is closed and the copy is returned.</span>
        </p>
      )}
      {loadFailed && (
        <p role="alert" className="message message-error">
          <span>!</span>
          <span>We couldn't load your checkouts. Please refresh.</span>
        </p>
      )}
      {!mine && !loadFailed && <div className="skeleton checkout-skeleton" aria-busy="true" />}

      {mine && (
        <>
          <section className="checkouts-section" aria-labelledby="lending-heading">
            <h2 id="lending-heading" className="checkouts-heading">
              Requests for your book
            </h2>
            {mine.lending.length === 0 ? (
              <div className="empty">
                <p>Nobody has asked to check out your book yet.</p>
              </div>
            ) : (
              <ul className="checkout-list">
                {mine.lending.map((item) => (
                  <LendingItem key={item.id} item={item} act={act} answered={answered} />
                ))}
              </ul>
            )}
          </section>

          <section className="checkouts-section" aria-labelledby="reading-heading">
            <h2 id="reading-heading" className="checkouts-heading">
              Books you've checked out
            </h2>
            {mine.reading.length === 0 ? (
              <div className="empty">
                <p>You haven't checked out a book yet.</p>
                <p>
                  <Link to="/">Browse the shelf</Link>
                </p>
              </div>
            ) : (
              <ul className="checkout-list">
                {mine.reading.map((item) => (
                  <ReadingItem key={item.id} item={item} act={act} answered={answered} />
                ))}
              </ul>
            )}
          </section>
        </>
      )}
    </main>
  );
}
