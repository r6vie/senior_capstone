import { type CSSProperties, useEffect, useId, useRef, useState } from "react";
import { Button } from "../../ui/Button";
import { type Affiliation, type MemberContext, MemberContextFields } from "../account/MemberContextFields";
import { ErrorMessage, IvTop } from "./InterviewFrame";
import { reducedMotion } from "./librarian/pen";
import "./IntroBook.css";

// The interview's first screen (StartInterview, approved by Josef 2026-11-23): the shelf's open book, empty.
// Three lines type onto its title page while the contents page draws in its chapter places; then the
// member's place at CWRU, an optional résumé, and Start. Skip, or reduced motion, opens on the end.

const LINES = [
  "I’ll ask you one question at a time.",
  "What you tell me becomes the chapters of your book.",
  "About 20 minutes. Nobody sees it until you put it on the shelf.",
];
const PLACES = 3;
// One letter every this many milliseconds, and a breath between lines.
const LETTER_MS = 30;
const LINE_PAUSE_MS = 350;

// The API's limit on a résumé.
const MAX_RESUME_BYTES = 5 * 1024 * 1024;

/** How far the intro has got: letters typed on each line, and chapter places drawn. */
interface Progress {
  typed: number[];
  drawn: number;
  done: boolean;
}

const END: Progress = { typed: LINES.map((line) => line.length), drawn: PLACES, done: true };

function useIntro(): [Progress, () => void] {
  const [progress, setProgress] = useState<Progress>(() =>
    reducedMotion() ? END : { typed: LINES.map(() => 0), drawn: 0, done: false },
  );
  const skipped = useRef(progress.done);
  useEffect(() => {
    if (skipped.current) return;
    const timers: ReturnType<typeof setTimeout>[] = [];
    let at = 0;
    LINES.forEach((line, index) => {
      for (let letter = 1; letter <= line.length; letter++) {
        const count = letter;
        timers.push(
          setTimeout(
            () =>
              setProgress((now) => ({ ...now, typed: now.typed.map((n, i) => (i === index ? count : n)) })),
            at + letter * LETTER_MS,
          ),
        );
      }
      // The chapters draw in, one by one, while the second line types.
      if (index === 1) {
        for (let place = 1; place <= PLACES; place++) {
          const drawn = place;
          timers.push(
            setTimeout(
              () => setProgress((now) => ({ ...now, drawn })),
              at + (line.length * LETTER_MS * place) / (PLACES + 1),
            ),
          );
        }
      }
      at += line.length * LETTER_MS + LINE_PAUSE_MS;
    });
    timers.push(setTimeout(() => setProgress(END), at));
    return () => {
      for (const timer of timers) clearTimeout(timer);
    };
  }, []);
  return [
    progress,
    () => {
      skipped.current = true;
      setProgress(END);
    },
  ];
}

export function IntroBook({
  error,
  busy,
  initialAffiliations,
  initialFounder,
  onStart,
}: {
  error: string | null;
  /** What the Librarian is doing after Start, said beside the button while it works. */
  busy: string | null;
  initialAffiliations: Affiliation[];
  initialFounder: boolean;
  onStart: (resume: File | null, context: MemberContext) => void;
}) {
  const [progress, skip] = useIntro();
  const [affiliations, setAffiliations] = useState(initialAffiliations);
  const [founder, setFounder] = useState(initialFounder);
  const [resume, setResume] = useState<File | null>(null);
  const [fileError, setFileError] = useState<string | null>(null);
  const [dragging, setDragging] = useState(false);
  const input = useRef<HTMLInputElement>(null);
  const inputId = useId();
  const titleId = useId();
  const start = useRef<HTMLDivElement>(null);

  // Skipping hands the keyboard to what comes next, rather than leaving it on a button that's gone.
  const skipNow = () => {
    skip();
    requestAnimationFrame(() => start.current?.querySelector<HTMLElement>("input, button")?.focus());
  };

  function pick(file: File | undefined) {
    if (!file) return;
    setFileError(null);
    if (file.type !== "application/pdf" && !file.name.toLowerCase().endsWith(".pdf")) {
      setFileError("That isn't a PDF. Choose a PDF, or start without one.");
      return;
    }
    if (file.size > MAX_RESUME_BYTES) {
      setFileError("That PDF is over 5 MB. Choose a smaller one, or start without it.");
      return;
    }
    setResume(file);
  }

  return (
    <div className="interview iv-intro">
      <IvTop />
      <main className="iv-intro-act" inert={Boolean(busy)} aria-busy={Boolean(busy)}>
        <div className="ib-book">
          <span className="ib-edge" aria-hidden="true" />
          <section className="ib-page ib-left" aria-labelledby={titleId}>
            <div className="ib-head">
              {!progress.done && (
                <button type="button" className="button button-quiet ib-skip" onClick={skipNow}>
                  Skip
                </button>
              )}
            </div>
            <h1 id={titleId} className="ib-says" data-done={progress.done || undefined}>
              {LINES.map((line, index) => {
                const typed = progress.typed[index] ?? 0;
                const typing = !progress.done && typed > 0 && typed < line.length;
                if (progress.done)
                  return (
                    <span key={line} className="ib-line">
                      {line}
                    </span>
                  );
                return (
                  <span key={line} className="ib-line">
                    {/* The whole line holds its place and is what a screen reader reads; the typing is ink. */}
                    <span className="ib-full">{line}</span>
                    <span className="ib-typed" aria-hidden="true">
                      {line.slice(0, typed)}
                      {typing && <span className="iv-caret" />}
                    </span>
                  </span>
                );
              })}
            </h1>
            {progress.done && (
              <div className="ib-after" ref={start}>
                <MemberContextFields
                  affiliations={affiliations}
                  founder={founder}
                  onAffiliationsChange={setAffiliations}
                  onFounderChange={setFounder}
                />
                <fieldset className="ib-resume">
                  <legend>A résumé, if you like</legend>
                  {/* biome-ignore lint/a11y/noStaticElementInteractions: a drop target for the mouse; "Choose a PDF" is the keyboard path */}
                  <div
                    className="ib-drop"
                    data-dragging={dragging || undefined}
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
                        <span className="ib-file">{resume.name}</span>
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
                        <span className="ib-drop-text">Drop a PDF here</span>
                        <label htmlFor={inputId} className="button button-secondary ib-choose">
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
                </fieldset>
                <ErrorMessage message={error} />
                {error && resume && (
                  <button
                    type="button"
                    className="iv-textlink"
                    onClick={() => onStart(null, { affiliations, founder })}
                  >
                    Start without it
                  </button>
                )}
                <div className="ib-start">
                  <Button
                    onClick={() => onStart(resume, { affiliations, founder })}
                    aria-busy={Boolean(busy)}
                    disabled={affiliations.length === 0}
                  >
                    Start the interview
                  </Button>
                  {busy ? (
                    <span className="ib-wait" role="status">
                      {busy}
                    </span>
                  ) : (
                    <span className="ib-minutes">About 20 minutes</span>
                  )}
                </div>
              </div>
            )}
          </section>
          <section className="ib-page ib-right" aria-label="Contents">
            <div className="ib-head ib-head-right">
              <span className="ib-tab" aria-current="page">
                Contents
              </span>
            </div>
            <h2 className="ib-pname">Contents</h2>
            <ol className="ib-places" aria-hidden="true">
              {Array.from({ length: PLACES }, (_, index) => (
                <li
                  // biome-ignore lint/suspicious/noArrayIndexKey: the contents' fixed, empty places
                  key={index}
                  data-drawn={index < progress.drawn || undefined}
                  style={{ "--w": `${[78, 64, 86][index]}%` } as CSSProperties}
                >
                  <b>{index < progress.drawn ? index + 1 : ""}</b>
                  <span>
                    <span className="ib-bar" />
                    <span className="ib-bar ib-bar-s" />
                  </span>
                </li>
              ))}
            </ol>
          </section>
        </div>
      </main>
    </div>
  );
}
