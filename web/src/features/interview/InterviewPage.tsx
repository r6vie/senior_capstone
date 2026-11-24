import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Link, Navigate, useLocation, useNavigate, useSearchParams } from "react-router-dom";
import { api } from "../../api/client";
import { errorMessage } from "../../api/errors";
import { Button } from "../../ui/Button";
import { usePageTitle } from "../../ui/usePageTitle";
import type { Affiliation, MemberContext } from "../account/MemberContextFields";
import { useAuth } from "../auth/AuthProvider";
import { AnswerPanel, clearDraft, draftKeyFor, keepDraft, takeOrphanDrafts } from "./AnswerPanel";
import { apiInterviewClient } from "./apiInterviewClient";
import {
  AskFrame,
  ErrorMessage,
  Frame,
  RetryContext,
  TypedQuestion,
  WAIT_SHOWS_AFTER_MS,
  Waiting,
} from "./InterviewFrame";
import { IntroBook } from "./IntroBook";
import {
  type BookEdit,
  type ChapterEdit,
  type DraftBook,
  type DraftChapter,
  type InterviewClient,
  InterviewError,
  type InterviewState,
  LostError,
  type TitleOption,
} from "./interviewClient";
import {
  FIRST_VERSION_SAVED,
  leaveWords,
  NOT_SAVED_ANOTHER_SCREEN,
  STARTED_FOR_EARLIER,
  useSavedLine,
} from "./LeftoverWords";
import { Hand } from "./librarian/Hand";
import { Notebook } from "./librarian/Notebook";
import { reducedMotion } from "./librarian/pen";
import { useAnnouncer } from "./librarian/useAnnouncer";
import { useNotebook } from "./librarian/useNotebook";
import { ChangesScreen, WaitBox } from "./ProposedChanges";
import { ReviewBook, TitleShelf, WritingBook } from "./RevealParts";
import { type LandingBook, ShelfLanding } from "./ShelfLanding";
import { UndoChanges } from "./UndoChanges";

// The interview, direction A (docs/design/shelf/project/InterviewA.dc.html, trove.md §4), with the band
// replaced by the Librarian's line across the top (StartReveal); the member acts below it.

// A wait past this limit stops and offers another try.
const GIVE_UP_AFTER_MS = 120_000;
// "Welcome back" is for coming back, not for a refresh seconds later.
const WELCOME_BACK_AFTER_MS = 60 * 60 * 1000;
// Once a waiting line shows, it stays at least this long, so it can be read.
const WAIT_MIN_SHOWN_MS = 500;
const LOST_DEFAULT = "That didn't reach the Librarian. Try again.";
const LOST_ANSWER = "That didn't reach the Librarian. Your answer is still here.";
// How often to look while changes are written in the background.
const LOOK_AGAIN_MS = 4000;
// For the first moments of a wait the book is usually nearly ready: look this often until then.
const LOOK_FAST_MS = 300;
const LOOK_FAST_FOR_MS = 5000;

class TimedOut extends Error {}

function giveUpAfter(ms: number): Promise<never> {
  return new Promise((_, reject) => setTimeout(() => reject(new TimedOut()), ms));
}

function isLost(reason: unknown): boolean {
  // fetch rejects with a TypeError when the network fails, and its own words aren't for members.
  return reason instanceof TypeError || reason instanceof TimedOut || reason instanceof LostError;
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
  if (state.stage === "asking") return `asking:${state.questionId ?? state.question}`;
  return state.stage === "drafting" && state.failed ? "draftingFailed" : state.stage;
}

async function saveContext(context: MemberContext): Promise<void> {
  const { data, error } = await api.PUT("/auth/me/context", { body: context });
  if (!data) throw new InterviewError(errorMessage(error));
}

export function InterviewPage({
  client = apiInterviewClient,
  saveMemberContext,
}: {
  client?: InterviewClient;
  saveMemberContext?: (context: MemberContext) => Promise<void>;
}) {
  usePageTitle("Your interview");
  const { user, refreshUser } = useAuth();
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
  const [loadProblem, setLoadProblem] = useState<string | null>(null);
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
  const fromLostReading = Boolean((location.state as { answerSaved?: boolean } | null)?.answerSaved);
  const navigate = useNavigate();
  // "Your book is on the shelf" is for the moment of shelving, from the review. Anything else that
  // arrives at done belongs on My book.
  const [justShelved, setJustShelved] = useState(false);
  // The title the member chose, so the book stays on screen, open, while it's written.
  const [chosenTitle, setChosenTitle] = useState<string | null>(null);
  // Where the review's book stood when the member shelved it: the landing flies from there.
  const [landingFrom, setLandingFrom] = useState<DOMRect | null>(null);
  // Just chosen: the book arrives closed and opens, once, on whichever open-book screen comes first.
  const [bookOpens, setBookOpens] = useState(false);
  useEffect(() => {
    if (!bookOpens || (stageOf(state) !== "drafting" && stageOf(state) !== "reviewing")) return;
    const timer = setTimeout(() => setBookOpens(false), OPEN_MS + 200);
    return () => clearTimeout(timer);
  }, [bookOpens, state]);
  const [leftAsIs, setLeftAsIs] = useState(false);
  // What the last send tried to save, when the reply never came, so nobody can tell if it arrived.
  const unsure = useRef<string | null>(null);

  // Sending again after a lost reply: the first try may have arrived. Look first, and send what's in the
  // field now only if it didn't, so a member's edit is never replaced by their first version.
  const lookThenSend = async (words: string | undefined, call: () => Promise<InterviewState>) => {
    const sent = unsure.current;
    if (sent === null) return call();
    const now = await client.current();
    if (!now || placeOf(now) === placeOf(latest.current)) return call();
    unsure.current = null;
    if (!words || words === sent) {
      if (sent) setNotice("Your answer was saved.");
    } else if (now.stage === "asking") {
      keepDraft(draftKeyFor(userId, now.questionId ?? now.question), words);
      setNotice("Your first version was saved. Your changes are still here for the next answer.");
    } else {
      leaveWords(userId, FIRST_VERSION_SAVED, words);
    }
    return now;
  };
  // On a 409 the interview has moved on. It may be this send that arrived, or another screen that
  // answered first, in which case the words here were never saved and must not disappear.
  const onMoved = (words: string | undefined) => (now: InterviewState, alreadySaved: boolean) => {
    unsure.current = null;
    if (!words) return;
    if (alreadySaved) {
      setNotice("Your answer was saved.");
    } else if (now.stage === "asking") {
      keepDraft(draftKeyFor(userId, now.questionId ?? now.question), words);
      setNotice(
        "You'd already moved past that question on another screen. Your words are still here. Send them if they fit.",
      );
    } else {
      leaveWords(userId, NOT_SAVED_ANOTHER_SCREEN, words);
    }
  };
  // The opening (StartOpen): an interview started on this visit opens with the Librarian's welcome
  // written in its notebook, then the first question typing in. One already under way skips it.
  const [opening, setOpening] = useState<{ place: string | null; writing: boolean } | null>(null);
  // Josef, 2026-11-23 (option A): the welcome is only the hello; the question types in at once beside it.
  const welcomeLines = useMemo(
    () => [`hello, ${(user?.first_name ?? "").toLowerCase()}.`],
    [user?.first_name],
  );
  const [hasSparks, setHasSparks] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  // The Librarian's notebook lives for the whole interview, so the next question can circle an entry.
  const announcer = useAnnouncer();
  const notebook = useNotebook(state?.stage === "asking" ? state.librarian : undefined, announcer.say);
  const savedLine = useSavedLine();

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
        setWelcomedBack(away && current?.stage === "asking" && current.hasAnswers);
        writeSeen(seenKey);
      })
      .catch((reason) => {
        if (!live) return;
        setLoadFailed(true);
        // On a developer's machine the API's reason (often a missing key) is the fastest way to the fix.
        setLoadProblem(import.meta.env.DEV && reason instanceof InterviewError ? reason.message : null);
      })
      .finally(() => live && setLoaded(true));
    return () => {
      live = false;
    };
  }, [client, seenKey, loadAttempt]);

  // Words typed here that were never sent, because another screen moved the interview on.
  const placeForDrafts =
    state?.stage === "asking" ? draftKeyFor(userId, state.questionId ?? state.question) : null;
  useEffect(() => {
    if (!loaded || !placeForDrafts) return;
    for (const text of takeOrphanDrafts(userId, placeForDrafts))
      leaveWords(userId, STARTED_FOR_EARLIER, text);
  }, [loaded, placeForDrafts, userId]);

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

  // The writing happens in the background, so the screen moves on by itself when it's done.
  const stage = state?.stage;
  const place = placeOf(state);
  // Right after a pick the book is usually ready within moments, so it looks often at first, then settles.
  useEffect(() => {
    if (stage !== "writing" && place !== "drafting") return;
    const began = Date.now();
    let timer: ReturnType<typeof setTimeout>;
    let live = true;
    const look = () => {
      const soon = Date.now() - began < LOOK_FAST_FOR_MS;
      timer = setTimeout(
        () => {
          client
            .current()
            .then((now) => {
              if (!live) return;
              if (now && placeOf(now) !== place) setState(now);
              else look();
            })
            .catch(() => live && look());
        },
        soon ? LOOK_FAST_MS : LOOK_AGAIN_MS,
      );
    };
    look();
    return () => {
      live = false;
      clearTimeout(timer);
    };
  }, [client, stage, place]);

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

  // The opening's first question gets its place as soon as it arrives; after that it is fixed.
  useEffect(() => {
    if (opening && opening.place === null && place.startsWith("asking:"))
      setOpening({ place, writing: opening.writing });
  }, [opening, place]);
  const openingWrites = Boolean(opening?.writing && opening.place === place);
  // The typed question stays in place once typed, so the heading's words don't change and aren't read twice.
  const openingHere = Boolean(opening && opening.place === place);

  // Whether the opening is about to write or is writing, read by the focus below without re-running it when
  // the opening ends: by then the member may be somewhere else, and TypedQuestion's onDone moves the keyboard.
  const openingPending = useRef(false);
  openingPending.current = Boolean(opening?.writing && (opening.place === null || opening.place === place));

  // A new question or screen starts at the top with the Librarian's words in view. Where there's a real
  // keyboard the member can start typing at once; on a phone that would cover the question.
  useEffect(() => {
    if (!loaded || loadFailed) return;
    document.documentElement.scrollTop = 0;
    // While the opening writes, the keyboard waits at the question; it moves to the answer once typed.
    const asking = place.startsWith("asking:") && !welcomedBack && !openingPending.current;
    const hasKeyboard = window.matchMedia?.("(hover: hover)").matches;
    const field =
      asking && hasKeyboard
        ? document.querySelector<HTMLElement>(".iv-answer textarea, .iv-answer [role=textbox]")
        : null;
    (field ?? document.querySelector<HTMLElement>(".iv-say"))?.focus({ preventScroll: true });
  }, [place, loaded, loadFailed, welcomedBack]);

  const calling = useRef(false);
  const mounted = useRef(true);
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);
  // Runs one call with a calm waiting line at the top; the screen stays put until it answers.
  const run = useCallback(
    async (
      waiting: string,
      call: () => Promise<InterviewState>,
      options: {
        /** What to repeat if the Librarian fails. */
        retryWith?: () => Promise<InterviewState>;
        /** Instead of Try again, when the API says the member's part was saved and the rest failed. */
        onSavedButStuck?: () => void;
        onSuccess?: () => void;
        /** The interview had already moved past this screen. */
        onMoved?: (now: InterviewState, alreadySaved: boolean) => void;
        lost?: string;
        /** The member's own button is the retry, so what's in the field now is what gets sent. */
        noRetry?: boolean;
        onLost?: () => void;
      } = {},
    ) => {
      // A second press while the first is on its way (a double click, Enter twice) does nothing.
      if (calling.current) return false;
      calling.current = true;
      const began = Date.now();
      setBusy(waiting);
      setError(null);
      setRetry(null);
      setNotice(null);
      // Where the interview really is, if it isn't where this screen thinks. Null if it's the same.
      const movedOn = async () => {
        const now = await client.current();
        return now && placeOf(now) !== placeOf(latest.current) ? now : null;
      };
      const arrive = (now: InterviewState) => {
        setState(now);
        setInterrupted(null);
        writeSeen(seenKey);
        options.onSuccess?.();
      };
      try {
        const now = await Promise.race([call(), giveUpAfter(GIVE_UP_AFTER_MS)]);
        // A waiting line that did appear stays long enough to be read, rather than flickering away.
        const shownFor = Date.now() - began - WAIT_SHOWS_AFTER_MS;
        if (shownFor > 0 && shownFor < WAIT_MIN_SHOWN_MS)
          await new Promise((done) => setTimeout(done, WAIT_MIN_SHOWN_MS - shownFor));
        arrive(now);
        return true;
      } catch (reason) {
        if (isLost(reason)) {
          setError(options.lost ?? LOST_DEFAULT);
          options.onLost?.();
          if (!options.noRetry) {
            // The first try may have arrived even though the reply didn't. Look before repeating it.
            const looked = async () => (await movedOn()) ?? call();
            setRetry(() => () => {
              run(waiting, looked, options);
            });
          }
        } else if (reason instanceof InterviewError && reason.conflict) {
          // A 409 means this screen is out of date. Show what's true rather than the refusal.
          const now = await movedOn().catch(() => null);
          if (now) {
            options.onMoved?.(now, reason.alreadySaved);
            arrive(now);
            return true;
          }
          setError(messageOf(reason));
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
        calling.current = false;
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
          {loadProblem && <p className="iv-note">{loadProblem}</p>}
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
              onClick={() =>
                // ?add only lasts until Start, so the end of this round doesn't land back here.
                run("The Librarian is getting ready…", () => client.reopen(), {
                  onSuccess: () => navigate("/interview", { replace: true }),
                })
              }
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
      const persistContext =
        saveMemberContext ??
        (async (context: MemberContext) => {
          await saveContext(context);
          await refreshUser().catch(() => undefined);
        });
      return (
        <StartScreen
          busy={busy}
          error={error}
          started={Boolean(retry)}
          initialAffiliations={user?.affiliations ?? []}
          initialFounder={user?.founder ?? false}
          onStart={(resume, context) =>
            run(
              resume ? "The Librarian is reading your résumé…" : "The Librarian is getting ready…",
              // "Already started" means an earlier press got through: load that interview rather than refuse.
              () =>
                persistContext(context)
                  .then(() => client.start(resume))
                  .catch(async (reason) => {
                    if (!(reason instanceof InterviewError && reason.conflict)) throw reason;
                    const now = await client.current();
                    if (!now) throw reason;
                    return now;
                  }),
              {
                // A 502 here means the interview exists but its first question failed.
                retryWith: () => client.askAgain(""),
                onSuccess: () => setOpening({ place: null, writing: !reducedMotion() }),
              },
            )
          }
        />
      );
    }

    const say = (text: string) => (busy ? <Waiting holding={text}>{busy}</Waiting> : text);

    switch (state.stage) {
      case "asking": {
        const draftKey = draftKeyFor(userId, state.questionId ?? state.question);
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
                <Button onClick={() => setWelcomedBack(false)}>Back to the question</Button>
              </div>
              <p className="iv-note">Everything you've said so far is saved.</p>
            </Frame>
          );
        }
        const moveOn = (
          kind: "answer" | "skip",
          words: string | undefined,
          call: () => Promise<InterviewState>,
        ) => {
          if (calling.current) return Promise.resolve(false);
          // While the next question is prepared, the Librarian's last look at this answer is written into
          // the notebook, so the wait shows it reading what was sent. Anything missed comes with the question.
          // A reply that lands once the next question is here, or after leaving, is dropped: the next
          // question's own notebook already carries it.
          const sentAt = placeOf(state);
          client
            .finalNotes(state.questionId ?? state.question)
            .then((reply) => {
              if (reply.status !== "done" || !mounted.current || placeOf(latest.current) !== sentAt) return;
              notebook.apply(reply.notebook);
            })
            .catch(() => undefined);
          return run("The Librarian is thinking…", () => lookThenSend(words, call), {
            lost: kind === "answer" ? LOST_ANSWER : LOST_DEFAULT,
            noRetry: true,
            onLost: () => {
              if (words) unsure.current = words;
            },
            onSuccess: () => {
              unsure.current = null;
              clearDraft(draftKey);
            },
            onMoved: onMoved(words),
            onSavedButStuck: () => {
              clearDraft(draftKey);
              unsure.current = null;
              if (interrupted) setNotice("That didn't work either. Try again in a moment.");
              setInterrupted(kind);
            },
          });
        };
        if (interrupted) {
          return (
            <Frame phase={phase} say={say(state.question)} busy={Boolean(busy)}>
              <ErrorMessage message={error} />
              <p className="iv-stuck" role="status">
                {interrupted === "answer" && "Your answer is saved. "}
                The next question didn't come through.
              </p>
              {notice && (
                <p className="iv-note" role="status">
                  {notice}
                </p>
              )}
              <div className="iv-row">
                <Button
                  aria-busy={Boolean(busy)}
                  onClick={() => moveOn(interrupted, undefined, () => client.askAgain(state.id))}
                >
                  Ask me the next question
                </Button>
              </div>
            </Frame>
          );
        }
        const welcome = opening && !inAdding ? { lines: welcomeLines, writing: openingWrites } : undefined;
        return (
          <AskFrame
            eyebrow={inAdding ? "Adding to your book" : "Question"}
            question={
              openingHere && !busy ? (
                <TypedQuestion
                  text={state.question}
                  after={0}
                  onDone={() => {
                    setOpening((now) => (now ? { ...now, writing: false } : now));
                    // Only if the member hasn't gone somewhere themselves in the meantime.
                    const focused = document.activeElement;
                    if (focused && focused !== document.body && !focused.classList.contains("iv-say")) return;
                    if (!window.matchMedia?.("(hover: hover)").matches) return;
                    document
                      .querySelector<HTMLElement>(".iv-answer textarea, .iv-answer [role=textbox]")
                      ?.focus({ preventScroll: true });
                  }}
                />
              ) : (
                say(state.question)
              )
            }
            typing={openingWrites}
            busy={Boolean(busy)}
            aside={<Notebook entries={notebook.entries} welcome={welcome} />}
          >
            <ErrorMessage message={error} />
            {notice && (
              <p className="iv-note" role="status">
                {notice}
              </p>
            )}
            {state.needsMore && (
              <p className="iv-note iv-note-big">I need a little more before I can write your book.</p>
            )}
            <AnswerPanel
              key={draftKey}
              draftKey={draftKey}
              busy={Boolean(busy)}
              onSend={(text) => moveOn("answer", text, () => client.answer(state.id, text))}
              onSkip={() => moveOn("skip", undefined, () => client.skip(state.id))}
              progress={state.nearlyDone ? "Most of the way there." : undefined}
              exit={
                state.canFinish
                  ? {
                      label: inAdding
                        ? "That's enough. Write the changes"
                        : "I've said enough. Show me my book",
                      labelWithWords: inAdding
                        ? "Send this, then write the changes"
                        : "Send this, then show me my book",
                      onFinish: (words) =>
                        run(
                          inAdding
                            ? "The Librarian is writing the changes…"
                            : "The Librarian is gathering what you said…",
                          () => lookThenSend(words, () => client.finish(state.id, words)),
                          {
                            lost: words ? LOST_ANSWER : LOST_DEFAULT,
                            noRetry: Boolean(words),
                            onLost: () => {
                              if (words) unsure.current = words;
                            },
                            onSuccess: () => {
                              unsure.current = null;
                              clearDraft(draftKey);
                            },
                            onMoved: onMoved(words),
                            // After a 502 the words are already saved, so a second try sends none.
                            retryWith: () => client.finish(state.id),
                          },
                        ),
                    }
                  : undefined
              }
              librarian={{
                client,
                interviewId: state.id,
                questionId: state.questionId ?? state.question,
                view: state.librarian,
                notebook,
                say: announcer.say,
              }}
            />
            {announcer.region}
          </AskFrame>
        );
      }
      case "choosing":
        return (
          <RevealScreen
            key={state.id}
            titles={state.titles}
            author={authorName}
            busy={busy}
            error={error}
            onChoose={(titleId) => {
              const title = state.titles.find((option) => option.id === titleId)?.title ?? null;
              setChosenTitle(title);
              setBookOpens(true);
              // Kept for a refresh during the writing, so the open book still shows its title.
              try {
                if (title) sessionStorage.setItem(`trove_chosen:${state.id}`, title);
              } catch {
                // Without storage the book shows its title bar until the book arrives.
              }
              return run("The Librarian is writing your book…", () => client.chooseTitle(state.id, titleId));
            }}
          />
        );
      case "reviewing":
        return (
          <ReviewScreen
            book={state.book}
            opening={bookOpens}
            signOff={state.signOff ?? null}
            onEditBook={async (edit) => {
              const book = await client.editBook(edit);
              setState({ id: state.id, stage: "reviewing", book });
            }}
            onEditChapter={async (chapterId, edit) => {
              const book = await client.editChapter(chapterId, edit);
              setState({ id: state.id, stage: "reviewing", book });
            }}
            busy={busy}
            error={error}
            loadOtherTitles={() => client.otherTitles(state.id)}
            onChangeTitle={(titleId) =>
              run("The Librarian is writing your book…", () => client.changeTitle(state.id, titleId))
            }
            onRemove={(chapterId) =>
              run("Removing that chapter…", () => client.removeChapter(state.id, chapterId))
            }
            onShelve={() => {
              // Where the book is now, so it can fly from there to the shelf.
              setLandingFrom(document.querySelector(".rv-open .ib-left")?.getBoundingClientRect() ?? null);
              return run("Putting your book on the shelf…", () => client.putOnShelf(state.id), {
                onSuccess: () => setJustShelved(true),
              });
            }}
          />
        );
      case "done":
        if (!justShelved) return <Navigate to="/my-book" replace state={{ leftAsIs }} />;
        return <DoneScreen book={state.book} from={landingFrom} />;
      case "drafting":
        if (state.failed) {
          const about = state.about === "titles" ? "your titles" : "your book";
          return (
            <Frame busy={Boolean(busy)} say={say(`I couldn't finish writing ${about}.`)}>
              <p className="iv-note iv-note-big">{savedLine}</p>
              <ErrorMessage message={error} />
              <div className="iv-row">
                <Button
                  aria-busy={Boolean(busy)}
                  onClick={() =>
                    run("The Librarian is writing…", () =>
                      client.retryDrafting(state.about, state.retryTitle),
                    )
                  }
                >
                  Try again
                </Button>
              </div>
            </Frame>
          );
        }
        return (
          <Frame
            busy
            // The titles take a while with the real Librarian; "still working" waits until it's news, and
            // the page already says the answers are saved, once.
            slowAfter={state.about === "titles" ? 45_000 : undefined}
            stillLine="Still working."
            say={
              state.closingLine ?? (
                <Waiting>
                  {state.about === "titles"
                    ? "The Librarian is finding your titles…"
                    : "The Librarian is writing your book…"}
                </Waiting>
              )
            }
          >
            {/* While the book is written, the chosen book is open on screen, its contents still blank. */}
            {state.about === "book" && (
              <WritingBook
                title={chosenTitle ?? storedTitle(state.id)}
                author={authorName}
                opening={bookOpens}
              />
            )}
            <p className="iv-note iv-note-big rv-saved">{savedLine}</p>
          </Frame>
        );
      case "notEnough":
        return (
          <Frame
            busy={Boolean(busy)}
            say={say("I don't have enough yet for three chapters. Everything you've said is saved.")}
          >
            <ErrorMessage message={error} />
            <div className="iv-row">
              <Button
                aria-busy={Boolean(busy)}
                onClick={() => run("The Librarian is thinking…", () => client.askAgain(state.id))}
              >
                Keep answering
              </Button>
            </div>
          </Frame>
        );
      case "writing":
        return (
          <Frame
            canLeave={false}
            say={fromReading ? "I'm checking whether this belongs in your book." : "I'm writing the changes."}
          >
            {fromLostReading && (
              <p className="iv-note" role="status">
                Your answer was saved.
              </p>
            )}
            <WaitBox />
          </Frame>
        );
      case "writeFailed":
        return (
          <Frame canLeave={false} busy={Boolean(busy)} say={say("I couldn't write the changes.")}>
            <p className="iv-note iv-note-big">Your answers are saved.</p>
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
            saveChoices={(approved) => client.saveChoices(approved)}
            apply={(approved, blurb, onDone) => {
              run("Updating your book…", () => client.applyChanges(approved, blurb), {
                onSuccess: () => {
                  setLeftAsIs(approved.length === 0);
                  onDone();
                },
              });
            }}
          />
        );
      case "nothing":
        if (state.droppedForNames) {
          const { readingQuestionId, readingAnswer } = state;
          return (
            <Frame canLeave={false} say="Nothing here changes your book.">
              <p className="iv-note iv-note-big">{droppedSentence(state.droppedWords)}</p>
              <div className="iv-row">
                {readingQuestionId && (
                  <Link
                    to={`/interview/reading/${readingQuestionId}`}
                    className="button button-primary"
                    onClick={() => {
                      if (readingAnswer) {
                        keepDraft(draftKeyFor(userId, `reading:${readingQuestionId}`), readingAnswer);
                      }
                    }}
                  >
                    Say it again
                  </Link>
                )}
                <Link
                  to="/my-book"
                  className={`button ${readingQuestionId ? "button-quiet" : "button-primary"}`}
                >
                  Back to my book
                </Link>
              </div>
            </Frame>
          );
        }
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
        return (
          <UpdatedScreen book={state.book} canUndo={state.canUndo} onUndo={() => client.undoChanges()} />
        );
    }
  })();

  return <RetryContext.Provider value={retry}>{screen}</RetryContext.Provider>;
}

// The API's limits (books/models.py and the engine's).
export const MAX_BOOK_TITLE = 80;
export const MAX_CHAPTER_TITLE = 100;
export const MAX_SUMMARY = 300;
export const MAX_BLURB = 600;

export function bookFields(book: DraftBook) {
  return [
    { key: "title", label: "Title", value: book.title, max: MAX_BOOK_TITLE },
    ...(book.blurb !== null
      ? [{ key: "blurb", label: "Back cover", value: book.blurb, max: MAX_BLURB, multiline: true }]
      : []),
  ];
}

export function chapterFields(chapter: DraftChapter) {
  return [
    { key: "title", label: "Chapter title", value: chapter.title, max: MAX_CHAPTER_TITLE },
    { key: "summary", label: "What it's about", value: chapter.summary, max: MAX_SUMMARY, multiline: true },
  ];
}

export function droppedSentence(words: string[] | undefined): string {
  return words?.length
    ? `I left this out because it named someone or somewhere: ${words.join(", ")}. Change those and I'll try again.`
    : "I left this out because it named someone or somewhere. Say it without the name and I'll try again.";
}

function messageOf(reason: unknown): string {
  return reason instanceof Error && reason.message
    ? reason.message
    : "Something went wrong. Please try again.";
}

// ---------- Start ----------

const START_SAY =
  "I'll ask you one question at a time, to find the book you haven't written yet. Nobody sees it until you put it on the shelf.";

function StartScreen({
  busy,
  error,
  started,
  initialAffiliations,
  initialFounder,
  onStart,
}: {
  busy: string | null;
  error: string | null;
  /** The interview exists and only its first question failed, so Try again is the one way on. */
  started: boolean;
  initialAffiliations: Affiliation[];
  initialFounder: boolean;
  onStart: (resume: File | null, context: MemberContext) => void;
}) {
  // Stays set through the retry's wait, so Start doesn't flash back while Try again is working.
  const [exists, setExists] = useState(started);
  useEffect(() => {
    if (started) setExists(true);
  }, [started]);

  // Starting again would only be refused: the interview is there, waiting for its first question.
  if (exists || started) {
    return (
      <Frame busy={Boolean(busy)} say={busy ? <Waiting holding={START_SAY}>{busy}</Waiting> : START_SAY}>
        <ErrorMessage message={error} />
      </Frame>
    );
  }

  return (
    <IntroBook
      error={error}
      busy={busy}
      initialAffiliations={initialAffiliations}
      initialFounder={initialFounder}
      onStart={onStart}
    />
  );
}

// ---------- The reveal ----------

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
  return (
    <Frame busy={Boolean(busy)} say={busy ? <Waiting holding={REVEAL_SAY}>{busy}</Waiting> : REVEAL_SAY}>
      {/* The three titles as white books on a shelf (StartReveal): the whole book is what you choose. */}
      <TitleShelf
        titles={titles}
        author={author}
        busy={Boolean(busy)}
        error={<ErrorMessage message={error} />}
        failed={Boolean(error)}
        onChoose={onChoose}
      />
    </Frame>
  );
}

// The reader's open (BookReader.css --open-time).
const OPEN_MS = 850;

function stageOf(state: InterviewState | null): string | null {
  return state?.stage ?? null;
}

function storedTitle(interviewId: string): string | null {
  try {
    return sessionStorage.getItem(`trove_chosen:${interviewId}`);
  } catch {
    return null;
  }
}

// ---------- Your book ----------

const REVIEW_SAY = "Here is your book. Edit or remove anything that doesn't sound like you.";
const MIN_CHAPTERS = 3;

function ReviewScreen({
  book,
  opening,
  signOff,
  onEditBook,
  onEditChapter,
  busy,
  error,
  loadOtherTitles,
  onChangeTitle,
  onRemove,
  onShelve,
}: {
  book: DraftBook;
  /** Arriving straight from the pick: the book comes forward closed and opens. */
  opening?: boolean;
  /** The Librarian's one line under the title, in its hand. */
  signOff: string | null;
  onEditBook: (edit: BookEdit) => Promise<void>;
  onEditChapter: (chapterId: string, edit: ChapterEdit) => Promise<void>;
  busy: string | null;
  error: string | null;
  loadOtherTitles: () => Promise<TitleOption[]>;
  onChangeTitle: (titleId: string) => Promise<boolean>;
  onRemove: (chapterId: string) => Promise<boolean>;
  onShelve: () => void;
}) {
  const [others, setOthers] = useState<TitleOption[] | null>(null);
  const [othersError, setOthersError] = useState<string | null>(null);
  const canRemove = book.chapters.length > MIN_CHAPTERS;
  // The back cover changes with a removal, and the member should be told. Until their next action.
  const [blurbAtRemoval, setBlurbAtRemoval] = useState<string | null | undefined>(undefined);

  async function remove(chapterId: string) {
    setBlurbAtRemoval(book.blurb);
    await onRemove(chapterId);
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
      {/* Review is the shelf's open book (StartReveal): every word a field that saves itself. */}
      <ReviewBook
        book={book}
        opening={opening}
        signOff={signOff ? <SignOff line={signOff} /> : null}
        canRemove={canRemove}
        onEditBook={onEditBook}
        onEditChapter={onEditChapter}
        onRemove={async (chapterId) => {
          await remove(chapterId);
          return true;
        }}
        notes={
          <>
            {blurbAtRemoval !== undefined && blurbAtRemoval !== book.blurb && (
              <p className="iv-note" role="status">
                Back cover rewritten to match.
              </p>
            )}
            {others !== null && (
              <div className="iv-others">
                <p className="iv-note">This rewrites your chapters to fit the new title.</p>
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
            <ErrorMessage message={error} />
          </>
        }
        onShelve={onShelve}
        busy={Boolean(busy)}
        others={
          others === null && (
            <button type="button" className="button button-quiet" onClick={seeOthers}>
              See the other titles
            </button>
          )
        }
      />
    </Frame>
  );
}

// ---------- Done ----------

// Written once, at pen pace, the first time the book is shown; at rest after that.
function SignOff({ line }: { line: string }) {
  const [life, setLife] = useState<"writing" | "resting">(() =>
    sessionStorage.getItem(`trove_signoff:${line}`) ? "resting" : "writing",
  );
  useEffect(() => {
    if (life !== "writing") return;
    try {
      sessionStorage.setItem(`trove_signoff:${line}`, "1");
    } catch {
      // It just writes again next time.
    }
    const timer = setTimeout(() => setLife("resting"), 4000);
    return () => clearTimeout(timer);
  }, [life, line]);
  return (
    <p className="lib-signoff">
      <span className="iv-visually-hidden">Librarian: {line}</span>
      <Hand text={line} life={life} delay={0.4} />
    </p>
  );
}

function DoneScreen({ book, from }: { book: DraftBook; from: DOMRect | null }) {
  // The book lands on the real shelf (StartReveal, step 7): its own id gives its cover art, and a few of the
  // shelf's books stand either side of it.
  const [shelf, setShelf] = useState<{ id: string; neighbours: LandingBook[] } | null>(null);
  useEffect(() => {
    let live = true;
    Promise.all([api.GET("/books/me"), api.GET("/books", { params: { query: { limit: 12 } } })])
      .then(([mine, all]) => {
        if (!live || !mine.data) return;
        const id = mine.data.id;
        const neighbours = (all.data?.books ?? [])
          .filter((other) => other.id !== id)
          .slice(0, 6)
          .map((other) => ({ id: other.id, title: other.title, authorName: other.author_name }));
        setShelf({ id, neighbours });
      })
      .catch(() => undefined);
    return () => {
      live = false;
    };
  }, []);
  return (
    <Frame say="Your book is on the shelf." canLeave={false}>
      <div className="iv-landing">
        {shelf ? (
          <ShelfLanding
            book={{ id: shelf.id, title: book.title, authorName: book.authorName }}
            neighbours={shelf.neighbours}
            from={from}
          />
        ) : (
          <div className="iv-landing-wait" aria-hidden="true" />
        )}
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

function UpdatedScreen({
  book,
  canUndo,
  onUndo,
}: {
  book: DraftBook;
  canUndo: boolean;
  onUndo: () => Promise<void>;
}) {
  const [undone, setUndone] = useState(false);
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
          <div className="iv-row">
            <Link to="/my-book" className="button button-primary">
              See my book
            </Link>
            {canUndo && !undone && <UndoChanges onUndo={onUndo} onDone={() => setUndone(true)} />}
          </div>
        </div>
      </div>
    </Frame>
  );
}
