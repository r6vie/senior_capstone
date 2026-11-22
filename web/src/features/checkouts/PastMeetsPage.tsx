import { useCallback, useEffect, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../../api/client";
import type { components } from "../../api/schema";
import { ContactDetails } from "./ContactDetails";
import { DidYouMeet } from "./DidYouMeet";
import { formatDay } from "./dates";
import "./Checkouts.css";

// Past meets (plan item C4, docs/trove.md §8): the people you've met through a checkout, newest first.
// Both people get one: the other's full name and book, their contact details, and the conversation,
// now read-only. A plain list with a bookmark on each; no counts and no red (docs/design/system.md).

type Meet = components["schemas"]["PastMeet"];

function MeetItem({ meet, reload }: { meet: Meet; reload: () => Promise<void> }) {
  return (
    <li className="co-card surf pm-card">
      <span className="past-meet-bookmark" aria-hidden="true" />
      <div>
        <h3 className="co-title">{meet.other_name}</h3>
        {meet.other_book && <p className="co-meta">Author of "{meet.other_book.title}"</p>}
      </div>
      <p>
        {meet.you_were === "reader"
          ? `You checked out "${meet.book_title}".`
          : `${meet.other_name} checked out your book, "${meet.book_title}".`}{" "}
        <span className="muted">Returned {formatDay(meet.met_on)}.</span>
      </p>
      {/* The other person may not have answered yet. A No from them means it isn't a Past meet after all. */}
      <DidYouMeet
        checkoutId={meet.checkout_id}
        name={meet.other_name}
        view={meet.did_you_meet}
        returned
        onAnswered={reload}
      />
      {meet.contact && <ContactDetails name={meet.other_name} contact={meet.contact} />}
      <div className="checkout-actions">
        <Link className="button button-secondary" to={`/checkouts/${meet.checkout_id}/messages`}>
          Your conversation
        </Link>
      </div>
    </li>
  );
}

export function PastMeetsPage() {
  const [meets, setMeets] = useState<Meet[] | null>(null);
  const [loadFailed, setLoadFailed] = useState(false);

  // Only the newest load may update the page, and none after leaving it.
  const latest = useRef(0);
  const load = useCallback(async () => {
    const request = ++latest.current;
    let data: Meet[] | undefined;
    try {
      ({ data } = await api.GET("/checkouts/past-meets"));
    } catch {
      // A dropped connection: shown as a failed load below.
    }
    if (request !== latest.current) return;
    if (data) setMeets(data);
    setLoadFailed(!data);
  }, []);

  useEffect(() => {
    load();
    return () => {
      latest.current += 1;
    };
  }, [load]);

  return (
    <main className="shell-page co-page">
      <h1 className="page-title">Past meets</h1>
      {loadFailed && (
        <p role="alert" className="message message-error">
          <span>!</span>
          <span>We couldn't load your past meets. Please refresh.</span>
        </p>
      )}
      {!meets && !loadFailed && <div className="skeleton checkout-skeleton" aria-busy="true" />}
      {meets &&
        (meets.length === 0 ? (
          <div className="empty">
            <h3>Nothing here yet</h3>
            <p>
              After a reading, answer "Did you meet?" on your Checkouts page, and the people you've met will
              be listed here.
            </p>
            <p>
              <Link to="/checkouts">Go to Checkouts</Link>
            </p>
          </div>
        ) : (
          <section className="pm-section" aria-label="People you've met">
            <ul className="pm-list">
              {meets.map((meet) => (
                <MeetItem key={meet.checkout_id} meet={meet} reload={load} />
              ))}
            </ul>
          </section>
        ))}
    </main>
  );
}
