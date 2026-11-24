import { type CSSProperties, useEffect, useId, useRef, useState } from "react";
import type { NotebookEntry } from "../interviewClient";
import { fold } from "./anchors";
import { Hand, writeTime } from "./Hand";
import { seeded } from "./pen";
import { strokeOf } from "./shapes";
import type { ShownEntry } from "./useNotebook";
import "./Librarian.css";

// The Librarian's notebook (LibDesktop, LibPhone, LibParts): one page for the whole interview, beside
// the answer on a wide screen and a sheet that lifts from a one-line peek on a phone. No bullets; each
// line sits a little off-level, in the red hand.

function lean(id: string) {
  const random = seeded(id);
  return {
    "--rot": `${((random() - 0.55) * 4).toFixed(2)}deg`,
    "--ml": `${Math.round(random() * 8)}px`,
    "--fs": `${23 + Math.round(random() * 4)}px`,
  } as CSSProperties;
}

function shownText(entry: NotebookEntry): string {
  return entry.kind === "clip" ? `“${entry.text}”` : entry.text;
}

/** The word an entry hangs on, underlined by hand: the first word of its own that the member said. */
function hangsOn(entry: NotebookEntry, text: string): number | undefined {
  if (entry.kind === "clip" || entry.kind === "note") return undefined;
  const said = new Set(
    entry.anchors
      .flatMap((anchor) => fold(anchor).split(/[^\p{L}\p{N}']+/u))
      .filter((word) => word.length >= 3),
  );
  const words = text.split(" ");
  const at = words.findIndex((word) => said.has(fold(word).replace(/[^\p{L}\p{N}']/gu, "")));
  return at < 0 ? undefined : at;
}

const SPOKEN: Record<NotebookEntry["status"], string> = {
  open: "",
  circled: " (circled: the question builds on it)",
  ticked: " (ticked off: this is the question)",
  called: " (a bet, called)",
  lost: " (a bet, lost)",
};

/** A revision that changes only a few words is done the way a person would: those words struck, and the
 * new ones written above them. A bigger one strikes the old line and writes the new one under it. */
function rewritten(
  old: string,
  text: string,
): { before: string; was: string; now: string; after: string } | null {
  const a = old.split(" ");
  const b = text.split(" ");
  let start = 0;
  while (start < a.length && start < b.length && a[start] === b[start]) start++;
  let end = 0;
  while (end < a.length - start && end < b.length - start && a[a.length - 1 - end] === b[b.length - 1 - end])
    end++;
  const was = a.slice(start, a.length - end);
  const now = b.slice(start, b.length - end);
  if (!was.length || !now.length || was.length > 3 || now.length > 4 || start + end === 0) return null;
  return {
    before: b.slice(0, start).join(" "),
    was: was.join(" "),
    now: now.join(" "),
    after: b.slice(b.length - end).join(" "),
  };
}

function Entry({ shown }: { shown: ShownEntry }) {
  const { entry, life, marking } = shown;
  const text = shownText(entry);
  const word = hangsOn(entry, text);
  const old = entry.struck[entry.struck.length - 1];
  const quote = (line: string) => (entry.kind === "clip" ? `“${line}”` : line);
  const swap = old && life !== "erasing" ? rewritten(quote(old), text) : null;
  const ink = life === "erasing" ? "resting" : life;
  const settled = entry.status === "called" || entry.status === "lost";
  return (
    <li
      className="lib-en"
      data-kind={entry.kind}
      data-status={entry.status}
      data-marking={marking || undefined}
      data-life={life}
      style={lean(entry.id)}
    >
      <span className="iv-visually-hidden">
        {text}
        {SPOKEN[entry.status]}
        {settled && entry.outcomeNote ? ` ${entry.outcomeNote}` : ""}
      </span>
      {(entry.status === "ticked" || entry.status === "called") && (
        <span className="lib-tick" aria-hidden="true" />
      )}
      <span className="lib-en-tx">
        {old && life !== "erasing" && !swap && (
          <span className="lib-old" aria-hidden="true">
            {quote(old)}
          </span>
        )}
        {swap ? (
          <span className="lib-line" aria-hidden="true">
            {swap.before && <Hand text={`${swap.before} `} life="resting" />}
            <span className="lib-rw">
              <s>{swap.was}</s>
              <span className="lib-rw-new">
                <Hand text={swap.now} life={ink} />
              </span>
            </span>
            {swap.after && <Hand text={` ${swap.after}`} life="resting" />}
          </span>
        ) : (
          <span className="lib-line">
            <Hand
              text={text}
              life={ink}
              underline={
                word === undefined
                  ? undefined
                  : {
                      word,
                      double: entry.kind === "connection",
                      shape: strokeOf(entry.kind === "connection" ? "double" : "under", entry.id),
                    }
              }
            />
          </span>
        )}
        {settled && entry.outcomeNote && (
          // Beside the bet, once a later answer settles it.
          <span className="lib-outcome" aria-hidden="true">
            <Hand text={entry.outcomeNote} life={marking ? "writing" : "resting"} delay={0.5} />
          </span>
        )}
      </span>
    </li>
  );
}

/** The welcome the Librarian writes on page one when an interview starts (StartOpen): its lines, and
 * whether it is being written now, line after line at pen pace, or is already on the page. */
export interface Welcome {
  lines: string[];
  writing: boolean;
}

// Each welcome line's lean, as drawn on the board (StartOpen), so the hello always looks the same.
const WELCOME_LEAN = [
  { rot: -0.55, ml: 9, fs: 26 },
  { rot: -1.65, ml: 9, fs: 24 },
  { rot: -1.1, ml: 2, fs: 23 },
  { rot: -1.1, ml: 7, fs: 23 },
];
// The welcome is written quicker than a note, so the question isn't kept waiting, with a breath between lines.
const WELCOME_PACE = 0.35;
const LINE_PAUSE_S = 0.25;

/** When each welcome line starts, in seconds, and when the last one is finished. */
export function welcomeTimes(lines: string[]): { starts: number[]; end: number } {
  const starts: number[] = [];
  let at = 0;
  for (const line of lines) {
    starts.push(at);
    at += writeTime(line) * WELCOME_PACE + LINE_PAUSE_S;
  }
  return { starts, end: at };
}

function WelcomeLines({ welcome }: { welcome: Welcome }) {
  const { starts } = welcomeTimes(welcome.lines);
  return (
    <>
      {welcome.lines.map((line, index) => {
        const lean = WELCOME_LEAN[index % WELCOME_LEAN.length] ?? WELCOME_LEAN[0];
        return (
          <li
            // biome-ignore lint/suspicious/noArrayIndexKey: the welcome's fixed lines, in order
            key={index}
            className="lib-en lib-welcome"
            style={
              {
                "--rot": `${lean?.rot}deg`,
                "--ml": `${lean?.ml}px`,
                "--fs": `${lean?.fs}px`,
              } as CSSProperties
            }
          >
            <span className="iv-visually-hidden">{line}</span>
            <span className="lib-en-tx">
              <span className="lib-line">
                <Hand
                  text={line}
                  life={welcome.writing ? "writing" : "resting"}
                  delay={starts[index] ?? 0}
                  pace={WELCOME_PACE}
                />
              </span>
            </span>
          </li>
        );
      })}
    </>
  );
}

function Pages({ entries, welcome }: { entries: ShownEntry[]; welcome?: Welcome }) {
  return (
    <ol className="lib-nbl">
      {welcome && <WelcomeLines welcome={welcome} />}
      {entries.map((shown) => (
        <Entry key={shown.entry.id} shown={shown} />
      ))}
    </ol>
  );
}

export function Notebook({ entries, welcome }: { entries: ShownEntry[]; welcome?: Welcome }) {
  const heading = useId();
  const [open, setOpen] = useState(false);
  const sheet = useRef<HTMLDivElement>(null);
  const opener = useRef<HTMLButtonElement>(null);
  const newest = [...entries].reverse().find((shown) => shown.life !== "erasing");

  // The sheet opens at whatever the question was built on, or else at the newest line.
  useEffect(() => {
    if (!open) return;
    const box = sheet.current;
    const target =
      box?.querySelector<HTMLElement>('[data-status="circled"], [data-status="ticked"]') ??
      box?.querySelector<HTMLElement>(".lib-en:last-child");
    target?.scrollIntoView?.({ block: "center" });
    box?.querySelector<HTMLElement>(".lib-close")?.focus();
  }, [open]);

  // The peek comes back once the sheet is closed; the keyboard goes back to its button.
  const returning = useRef(false);
  useEffect(() => {
    if (open || !returning.current) return;
    returning.current = false;
    opener.current?.focus();
  }, [open]);
  const close = () => {
    returning.current = true;
    setOpen(false);
  };

  return (
    <>
      <section className="lib-nbook surf surf-spine" aria-labelledby={heading}>
        <h2 id={heading} className="lib-nbh">
          The Librarian’s notebook
        </h2>
        <Pages entries={entries} welcome={welcome} />
      </section>

      {(newest || welcome) && !open && (
        <div className="lib-peek">
          <span className="lib-peekl" aria-hidden="true">
            Notes
          </span>
          <span className="lib-peek-line" aria-hidden="true">
            {newest ? (
              <Hand text={shownText(newest.entry)} life={newest.life} />
            ) : (
              // Before the Librarian has any notes, the peek holds the welcome's hello.
              <Hand
                text={welcome?.lines[0] ?? ""}
                life={welcome?.writing ? "writing" : "resting"}
                pace={WELCOME_PACE}
              />
            )}
          </span>
          <button
            type="button"
            ref={opener}
            className="lib-ibtn"
            aria-label="Open the Librarian’s notebook"
            onClick={() => setOpen(true)}
          >
            <Chevron up />
          </button>
        </div>
      )}
      {open && (
        <>
          <div className="lib-shade" aria-hidden="true" onClick={close} />
          <div
            className="lib-sheet"
            role="dialog"
            aria-modal="true"
            aria-label="The Librarian’s notebook"
            ref={sheet}
            onKeyDown={(event) => {
              if (event.key === "Escape") close();
            }}
          >
            <div className="lib-nbh">
              <span>The Librarian’s notebook</span>
              <button
                type="button"
                className="lib-ibtn lib-close"
                aria-label="Close the notebook"
                onClick={close}
              >
                <Chevron />
              </button>
            </div>
            <Pages entries={entries} welcome={welcome} />
          </div>
        </>
      )}
    </>
  );
}

function Chevron({ up }: { up?: boolean }) {
  return (
    <svg
      width="16"
      height="10"
      viewBox="0 0 16 10"
      fill="none"
      stroke="currentColor"
      strokeWidth="2.4"
      aria-hidden="true"
    >
      <path d={up ? "M2 8l6-6 6 6" : "M2 2l6 6 6-6"} />
    </svg>
  );
}
