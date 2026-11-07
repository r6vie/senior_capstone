import { type ReactNode, useCallback, useEffect, useId, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { Button } from "../../ui/Button";
import { useAuth } from "../auth/AuthProvider";
import { AnswerPanel, clearDraft } from "./AnswerPanel";
import { createFakeInterviewClient } from "./fakeInterviewClient";
import type { DraftBook, InterviewClient, InterviewState, Phase } from "./interviewClient";
import "./InterviewPage.css";

// The interview, direction A "The question band" (docs/design/shelf/project/InterviewA.dc.html,
// trove.md §4). The Librarian's words stand alone on the black band; the member acts below it.

const PHASES: { id: Phase; label: string }[] = [
  { id: "sweep", label: "Sweep" },
  { id: "dig", label: "Dig" },
  { id: "shape", label: "Shape" },
];

function Frame({
  phase,
  say,
  busy,
  canLeave = true,
  children,
}: {
  phase?: Phase;
  canLeave?: boolean;
  say: ReactNode;
  /** While the Librarian works, the member's side holds still rather than greying out. */
  busy?: boolean;
  children?: ReactNode;
}) {
  return (
    <div className="interview">
      <header className="iv-top">
        <span className="wordmark">Trove</span>
        {phase && (
          <nav className="iv-phases" aria-label="Where we are">
            {PHASES.map((item) => (
              <span key={item.id} aria-current={item.id === phase ? "step" : undefined}>
                {item.label}
              </span>
            ))}
          </nav>
        )}
        {canLeave && (
          <Link to="/" className="button button-quiet">
            Leave for now
          </Link>
        )}
      </header>
      <section className="iv-band dark">
        <span className="halo" />
        <p className="iv-say" aria-live="polite">
          {say}
        </p>
      </section>
      <main className="iv-act" inert={busy} aria-busy={busy}>
        {children}
      </main>
    </div>
  );
}

function Waiting({ children, holding }: { children: ReactNode; holding?: ReactNode }) {
  // The band keeps the height of what it held, so the page doesn't jump while the Librarian thinks.
  return (
    <>
      {holding && (
        <span className="iv-holding" aria-hidden="true">
          {holding}
        </span>
      )}
      <span className="iv-waiting" data-over={Boolean(holding)}>
        {children}
      </span>
    </>
  );
}

function ErrorMessage({ message }: { message: string | null }) {
  if (!message) return null;
  return (
    <div className="message message-error" role="alert">
      <span>{message}</span>
    </div>
  );
}

function SmallBook({ title, author }: { title: string; author: string }) {
  return (
    <span className="book book-sm">
      <span className="book-cover">
        <span className="book-title">{title}</span>
        <span className="book-author">{author}</span>
      </span>
    </span>
  );
}

export function InterviewPage({ client: given }: { client?: InterviewClient }) {
  const { user } = useAuth();
  const firstName = user?.first_name ?? "";
  const client = useMemo(() => given ?? createFakeInterviewClient(firstName), [given, firstName]);

  const [state, setState] = useState<InterviewState | null>(null);
  const [loaded, setLoaded] = useState(false);
  const [welcomedBack, setWelcomedBack] = useState(false);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let live = true;
    client
      .current()
      .then((current) => {
        if (!live) return;
        setState(current);
        setWelcomedBack(current?.stage === "asking" && current.hasAnswers);
      })
      .catch((reason: unknown) => live && setError(messageOf(reason)))
      .finally(() => live && setLoaded(true));
    return () => {
      live = false;
    };
  }, [client]);

  // Runs one call with a calm waiting line on the band; the screen stays put until it answers.
  const run = useCallback(async (waiting: string, call: () => Promise<InterviewState>) => {
    setBusy(waiting);
    setError(null);
    try {
      setState(await call());
      return true;
    } catch (reason) {
      setError(messageOf(reason));
      return false;
    } finally {
      setBusy(null);
    }
  }, []);

  if (!loaded) return <Frame say={<Waiting>The Librarian is finding your place…</Waiting>} />;

  if (!state) {
    return (
      <StartScreen
        busy={busy}
        error={error}
        onStart={(resume) =>
          run(resume ? "The Librarian is reading your résumé…" : "The Librarian is getting ready…", () =>
            client.start(resume),
          )
        }
      />
    );
  }

  const say = (text: string) => (busy ? <Waiting holding={text}>{busy}</Waiting> : text);

  switch (state.stage) {
    case "asking": {
      const draftKey = `trove_interview_draft:${state.id}:${state.question}`;
      if (welcomedBack && state.lastTopic) {
        return (
          <Frame
            phase={state.phase}
            busy={Boolean(busy)}
            say={say(`Welcome back. Last time you were telling me about ${state.lastTopic}.`)}
          >
            <ErrorMessage message={error} />
            <div className="iv-row">
              <Button onClick={() => setWelcomedBack(false)}>Pick up where we left off</Button>
              {/* The waiting question is saved as asked; starting again only clears the unsent draft. */}
              <button
                type="button"
                className="button button-quiet"
                onClick={() => {
                  clearDraft(draftKey);
                  setWelcomedBack(false);
                }}
              >
                Start that part again
              </button>
            </div>
            <p className="iv-note">Everything you've said so far is saved.</p>
          </Frame>
        );
      }
      return (
        <Frame phase={state.phase} say={say(state.question)} busy={Boolean(busy)}>
          <ErrorMessage message={error} />
          <AnswerPanel
            key={draftKey}
            draftKey={draftKey}
            busy={Boolean(busy)}
            hasSavedAnswers={state.hasAnswers}
            onSend={async (text) => {
              if (await run("The Librarian is reading…", () => client.answer(state.id, text)))
                clearDraft(draftKey);
            }}
          >
            {state.canFinish && (
              <div className="iv-exit">
                <button
                  type="button"
                  className="button button-quiet"
                  onClick={() =>
                    run("The Librarian is gathering what you said…", () => client.finish(state.id))
                  }
                >
                  I've said enough. Show me my book
                </button>
              </div>
            )}
          </AnswerPanel>
        </Frame>
      );
    }
    case "shaping":
      return (
        <ShapeScreen
          playback={say(state.playback)}
          busy={busy}
          error={error}
          onConfirm={() => run("The Librarian is finding your titles…", () => client.confirmShape(state.id))}
          onCorrect={(correction) =>
            run("The Librarian is listening again…", () => client.correctShape(state.id, correction))
          }
        />
      );
    case "choosing":
      return (
        <RevealScreen
          key={state.id}
          titles={state.titles}
          author={firstName}
          busy={busy}
          error={error}
          onChoose={(titleId) =>
            run("The Librarian is writing your book…", () => client.chooseTitle(state.id, titleId))
          }
        />
      );
    case "reviewing":
      return (
        <ReviewScreen
          book={state.book}
          busy={busy}
          error={error}
          onRewrite={(chapterId) =>
            run("The Librarian is rewriting that chapter…", () => client.rewriteChapter(state.id, chapterId))
          }
          onRemove={(chapterId) =>
            run("Removing that chapter…", () => client.removeChapter(state.id, chapterId))
          }
          onShelve={() => run("Putting your book on the shelf…", () => client.putOnShelf(state.id))}
        />
      );
    case "done":
      return <DoneScreen book={state.book} />;
  }
}

function messageOf(reason: unknown): string {
  return reason instanceof Error && reason.message
    ? reason.message
    : "Something went wrong. Please try again.";
}

// ---------- Start ----------

const START_SAY =
  "In about twenty minutes I'll ask you questions, one at a time, to find the book you haven't written yet.";

function StartScreen({
  busy,
  error,
  onStart,
}: {
  busy: string | null;
  error: string | null;
  onStart: (resume: File | null) => void;
}) {
  const [resume, setResume] = useState<File | null>(null);
  const [fileError, setFileError] = useState<string | null>(null);
  const [dragging, setDragging] = useState(false);
  const input = useRef<HTMLInputElement>(null);
  const inputId = useId();

  function pick(file: File | undefined) {
    if (!file) return;
    if (file.type !== "application/pdf" && !file.name.toLowerCase().endsWith(".pdf")) {
      setFileError("That isn't a PDF. Choose a PDF, or start without one.");
      return;
    }
    setFileError(null);
    setResume(file);
  }

  return (
    <Frame busy={Boolean(busy)} say={busy ? <Waiting holding={START_SAY}>{busy}</Waiting> : START_SAY}>
      <div className="panel iv-resume">
        <h3>A résumé, if you like</h3>
        {/* biome-ignore lint/a11y/noStaticElementInteractions: a drop target for the mouse; "Choose a PDF" is the keyboard path */}
        <div
          className="iv-drop"
          data-dragging={dragging}
          onDragOver={(event) => {
            event.preventDefault();
            setDragging(true);
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={(event) => {
            event.preventDefault();
            setDragging(false);
            pick(event.dataTransfer.files[0]);
          }}
        >
          {resume ? (
            <>
              <span className="iv-file">{resume.name}</span>
              <button type="button" className="button button-quiet" onClick={() => setResume(null)}>
                Remove
              </button>
            </>
          ) : (
            <>
              <span>Drop a PDF here</span>
              <label htmlFor={inputId} className="button button-secondary iv-sm">
                Choose a PDF
              </label>
            </>
          )}
          <input
            id={inputId}
            ref={input}
            type="file"
            accept="application/pdf,.pdf"
            className="iv-visually-hidden"
            onChange={(event) => {
              pick(event.target.files?.[0]);
              event.target.value = "";
            }}
          />
        </div>
        {fileError && (
          <p className="message" role="status">
            {fileError}
          </p>
        )}
        <p className="iv-note">
          Optional. It only shapes my questions. It is never stored, and nothing from it goes into your book.
        </p>
      </div>
      <ErrorMessage message={error} />
      <div className="iv-row">
        <Button onClick={() => onStart(resume)} aria-busy={Boolean(busy)}>
          Start the interview
        </Button>
        <span className="iv-quiet-note">Twenty to twenty-five minutes. Leave and come back at any time.</span>
      </div>
    </Frame>
  );
}

// ---------- Shape ----------

function ShapeScreen({
  playback,
  busy,
  error,
  onConfirm,
  onCorrect,
}: {
  playback: ReactNode;
  busy: string | null;
  error: string | null;
  onConfirm: () => void;
  onCorrect: (correction: string) => Promise<boolean>;
}) {
  const [correction, setCorrection] = useState("");
  const [needsWords, setNeedsWords] = useState(false);
  const field = useRef<HTMLTextAreaElement>(null);
  const fieldId = useId();

  return (
    <Frame phase="shape" say={playback} busy={Boolean(busy)}>
      <div className="field iv-answer iv-answer-short" data-invalid={needsWords || undefined}>
        <label htmlFor={fieldId}>Yes, or tell me what's different</label>
        <textarea
          id={fieldId}
          ref={field}
          value={correction}
          placeholder="It's close, but…"
          onChange={(event) => {
            setCorrection(event.target.value);
            setNeedsWords(false);
          }}
        />
        {needsWords && <span className="hint">Tell me what's different, then press Not quite.</span>}
      </div>
      <ErrorMessage message={error} />
      <div className="iv-row">
        <Button onClick={onConfirm} aria-busy={Boolean(busy)}>
          Yes, that's me
        </Button>
        <Button
          variant="secondary"
          onClick={async () => {
            if (!correction.trim()) {
              setNeedsWords(true);
              field.current?.focus();
              return;
            }
            if (await onCorrect(correction.trim())) setCorrection("");
          }}
        >
          Not quite
        </Button>
      </div>
    </Frame>
  );
}

// ---------- The reveal ----------

const REVEAL_STEP_MS = 700;

function RevealScreen({
  titles,
  author,
  busy,
  error,
  onChoose,
}: {
  titles: { id: string; title: string; why: string }[];
  author: string;
  busy: string | null;
  error: string | null;
  onChoose: (titleId: string) => void;
}) {
  const reduceMotion = useMemo(
    () => typeof window !== "undefined" && window.matchMedia?.("(prefers-reduced-motion: reduce)").matches,
    [],
  );
  // The three titles arrive one at a time (trove.md §4), unless the member asked for less motion.
  const [shown, setShown] = useState(reduceMotion ? titles.length : 1);
  const [picked, setPicked] = useState<string | null>(null);

  useEffect(() => {
    if (shown >= titles.length) return;
    const timer = setTimeout(() => setShown((count) => count + 1), REVEAL_STEP_MS);
    return () => clearTimeout(timer);
  }, [shown, titles.length]);

  return (
    <Frame
      busy={Boolean(busy)}
      say={
        busy ? (
          <Waiting holding={"Here are three titles for your book. Take a moment with each."}>{busy}</Waiting>
        ) : (
          "Here are three titles for your book. Take a moment with each."
        )
      }
    >
      <fieldset className="iv-picks">
        <legend className="iv-visually-hidden">Choose a title</legend>
        {titles.map((option, index) => (
          <label key={option.id} className="iv-pick" data-on={picked === option.id} hidden={index >= shown}>
            <SmallBook title={option.title} author={author} />
            <input
              type="radio"
              name="title"
              value={option.id}
              checked={picked === option.id}
              onChange={() => setPicked(option.id)}
            />
            <b>{option.title}</b>
            <span className="iv-why">{option.why}</span>
          </label>
        ))}
      </fieldset>
      <ErrorMessage message={error} />
      <div className="iv-row">
        <Button disabled={!picked} aria-busy={Boolean(busy)} onClick={() => picked && onChoose(picked)}>
          Choose this title
        </Button>
        {!picked && shown >= titles.length && (
          <span className="iv-quiet-note">Pick the one that sounds most like you.</span>
        )}
      </div>
    </Frame>
  );
}

// ---------- Your book ----------

function ReviewScreen({
  book,
  busy,
  error,
  onRewrite,
  onRemove,
  onShelve,
}: {
  book: DraftBook;
  busy: string | null;
  error: string | null;
  onRewrite: (chapterId: string) => Promise<boolean>;
  onRemove: (chapterId: string) => Promise<boolean>;
  onShelve: () => void;
}) {
  const [working, setWorking] = useState<{ chapterId: string; action: "rewrite" | "remove" } | null>(null);

  async function act(chapterId: string, action: "rewrite" | "remove") {
    setWorking({ chapterId, action });
    await (action === "rewrite" ? onRewrite : onRemove)(chapterId);
    setWorking(null);
  }

  return (
    <Frame
      busy={Boolean(busy)}
      say={
        busy ? (
          <Waiting holding={"Here is your book. Change anything that doesn't sound like you."}>
            {busy}
          </Waiting>
        ) : (
          "Here is your book. Change anything that doesn't sound like you."
        )
      }
    >
      <div className="iv-booktitle">
        <SmallBook title={book.title} author={book.authorName} />
        <div>
          <h2>{book.title}</h2>
          <p>by {book.authorName}</p>
        </div>
      </div>
      <ol className="iv-chapters">
        {book.chapters.map((chapter, index) => (
          <li key={chapter.id}>
            <span className="iv-n">{index + 1}</span>
            <div>
              <b>{chapter.title}</b>
              <span>{chapter.summary}</span>
            </div>
            <div className="iv-ch-act">
              <Button
                variant="secondary"
                className="iv-sm"
                aria-busy={working?.chapterId === chapter.id && working.action === "rewrite"}
                onClick={() => act(chapter.id, "rewrite")}
              >
                Rewrite this one
              </Button>
              <button
                type="button"
                className="button button-quiet iv-sm"
                onClick={() => act(chapter.id, "remove")}
              >
                Remove
              </button>
            </div>
          </li>
        ))}
      </ol>
      <ErrorMessage message={error} />
      <div className="iv-row">
        <Button onClick={onShelve} aria-busy={Boolean(busy)}>
          Put it on the shelf
        </Button>
      </div>
    </Frame>
  );
}

// ---------- Done ----------

function DoneScreen({ book }: { book: DraftBook }) {
  return (
    <Frame say="Your book is on the shelf." canLeave={false}>
      <div className="iv-booktitle">
        <SmallBook title={book.title} author={book.authorName} />
        <div>
          <h2>{book.title}</h2>
          <p>by {book.authorName}</p>
        </div>
      </div>
      <div className="iv-row">
        <Link to="/" className="button button-primary">
          Go to the shelf
        </Link>
      </div>
    </Frame>
  );
}
