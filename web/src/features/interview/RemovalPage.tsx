import { useEffect, useState } from "react";
import { Link, Navigate, useNavigate, useParams, useSearchParams } from "react-router-dom";
import { Button } from "../../ui/Button";
import { apiInterviewClient } from "./apiInterviewClient";
import { ErrorMessage, Frame, focusBand, Waiting } from "./InterviewFrame";
import type { InterviewClient, MyBook } from "./interviewClient";
import { BackCover, ChangeCard, WaitBox } from "./ProposedChanges";

// Taking a chapter out of a book on the shelf (board G3, frame 5). Looking costs nothing: pressing
// Remove is what starts it. Then it's the same step as any other change: the member sees the back cover
// written for the shorter book, and nothing is live until they confirm.

const MIN_CHAPTERS = 3;

export function RemovalPage({ client = apiInterviewClient }: { client?: InterviewClient }) {
  const { chapterId = "" } = useParams();
  const [search] = useSearchParams();
  const navigate = useNavigate();
  const [book, setBook] = useState<MyBook | null | undefined>(undefined);
  // Coming back to finish one already started skips the question.
  const [started, setStarted] = useState(search.has("finish"));
  const [blurb, setBlurb] = useState<string | null>(null);
  const [blurbFailed, setBlurbFailed] = useState(false);
  const [writing, setWriting] = useState(search.has("finish"));
  const [attempt, setAttempt] = useState(0);
  const [choice, setChoice] = useState<"approve" | "decline">("approve");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let live = true;
    client
      .myBook()
      .then((found) => live && setBook(found))
      .catch(() => live && setBook(null));
    return () => {
      live = false;
    };
  }, [client]);

  // biome-ignore lint/correctness/useExhaustiveDependencies: attempt is what asks for another try
  useEffect(() => {
    if (!started) return;
    let live = true;
    setWriting(true);
    setBlurbFailed(false);
    client
      .blurbWithout(chapterId)
      .then((written) => live && setBlurb(written))
      .catch(() => live && setBlurbFailed(true))
      .finally(() => live && setWriting(false));
    return () => {
      live = false;
    };
  }, [client, chapterId, attempt, started]);

  const arrived = book !== undefined;
  // biome-ignore lint/correctness/useExhaustiveDependencies: each step is a new screen for the keyboard
  useEffect(() => {
    if (arrived) focusBand();
  }, [arrived, started, writing]);

  if (book === undefined) return <Frame busy say={<Waiting>The Librarian is finding your place…</Waiting>} />;

  const chapter = book?.chapters.find((candidate) => candidate.id === chapterId);
  if (!book || !chapter || book.chapters.length <= MIN_CHAPTERS) return <Navigate to="/my-book" replace />;

  if (!started) {
    return (
      <Frame canLeave={false} say="Remove this chapter?">
        <ChangeCard
          caption="Removing"
          name={chapter.title}
          now={{ title: chapter.title, text: chapter.summary }}
          proposed={null}
        />
        <div className="iv-row">
          <Button variant="secondary" onClick={() => setStarted(true)}>
            Remove
          </Button>
          <Link to="/my-book" className="button button-quiet">
            Keep it
          </Link>
        </div>
      </Frame>
    );
  }

  async function backOut() {
    setError(null);
    try {
      await client.cancelRemoval();
      navigate("/my-book");
    } catch {
      setError("That didn't go through. Your book is as it was. Try again.");
    }
  }

  if (writing) {
    return (
      <Frame canLeave={false} say="I'm writing the back cover without that chapter.">
        <WaitBox />
      </Frame>
    );
  }

  const say = "You asked to remove a chapter.";

  async function confirm() {
    setBusy(true);
    setError(null);
    try {
      await client.removeFromShelf(chapterId, choice === "approve" && !blurbFailed ? blurb : null);
      navigate("/my-book");
    } catch {
      setError("That didn't go through. Your book is as it was. Try again.");
      setBusy(false);
    }
  }

  return (
    <Frame
      busy={busy}
      canLeave={false}
      say={busy ? <Waiting holding={say}>Updating your book…</Waiting> : say}
    >
      <div className="iv-chgs">
        <ChangeCard
          caption="Removing"
          name={chapter.title}
          now={{ title: chapter.title, text: chapter.summary }}
          proposed={null}
        />
        <BackCover
          now={book.blurb}
          proposed={blurb}
          failed={blurbFailed}
          onRetry={() => setAttempt((count) => count + 1)}
          choice={choice}
          onChoose={setChoice}
          note="Rewritten without this chapter. Decline keeps the back cover you have now."
        />
      </div>
      <ErrorMessage message={error} />
      <div className="iv-row">
        <Button onClick={confirm} aria-busy={busy}>
          Update my book on the shelf
        </Button>
        <button type="button" className="button button-quiet" onClick={backOut}>
          Back to my book
        </button>
      </div>
      <p className="iv-note">Until you confirm, your book on the shelf stays exactly as it is.</p>
    </Frame>
  );
}
