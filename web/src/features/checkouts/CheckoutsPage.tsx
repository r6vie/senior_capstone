import { type ReactNode, useCallback, useEffect, useRef, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { api } from "../../api/client";
import { errorMessage } from "../../api/errors";
import type { components } from "../../api/schema";
import { Button } from "../../ui/Button";
import { PageLoading } from "../../ui/Loading";
import { downloadInvite } from "../meetings/invite";
import { ContactDetails } from "./ContactDetails";
import { DidYouMeet } from "./DidYouMeet";
import { formatDay, slipDay, slipWhen } from "./dates";
import { DateSlip, MetStamp } from "./Slips";
import "./Checkouts.css";
import { usePageTitle } from "../../ui/usePageTitle";

// Checkouts (plan item C1, docs/trove.md §6), grouped by what each one needs from you: first what's waiting on
// you (a request for your book, a "Did you meet?" to answer), then what's under way, then a short list of earlier
// ones. Your book and books you've checked out sit together in each group; each card says which. No counts
// anywhere, and no red: nothing here is the one next step for every member (docs/design/system.md).

type Mine = components["schemas"]["MyCheckouts"];
type Lending = components["schemas"]["LendingCheckout"];
type Reading = components["schemas"]["ReadingCheckout"];
type Act = (path: "accept" | "decline" | "cancel", id: string) => Promise<string | null>;
// After a Yes or No to "Did you meet?": the checkout closes, so the page says so before it reloads.
type Answered = (name: string, final: boolean) => Promise<void>;

function Note({ text }: { text: string }) {
  return <blockquote className="checkout-note">{text}</blockquote>;
}

function Chip({ text, solid = false }: { text: string; solid?: boolean }) {
  return <span className={solid ? "co-chip co-chip-solid" : "co-chip"}>{text}</span>;
}

// After a yes: the conversation (C3) and arranging the meeting (M1). "New message" is private to you and
// never a count (docs/trove.md §6).
// Once a time is agreed (M1), the card shows it on a slip with a calendar file, and the meeting link becomes
// "Meeting details"; until then it's "Arrange the reading".
function AcceptedActions({
  id,
  newMessages,
  meetingStart,
}: {
  id: string;
  newMessages: boolean;
  meetingStart?: string | null;
}) {
  const [busy, setBusy] = useState(false);
  const [problem, setProblem] = useState<string | null>(null);

  async function addToCalendar() {
    setBusy(true);
    setProblem(await downloadInvite(id));
    setBusy(false);
  }

  return (
    <>
      {meetingStart && (
        <div className="co-slip-row">
          <DateSlip label="Meeting" when={slipWhen(meetingStart)} />
          <Button variant="quiet" disabled={busy} aria-busy={busy || undefined} onClick={addToCalendar}>
            Add to calendar
          </Button>
        </div>
      )}
      <div className="checkout-actions">
        <Link className="button button-secondary" to={`/checkouts/${id}/messages`}>
          Messages
        </Link>
        {newMessages && <span className="co-new">New message</span>}
        <Link className="button button-quiet" to={`/checkouts/${id}/meeting`}>
          {meetingStart ? "Meeting details" : "Arrange the reading"}
        </Link>
      </div>
      <ItemError text={problem} />
    </>
  );
}

// How long the stamp stays on the card before it moves to Earlier, so the moment can be seen.
const STAMP_MS = 900;

/** "Did you meet?" on a card: a Yes stamps the card, with today's date, for a moment before it moves to Earlier. */
function useStampedAnswer(answered: Answered, name: string) {
  // The day it was stamped, taken once at the click so it can't change while it's showing.
  const [stampedOn, setStampedOn] = useState<string | null>(null);
  async function onAnswered(answer: string) {
    if (answer === "met") {
      setStampedOn(new Date().toISOString());
      await new Promise((done) => setTimeout(done, STAMP_MS));
    }
    await answered(name, answer !== "not_yet");
  }
  return { stampedOn, onAnswered };
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

function CardHead({ title, meta, chip }: { title: string; meta: string; chip: ReactNode }) {
  return (
    <div className="co-head">
      <div>
        <h3 className="co-title">{title}</h3>
        <p className="co-meta">{meta}</p>
      </div>
      {chip}
    </div>
  );
}

function LendingCard({ item, act, answered }: { item: Lending; act: Act; answered: Answered }) {
  const [busy, setBusy] = useState(false);
  const [confirming, setConfirming] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function run(path: "accept" | "decline") {
    setBusy(true);
    setError(await act(path, item.id));
    setBusy(false);
  }

  const theirBook = item.reader_book ? `Author of "${item.reader_book.title}"` : null;
  const accepted = item.status === "accepted";
  const stamp = useStampedAnswer(answered, item.reader_name);
  return (
    <li className="co-card surf">
      {stamp.stampedOn && <MetStamp on={slipDay(stamp.stampedOn)} fresh />}
      <CardHead
        title={item.reader_name}
        meta={accepted ? ["Checked out your book", theirBook].filter(Boolean).join(" · ") : (theirBook ?? "")}
        chip={accepted ? <Chip text="Accepted" solid /> : <Chip text="Asks for your book" />}
      />
      {accepted ? (
        <>
          {item.did_you_meet && (
            <DidYouMeet
              checkoutId={item.id}
              name={item.reader_name}
              view={item.did_you_meet}
              onAnswered={stamp.onAnswered}
            />
          )}
          {item.reader_contact && <ContactDetails name={item.reader_name} contact={item.reader_contact} />}
          <AcceptedActions
            id={item.id}
            newMessages={item.new_messages ?? false}
            meetingStart={item.meeting_start}
          />
        </>
      ) : (
        <>
          <Note text={item.message} />
          {item.expires_at && (
            <div className="co-slip-row">
              <DateSlip label="Answer by" when={slipDay(item.expires_at)} />
              <span className="co-due">It closes on its own if you haven't answered by then.</span>
            </div>
          )}
          {confirming ? (
            <div className="checkout-actions">
              <span>
                Decline {item.reader_name}'s checkout? They'll see the book isn't available right now.
              </span>
              <Button variant="secondary" disabled={busy} aria-busy={busy} onClick={() => run("decline")}>
                Decline
              </Button>
              <Button variant="quiet" disabled={busy} onClick={() => setConfirming(false)}>
                Keep it
              </Button>
            </div>
          ) : (
            <div className="checkout-actions">
              <Button variant="secondary" disabled={busy} aria-busy={busy} onClick={() => run("accept")}>
                Accept
              </Button>
              <Button variant="quiet" disabled={busy} onClick={() => setConfirming(true)}>
                Decline
              </Button>
            </div>
          )}
        </>
      )}
      <ItemError text={error} />
    </li>
  );
}

function ReadingCard({ item, act, answered }: { item: Reading; act: Act; answered: Answered }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function cancel() {
    setBusy(true);
    setError(await act("cancel", item.id));
    setBusy(false);
  }

  const chip =
    item.status === "waiting" ? (
      <Chip text="Waiting" />
    ) : item.status === "accepted" ? (
      <Chip text="Accepted" solid />
    ) : (
      <Chip text="Returned" />
    );
  const stamp = useStampedAnswer(answered, item.author_name);
  return (
    <li className="co-card surf">
      {stamp.stampedOn && <MetStamp on={slipDay(stamp.stampedOn)} fresh />}
      <CardHead title={item.book_title} meta={`by ${item.author_name}`} chip={chip} />
      {item.status === "waiting" && <Note text={item.message} />}
      {item.did_you_meet && (
        <DidYouMeet
          checkoutId={item.id}
          name={item.author_name}
          view={item.did_you_meet}
          returned={item.status === "returned"}
          onAnswered={stamp.onAnswered}
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
        <AcceptedActions
          id={item.id}
          newMessages={item.new_messages ?? false}
          meetingStart={item.meeting_start}
        />
      )}
      {item.status === "waiting" && (
        <>
          {item.expires_at ? (
            <div className="co-slip-row">
              <DateSlip label="Answer due" when={slipDay(item.expires_at)} />
              <span className="co-due">
                Waiting for an answer from {item.author_name}. It closes on its own if there's none by then.
              </span>
            </div>
          ) : (
            <p className="co-due">Waiting for an answer from {item.author_name}.</p>
          )}
          <div className="checkout-actions">
            <Button variant="quiet" disabled={busy} aria-busy={busy} onClick={cancel}>
              Cancel checkout
            </Button>
          </div>
        </>
      )}
      <ItemError text={error} />
    </li>
  );
}

function earlierStatus(item: Reading): string {
  switch (item.status) {
    case "returned":
      return "Returned";
    case "cancelled":
      return "You cancelled it";
    default:
      return "Not available";
  }
}

// Closed checkouts: one line each, so they don't crowd what's live.
function EarlierItem({ item }: { item: Reading }) {
  return (
    <li className="co-earlier-item">
      <span className="co-earlier-title">{item.book_title}</span>
      <span className="co-earlier-what">
        {item.author_name} · {earlierStatus(item)}
      </span>
      {item.status === "returned" && item.author_contact ? (
        <Link to="/past-meets">See {item.author_name} in Past meets</Link>
      ) : (
        <span />
      )}
    </li>
  );
}

/** Sorts every checkout into what's waiting on you, what's under way, and what's closed. */
function arrange(mine: Mine, act: Act, answered: Answered) {
  const yours: ReactNode[] = [];
  const underway: ReactNode[] = [];
  const earlier: Reading[] = [];
  for (const item of mine.lending) {
    const card = <LendingCard key={item.id} item={item} act={act} answered={answered} />;
    if (item.status === "waiting" || item.did_you_meet?.can_answer) yours.push(card);
    else underway.push(card);
  }
  for (const item of mine.reading) {
    const card = <ReadingCard key={item.id} item={item} act={act} answered={answered} />;
    if (item.did_you_meet?.can_answer) yours.push(card);
    else if (item.status === "waiting" || item.status === "accepted") underway.push(card);
    else earlier.push(item);
  }
  return { yours, underway, earlier };
}

function Section({ id, title, children }: { id: string; title: string; children: ReactNode }) {
  return (
    <section className="co-section" aria-labelledby={id}>
      <h2 id={id} className="co-heading">
        {title}
      </h2>
      {children}
    </section>
  );
}

export function CheckoutsPage() {
  usePageTitle("Checkouts");
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
    let data: Mine | undefined;
    try {
      ({ data } = await api.GET("/checkouts"));
    } catch {
      // A dropped connection: shown as a failed load below.
    }
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
    <main className="shell-page co-page">
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
      {!mine && !loadFailed && <PageLoading />}

      {mine && <Groups mine={mine} act={act} answered={answered} />}
    </main>
  );
}

function Groups({ mine, act, answered }: { mine: Mine; act: Act; answered: Answered }) {
  const { yours, underway, earlier } = arrange(mine, act, answered);
  if (!yours.length && !underway.length && !earlier.length) {
    return (
      <div className="empty">
        <h2>No checkouts yet</h2>
        <p className="voice co-voice">
          When someone asks for your book, or you ask for theirs, the Librarian sets it out here.
        </p>
        <p>
          <Link to="/">Browse the shelf</Link>
        </p>
      </div>
    );
  }
  return (
    <>
      <Section id="co-yours" title="Waiting on you">
        {yours.length ? (
          <ul className="co-grid">{yours}</ul>
        ) : (
          <p className="voice co-voice">Nothing needs you right now.</p>
        )}
      </Section>
      {underway.length > 0 && (
        <Section id="co-underway" title="Under way">
          <ul className="co-grid">{underway}</ul>
        </Section>
      )}
      {earlier.length > 0 && (
        <Section id="co-earlier" title="Earlier">
          <ul className="co-earlier">
            {earlier.map((item) => (
              <EarlierItem key={item.id} item={item} />
            ))}
          </ul>
        </Section>
      )}
    </>
  );
}
