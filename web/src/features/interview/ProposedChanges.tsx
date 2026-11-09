import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Button } from "../../ui/Button";
import { addedWords } from "./addedWords";
import { ErrorMessage, Frame, Waiting } from "./InterviewFrame";
import type { InterviewState } from "./interviewClient";
import "./ProposedChanges.css";

// Proposed changes to a book on the shelf (trove.md §3, board G3). The member decides on each one, sees
// the back cover written for exactly what they approved, and nothing is live until they confirm.

type Choice = "approve" | "decline";
type Choices = Record<string, Choice>;

const NOTE_NOT_LIVE = "Until you confirm, your book on the shelf stays exactly as it is.";

export function WaitBox({ title, children }: { title: string; children?: React.ReactNode }) {
  return (
    <div className="empty iv-waitbox" aria-busy="true">
      <h3>{title}</h3>
      <p>This can take a while. You can leave. The result will be here when you come back.</p>
      <div className="iv-row iv-waitbox-act">
        {children ?? (
          <Link to="/my-book" className="button button-quiet">
            Back to my book
          </Link>
        )}
      </div>
    </div>
  );
}

function Toggle({
  name,
  choice,
  onChoose,
}: {
  name: string;
  choice: Choice | undefined;
  onChoose: (choice: Choice) => void;
}) {
  return (
    <div className="iv-toggle">
      <button
        type="button"
        className="button button-secondary iv-sm"
        aria-pressed={choice === "approve"}
        aria-label={`Approve: ${name}`}
        onClick={() => onChoose("approve")}
      >
        Approve
      </button>
      <button
        type="button"
        className="button button-secondary iv-sm"
        aria-pressed={choice === "decline"}
        aria-label={`Decline: ${name}`}
        onClick={() => onChoose("decline")}
      >
        Decline
      </button>
    </div>
  );
}

function Marked({ now, proposed }: { now: string | undefined; proposed: string }) {
  if (now === undefined) return <>{proposed}</>;
  return (
    <>
      {addedWords(now, proposed).map((piece, index) =>
        // biome-ignore lint/suspicious/noArrayIndexKey: pieces are in a fixed order for this text
        piece.added ? <ins key={index}>{piece.text}</ins> : <span key={index}>{piece.text}</span>,
      )}
    </>
  );
}

const STATUS: Record<Choice | "none", string> = {
  approve: "Approved",
  decline: "Declined",
  none: "Not decided",
};

/** One change: the line on what it adds, what's there now, what would replace it, and the decision. */
export function ChangeCard({
  caption,
  note,
  name,
  now,
  proposed,
  choice,
  onChoose,
}: {
  caption: string;
  note: string;
  /** What a screen reader hears on the toggle. */
  name: string;
  now: { title?: string; text: string } | null;
  proposed: { title?: string; text: string } | null;
  choice?: Choice;
  onChoose?: (choice: Choice) => void;
}) {
  const [showingNow, setShowingNow] = useState(false);
  const replaces = now !== null && proposed !== null;
  return (
    <article className="iv-chg" data-declined={choice === "decline" || undefined}>
      <div className="iv-chg-head">
        <span className="caption">{caption}</span>
        {onChoose && <span className="iv-chg-status">{STATUS[choice ?? "none"]}</span>}
      </div>
      <p className="iv-chg-note">{note}</p>
      <div className="iv-chg-cols">
        <div className="iv-chg-now" data-open={showingNow || !replaces || undefined}>
          <i>Now</i>
          {now ? (
            <>
              {now.title && <b>{now.title}</b>}
              <span>{now.text}</span>
            </>
          ) : (
            <div className="iv-chg-blank">Not in your book yet.</div>
          )}
        </div>
        <div className="iv-chg-new">
          <i>Proposed</i>
          {proposed ? (
            <>
              {proposed.title && <b>{proposed.title}</b>}
              <span>
                <Marked now={now?.text} proposed={proposed.text} />
              </span>
            </>
          ) : (
            <div className="iv-chg-blank">Comes out of your book.</div>
          )}
        </div>
      </div>
      {replaces && (
        <div className="iv-chg-nowtoggle">
          <button
            type="button"
            className="button button-quiet iv-sm iv-show"
            aria-expanded={showingNow}
            onClick={() => setShowingNow((open) => !open)}
          >
            {showingNow ? "Hide what's there now" : "See what's there now"}
          </button>
        </div>
      )}
      {onChoose && <Toggle name={name} choice={choice} onChoose={onChoose} />}
    </article>
  );
}

function readChoices(key: string): Choices {
  try {
    return JSON.parse(localStorage.getItem(key) ?? "{}") as Choices;
  } catch {
    return {};
  }
}

function writeChoices(key: string, choices: Choices) {
  try {
    localStorage.setItem(key, JSON.stringify(choices));
  } catch {
    // Without storage the choices last only as long as this screen.
  }
}

function clearChoices(key: string) {
  try {
    localStorage.removeItem(key);
  } catch {
    // Nothing to clear.
  }
}

/** A failed back cover keeps the old one, and the member can still confirm. */
export function BackCover({
  now,
  proposed,
  failed,
  onRetry,
  choice,
  onChoose,
}: {
  now: string | null;
  proposed: string | null;
  failed: boolean;
  onRetry: () => void;
  choice: Choice;
  onChoose: (choice: Choice) => void;
}) {
  if (failed) {
    return (
      <div className="panel iv-backcover-failed">
        <h3>Back cover</h3>
        <p>I couldn't rewrite the back cover. The old one stays unless you try again.</p>
        <div className="iv-row">
          <Button variant="secondary" className="iv-sm" onClick={onRetry}>
            Try again
          </Button>
        </div>
      </div>
    );
  }
  if (!proposed) return null;
  return (
    <ChangeCard
      caption="Back cover"
      note="Rewritten to include what you approved. Decline keeps the back cover you have now."
      name="the back cover"
      now={now ? { text: now } : null}
      proposed={{ text: proposed }}
      choice={choice}
      onChoose={onChoose}
    />
  );
}

export function ChangesScreen({
  state,
  userId,
  busy,
  error,
  writeBlurb,
  saveChoices,
  apply,
}: {
  state: Extract<InterviewState, { stage: "proposing" }>;
  userId: string;
  busy: string | null;
  error: string | null;
  writeBlurb: (approved: string[]) => Promise<string | null>;
  saveChoices: (approved: string[]) => Promise<void>;
  apply: (approved: string[], blurb: string | null, onDone: () => void) => void;
}) {
  const { changes } = state;
  // Saved per set of changes, so "Decide later" means it.
  const key = `trove_change_choices:${userId}:${changes.map((change) => change.id).join(",")}`;
  // The API keeps what was approved, for any device. This browser also remembers what was declined.
  const [choices, setChoices] = useState<Choices>(() => {
    const here = readChoices(key);
    for (const id of state.approved ?? []) here[id] = "approve";
    return here;
  });
  const [step, setStep] = useState<"choose" | "writing" | "confirm">("choose");
  const [blurb, setBlurb] = useState<string | null>(null);
  const [blurbFailed, setBlurbFailed] = useState(false);
  const [blurbChoice, setBlurbChoice] = useState<Choice>("approve");

  useEffect(() => writeChoices(key, choices), [key, choices]);

  const approved = changes.filter((change) => choices[change.id] === "approve");
  const others = changes.filter((change) => choices[change.id] !== "approve");
  const approvedIds = approved.map((change) => change.id);

  async function review() {
    if (!approved.length) {
      setStep("confirm");
      return;
    }
    setStep("writing");
    setBlurbFailed(false);
    try {
      setBlurb(await writeBlurb(approvedIds));
      setBlurbChoice("approve");
    } catch {
      setBlurb(null);
      setBlurbFailed(true);
    }
    setStep("confirm");
  }

  function confirm() {
    const chosen = blurbChoice === "approve" && !blurbFailed ? blurb : null;
    apply(approvedIds, chosen, () => clearChoices(key));
  }

  if (step === "writing") {
    return (
      <Frame canLeave={false} say="I'm writing the back cover for what you approved.">
        <WaitBox title="Writing the back cover." />
      </Frame>
    );
  }

  if (step === "confirm") {
    const nothing = approved.length === 0;
    const say = nothing ? "Nothing will change on the shelf." : "Here is what changes on the shelf.";
    return (
      <Frame canLeave={false} busy={Boolean(busy)} say={busy ? <Waiting holding={say}>{busy}</Waiting> : say}>
        <div className="iv-confirm-cols" data-single={nothing || others.length === 0 || undefined}>
          {!nothing && (
            <div className="panel iv-conf">
              <h3>Will change on the shelf</h3>
              <ul className="iv-clist">
                {approved.map((change) => (
                  <li key={change.id}>
                    <span className="iv-tag">
                      {change.kind === "new" ? "New" : change.kind === "remove" ? "Removing" : "Changed"}
                    </span>
                    <b>{change.title}</b>
                  </li>
                ))}
              </ul>
            </div>
          )}
          {others.length > 0 && (
            <div className="panel iv-conf">
              <h3>Stays as it is</h3>
              <ul className="iv-clist">
                {others.map((change) => (
                  <li key={change.id}>
                    <span className="iv-tag">
                      {choices[change.id] === "decline" ? "Declined" : "Not decided"}
                    </span>
                    <b>{change.now?.title ?? change.title}</b>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
        {!nothing && (
          <BackCover
            now={state.blurb}
            proposed={blurb}
            failed={blurbFailed}
            onRetry={review}
            choice={blurbChoice}
            onChoose={setBlurbChoice}
          />
        )}
        <ErrorMessage message={error} />
        <div className="iv-row">
          <Button onClick={confirm} aria-busy={Boolean(busy)}>
            {nothing ? "Leave my book as it is" : "Update my book on the shelf"}
          </Button>
          <button type="button" className="button button-quiet" onClick={() => setStep("choose")}>
            Back to the changes
          </button>
        </div>
        <p className="iv-note">
          {nothing ? "Your book on the shelf stays exactly as it is." : NOTE_NOT_LIVE}
        </p>
      </Frame>
    );
  }

  return (
    <Frame canLeave={false} say="Here is what I would change in your book.">
      <div className="iv-chgs">
        {changes.map((change) => (
          <ChangeCard
            key={change.id}
            caption={
              change.kind === "new"
                ? "New chapter"
                : change.kind === "remove"
                  ? "Removing"
                  : "Changed chapter"
            }
            note={change.note}
            name={change.title}
            now={change.now ? { title: change.now.title, text: change.now.summary } : null}
            proposed={change.kind === "remove" ? null : { title: change.title, text: change.summary }}
            choice={choices[change.id]}
            onChoose={(choice) => {
              const next = { ...choices, [change.id]: choice };
              setChoices(next);
              // Reviewing saves them again, so a failure here costs nothing.
              saveChoices(changes.filter((item) => next[item.id] === "approve").map((item) => item.id)).catch(
                () => undefined,
              );
            }}
          />
        ))}
      </div>
      <div className="iv-row">
        <Button onClick={review}>Review your choices</Button>
        <Link to="/my-book" className="button button-quiet">
          Decide later
        </Link>
      </div>
      <p className="iv-note">
        Nothing changes on the shelf until you confirm. Anything you haven't decided stays as it is. Your
        choices are saved.
      </p>
    </Frame>
  );
}
