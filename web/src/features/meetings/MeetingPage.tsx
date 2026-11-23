import { type FormEvent, type RefObject, useCallback, useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { api } from "../../api/client";
import { errorMessage } from "../../api/errors";
import type { components } from "../../api/schema";
import { Button } from "../../ui/Button";
import { PageLoading } from "../../ui/Loading";
import { TextField } from "../../ui/TextField";
import { downloadInvite } from "./invite";
import "./MeetingPage.css";
import { usePageTitle } from "../../ui/usePageTitle";

// Arranging the meeting (plan item M1, docs/trove.md §9.7): each person offers a few times, the app shows
// where they overlap, either person confirms one, and the video link goes here. Nothing more.
// Once a time is confirmed, the confirmed meeting is the page: changing the time, and changing details
// already saved, wait behind a button each, so the page reads as arranged rather than still asking.

type Meeting = components["schemas"]["MeetingView"];
type Notice = { kind: "saved" | "error"; text: string } | null;

const MAX_TIMES = 5;

const dateFormat = new Intl.DateTimeFormat(undefined, {
  weekday: "long",
  month: "long",
  day: "numeric",
  hour: "numeric",
  minute: "2-digit",
});

// "2026-11-20T15:30:00Z" -> the same instant in this person's own time zone, in words.
const when = (iso: string) => dateFormat.format(new Date(iso));

// The value a datetime-local field gives is the person's own clock time with no zone.
function toIso(local: string): string | null {
  const date = new Date(local);
  if (Number.isNaN(date.getTime())) return null;
  return date.toISOString();
}

const sameInstant = (a: string, b: string) => new Date(a).getTime() === new Date(b).getTime();

function Feedback({ notice }: { notice: Notice }) {
  if (!notice) return null;
  return (
    <p role={notice.kind === "error" ? "alert" : "status"} className={`message meeting-${notice.kind}`}>
      <span>{notice.kind === "error" ? "!" : "✓"}</span>
      <span>{notice.text}</span>
    </p>
  );
}

function TimesSection({ meeting, onChange }: { meeting: Meeting; onChange: (next: Meeting) => void }) {
  const [times, setTimes] = useState<string[]>(meeting.my_times);
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState<Notice>(null);
  const changed =
    times.length !== meeting.my_times.length ||
    times.some((time, i) => !sameInstant(time, meeting.my_times[i] ?? ""));

  function add() {
    const iso = toIso(draft);
    if (!iso) return setNotice({ kind: "error", text: "Choose a day and a time first." });
    if (new Date(iso).getTime() <= Date.now())
      return setNotice({ kind: "error", text: "Pick a time that hasn't passed yet." });
    if (new Date(draft).getMinutes() % 30 !== 0) {
      return setNotice({
        kind: "error",
        text: "Start on the hour or the half hour, so your times can line up.",
      });
    }
    if (times.some((time) => sameInstant(time, iso))) return setDraft("");
    if (times.length >= MAX_TIMES) {
      return setNotice({ kind: "error", text: `Offer up to ${MAX_TIMES} times. Remove one to add another.` });
    }
    setNotice(null);
    setTimes([...times, iso].sort());
    setDraft("");
  }

  async function save() {
    setBusy(true);
    setNotice(null);
    const { data, error } = await api.PUT("/meetings/{checkout_id}/times", {
      params: { path: { checkout_id: meeting.checkout_id } },
      body: { times },
    });
    setBusy(false);
    if (!data) return setNotice({ kind: "error", text: errorMessage(error) });
    onChange(data);
    setTimes(data.my_times);
    setNotice({ kind: "saved", text: "Your times are saved." });
  }

  return (
    <section aria-labelledby="times-heading" className="meeting-section">
      <h2 id="times-heading" className="meeting-heading">
        Times that work for you
      </h2>
      <p className="muted">
        Each is 30 minutes, shown in your own time zone. {meeting.other_name} sees them in theirs.
      </p>
      {times.length === 0 ? (
        <p className="meeting-empty">No times yet. Add a few below.</p>
      ) : (
        <ul className="meeting-times">
          {times.map((time) => (
            <li key={time}>
              <span>{when(time)}</span>
              <button
                type="button"
                className="button button-quiet"
                onClick={() => setTimes(times.filter((other) => other !== time))}
                aria-label={`Remove ${when(time)}`}
              >
                Remove
              </button>
            </li>
          ))}
        </ul>
      )}
      <div className="meeting-add">
        <label className="field">
          <span>Add a time</span>
          <input
            type="datetime-local"
            step={1800}
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
          />
        </label>
        <Button variant="secondary" onClick={add}>
          Add this time
        </Button>
      </div>
      <Feedback notice={notice} />
      <div>
        <Button onClick={save} disabled={busy || !changed} aria-busy={busy}>
          Save my times
        </Button>
      </div>
    </section>
  );
}

function PickSection({ meeting, onChange }: { meeting: Meeting; onChange: (next: Meeting) => void }) {
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState<Notice>(null);

  const offered = [...meeting.my_times, ...meeting.their_times]
    .filter((time, i, all) => all.findIndex((other) => sameInstant(other, time)) === i)
    .sort();
  const isShared = (time: string) => meeting.shared_times.some((other) => sameInstant(other, time));
  const offeredBy = (time: string) => {
    if (isShared(time)) return "You both offered this";
    return meeting.my_times.some((other) => sameInstant(other, time))
      ? "You offered this"
      : `${meeting.other_name} offered this`;
  };

  async function confirm(start: string) {
    setBusy(true);
    setNotice(null);
    const { data, error } = await api.PUT("/meetings/{checkout_id}/confirm", {
      params: { path: { checkout_id: meeting.checkout_id } },
      body: { start },
    });
    setBusy(false);
    if (!data) return setNotice({ kind: "error", text: errorMessage(error) });
    onChange(data);
  }

  return (
    <section aria-labelledby="pick-heading" className="meeting-section">
      <h2 id="pick-heading" className="meeting-heading">
        {meeting.start ? "Change the time" : "Pick a time"}
      </h2>
      {offered.length === 0 ? (
        <p className="meeting-empty">
          Nothing to pick yet. Once either of you offers times, they show up here.
        </p>
      ) : (
        <>
          {meeting.shared_times.length === 0 && (
            <p className="muted">None of your times overlap yet. You can still pick any of these.</p>
          )}
          <ul className="meeting-times">
            {offered.map((time) => (
              <li key={time} data-shared={isShared(time)}>
                <span>
                  {when(time)}
                  <small className="muted">{offeredBy(time)}</small>
                </span>
                <Button
                  variant="secondary"
                  disabled={busy || (meeting.start !== null && sameInstant(meeting.start, time))}
                  onClick={() => confirm(time)}
                  aria-label={`Confirm ${when(time)}`}
                >
                  Confirm this time
                </Button>
              </li>
            ))}
          </ul>
        </>
      )}
      <Feedback notice={notice} />
    </section>
  );
}

function DetailsSection({
  meeting,
  onChange,
  onSaved,
}: {
  meeting: Meeting;
  onChange: (next: Meeting) => void;
  onSaved?: () => void;
}) {
  const [link, setLink] = useState(meeting.video_link ?? "");
  const [place, setPlace] = useState(meeting.place_note ?? "");
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState<Notice>(null);

  async function save(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setNotice(null);
    const { data, error } = await api.PUT("/meetings/{checkout_id}/details", {
      params: { path: { checkout_id: meeting.checkout_id } },
      body: { video_link: link.trim() || null, place_note: place.trim() || null },
    });
    setBusy(false);
    if (!data) return setNotice({ kind: "error", text: errorMessage(error) });
    onChange(data);
    setLink(data.video_link ?? "");
    setPlace(data.place_note ?? "");
    setNotice({ kind: "saved", text: "Saved. Both of you can see this." });
    onSaved?.();
  }

  return (
    <section aria-labelledby="details-heading" className="meeting-section">
      <h2 id="details-heading" className="meeting-heading">
        Where you'll meet
      </h2>
      <p className="muted">
        Either of you can add the link. Calls happen on Zoom, Meet or whatever you already use.
      </p>
      <form onSubmit={save} className="stack">
        <TextField
          label="Video link"
          value={link}
          onChange={setLink}
          autoComplete="off"
          hint="Starts with https://"
        />
        <TextField
          label="Or a place, if you're both nearby (optional)"
          value={place}
          onChange={setPlace}
          autoComplete="off"
        />
        <Feedback notice={notice} />
        <div>
          <Button type="submit" variant="secondary" disabled={busy} aria-busy={busy}>
            Save meeting details
          </Button>
        </div>
      </form>
    </section>
  );
}

function Confirmed({
  meeting,
  headingRef,
}: {
  meeting: Meeting;
  headingRef: RefObject<HTMLHeadingElement | null>;
}) {
  const [notice, setNotice] = useState<Notice>(null);

  async function download() {
    setNotice(null);
    const problem = await downloadInvite(meeting.checkout_id);
    if (problem) setNotice({ kind: "error", text: problem });
  }

  if (!meeting.start) return null;
  return (
    <section aria-labelledby="confirmed-heading" className="meeting-confirmed">
      <p className="caption">Confirmed</p>
      <h2 id="confirmed-heading" className="meeting-when" ref={headingRef} tabIndex={-1}>
        {when(meeting.start)}
      </h2>
      <p>
        {meeting.minutes} minutes with {meeting.other_name}
      </p>
      {meeting.video_link && (
        <p>
          <a href={meeting.video_link} target="_blank" rel="noreferrer noopener">
            Open the video link
          </a>
        </p>
      )}
      {meeting.place_note && <p>{meeting.place_note}</p>}
      <Feedback notice={notice} />
      <div>
        <Button variant="secondary" onClick={download}>
          Add to my calendar
        </Button>
      </div>
    </section>
  );
}

function Toggle({
  open,
  onToggle,
  closed,
  opened,
}: {
  open: boolean;
  onToggle: () => void;
  closed: string;
  opened: string;
}) {
  return (
    <Button variant="quiet" aria-expanded={open} onClick={onToggle}>
      {open ? opened : closed}
    </Button>
  );
}

function BackLink() {
  return (
    <p className="meeting-back">
      <Link to="/checkouts">
        <span aria-hidden="true">← </span>Back to Checkouts
      </Link>
    </p>
  );
}

export function MeetingPage() {
  const { checkoutId = "" } = useParams();
  const [meeting, setMeeting] = useState<Meeting | null>(null);
  const [changingTime, setChangingTime] = useState(false);
  const [editingDetails, setEditingDetails] = useState(false);
  // The button just pressed goes away when a change is saved, so focus moves to the meeting it changed.
  const confirmedHeading = useRef<HTMLHeadingElement>(null);
  const backToConfirmed = () => requestAnimationFrame(() => confirmedHeading.current?.focus());
  usePageTitle(meeting ? `Meeting ${meeting.other_name}` : "Arrange your meeting");
  const [failed, setFailed] = useState(false);

  const load = useCallback(() => {
    // A late answer from an earlier request must not replace a newer one.
    let stale = false;
    api.GET("/meetings/{checkout_id}", { params: { path: { checkout_id: checkoutId } } }).then(({ data }) => {
      if (stale) return;
      if (data) setMeeting(data);
      else setFailed(true);
    });
    return () => {
      stale = true;
    };
  }, [checkoutId]);

  useEffect(() => load(), [load]);

  if (failed) {
    return (
      <main className="meeting-page">
        <h1 className="page-title">Arrange your meeting</h1>
        <p className="meeting-empty">
          We couldn't find this meeting. It opens once the author says yes.{" "}
          <Link to="/checkouts">Back to Checkouts</Link>
        </p>
      </main>
    );
  }
  if (!meeting) {
    return (
      <main className="meeting-page" aria-busy="true">
        <PageLoading />
      </main>
    );
  }

  if (!meeting.start) {
    return (
      <main className="meeting-page">
        <BackLink />
        <p className="caption">{meeting.book_title}</p>
        <h1 className="page-title">Meeting {meeting.other_name}</h1>
        <TimesSection meeting={meeting} onChange={setMeeting} />
        <PickSection
          meeting={meeting}
          onChange={(next) => {
            setMeeting(next);
            backToConfirmed();
          }}
        />
        <DetailsSection meeting={meeting} onChange={setMeeting} />
      </main>
    );
  }

  // Details nobody has added yet are the next thing to do, so that form stays open until something is saved.
  const hasDetails = Boolean(meeting.video_link || meeting.place_note);
  const showDetails = !hasDetails || editingDetails;

  return (
    <main className="meeting-page">
      <BackLink />
      <p className="caption">{meeting.book_title}</p>
      <h1 className="page-title">Meeting {meeting.other_name}</h1>
      <Confirmed meeting={meeting} headingRef={confirmedHeading} />
      <div className="meeting-actions">
        <Toggle
          open={changingTime}
          onToggle={() => setChangingTime(!changingTime)}
          closed="Change the time"
          opened="Keep this time"
        />
        {hasDetails && (
          <Toggle
            open={editingDetails}
            onToggle={() => setEditingDetails(!editingDetails)}
            closed="Edit where you'll meet"
            opened="Stop editing"
          />
        )}
      </div>
      {changingTime && (
        <>
          <TimesSection meeting={meeting} onChange={setMeeting} />
          <PickSection
            meeting={meeting}
            onChange={(next) => {
              setMeeting(next);
              setChangingTime(false);
              backToConfirmed();
            }}
          />
        </>
      )}
      {showDetails && (
        <DetailsSection
          meeting={meeting}
          onChange={setMeeting}
          onSaved={() => {
            setEditingDetails(false);
            backToConfirmed();
          }}
        />
      )}
    </main>
  );
}
