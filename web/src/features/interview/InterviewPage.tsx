import { type ReactNode, useCallback, useEffect, useId, useMemo, useRef, useState } from "react";
import { Link, Navigate, useLocation, useSearchParams } from "react-router-dom";
import { Button } from "../../ui/Button";
import { useAuth } from "../auth/AuthProvider";
import { AnswerPanel, clearDraft, draftKeyFor } from "./AnswerPanel";
import { apiInterviewClient } from "./apiInterviewClient";
import { ErrorMessage, Frame, RetryContext, SmallBook, Waiting } from "./InterviewFrame";
import {
  type DraftBook,
  type DraftChapter,
  type InterviewClient,
  InterviewError,
  type InterviewState,
  type TitleOption,
} from "./interviewClient";
import { ChangesScreen, WaitBox } from "./ProposedChanges";

// The interview, direction A "The question band" (docs/design/shelf/project/InterviewA.dc.html,
// trove.md §4). The Librarian's words stand alone on the black band; the member acts below it.

// A wait past this limit stops and offers another try.
const GIVE_UP_AFTER_MS = 120_000;
// "Welcome back" is for coming back, not for a refresh seconds later.
const WELCOME_BACK_AFTER_MS = 60 * 60 * 1000;
const LOST_DEFAULT = "That didn't reach the Librarian. Try again.";
const LOST_ANSWER = "That didn't reach the Librarian. Your answer is still here.";
// How often to look while changes are written in the background.
const LOOK_AGAIN_MS = 4000;

class TimedOut extends Error {}

function giveUpAfter(ms: number): Promise<never> {
  return new Promise((_, reject) => setTimeout(() => reject(new TimedOut()), ms));
}

function isLost(reason: unknown): boolean {
  // fetch rejects with a TypeError when the network fails, and its own words aren't for members.
  return reason instanceof TypeError || reason instanceof TimedOut;
}

function readSeen(key: string): number | null {
  try {
    const value = localStorage.getItem(key);
    return value ? Number(value) : null;
  } catch {
    return null;
  }
}

function writeSeen(key: string) {
  try {
    localStorage.setItem(key, String(Date.now()));
  } catch {
    // Without storage the member is welcomed back a little too often. No harm done.
  }
}

// Where the member is, to tell a new question or screen from the same one.
function placeOf(state: InterviewState | null): string {
  if (!state) return "";
  return state.stage === "asking" ? `asking:${state.question}` : state.stage;
}

export function InterviewPage({ client = apiInterviewClient }: { client?: InterviewClient }) {
  const { user } = useAuth();
  // Books carry the full name; it falls back to the first name for accounts made before last names.
  const authorName = user?.full_name ?? "";

  const userId = user?.id ?? "anon";
  const seenKey = `trove_interview_seen:${userId}`;

  const [state, setState] = useState<InterviewState | null>(null);
  const [loaded, setLoaded] = useState(false);
  const [welcomedBack, setWelcomedBack] = useState(false);
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [retry, setRetry] = useState<(() => void) | null>(null);
  const [loadFailed, setLoadFailed] = useState(false);
  const [loadAttempt, setLoadAttempt] = useState(0);
  // The answer or skip is saved, but the next question didn't come through.
  const [interrupted, setInterrupted] = useState<"answer" | "skip" | null>(null);
  const latest = useRef(state);
  latest.current = state;
  const [search] = useSearchParams();
  const adding = search.has("add");
  const location = useLocation();
  // Arrived from answering the question after a reading: the wait and the outcome say so.
  const fromReading = Boolean((location.state as { fromReading?: boolean } | null)?.fromReading);
  // Done from an earlier visit has nothing to do here. Done just now is the moment to say so.
  const [doneOnArrival, setDoneOnArrival] = useState(false);
  const [hasSparks, setHasSparks] = useState(false);

  // biome-ignore lint/correctness/useExhaustiveDependencies: loadAttempt is what asks for another try
  useEffect(() => {
    let live = true;
    client
      .current()
      .then((current) => {
        if (!live) return;
        const seen = readSeen(seenKey);
        const away = seen === null || Date.now() - seen > WELCOME_BACK_AFTER_MS;
        setState(current);
        setDoneOnArrival(current?.stage === "done");
        setWelcomedBack(away && current?.stage === "asking" && current.hasAnswers);
        writeSeen(seenKey);
      })
      .catch(() => live && setLoadFailed(true))
      .finally(() => live && setLoaded(true));
    return () => {
      live = false;
    };
  }, [client, seenKey, loadAttempt]);

  // Sparks shape the questions, so the start screens mention them when there are any. Never a number.
  useEffect(() => {
    let live = true;
    client
      .sparks()
      .then((sparks) => live && setHasSparks(sparks.length > 0))
      .catch(() => undefined);
    return () => {
      live = false;
    };
  }, [client]);

  // The changes are written in the background, so the screen moves on by itself when they're ready.
  const stage = state?.stage;
  useEffect(() => {
    if (stage !== "writing") return;
    const timer = setInterval(() => {
      client
        .current()
        .then((now) => {
          if (now && now.stage !== "writing") setState(now);
        })
        .catch(() => undefined);
    }, LOOK_AGAIN_MS);
    return () => clearInterval(timer);
  }, [client, stage]);

  // While the Librarian works the member's side is inert, which drops keyboard focus to the page.
  // If they stayed on the same screen, put it back at the start of their side.
  const wasBusy = useRef(false);
  useEffect(() => {
    if (busy) {
      wasBusy.current = true;
      return;
    }
    if (!wasBusy.current) return;
    wasBusy.current = false;
    const focused = document.activeElement;
    if (!focused || focused === document.body) {
      document.querySelector<HTMLElement>(".iv-act")?.focus({ preventScroll: true });
    }
  }, [busy]);

  // A new question or screen starts at the top with the Librarian's words in view. Where there's a real
  // keyboard the member can start typing at once; on a phone that would cover the question.
  const place = placeOf(state);
  useEffect(() => {
    if (!loaded || loadFailed) return;
    document.documentElement.scrollTop = 0;
    const asking = place.startsWith("asking:") && !welcomedBack;
    const hasKeyboard = window.matchMedia?.("(hover: hover)").matches;
    const field = asking && hasKeyboard ? document.querySelector<HTMLElement>(".iv-answer textarea") : null;
    (field ?? document.querySelector<HTMLElement>(".iv-say"))?.focus({ preventScroll: true });
  }, [place, loaded, loadFailed, welcomedBack]);

  // Runs one call with a calm waiting line on the band; the screen stays put until it answers.
  const run = useCallback(
    async (
      waiting: string,
      call: () => Promise<InterviewState>,
      options: {
        /** What to repeat if the Librarian fails: after a saved answer, ask again rather than resend. */
        retryWith?: () => Promise<InterviewState>;
        /** Instead of Try again, when the Librarian failed after the member's part was saved. */
        onSavedButStuck?: () => void;
        onSuccess?: () => void;
        lost?: string;
      } = {},
    ) => {
      setBusy(waiting);
      setError(null);
      setRetry(null);
      try {
        setState(await Promise.race([call(), giveUpAfter(GIVE_UP_AFTER_MS)]));
        setInterrupted(null);
        writeSeen(seenKey);
        options.onSuccess?.();
        return true;
      } catch (reason) {
        if (isLost(reason)) {
          setError(options.lost ?? LOST_DEFAULT);
          // The first try may have arrived even though the reply didn't. Look before repeating it.
          const looked = async () => {
            const now = await client.current();
            return now && placeOf(now) !== placeOf(latest.current) ? now : call();
          };
          setRetry(() => () => {
            run(waiting, looked, options);
          });
        } else if (reason instanceof InterviewError && reason.retryable) {
          if (options.onSavedButStuck) {
            options.onSavedButStuck();
          } else {
            setError(messageOf(reason));
            const again = options.retryWith ?? call;
            setRetry(() => () => {
              run(waiting, again, { ...options, retryWith: again });
            });
          }
        } else {
          setError(messageOf(reason));
        }
        return false;
      } finally {
        setBusy(null);
      }
    },
    [client, seenKey],
  );

  const screen = (() => {
    if (!loaded) return <Frame busy say={<Waiting>The Librarian is finding your place…</Waiting>} />;

    // Not the start screen: this member may well have an interview we just couldn't read.
    if (loadFailed) {
      return (
        <Frame say="I couldn't find your place just now. Nothing you've said is lost.">
          <div className="iv-row">
            <Button
              onClick={() => {
                setLoadFailed(false);
                setLoaded(false);
                setLoadAttempt((count) => count + 1);
              }}
            >
              Try again
            </Button>
          </div>
        </Frame>
      );
    }

    // Reopening: from My book, on a book that's on the shelf. Nothing is open until they press Start.
    if (adding && (!state || state.stage === "done" || state.stage === "nothing")) {
      const say = "A few more questions, about what isn't in your book yet. You can finish after any answer.";
      return (
        <Frame
          canLeave={false}
          busy={Boolean(busy)}
          say={busy ? <Waiting holding={say}>{busy}</Waiting> : say}
        >
          <p className="iv-note iv-note-big">
            Nothing changes on the shelf until you approve it.
            {hasSparks && ' Chapters you marked "I have one like this" will shape some of the questions.'}
          </p>
          <ErrorMessage message={error} />
          <div className="iv-row">
            <Button
              aria-busy={Boolean(busy)}
              onClick={() => run("The Librarian is getting ready…", () => client.reopen())}
            >
              Start the questions
            </Button>
            <Link to="/my-book" className="button button-quiet">
              Back to my book
            </Link>
          </div>
        </Frame>
      );
    }

    if (!state) {
      return (
        <StartScreen
          hasSparks={hasSparks}
          busy={busy}
          error={error}
          onStart={(resume) =>
            run(
              resume ? "The Librarian is reading your résumé…" : "The Librarian is getting ready…",
              () => client.start(resume),
              // A 502 here means the interview exists but its first question failed.
              { retryWith: () => client.askAgain("") },
            )
          }
        />
      );
    }

    const say = (text: string) => (busy ? <Waiting holding={text}>{busy}</Waiting> : text);

    switch (state.stage) {
      case "asking": {
        const draftKey = draftKeyFor(userId, state.question);
        const inAdding = state.round === "adding";
        const phase = inAdding ? undefined : state.phase;
        if (welcomedBack && state.lastTopic) {
          return (
            <Frame
              phase={phase}
              busy={Boolean(busy)}
              say={say(`Welcome back. Last time you were telling me about ${state.lastTopic}.`)}
            >
              <ErrorMessage message={error} />
              <div className="iv-row">
                <Button onClick={() => setWelcomedBack(false)}>Continue</Button>
                {/* Leaves the same way "Leave for now" does: everything is already saved. */}
                <Link to="/my-book" className="button button-quiet">
                  Continue later
                </Link>
              </div>
              <p className="iv-note">Everything you've said so far is saved.</p>
            </Frame>
          );
        }
        // What was said is safe once this runs, whichever try gets through.
        const moveOn = (kind: "answer" | "skip", call: () => Promise<InterviewState>) =>
          run("The Librarian is thinking…", call, {
            lost: kind === "answer" ? LOST_ANSWER : LOST_DEFAULT,
            onSuccess: () => clearDraft(draftKey),
            onSavedButStuck: () => {
              clearDraft(draftKey);
              setInterrupted(kind);
            },
          });
        if (interrupted) {
          return (
            <Frame phase={phase} say={say(state.question)} busy={Boolean(busy)}>
              <ErrorMessage message={error} />
              <p className="iv-stuck" role="status">
                {interrupted === "answer" && "Your answer is saved. "}
                The next question didn't come through.
              </p>
              <div className="iv-row">
                <Button
                  aria-busy={Boolean(busy)}
                  onClick={() => moveOn(interrupted, () => client.askAgain(state.id))}
                >
                  Ask me the next question
                </Button>
              </div>
            </Frame>
          );
        }
        return (
          <Frame phase={phase} say={say(state.question)} busy={Boolean(busy)}>
            <ErrorMessage message={error} />
            <AnswerPanel
              key={draftKey}
              draftKey={draftKey}
              busy={Boolean(busy)}
              onSend={(text) => moveOn("answer", () => client.answer(state.id, text))}
              onSkip={() => moveOn("skip", () => client.skip(state.id))}
              exit={
                state.canFinish
                  ? {
                      label: inAdding
                        ? "That's enough. Write the changes"
                        : "I've said enough. Show me my book",
                      labelWithWords: inAdding
                        ? "Send this, then write the changes"
                        : "Send this, then show me my book",
                      note: !inAdding && state.phase === "dig" ? "Most of the way there." : undefined,
                      onFinish: (words) =>
                        run(
                          inAdding
                            ? "The Librarian is writing the changes…"
                            : "The Librarian is gathering what you said…",
                          () => client.finish(state.id, words),
                          {
                            lost: words ? LOST_ANSWER : LOST_DEFAULT,
                            onSuccess: () => clearDraft(draftKey),
                            // After a 502 the words are already saved, so a second try sends none.
                            retryWith: () => client.finish(state.id),
                          },
                        ),
                    }
                  : undefined
              }
            />
          </Frame>
        );
      }
      case "shaping":
        return (
          <ShapeScreen
            playback={say(state.playback)}
            busy={busy}
            error={error}
            onConfirm={() =>
              run("The Librarian is finding your titles…", () => client.confirmShape(state.id), {
                retryWith: () => client.askAgain(state.id),
              })
            }
            onCorrect={(correction) =>
              run("The Librarian is listening again…", () => client.correctShape(state.id, correction), {
                retryWith: () => client.askAgain(state.id),
              })
            }
          />
        );
      case "choosing":
        return (
          <RevealScreen
            key={state.id}
            titles={state.titles}
            author={authorName}
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
            loadOtherTitles={() => client.otherTitles(state.id)}
            onChangeTitle={(titleId) =>
              run("The Librarian is writing your book…", () => client.changeTitle(state.id, titleId))
            }
            onRewriteBlurb={() =>
              run("The Librarian is rewriting the back cover…", () => client.rewriteBlurb(state.id))
            }
            onRewrite={(chapterId) =>
              run("The Librarian is rewriting that chapter…", () =>
                client.rewriteChapter(state.id, chapterId),
              )
            }
            onRemove={(chapterId) =>
              run("Removing that chapter…", () => client.removeChapter(state.id, chapterId))
            }
            onShelve={() => run("Putting your book on the shelf…", () => client.putOnShelf(state.id))}
          />
        );
      case "done":
        if (doneOnArrival) return <Navigate to="/my-book" replace />;
        return <DoneScreen book={state.book} />;
      case "writing":
        return fromReading ? (
          <Frame canLeave={false} say="I'm checking whether this belongs in your book.">
            <WaitBox title="Reading your answer against your book." />
          </Frame>
        ) : (
          <Frame canLeave={false} say="I'm writing the changes.">
            <WaitBox title="Writing your changes." />
          </Frame>
        );
      case "writeFailed":
        return (
          <Frame canLeave={false} busy={Boolean(busy)} say={say("I couldn't write the changes.")}>
            <p className="iv-note iv-note-big">The changes weren't written. Your answers are saved.</p>
            <div className="iv-row">
              <Button
                aria-busy={Boolean(busy)}
                onClick={() => run("I'm writing the changes.", () => client.retryWriting(state.id))}
              >
                Try again
              </Button>
              <Link to="/my-book" className="button button-quiet">
                Back to my book
              </Link>
            </div>
          </Frame>
        );
      case "proposing":
        return (
          <ChangesScreen
            state={state}
            userId={userId}
            busy={busy}
            error={error}
            writeBlurb={(approved) => client.blurbFor(approved)}
            apply={(approved, blurb, onDone) => {
              run("Updating your book…", () => client.applyChanges(approved, blurb), { onSuccess: onDone });
            }}
          />
        );
      case "nothing":
        return (
          <Frame canLeave={false} say="Nothing here changes your book.">
            <p className="iv-note iv-note-big">
              {fromReading
                ? "What you said is saved."
                : "What you said is saved, and the next questions can use it."}
            </p>
            <div className="iv-row">
              <Link to="/my-book" className="button button-primary">
                Back to my book
              </Link>
            </div>
          </Frame>
        );
      case "updated":
        return <UpdatedScreen book={state.book} onUndo={() => client.undoChanges()} />;
    }
  })();

  return <RetryContext.Provider value={retry}>{screen}</RetryContext.Provider>;
}

function messageOf(reason: unknown): string {
  return reason instanceof Error && reason.message
    ? reason.message
    : "Something went wrong. Please try again.";
}

// ---------- Start ----------

const START_SAY =
  "I'll ask you one question at a time, to find the book you haven't written yet. Nobody sees it until you put it on the shelf.";

// The API's limit on a résumé.
const MAX_RESUME_BYTES = 5 * 1024 * 1024;

function StartScreen({
  hasSparks,
  busy,
  error,
  onStart,
}: {
  hasSparks: boolean;
  busy: string | null;
  error: string | null;
  onStart: (resume: File | null) => void;
}) {
  const [resume, setResume] = useState<File | null>(null);
  const [fileError, setFileError] = useState<string | null>(null);
  const [dragging, setDragging] = useState(false);
  const [addingResume, setAddingResume] = useState(false);
  const input = useRef<HTMLInputElement>(null);
  const inputId = useId();

  function pick(file: File | undefined) {
    if (!file) return;
    if (file.type !== "application/pdf" && !file.name.toLowerCase().endsWith(".pdf")) {
      setFileError("That isn't a PDF. Choose a PDF, or start without one.");
      return;
    }
    if (file.size > MAX_RESUME_BYTES) {
      setFileError("That PDF is over 5 MB. Choose a smaller one, or start without it.");
      return;
    }
    setFileError(null);
    setResume(file);
  }

  return (
    <Frame busy={Boolean(busy)} say={busy ? <Waiting holding={START_SAY}>{busy}</Waiting> : START_SAY}>
      <ErrorMessage message={error} />
      <div className="iv-row">
        <Button onClick={() => onStart(resume)} aria-busy={Boolean(busy)}>
          Start the interview
        </Button>
        <span className="iv-quiet-note">
          About twenty minutes. You can stop sooner, and leave and come back at any time.
        </span>
      </div>
      {hasSparks && (
        <p className="iv-note">I'll use the chapters you marked to shape some of the questions.</p>
      )}
      {!addingResume && (
        <button type="button" className="iv-textlink" onClick={() => setAddingResume(true)}>
          Have a résumé? Add a PDF so my first questions fit you.
        </button>
      )}
      {addingResume && (
        <div className="panel iv-resume">
          <h2>A résumé, if you like</h2>
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
                <button
                  type="button"
                  className="button button-quiet"
                  onClick={() => {
                    setResume(null);
                    input.current?.focus();
                  }}
                >
                  Remove
                </button>
              </>
            ) : (
              <>
                <span className="iv-drop-text">Drop a PDF here</span>
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
              tabIndex={resume ? -1 : undefined}
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
            Optional. I read it for places to dig. The file isn't kept, its text is deleted when the interview
            ends, and nothing from it goes into your book.
          </p>
        </div>
      )}
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
  const fieldId = useId();
  const words = correction.trim();

  async function correct() {
    if (await onCorrect(words)) setCorrection("");
  }

  return (
    <Frame phase="shape" say={playback} busy={Boolean(busy)}>
      <div className="field iv-answer iv-answer-short">
        <label htmlFor={fieldId}>Yes, or tell me what's different</label>
        <textarea
          id={fieldId}
          value={correction}
          placeholder="It's close, but…"
          onChange={(event) => setCorrection(event.target.value)}
          onKeyDown={(event) => {
            if (words && event.key === "Enter" && (event.metaKey || event.ctrlKey)) {
              event.preventDefault();
              correct();
            }
          }}
        />
      </div>
      <ErrorMessage message={error} />
      {/* The red button always does what the field says, so a typed correction can't be lost to it. */}
      {words ? (
        <div className="iv-row">
          <Button onClick={correct} aria-busy={Boolean(busy)} aria-keyshortcuts="Meta+Enter Control+Enter">
            Send my correction
          </Button>
          <button type="button" className="iv-textlink" onClick={onConfirm}>
            Yes, that's me, ignore this
          </button>
        </div>
      ) : (
        <div className="iv-row">
          <Button onClick={onConfirm} aria-busy={Boolean(busy)}>
            Yes, that's me
          </Button>
        </div>
      )}
    </Frame>
  );
}

// ---------- The reveal ----------

const REVEAL_STEP_MS = 700;
const REVEAL_SAY = "Here are three titles for your book.";

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
    <Frame busy={Boolean(busy)} say={busy ? <Waiting holding={REVEAL_SAY}>{busy}</Waiting> : REVEAL_SAY}>
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

const REVIEW_SAY = "Here is your book. Rewrite or remove anything that doesn't sound like you.";
const MIN_CHAPTERS = 3;

function ChapterRow({
  index,
  chapter,
  canRemove,
  working,
  onAct,
}: {
  index: number;
  chapter: DraftChapter;
  canRemove: boolean;
  working: boolean;
  onAct: (action: "rewrite" | "remove") => void;
}) {
  const [showing, setShowing] = useState(false);
  const [removing, setRemoving] = useState(false);

  if (removing) {
    return (
      <li className="iv-confirm">
        <span className="iv-n">{index + 1}</span>
        <div>
          <b>Remove this chapter?</b>
          <span>{chapter.title}</span>
        </div>
        <div className="iv-ch-act">
          <button
            type="button"
            className="button button-quiet iv-sm"
            aria-label={`Remove ${chapter.title}`}
            onClick={() => onAct("remove")}
          >
            Remove
          </button>
          <button type="button" className="button button-quiet iv-sm" onClick={() => setRemoving(false)}>
            Keep it
          </button>
        </div>
      </li>
    );
  }

  return (
    <li>
      <span className="iv-n">{index + 1}</span>
      <div>
        <b>{chapter.title}</b>
        <span>{chapter.summary}</span>
        {chapter.quotes.length > 0 && (
          <>
            <button
              type="button"
              className="button button-quiet iv-sm iv-show"
              aria-expanded={showing}
              aria-label={`${showing ? "Hide" : "Show"} what you said for ${chapter.title}`}
              onClick={() => setShowing((now) => !now)}
            >
              {showing ? "Hide what you said" : "Show what you said"}
            </button>
            {showing && (
              <div className="iv-quotes">
                {chapter.quotes.map((quote) => (
                  <p key={quote}>{quote}</p>
                ))}
              </div>
            )}
          </>
        )}
      </div>
      <div className="iv-ch-act">
        <button
          type="button"
          className="button button-quiet iv-sm"
          aria-busy={working}
          aria-label={`Rewrite ${chapter.title}`}
          onClick={() => onAct("rewrite")}
        >
          Rewrite
        </button>
        {canRemove && (
          <button
            type="button"
            className="button button-quiet iv-sm"
            aria-label={`Remove ${chapter.title}`}
            onClick={() => setRemoving(true)}
          >
            Remove
          </button>
        )}
      </div>
    </li>
  );
}

function ReviewScreen({
  book,
  busy,
  error,
  loadOtherTitles,
  onChangeTitle,
  onRewriteBlurb,
  onRewrite,
  onRemove,
  onShelve,
}: {
  book: DraftBook;
  busy: string | null;
  error: string | null;
  loadOtherTitles: () => Promise<TitleOption[]>;
  onChangeTitle: (titleId: string) => Promise<boolean>;
  onRewriteBlurb: () => void;
  onRewrite: (chapterId: string) => Promise<boolean>;
  onRemove: (chapterId: string) => Promise<boolean>;
  onShelve: () => void;
}) {
  const [working, setWorking] = useState<string | null>(null);
  const [others, setOthers] = useState<TitleOption[] | null>(null);
  const [othersError, setOthersError] = useState<string | null>(null);
  const canRemove = book.chapters.length > MIN_CHAPTERS;

  async function act(chapterId: string, action: "rewrite" | "remove") {
    setWorking(action === "rewrite" ? chapterId : null);
    await (action === "rewrite" ? onRewrite : onRemove)(chapterId);
    setWorking(null);
  }

  async function seeOthers() {
    setOthersError(null);
    try {
      setOthers((await loadOtherTitles()).filter((option) => option.title !== book.title));
    } catch (reason) {
      setOthersError(messageOf(reason));
    }
  }

  return (
    <Frame
      quiet
      busy={Boolean(busy)}
      say={busy ? <Waiting holding={REVIEW_SAY}>{busy}</Waiting> : REVIEW_SAY}
    >
      <div className="iv-booktitle">
        <span className="book" aria-hidden="true">
          <span className="book-cover">
            <span className="book-title">{book.title}</span>
            <span className="book-author">{book.authorName}</span>
          </span>
        </span>
        <div>
          <h2>{book.title}</h2>
          <p className="iv-by">by {book.authorName}</p>
          {book.blurb && <p className="iv-blurb">{book.blurb}</p>}
          <div className="iv-head-act">
            {book.blurb && (
              <button type="button" className="button button-quiet iv-sm iv-show" onClick={onRewriteBlurb}>
                Rewrite the back cover
              </button>
            )}
            {others === null && (
              <button type="button" className="button button-quiet iv-sm iv-show" onClick={seeOthers}>
                See the other titles
              </button>
            )}
          </div>
          {others !== null && (
            <div className="iv-others">
              <p className="iv-note">
                Picking one writes your book again, so any chapter you rewrote may change.
              </p>
              {others.map((option) => (
                <button
                  key={option.id}
                  type="button"
                  className="iv-other"
                  onClick={async () => {
                    if (await onChangeTitle(option.id)) setOthers(null);
                  }}
                >
                  <b>{option.title}</b>
                  <span className="iv-why">{option.why}</span>
                </button>
              ))}
              <button
                type="button"
                className="button button-quiet iv-sm iv-show"
                onClick={() => setOthers(null)}
              >
                Keep this title
              </button>
            </div>
          )}
          {othersError && (
            <p className="message" role="status">
              {othersError}
            </p>
          )}
        </div>
      </div>
      <p className="iv-note">The words under a chapter are yours. Only you see them.</p>
      <ol className="iv-chapters">
        {book.chapters.map((chapter, index) => (
          <ChapterRow
            key={chapter.id}
            index={index}
            chapter={chapter}
            canRemove={canRemove}
            working={working === chapter.id}
            onAct={(action) => act(chapter.id, action)}
          />
        ))}
      </ol>
      {!canRemove && <p className="iv-note">A book keeps at least three chapters.</p>}
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
      <div className="panel iv-done">
        <span className="book">
          <span className="book-cover">
            <span className="book-title">{book.title}</span>
            <span className="book-author">{book.authorName}</span>
          </span>
        </span>
        <div className="iv-done-text">
          <p>
            Other members can find it now. When someone asks to check it out, you say yes or no. Your contact
            details stay private until you say yes.
          </p>
          <div className="iv-row">
            <Link to="/my-book" className="button button-primary">
              See my book
            </Link>
            <Link to="/" className="button button-quiet">
              Go to the shelf
            </Link>
          </div>
        </div>
      </div>
    </Frame>
  );
}

function UpdatedScreen({ book, onUndo }: { book: DraftBook; onUndo: () => Promise<void> }) {
  const [undone, setUndone] = useState(false);
  const [failed, setFailed] = useState(false);
  const say = undone ? "Your book is back as it was." : "Your book on the shelf is updated.";
  return (
    <Frame say={say} canLeave={false}>
      <div className="panel iv-done">
        <span className="book" aria-hidden="true">
          <span className="book-cover">
            <span className="book-title">{book.title}</span>
            <span className="book-author">{book.authorName}</span>
          </span>
        </span>
        <div className="iv-done-text">
          {failed && (
            <p className="message" role="alert">
              That didn't go through. Your changes are still on the shelf. Try again.
            </p>
          )}
          <div className="iv-row">
            <Link to="/my-book" className="button button-primary">
              See my book
            </Link>
            {!undone && (
              <button
                type="button"
                className="button button-quiet"
                onClick={async () => {
                  setFailed(false);
                  try {
                    await onUndo();
                    setUndone(true);
                  } catch {
                    setFailed(true);
                  }
                }}
              >
                Undo these changes
              </button>
            )}
          </div>
        </div>
      </div>
    </Frame>
  );
}
