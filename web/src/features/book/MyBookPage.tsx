import { useCallback, useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { Button } from "../../ui/Button";
import { apiInterviewClient } from "../interview/apiInterviewClient";
import type {
  BookStage,
  DraftChapter,
  InterviewClient,
  MyBook,
  ReadingQuestion,
  Spark,
} from "../interview/interviewClient";
import { readingCaption } from "../interview/ReadingQuestionPage";
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
  onDismiss,
}: {
  question: ReadingQuestion;
  onDismiss: (id: string) => void;
}) {
  return (
    <section className="panel mb-reading">
      <span className="mb-reading-caption">{readingCaption(question)}</span>
      <p>{question.question}</p>
      <div className="iv-row">
        <Link to={`/interview/reading/${question.id}`} className="button button-secondary iv-sm">
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

function NextStep({
  stage,
  canUndo,
  onUndo,
  onRetry,
  retrying,
}: {
  stage: BookStage;
  canUndo: boolean;
  onUndo: () => void;
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
            {canUndo && (
              <button type="button" className="button button-quiet" onClick={onUndo}>
                Undo these changes
              </button>
            )}
          </div>
          {canUndo && (
            <p className="mb-note">
              Your book was updated just now. You can undo these changes until the next time you change it.
            </p>
          )}
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

  const load = useCallback(async () => {
    setFailed(false);
    try {
      const [nextStage, nextBook] = await Promise.all([client.stage(), client.myBook()]);
      setStage(nextStage);
      setBook(nextBook);
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

  async function attempt(call: () => Promise<unknown>, after: () => void) {
    setProblem(null);
    try {
      await call();
      after();
    } catch {
      setProblem("That didn't go through. Try again.");
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

  if (!stage) return <main className="mb-page" aria-busy="true" />;

  const removeSpark = (id: string) =>
    attempt(
      () => client.removeSpark(id),
      () => setSparks((now) => now.filter((spark) => spark.id !== id)),
    );

  if (!book) {
    return (
      <main className="mb-page">
        <h1 className="mb-title">My book</h1>
        <div className="mb-one">
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
      <div className={aside ? "mb-two" : "mb-one-wide"}>
        <div>
          <section className="mb-head">
            <span className="book book-lg" aria-hidden="true">
              <span className="book-cover">
                <span className="book-title">{book.title}</span>
                <span className="book-author">{book.authorName}</span>
              </span>
            </span>
            <div className="mb-meta">
              <span className="caption">{onShelf ? "On the shelf" : "Draft, not on the shelf yet"}</span>
              <h1>{book.title}</h1>
              <p className="mb-by">by {book.authorName}</p>
              {book.blurb && <p className="mb-blurb">{book.blurb}</p>}
              <NextStep
                stage={stage}
                canUndo={book.canUndo}
                retrying={retrying}
                onUndo={() => attempt(() => client.undoChanges(), load)}
                onRetry={async () => {
                  setRetrying(true);
                  await attempt(() => client.retryWriting("me"), load);
                  setRetrying(false);
                }}
              />
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
            The words under a chapter are yours, from your answers. Only you see them.
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
