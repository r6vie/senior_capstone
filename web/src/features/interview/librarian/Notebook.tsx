import { type CSSProperties, useEffect, useId, useRef, useState } from "react";
import type { NotebookEntry } from "../interviewClient";
import { fold } from "./anchors";
import { Hand } from "./Hand";
import { seeded } from "./pen";
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
};

function Entry({ shown }: { shown: ShownEntry }) {
  const { entry, life, marking } = shown;
  const text = shownText(entry);
  const word = hangsOn(entry, text);
  const old = entry.struck[entry.struck.length - 1];
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
      </span>
      {entry.status === "ticked" && <span className="lib-tick" aria-hidden="true" />}
      <span className="lib-en-tx">
        {old && life !== "erasing" && (
          <span className="lib-old" aria-hidden="true">
            {entry.kind === "clip" ? `“${old}”` : old}
          </span>
        )}
        <Hand
          text={text}
          life={life === "erasing" ? "resting" : life}
          underline={word === undefined ? undefined : { word, double: entry.kind === "connection" }}
        />
      </span>
    </li>
  );
}

function Pages({ entries }: { entries: ShownEntry[] }) {
  return (
    <ol className="lib-nbl">
      {entries.map((shown) => (
        <Entry key={shown.entry.id} shown={shown} />
      ))}
    </ol>
  );
}

export function Notebook({ entries }: { entries: ShownEntry[] }) {
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
      <section className="lib-nbook" aria-labelledby={heading}>
        <h2 id={heading} className="lib-nbh">
          The Librarian’s notebook
        </h2>
        <Pages entries={entries} />
      </section>

      {newest && !open && (
        <div className="lib-peek">
          <span className="lib-peekl" aria-hidden="true">
            Notes
          </span>
          <span className="lib-peek-line" aria-hidden="true">
            <Hand text={shownText(newest.entry)} life={newest.life} />
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
            <Pages entries={entries} />
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
