import { useEffect, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useAuth } from "../auth/AuthProvider";
import { AnswerPanel, clearDraft, draftKeyFor } from "./AnswerPanel";
import { apiInterviewClient } from "./apiInterviewClient";
import { ErrorMessage, Frame, focusBand, Waiting } from "./InterviewFrame";
import { type InterviewClient, InterviewError, type ReadingQuestion } from "./interviewClient";

// The question after a reading (trove.md §3, board G5). The other person's name is shown to the author
// here, and it never goes to a prompt or into the book.

export function readingCaption(question: ReadingQuestion): string {
  const date = new Date(question.createdAt).toLocaleDateString("en-US", { month: "short", day: "numeric" });
  return question.readerName
    ? `After your reading with ${question.readerName}, ${date}`
    : `After your reading, ${date}`;
}

export function ReadingQuestionPage({ client = apiInterviewClient }: { client?: InterviewClient }) {
  const { questionId } = useParams();
  const { user } = useAuth();
  const navigate = useNavigate();
  const [question, setQuestion] = useState<ReadingQuestion | null>(null);
  const [loaded, setLoaded] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let live = true;
    client
      .readingQuestions()
      .then((questions) => {
        if (!live) return;
        setQuestion(questions.find((candidate) => candidate.id === questionId) ?? null);
        setLoaded(true);
      })
      .catch(() => {
        if (!live) return;
        setError("That didn't reach the Librarian. Try again from My book.");
        setLoaded(true);
      });
    return () => {
      live = false;
    };
  }, [client, questionId]);

  // biome-ignore lint/correctness/useExhaustiveDependencies: arriving is a new screen for the keyboard
  useEffect(() => {
    if (loaded) focusBand();
  }, [loaded]);

  if (!loaded) return <Frame busy say={<Waiting>The Librarian is finding your place…</Waiting>} />;

  if (!question) {
    return (
      <Frame say="That question isn't waiting any more.">
        <ErrorMessage message={error} />
        <div className="iv-row">
          <Link to="/my-book" className="button button-primary">
            Back to my book
          </Link>
        </div>
      </Frame>
    );
  }

  const draftKey = draftKeyFor(user?.id ?? "anon", `reading:${question.id}`);
  const say = question.question;

  async function send(text: string) {
    setBusy(true);
    setError(null);
    try {
      await client.answerReading(question?.id ?? "", text);
      clearDraft(draftKey);
      navigate("/interview", { state: { fromReading: true } });
    } catch (reason) {
      // Whether it arrived is what matters: the question is used up once an answer is saved.
      const waiting = await client.readingQuestions().catch(() => null);
      if (waiting && !waiting.some((candidate) => candidate.id === question?.id)) {
        clearDraft(draftKey);
        navigate("/interview", { state: { fromReading: true, answerSaved: true } });
        return;
      }
      // Still waiting, so the answer stays in the field to send again.
      setError(
        reason instanceof InterviewError
          ? reason.message
          : "That didn't reach the Librarian. Your answer is still here.",
      );
      setBusy(false);
    }
  }

  return (
    <Frame
      busy={busy}
      canLeave={false}
      say={busy ? <Waiting holding={say}>The Librarian is reading…</Waiting> : say}
      eyebrow={readingCaption(question)}
    >
      <ErrorMessage message={error} />
      <AnswerPanel
        key={draftKey}
        draftKey={draftKey}
        busy={busy}
        onSend={send}
        note="Leave names out. This can become part of your book."
        // "Not now" only goes back. "No thanks" on My book is what dismisses it.
        aside={
          <Link to="/my-book" className="button button-quiet">
            Not now
          </Link>
        }
      />
    </Frame>
  );
}
