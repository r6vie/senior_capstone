import { useCallback, useEffect, useRef, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { Button } from "../../ui/Button";
import { useAuth } from "../auth/AuthProvider";
import { draftKeyFor, keepDraft } from "../interview/AnswerPanel";
import { apiInterviewClient } from "../interview/apiInterviewClient";
import { droppedSentence } from "../interview/InterviewPage";
import type {
  BookStage,
  DraftChapter,
  InterviewClient,
  LastRound,
  MyBook,
  ReadingQuestion,
  Spark,
} from "../interview/interviewClient";
import { LeftoverWords } from "../interview/LeftoverWords";
import { readingCaption } from "../interview/ReadingQuestionPage";
import { UndoChanges } from "../interview/UndoChanges";
import "./MyBookPage.css";

// The member's own page (board G1): their book as an object, and the one next step for its stage.
// It shows no numbers of any kind: no checkouts, no sparks count, no copies.

const LOOK_AGAIN_MS = 4000;
const MIN_CHAPTERS = 3;

function NoBookYet({ stage }: { stage: BookStage }) {
  if (stage === "writingTitles" || stage === "writingBook") {
    return (
      <div className="empty" aria-busy="true">
        <h3>{stage === "writingTitles" ? "I'm finding your titles." : "I'm writing your book."}</h3>
        <p>Everything you've said is saved.</p>
      </div>
    );
  }
  if (stage === "titles") {
    return (
      <div className="empty">
        <h3>Your three titles are ready.</h3>
        <p>Pick one and I'll write your book.</p>
        <div className="iv-row mb-empty-act">
          <Link to="/interview" className="button button-primary">
            See your titles
          </Link>
        </div>
      </div>
    );
  }
  if (stage === "interviewing") {
    return (
      <div className="empty">
        <h3>Your interview is in progress.</h3>
        <p>Everything you've said so far is saved.</p>
        <div className="iv-row mb-empty-act">
          <Link to="/interview" className="button button-primary">
            Continue your interview
          </Link>
        </div>
      </div>
    );
  }
  return (
    <div className="empty">
      <h3>You haven't started your book yet.</h3>
      <p>
        About twenty minutes. You can stop sooner, and leave and come back at any time. Nobody sees your book
        until you put it on the shelf.
      </p>
      <div className="iv-row mb-empty-act">
        <Link to="/interview" className="button button-primary">
          Start the interview
        </Link>
      </div>
    </div>
  );
}

function Sparks({
  sparks,
  shaping,
  onRemove,
}: {
  sparks: Spark[];
  /** A round is open, so they're in use now. */
  shaping: boolean;
  onRemove: (id: string) => void;
}) {
  if (!sparks.length) return null;
  return (
    <section className="mb-sparks">
      <h2 className="mb-heading">For your next questions</h2>
      <p className="mb-note">
        {shaping
          ? "These are shaping the questions you're answering now."
          : 'Chapters you marked "I have one like this". Only you see this list. They shape the next questions. Nothing from them goes into your book.'}
      </p>
      <ul>
        {sparks.map((spark) => (
          <li key={spark.id}>
            <span>{spark.chapterTitle}</span>
            <button
              type="button"
              className="button button-quiet iv-sm"
              aria-label={`Remove ${spark.chapterTitle}`}
              onClick={() => onRemove(spark.id)}
            >
              Remove
            </button>
          </li>
        ))}
      </ul>
    </section>
  );
}

function ReadingPanel({
  question,
  onAnswer,
  onDismiss,
}: {
  question: ReadingQuestion;
  onAnswer: () => void;
  onDismiss: (id: string) => void;
}) {
  return (
    <section className="panel mb-reading">
      <span className="mb-reading-caption">{readingCaption(question)}</span>
      <p>{question.question}</p>
      <div className="iv-row">
        <Link
          to={`/interview/reading/${question.id}`}
          className="button button-secondary iv-sm"
          onClick={onAnswer}
        >
          Answer
        </Link>
        <button type="button" className="button button-quiet iv-sm" onClick={() => onDismiss(question.id)}>
          No thanks
        </button>
      </div>
    </section>
  );
}

function ChapterRow({
  index,
  chapter,
  canRemove,
}: {
  index: number;
  chapter: DraftChapter;
  canRemove: boolean;
}) {
  const [showing, setShowing] = useState(false);
  return (
    <li>
      <span className="mb-n">{index + 1}</span>
      <div>
        <b>{chapter.title}</b>
        <span className="mb-summary">{chapter.summary}</span>
        <div className="mb-row-act">
          {chapter.quotes.length > 0 && (
            <button
              type="button"
              className="button button-quiet iv-sm iv-show"
              aria-expanded={showing}
              aria-label={`${showing ? "Hide" : "Show"} what you said for ${chapter.title}`}
              onClick={() => setShowing((now) => !now)}
            >
              {showing ? "Hide what you said" : "Show what you said"}
            </button>
          )}
          {canRemove && (
            <Link
              to={`/my-book/remove/${chapter.id}`}
              className="button button-quiet iv-sm iv-show"
              aria-label={`Remove this chapter: ${chapter.title}`}
            >
              Remove this chapter
            </Link>
          )}
        </div>
        {showing && (
          <div className="iv-quotes mb-quotes">
            {chapter.quotes.map((quote) => (
              <p key={quote}>{quote}</p>
            ))}
          </div>
        )}
      </div>
    </li>
  );
}

function updatedOn(when: string | null | undefined): string {
  const undoable = "You can undo these changes until the next time you change it.";
  if (!when) return undoable;
  const date = new Date(when).toLocaleDateString("en-US", { month: "short", day: "numeric" });
  return `Your book was updated on ${date}. ${undoable}`;
}

function NextStep({
  stage,
  canUndo,
  changedAt,
  removal,
  onCancelRemoval,
  onUndo,
  onUndone,
  onRetry,
  retrying,
}: {
  stage: BookStage;
  canUndo: boolean;
  changedAt?: string | null;
  /** The only open change is a removal the member started. */
  removal: { chapterId: string; title: string } | null;
  onCancelRemoval: () => void;
  onUndo: () => Promise<void>;
  onUndone: () => void;
  onRetry: () => void;
  retrying: boolean;
}) {
  switch (stage) {
    case "draft":
      return (
        <>
          <div className="iv-row">
            <Link to="/interview" className="button button-primary">
              Review your book
            </Link>
          </div>
          <p className="mb-note">Other members can't see it until you put it on the shelf.</p>
        </>
      );
    case "adding":
      return (
        <>
          <div className="iv-row">
            <Link to="/interview" className="button button-primary">
              Continue adding to your book
            </Link>
          </div>
          <p className="mb-note">You have questions in progress. Your book on the shelf hasn't changed.</p>
        </>
      );
    case "writing":
      return <p className="mb-note">I'm writing your changes. Your book on the shelf hasn't changed.</p>;
    case "writeFailed":
      return (
        <>
          <div className="iv-row">
            <Button onClick={onRetry} aria-busy={retrying}>
              Try again
            </Button>
          </div>
          <p className="mb-note">Your changes couldn't be written. Your answers are saved.</p>
        </>
      );
    case "changesWaiting":
      if (removal) {
        return (
          <>
            <div className="iv-row">
              <Link to={`/my-book/remove/${removal.chapterId}?finish`} className="button button-primary">
                Finish removing
              </Link>
              <button type="button" className="button button-quiet" onClick={onCancelRemoval}>
                Keep it
              </button>
            </div>
            <p className="mb-note">You started removing {removal.title}.</p>
          </>
        );
      }
      return (
        <>
          <div className="iv-row">
            <Link to="/interview" className="button button-primary">
              Review the proposed changes
            </Link>
          </div>
          <p className="mb-note">
            Your book on the shelf hasn't changed. These changes go live only when you confirm.
          </p>
        </>
      );
    default:
      return (
        <>
          <div className="iv-row">
            <Link to="/interview?add" className="button button-primary">
              Add to your book
            </Link>
            {canUndo && <UndoChanges onUndo={onUndo} onDone={onUndone} />}
          </div>
          {canUndo && <p className="mb-note">{updatedOn(changedAt)}</p>}
        </>
      );
  }
}

export function MyBookPage({ client = apiInterviewClient }: { client?: InterviewClient }) {
  const [stage, setStage] = useState<BookStage | null>(null);
  const [book, setBook] = useState<MyBook | null>(null);
  const [sparks, setSparks] = useState<Spark[]>([]);
  const [reading, setReading] = useState<ReadingQuestion[]>([]);
  const [failed, setFailed] = useState(false);
  const [problem, setProblem] = useState<string | null>(null);
  const [retrying, setRetrying] = useState(false);
  const [removal, setRemoval] = useState<{ chapterId: string; title: string } | null>(null);
  const [lastRound, setLastRound] = useState<LastRound>({ empty: false });
  const { user } = useAuth();
  const [undone, setUndone] = useState(false);
  const location = useLocation();
  const leftAsIs = Boolean((location.state as { leftAsIs?: boolean } | null)?.leftAsIs);
  const stageNow = useRef<BookStage | null>(null);
  const heading = useRef<HTMLHeadingElement>(null);
  const focusAfterSpark = useRef(false);

  const load = useCallback(async () => {
    setFailed(false);
    try {
      // All together, so the next step is drawn once, right the first time.
      const [nextStage, nextBook, nextRound] = await Promise.all([
        client.stage(),
        client.myBook(),
        client.lastRound().catch(() => ({ empty: false })),
      ]);
      const nextRemoval =
        nextStage === "changesWaiting" ? await client.openRemoval().catch(() => null) : null;
      stageNow.current = nextStage;
      setStage(nextStage);
      setBook(nextBook);
      setLastRound(nextRound);
      setRemoval(nextRemoval);
    } catch {
      setFailed(true);
      return;
    }
    // A book without its extras is still the page the member came for.
    client.sparks().then(setSparks, () => undefined);
    client.readingQuestions().then(setReading, () => undefined);
  }, [client]);

  useEffect(() => {
    load();
  }, [load]);

  // The changes are written in the background, so the page moves on by itself when they're ready.
  useEffect(() => {
    if (stage !== "writing" && stage !== "writingTitles" && stage !== "writingBook") return;
    const timer = setInterval(load, LOOK_AGAIN_MS);
    return () => clearInterval(timer);
  }, [load, stage]);

  // Arriving on the page starts the keyboard at its heading; so does anything that takes away the
  // control the member just used.
  const arrived = Boolean(stage);
  useEffect(() => {
    if (arrived) heading.current?.focus({ preventScroll: true });
  }, [arrived]);

  // A spark's Remove goes with its row, so the keyboard moves on to the next one, if there is one.
  // biome-ignore lint/correctness/useExhaustiveDependencies: runs when the list changes
  useEffect(() => {
    if (!focusAfterSpark.current) return;
    focusAfterSpark.current = false;
    const next = [...document.querySelectorAll<HTMLElement>(".mb-sparks li button")].find(
      (button) => button.offsetParent !== null || document.documentElement.clientWidth === 0,
    );
    next?.focus({ preventScroll: true });
  }, [sparks]);

  async function attempt(call: () => Promise<unknown>, after: () => void) {
    setProblem(null);
    const before = stageNow.current;
    try {
      await call();
      after();
      heading.current?.focus({ preventScroll: true });
    } catch {
      // Often the server has moved on and the page is what's out of date. Say so only if it isn't.
      await load();
      if (stageNow.current === before) setProblem("That didn't go through. Try again.");
    }
  }

  if (failed) {
    return (
      <main className="mb-page">
        <h1 className="mb-title">My book</h1>
        <div className="empty">
          <h3>I couldn't find your book just now.</h3>
          <p>Nothing you've said is lost.</p>
          <div className="iv-row mb-empty-act">
            <Button onClick={load}>Try again</Button>
          </div>
        </div>
      </main>
    );
  }

  if (!stage) {
    return (
      <main className="mb-page" aria-busy="true">
        <h1 className="mb-title">My book</h1>
        <p className="mb-note">Finding your book…</p>
      </main>
    );
  }

  const removeSpark = (id: string) =>
    attempt(
      () => client.removeSpark(id),
      () => {
        setSparks((now) => now.filter((spark) => spark.id !== id));
        focusAfterSpark.current = true;
      },
    );

  if (!book) {
    return (
      <main className="mb-page">
        <h1 className="mb-title" ref={heading} tabIndex={-1}>
          My book
        </h1>
        <div className="mb-one">
          <LeftoverWords />
          <NoBookYet stage={stage} />
          {problem && (
            <p className="message" role="alert">
              {problem}
            </p>
          )}
          {stage !== "titles" && stage !== "writingTitles" && stage !== "writingBook" && (
            <Sparks sparks={sparks} shaping={false} onRemove={removeSpark} />
          )}
        </div>
      </main>
    );
  }

  const onShelf = stage !== "draft";
  const open =
    stage === "adding" || stage === "writing" || stage === "writeFailed" || stage === "changesWaiting";
  const question = onShelf && !open ? reading[0] : undefined;
  const aside = onShelf && (question || sparks.length > 0);

  const readingPanel = question && (
    <ReadingPanel
      question={question}
      onAnswer={() => {
        if (lastRound.readingAnswer && lastRound.readingQuestionId === question.id) {
          keepDraft(draftKeyFor(user?.id ?? "anon", `reading:${question.id}`), lastRound.readingAnswer);
        }
      }}
      onDismiss={(id) =>
        attempt(
          () => client.dismissReading(id),
          () => setReading((now) => now.filter((item) => item.id !== id)),
        )
      }
    />
  );

  return (
    <main className="mb-page">
      <LeftoverWords />
      <div className={aside ? "mb-two" : "mb-one-wide"}>
        <div>
          <section className="mb-head">
            {/* The large book on a wide screen, the regular one on a phone. */}
            <span className="book book-lg mb-book-wide" aria-hidden="true">
              <span className="book-cover">
                <span className="book-title">{book.title}</span>
                <span className="book-author">{book.authorName}</span>
              </span>
            </span>
            <span className="book mb-book-narrow" aria-hidden="true">
              <span className="book-cover">
                <span className="book-title">{book.title}</span>
                <span className="book-author">{book.authorName}</span>
              </span>
            </span>
            <div className="mb-meta">
              <span className="caption">{onShelf ? "On the shelf" : "Draft, not on the shelf yet"}</span>
              <h1 ref={heading} tabIndex={-1}>
                {book.title}
              </h1>
              <p className="mb-by">by {book.authorName}</p>
              {book.blurb && <p className="mb-blurb">{book.blurb}</p>}
              <NextStep
                stage={stage}
                canUndo={book.canUndo}
                changedAt={book.changedAt}
                removal={removal}
                onCancelRemoval={() => attempt(() => client.cancelRemoval(), load)}
                retrying={retrying}
                onUndo={() => client.undoChanges()}
                onUndone={() => {
                  setUndone(true);
                  load();
                  heading.current?.focus({ preventScroll: true });
                }}
                onRetry={async () => {
                  setRetrying(true);
                  await attempt(() => client.retryWriting("me"), load);
                  setRetrying(false);
                }}
              />
              {undone && (
                <p className="mb-note" role="status">
                  Your book is back as it was.
                </p>
              )}
              {leftAsIs && !undone && <p className="mb-note">Your book stays as it is.</p>}
              {lastRound.empty && onShelf && !open && (
                <p className="mb-note">
                  {lastRound.droppedForNames
                    ? droppedSentence(lastRound.droppedWords)
                    : "Your last answers didn't change your book. They're saved, and the next questions can use them."}
                </p>
              )}
              {problem && (
                <p className="message" role="alert">
                  {problem}
                </p>
              )}
            </div>
          </section>
          {/* On a phone the question comes before the chapters, as it's the thing to act on. */}
          {readingPanel && <div className="mb-reading-top">{readingPanel}</div>}
          <h2 className="mb-heading">Chapters</h2>
          <p className="mb-note">
            "Show what you said" opens your own words behind each chapter. Only you see those.
          </p>
          <ol className="mb-chapters">
            {book.chapters.map((chapter, index) => (
              <ChapterRow
                key={chapter.id}
                index={index}
                chapter={chapter}
                canRemove={onShelf && !open && book.chapters.length > MIN_CHAPTERS}
              />
            ))}
          </ol>
          {onShelf && (
            <div className="mb-sparks-below">
              <Sparks sparks={sparks} shaping={open} onRemove={removeSpark} />
            </div>
          )}
        </div>
        {aside && (
          <aside className="mb-aside">
            {readingPanel}
            <Sparks sparks={sparks} shaping={open} onRemove={removeSpark} />
          </aside>
        )}
      </div>
    </main>
  );
}
