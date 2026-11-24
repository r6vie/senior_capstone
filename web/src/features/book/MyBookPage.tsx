import { type ReactNode, useCallback, useEffect, useRef, useState } from "react";
import { Link, useLocation } from "react-router-dom";
import { artFor } from "../../ui/art/bookArt";
import { Button } from "../../ui/Button";
import { PageLoading } from "../../ui/Loading";
import { usePageTitle } from "../../ui/usePageTitle";
import { forgetOwnBook, loadOwnBook } from "../discovery/bookPreload";
import { apiInterviewClient } from "../interview/apiInterviewClient";
import { droppedSentence } from "../interview/InterviewPage";
import type { BookStage, InterviewClient, LastRound, MyBook } from "../interview/interviewClient";
import { LeftoverWords } from "../interview/LeftoverWords";
import { DesignPicker } from "./DesignPicker";
import { OwnBook } from "./OwnBook";
import "./MyBookPage.css";

// The member's own page (My book D2, approved by Josef 2026-11-23): the shelf's open book, opened to its author and
// edited where it is; a switch for being on the shelf; the Librarian underneath with the next step. No numbers of any
// kind, and no Save or Cancel: every word saves as it's typed.

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
        About ten minutes. You can stop sooner, and leave and come back at any time. Nobody sees your book
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

/** On the shelf, as a switch: turning it off takes the book off the shelf, and on puts it back. */
function ShelfSwitch({
  on,
  busy,
  onChange,
}: {
  on: boolean;
  busy: boolean;
  onChange: (on: boolean) => void;
}) {
  return (
    <button
      type="button"
      role="switch"
      className="mb-switch"
      aria-checked={on}
      aria-busy={busy || undefined}
      // Never disabled, so the keyboard stays on it: presses while one is saving are queued, the latest winning.
      onClick={() => onChange(!on)}
    >
      <span>On the shelf</span>
      <i aria-hidden="true" />
    </button>
  );
}

/** The Librarian, one black block under the book: what comes next, and the way to it. */
function Librarian({ line, children }: { line?: ReactNode; children?: ReactNode }) {
  return (
    <section className="mb-lib" aria-label="The Librarian">
      <span className="caption mb-lib-caption">The Librarian</span>
      {line && <p className="mb-lib-line">{line}</p>}
      {children && <div className="mb-lib-go">{children}</div>}
    </section>
  );
}

function NextStep({
  stage,
  question,
  removal,
  onCancelRemoval,
  onRetry,
  retrying,
}: {
  stage: BookStage;
  /** The question waiting in a round that's already open. */
  question: string | null;
  /** The only open change is a removal the member started. */
  removal: { chapterId: string; title: string } | null;
  onCancelRemoval: () => void;
  onRetry: () => void;
  retrying: boolean;
}) {
  switch (stage) {
    case "draft":
      return (
        <Librarian line="Other members can't see it until you put it on the shelf.">
          <Link to="/interview" className="button button-primary">
            Review your book
          </Link>
        </Librarian>
      );
    case "adding":
      return (
        <Librarian line={question ?? undefined}>
          <Link to="/interview" className="button button-primary">
            Continue adding to your book
          </Link>
        </Librarian>
      );
    case "writing":
      return <Librarian line="I'm writing your changes. Your book on the shelf hasn't changed." />;
    case "writeFailed":
      return (
        <Librarian line="Your changes couldn't be written. Your answers are saved.">
          <Button onClick={onRetry} aria-busy={retrying}>
            Try again
          </Button>
        </Librarian>
      );
    case "changesWaiting":
      if (removal) {
        return (
          <Librarian line={`You started removing ${removal.title}.`}>
            <Link to={`/my-book/remove/${removal.chapterId}?finish`} className="button button-primary">
              Finish removing
            </Link>
            <button type="button" className="button button-quiet" onClick={onCancelRemoval}>
              Keep it
            </button>
          </Librarian>
        );
      }
      return (
        <Librarian line="Your book on the shelf hasn't changed. These changes go live only when you confirm.">
          <Link to="/interview" className="button button-primary">
            Review the proposed changes
          </Link>
        </Librarian>
      );
    default:
      // No round open, so no question yet: a fixed line in its place (Josef, 2026-11-24).
      return (
        <Librarian line="There's more to your story.">
          <Link to="/interview?add" className="button button-primary">
            Continue with the Librarian
          </Link>
        </Librarian>
      );
  }
}

export function MyBookPage({ client = apiInterviewClient }: { client?: InterviewClient }) {
  usePageTitle("My book");
  const [stage, setStage] = useState<BookStage | null>(null);
  const [book, setBook] = useState<MyBook | null>(null);
  // The book's id chooses its cover art (ui/art/bookArt.ts); the interview client's book doesn't carry it.
  const [bookId, setBookId] = useState<string | null>(null);
  const [failed, setFailed] = useState(false);
  const [problem, setProblem] = useState<string | null>(null);
  const [retrying, setRetrying] = useState(false);
  const [removal, setRemoval] = useState<{ chapterId: string; title: string } | null>(null);
  const [lastRound, setLastRound] = useState<LastRound>({ empty: false });
  const [question, setQuestion] = useState<string | null>(null);
  const [switching, setSwitching] = useState(false);
  // The switch moves at once; the server catches up, and if it refuses, the page shows what's true.
  const [wanted, setWanted] = useState<boolean | null>(null);
  // The latest position asked for, and whether a save is under way: one save at a time, each for the latest ask,
  // so a quick off-then-on ends on the shelf, as the switch shows.
  const latest = useRef<boolean | null>(null);
  const saving = useRef(false);
  const onShelfNow = useRef(false);
  const [designing, setDesigning] = useState(false);
  // Leaving the picker hands the keyboard back to the pen that opened it.
  const backToPen = useRef(false);
  useEffect(() => {
    if (designing || !backToPen.current) return;
    backToPen.current = false;
    document.querySelector<HTMLElement>(".mb-pen")?.focus({ preventScroll: true });
  }, [designing]);
  const [savingDesign, setSavingDesign] = useState(false);
  const [designProblem, setDesignProblem] = useState<string | null>(null);
  const leftAsIs = Boolean((useLocation().state as { leftAsIs?: boolean } | null)?.leftAsIs);
  const stageNow = useRef<BookStage | null>(null);
  const heading = useRef<HTMLHeadingElement>(null);

  const load = useCallback(async () => {
    setFailed(false);
    try {
      // All together, so the next step is drawn once, right the first time.
      const [nextStage, nextBook, nextRound, own] = await Promise.all([
        client.stage(),
        client.myBook(),
        client.lastRound().catch(() => ({ empty: false })),
        loadOwnBook(),
      ]);
      const [nextRemoval, open] = await Promise.all([
        nextStage === "changesWaiting" ? client.openRemoval().catch(() => null) : null,
        // A round already open: the Librarian's block shows the question waiting in it.
        nextStage === "adding" ? client.current().catch(() => null) : null,
      ]);
      setQuestion(open?.stage === "asking" ? open.question : null);
      stageNow.current = nextStage;
      setStage(nextStage);
      setBook(nextBook);
      setBookId(own?.id ?? null);
      setLastRound(nextRound);
      setRemoval(nextRemoval);
    } catch {
      setFailed(true);
    }
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

  // Arriving on the page starts the keyboard at its heading.
  const arrived = Boolean(stage);
  useEffect(() => {
    if (arrived) heading.current?.focus({ preventScroll: true });
  }, [arrived]);

  async function attempt(call: () => Promise<unknown>, after: () => void) {
    setProblem(null);
    const before = stageNow.current;
    try {
      await call();
      after();
    } catch {
      // Often the server has moved on and the page is what's out of date. Say so only if it isn't.
      await load();
      if (stageNow.current === before) setProblem("That didn't go through. Try again.");
    }
  }

  const title = (
    <h1 className="mb-title" ref={heading} tabIndex={-1}>
      My book
    </h1>
  );

  if (failed) {
    return (
      <main className="mb-page">
        {title}
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
        <PageLoading />
        <h1 className="mb-title">My book</h1>
        <p className="mb-note">Finding your book…</p>
      </main>
    );
  }

  if (!book) {
    return (
      <main className="mb-page">
        {title}
        <div className="mb-one">
          <LeftoverWords />
          <NoBookYet stage={stage} />
          {problem && (
            <p className="message" role="alert">
              {problem}
            </p>
          )}
        </div>
      </main>
    );
  }

  const onShelf = stage !== "draft";
  const open =
    stage === "adding" || stage === "writing" || stage === "writeFailed" || stage === "changesWaiting";
  const art = bookId ? artFor(bookId, book.design) : null;
  // Saved means live, so the page shows the book as the server now has it.
  const editBook = async (edit: Parameters<InterviewClient["editBook"]>[0]) => {
    setBook(await client.editBook(edit));
  };
  const editChapter = async (chapterId: string, edit: Parameters<InterviewClient["editChapter"]>[1]) => {
    setBook(await client.editChapter(chapterId, edit));
  };

  return (
    <main className="mb-page mb-d2">
      <LeftoverWords />
      <div className="mb-top">
        {title}
        {onShelf && (
          <ShelfSwitch
            on={wanted ?? book.status === "on_shelf"}
            busy={switching}
            onChange={async (on) => {
              latest.current = on;
              setWanted(on);
              if (saving.current) return;
              saving.current = true;
              setSwitching(true);
              onShelfNow.current = book.status === "on_shelf";
              while (latest.current !== null && latest.current !== onShelfNow.current) {
                const target = latest.current;
                await attempt(
                  async () => {
                    const saved = await (target ? client.putBackOnShelf() : client.takeOffShelf());
                    onShelfNow.current = saved.status === "on_shelf";
                    setBook(saved);
                  },
                  () => undefined,
                ).catch(() => undefined);
                // attempt() reloads and says so when a save is refused; then the page shows what's true.
                if (onShelfNow.current !== target) break;
              }
              latest.current = null;
              saving.current = false;
              setWanted(null);
              setSwitching(false);
            }}
          />
        )}
      </div>
      {designing && art ? (
        <DesignPicker
          current={art}
          title={book.title}
          author={book.authorName}
          busy={savingDesign}
          error={designProblem}
          onUse={async (chosen) => {
            if (chosen.id === art.id) {
              backToPen.current = true;
              setDesigning(false);
              return;
            }
            setSavingDesign(true);
            setDesignProblem(null);
            try {
              setBook(await client.editBook({ design: chosen.id }));
              forgetOwnBook();
              backToPen.current = true;
              setDesigning(false);
            } catch (reason) {
              setDesignProblem(reason instanceof Error ? reason.message : "That didn't save. Try again.");
            } finally {
              setSavingDesign(false);
            }
          }}
          onBack={() => {
            setDesignProblem(null);
            backToPen.current = true;
            setDesigning(false);
          }}
        />
      ) : (
        <>
          <OwnBook
            book={book}
            art={art}
            canRemove={onShelf && !open && book.chapters.length > MIN_CHAPTERS}
            onEditBook={editBook}
            onEditChapter={editChapter}
            onRemove={(chapterId) => attempt(() => client.removeFromShelf(chapterId, null), load)}
            onDesign={() => setDesigning(true)}
          />
          <NextStep
            stage={stage}
            question={question}
            removal={removal}
            onCancelRemoval={() => attempt(() => client.cancelRemoval(), load)}
            retrying={retrying}
            onRetry={async () => {
              setRetrying(true);
              await attempt(() => client.retryWriting("me"), load);
              setRetrying(false);
            }}
          />
          {leftAsIs && <p className="mb-note">Your book stays as it is.</p>}
          {lastRound.empty && onShelf && !open && (
            <p className="mb-note">
              {lastRound.droppedForNames
                ? droppedSentence(lastRound.droppedWords)
                : "Your last answers didn't change your book. They're saved, and the next questions can use them."}
            </p>
          )}
        </>
      )}
      {problem && (
        <p className="message" role="alert">
          {problem}
        </p>
      )}
    </main>
  );
}
