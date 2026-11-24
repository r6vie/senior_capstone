import { useCallback, useEffect, useRef, useState } from "react";
import type { LibrarianView, NotebookEntry, NotesReply } from "../interviewClient";
import { holds } from "./anchors";
import { type Life, rubTime, writeTime } from "./Hand";
import { reducedMotion } from "./pen";

// The Librarian's notebook across the whole interview: one page, kept from question to question, so an
// entry the next question builds on can be circled (or ticked) in front of the member.

export interface ShownEntry {
  entry: NotebookEntry;
  life: Life;
  /** The circle or tick is being drawn now. */
  marking: boolean;
}

export interface Notebook {
  entries: ShownEntry[];
  /** Ids on screen, for the notes call. */
  shown: () => string[];
  /** What a notes call said to do with the notebook. */
  apply: (delta: NotesReply["notebook"]) => void;
  /** The answer changed: this answer's entries whose words are gone are rubbed out. */
  hold: (text: string) => void;
  /** The answer went quiet: rub out everything built on it. */
  silence: () => void;
}

const MARK_MS = 700;

function spokenStatus(entry: NotebookEntry): string {
  switch (entry.status) {
    case "ticked":
      return `Librarian ticked off: ${entry.text}`;
    case "called":
      return `Librarian's bet, ${entry.text}: ${entry.outcomeNote ?? "called it."}`;
    case "lost":
      return `Librarian crossed out its bet, ${entry.text}: ${entry.outcomeNote ?? "wrong. good."}`;
    default:
      return `Librarian circled: ${entry.text}`;
  }
}

function isMine(entry: NotebookEntry, turn: number): boolean {
  return entry.sourceTurns.length > 0 && Math.max(...entry.sourceTurns) === turn;
}

function stillHolds(entry: NotebookEntry, text: string): boolean {
  // A clip is the member's exact words, so it goes as soon as they change.
  if (entry.kind === "clip") return holds(text, entry.text);
  return entry.anchors.length === 0 || entry.anchors.some((anchor) => holds(text, anchor));
}

export function useNotebook(view: LibrarianView | null | undefined, say: (line: string) => void): Notebook {
  const [entries, setEntries] = useState<ShownEntry[]>(() =>
    (view?.notebook ?? []).map((entry) => ({ entry, life: "resting", marking: false })),
  );
  const current = useRef(entries);
  current.current = entries;
  const turn = (view?.answered ?? 0) + 1;
  const timers = useRef(new Set<ReturnType<typeof setTimeout>>());

  useEffect(() => {
    const pending = timers.current;
    return () => {
      for (const timer of pending) clearTimeout(timer);
    };
  }, []);

  const later = useCallback((ms: number, then: () => void) => {
    const timer = setTimeout(() => {
      timers.current.delete(timer);
      then();
    }, ms);
    timers.current.add(timer);
  }, []);

  const update = useCallback((id: string, change: (shown: ShownEntry) => ShownEntry | null) => {
    setEntries((all) => all.flatMap((shown) => (shown.entry.id === id ? (change(shown) ?? []) : [shown])));
  }, []);

  const write = useCallback(
    (entry: NotebookEntry) => {
      say(`Librarian's notebook: ${entry.kind === "clip" ? `“${entry.text}”` : entry.text}`);
      later(reducedMotion() ? 300 : writeTime(entry.text) * 1000 + 120, () =>
        update(entry.id, (shown) => (shown.life === "writing" ? { ...shown, life: "resting" } : shown)),
      );
    },
    [later, say, update],
  );

  const erase = useCallback(
    (id: string) => {
      const shown = current.current.find((item) => item.entry.id === id);
      if (!shown || shown.life === "erasing") return;
      update(id, (item) => ({ ...item, life: "erasing" }));
      later((reducedMotion() ? 0.2 : rubTime(shown.entry.text)) * 1000 + 60, () => update(id, () => null));
    },
    [later, update],
  );

  // A new state from the API: it is the truth. Keep what's on screen as it is, circle or tick whatever
  // the new question was built on, and rub out anything the API no longer has.
  const lastView = useRef(view);
  // Every entry id the page has shown. The first view the page gets is its baseline, shown at rest (a
  // member coming back sees their notebook, not a rewrite of it); after that, only an id never seen is
  // written out, so an entry rubbed out here and kept by the API comes back quietly.
  const seen = useRef(new Set((view?.notebook ?? []).map((entry) => entry.id)));
  const seeded = useRef(Boolean(view));
  // Entries kept on the page after the API moved past them; they stay for the rest of the visit.
  const kept = useRef(new Set<string>());
  useEffect(() => {
    if (view === lastView.current) return;
    lastView.current = view;
    if (!view) return;
    const baseline = !seeded.current;
    seeded.current = true;
    const known = new Map(current.current.map((shown) => [shown.entry.id, shown]));
    const unseen = new Set(
      baseline ? [] : view.notebook.filter((entry) => !seen.current.has(entry.id)).map((entry) => entry.id),
    );
    for (const entry of view.notebook) seen.current.add(entry.id);
    const fresh = new Set(view.notebook.map((entry) => entry.id));
    // What the member's last answer brought stays on the page when the next question arrives, even once the
    // API has moved past it: an "ask" the question took up is ticked, never wiped as the question lands.
    const answered = view.answered;
    const stays = (shown: ShownEntry) =>
      shown.life !== "erasing" &&
      shown.entry.sourceTurns.length > 0 &&
      Math.max(...shown.entry.sourceTurns) === answered;
    const staying = new Set(
      current.current
        .filter((shown) => !fresh.has(shown.entry.id) && (stays(shown) || kept.current.has(shown.entry.id)))
        .map((shown) => shown.entry.id),
    );
    for (const id of staying) kept.current.add(id);
    for (const shown of current.current)
      if (!fresh.has(shown.entry.id) && !staying.has(shown.entry.id)) erase(shown.entry.id);
    setEntries((all) => {
      const left = all
        .filter((shown) => !fresh.has(shown.entry.id))
        .map(
          (shown): ShownEntry =>
            staying.has(shown.entry.id) && shown.entry.kind === "saving"
              ? { ...shown, entry: { ...shown.entry, status: "ticked" } }
              : shown,
        );
      const next = view.notebook.map((entry): ShownEntry => {
        const before = known.get(entry.id);
        const marking = Boolean(before && before.entry.status === "open" && entry.status !== "open");
        // An entry the page hasn't seen (the answer's final look, when the wait's call missed it) is
        // written in front of the member, not dropped onto the page.
        if (unseen.has(entry.id)) return { entry, life: "writing", marking };
        return { entry, life: !before || before.life === "erasing" ? "resting" : before.life, marking };
      });
      return [
        ...next,
        ...left.filter((shown) => staying.has(shown.entry.id)),
        ...left.filter((shown) => shown.life === "erasing"),
      ];
    });
    for (const entry of view.notebook) {
      const before = known.get(entry.id);
      if (unseen.has(entry.id)) write(entry);
      if (before && before.entry.status === "open" && entry.status !== "open") {
        say(spokenStatus(entry));
        later(MARK_MS + 1500, () => update(entry.id, (shown) => ({ ...shown, marking: false })));
      }
    }
  }, [view, erase, later, say, update, write]);

  // A bet called or lost, a saving ticked, an entry circled: drawn now, in front of the member.
  const settle = useCallback(
    (entry: NotebookEntry, before: NotebookEntry) => {
      update(entry.id, (shown) => ({ ...shown, entry: { ...entry, struck: before.struck }, marking: true }));
      say(spokenStatus(entry));
      later(MARK_MS + 1500, () => update(entry.id, (shown) => ({ ...shown, marking: false })));
    },
    [later, say, update],
  );

  const apply = useCallback(
    (delta: NotesReply["notebook"]) => {
      const have = new Set(current.current.map((shown) => shown.entry.id));
      const added = delta.add.filter((entry) => !have.has(entry.id));
      for (const entry of added) seen.current.add(entry.id);
      if (added.length) {
        setEntries((all) => [
          ...all,
          ...added.map((entry): ShownEntry => ({ entry, life: "writing", marking: false })),
        ]);
        for (const entry of added) write(entry);
      }
      for (const revised of delta.revise) {
        const before = current.current.find((shown) => shown.entry.id === revised.id);
        if (!before) continue;
        if (before.entry.status !== revised.status) settle(revised, before.entry);
        if (before.entry.text === revised.text) continue;
        // The old wording is struck and kept above the new one, which is written fresh.
        const struck = revised.struck.length ? revised.struck : [...before.entry.struck, before.entry.text];
        update(revised.id, () => ({ entry: { ...revised, struck }, life: "writing", marking: false }));
        write(revised);
      }
      for (const id of delta.erase) erase(id);
    },
    [erase, settle, update, write],
  );

  const hold = useCallback(
    (text: string) => {
      for (const shown of current.current) {
        if (shown.life !== "erasing" && isMine(shown.entry, turn) && !stillHolds(shown.entry, text))
          erase(shown.entry.id);
      }
    },
    [erase, turn],
  );

  const silence = useCallback(() => {
    for (const shown of current.current) if (isMine(shown.entry, turn)) erase(shown.entry.id);
  }, [erase, turn]);

  const shown = useCallback(
    () => current.current.filter((item) => item.life !== "erasing").map((item) => item.entry.id),
    [],
  );

  return { entries, shown, apply, hold, silence };
}
