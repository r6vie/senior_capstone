import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { InterviewClient, LibMark, LibrarianView, MarkMove } from "../interviewClient";
import { type Placed, place } from "./anchors";
import { type Life, rubTime, writeTime } from "./Hand";
import { reducedMotion } from "./pen";
import {
  CONTACT_LATER,
  hasContactDetails,
  MASHING,
  mashing,
  OWN_WORDS,
  PASTE_HIGHLIGHT,
  resumeSentences,
} from "./scripted";
import { isSilent } from "./silence";
import type { Notebook } from "./useNotebook";

// The Librarian reading one answer as it's typed: when to look (LIBRARIAN_SPEC.md §14), what it marks,
// the instant moves with no AI (§8), going quiet (§4), and the line when the member goes quiet (§9).

export type Move = MarkMove | "highlight";

export interface DrawnMark {
  id: string;
  move: Move;
  anchor: string;
  occurrence: number;
  note: string | null;
  /** An instant move, made here rather than by the API. */
  scripted?: boolean;
}

export interface ShownMark {
  mark: DrawnMark;
  life: Life;
}

export interface MarginLine {
  id: string;
  text: string;
  life: Life;
}

// When to look: a pause, a finished sentence, or about seven new words. Never per keystroke.
const PAUSE_MS = 1100;
const NEW_WORDS = 7;
// Gates on every look.
const MIN_GAP_MS = 2500;
const MIN_CHANGE = 4;
const MAX_LOOKS = 8;
const TIMEOUT_MS = 7000;
// The line in the margin when nothing has been typed for a while.
const IDLE_MS = 24_000;
const IDLE_MAX = 3;
export const IDLE_LINES = [
  "start with what you’d say out loud.",
  "the blank page is not the answer.",
  "one sentence will do. pick one.",
];

/** How long a stroke takes before its note starts, in seconds. */
export const STROKE_S = 0.3;
export const NOTE_AFTER_S = 0.35;

function changed(before: string, after: string): number {
  let start = 0;
  while (start < before.length && start < after.length && before[start] === after[start]) start++;
  let end = 0;
  while (
    end < before.length - start &&
    end < after.length - start &&
    before[before.length - 1 - end] === after[after.length - 1 - end]
  )
    end++;
  return Math.max(before.length - start - end, after.length - start - end);
}

function words(text: string): number {
  return text.split(/\s+/).filter(Boolean).length;
}

function idleKey(interviewId: string) {
  return `trove_librarian_idle:${interviewId}`;
}

function idleUsed(interviewId: string): number {
  try {
    return Number(localStorage.getItem(idleKey(interviewId)) ?? 0) || 0;
  } catch {
    return IDLE_MAX;
  }
}

function useIdle(interviewId: string) {
  return {
    used: () => idleUsed(interviewId),
    spend: () => {
      try {
        localStorage.setItem(idleKey(interviewId), String(idleUsed(interviewId) + 1));
      } catch {
        // Without storage, no idle lines: better none than the same one again.
      }
    },
  };
}

/** The instant moves for this text: résumé-speak and long pastes highlighted, keyboard mashing noted. */
function scriptedMarks(text: string, pastes: string[]): DrawnMark[] {
  const marks: DrawnMark[] = [];
  const lit = [...resumeSentences(text), ...pastes.filter((paste) => text.includes(paste))];
  lit.forEach((anchor, index) => {
    if (marks.some((mark) => mark.anchor.includes(anchor) || anchor.includes(mark.anchor))) return;
    marks.push({
      id: `s:hl:${anchor}`,
      move: "highlight",
      anchor,
      occurrence: 1,
      // The question goes once, on the first: two would be nagging.
      note: index === 0 ? OWN_WORDS : null,
      scripted: true,
    });
  });
  const mash = mashing(text);
  if (mash)
    marks.push({
      id: `s:mash:${mash}`,
      move: "note",
      anchor: mash,
      occurrence: 1,
      note: MASHING,
      scripted: true,
    });
  return marks;
}

function drawTime(mark: DrawnMark): number {
  if (reducedMotion()) return 0.3;
  return mark.note ? NOTE_AFTER_S + writeTime(mark.note) : STROKE_S;
}

function eraseTime(mark: DrawnMark): number {
  if (reducedMotion()) return 0.2;
  return rubTime(mark.anchor) + (mark.note ? 0.12 + rubTime(mark.note) : 0);
}

interface Options {
  client: InterviewClient;
  interviewId: string;
  questionId: string;
  view: LibrarianView | null | undefined;
  notebook: Notebook;
  text: string;
  say: (line: string) => void;
}

export function useLibrarian({ client, interviewId, questionId, view, notebook, text, say }: Options) {
  const [marks, setMarks] = useState<ShownMark[]>(() =>
    view?.silent ? [] : (view?.marks ?? []).map((mark) => ({ mark, life: "resting" as Life })),
  );
  const [margin, setMargin] = useState<MarginLine | null>(null);
  const [serverSilent, setServerSilent] = useState(Boolean(view?.silent));
  const silent = serverSilent || isSilent(text);
  const [pastes, setPastes] = useState<string[]>([]);
  const current = useRef(marks);
  current.current = marks;
  const latestText = useRef(text);
  latestText.current = text;
  const live = useRef(true);
  const timers = useRef(new Set<ReturnType<typeof setTimeout>>());
  const idle = useIdle(interviewId);
  const firstQuestion = (view?.answered ?? 0) === 0;

  useEffect(() => {
    live.current = true;
    const pending = timers.current;
    return () => {
      live.current = false;
      for (const timer of pending) clearTimeout(timer);
    };
  }, []);

  const later = useCallback((ms: number, then: () => void) => {
    const timer = setTimeout(() => {
      timers.current.delete(timer);
      if (live.current) then();
    }, ms);
    timers.current.add(timer);
    return timer;
  }, []);

  const settle = useCallback(
    (id: string, life: "resting" | null, after: number) => {
      later(after * 1000 + 80, () =>
        setMarks((all) =>
          all.flatMap((shown) => {
            if (shown.mark.id !== id) return [shown];
            if (life === null) return shown.life === "erasing" ? [] : [shown];
            return [shown.life === "writing" ? { ...shown, life } : shown];
          }),
        ),
      );
    },
    [later],
  );

  const draw = useCallback(
    (added: DrawnMark[]) => {
      const have = new Set(current.current.filter((s) => s.life !== "erasing").map((s) => s.mark.id));
      const fresh = added.filter((mark) => !have.has(mark.id));
      if (!fresh.length) return;
      setMarks((all) => [
        ...all.filter((shown) => !fresh.some((mark) => mark.id === shown.mark.id)),
        ...fresh.map((mark) => ({ mark, life: "writing" as Life })),
      ]);
      for (const mark of fresh) {
        if (mark.note)
          say(
            mark.move === "strike"
              ? `Librarian crossed out ${mark.anchor}, wrote ${mark.note}`
              : `Librarian: ${mark.note}`,
          );
        settle(mark.id, "resting", drawTime(mark));
      }
    },
    [say, settle],
  );

  const rub = useCallback(
    (ids: string[]) => {
      const going = current.current.filter(
        (shown) => ids.includes(shown.mark.id) && shown.life !== "erasing",
      );
      if (!going.length) return;
      setMarks((all) => all.map((shown) => (going.includes(shown) ? { ...shown, life: "erasing" } : shown)));
      for (const shown of going) settle(shown.mark.id, null, eraseTime(shown.mark));
    },
    [settle],
  );

  // Every edit: marks whose words are gone are rubbed out, and the instant moves are worked out again.
  const placed = useMemo(
    () =>
      place(
        text,
        marks.map((shown) => shown.mark),
      ),
    [text, marks],
  );
  useEffect(() => {
    if (silent) {
      rub(current.current.map((shown) => shown.mark.id));
      notebook.silence();
      return;
    }
    const here = new Set(placed.map((p) => p.item.id));
    rub(current.current.filter((shown) => !here.has(shown.mark.id)).map((shown) => shown.mark.id));
    const scripted = scriptedMarks(text, pastes);
    const wanted = new Set(scripted.map((mark) => mark.id));
    rub(current.current.filter((s) => s.mark.scripted && !wanted.has(s.mark.id)).map((s) => s.mark.id));
    draw(scripted);
    notebook.hold(text);
  }, [text, pastes, silent, placed, rub, draw, notebook.hold, notebook.silence]);

  // ---------- Looking: when to call, and the gates on every call ----------
  const look = useRef({ text: view?.marks.length ? text : "", at: 0, calls: 0, pasted: false });
  const inflight = useRef<AbortController | null>(null);
  const pending = useRef<ReturnType<typeof setTimeout> | null>(null);

  const call = useCallback(async () => {
    const now = latestText.current;
    const state = look.current;
    if (silent || isSilent(now) || state.calls >= MAX_LOOKS) return;
    if (!now.trim() || now === state.text || changed(state.text, now) < MIN_CHANGE) return;
    const wait = state.at + MIN_GAP_MS - Date.now();
    if (wait > 0) {
      // Too early: deferred, not dropped.
      if (pending.current) clearTimeout(pending.current);
      pending.current = later(wait, () => {
        pending.current = null;
        call();
      });
      return;
    }
    inflight.current?.abort();
    const controller = new AbortController();
    inflight.current = controller;
    const previous = state.text;
    look.current = { text: now, at: Date.now(), calls: state.calls + 1, pasted: false };
    const timeout = later(TIMEOUT_MS, () => controller.abort());
    try {
      const reply = await client.notes(
        {
          questionId,
          text: now,
          previousText: previous,
          pasted: state.pasted,
          shown: [
            ...current.current.filter((s) => !s.mark.scripted && s.life !== "erasing").map((s) => s.mark.id),
            ...notebook.shown(),
          ],
        },
        controller.signal,
      );
      // A late reply, or one for a question the member has left, is never drawn.
      if (controller.signal.aborted || !live.current || isSilent(latestText.current)) return;
      if (reply.silent) {
        setServerSilent(true);
        return;
      }
      const keep = new Set([...reply.marks.keep, ...reply.marks.add.map((mark) => mark.id)]);
      rub(current.current.filter((s) => !s.mark.scripted && !keep.has(s.mark.id)).map((s) => s.mark.id));
      // Placed only while the anchor still matches what's in the field now.
      const fits = place(latestText.current, reply.marks.add).map((p: Placed<LibMark>) => p.item);
      draw(fits);
      notebook.apply(reply.notebook);
    } catch {
      // The Librarian failing to be funny is never an error: the answer just stays plain.
    } finally {
      clearTimeout(timeout);
      timers.current.delete(timeout);
      if (inflight.current === controller) inflight.current = null;
    }
  }, [client, questionId, silent, later, rub, draw, notebook]);

  const lastTyped = useRef(text);
  useEffect(() => {
    const before = lastTyped.current;
    lastTyped.current = text;
    if (text === before || silent) return;
    if (pending.current) clearTimeout(pending.current);
    const grew = text.length > before.length;
    const finished = grew && /[.!?]\s*$/.test(text) && !/[.!?]\s*$/.test(before);
    if (finished || words(text) - words(look.current.text) >= NEW_WORDS) {
      call();
      return;
    }
    pending.current = later(PAUSE_MS, () => {
      pending.current = null;
      call();
    });
  }, [text, silent, call, later]);

  useEffect(() => () => inflight.current?.abort(), []);
  // Going quiet cancels any look still in flight: a late reply is never drawn.
  useEffect(() => {
    if (silent) inflight.current?.abort();
  }, [silent]);

  // ---------- The margin: idle lines, and the contact-details line ----------
  const writeMargin = useCallback(
    (line: string, id: string) => {
      say(`Librarian: ${line}`);
      setMargin({ id, text: line, life: "writing" });
      later((reducedMotion() ? 0.3 : writeTime(line)) * 1000 + 80, () =>
        setMargin((now) => (now?.id === id && now.life === "writing" ? { ...now, life: "resting" } : now)),
      );
    },
    [later, say],
  );
  const rubMargin = useCallback(() => {
    setMargin((now) => {
      if (!now || now.life === "erasing") return now;
      later((reducedMotion() ? 0.2 : rubTime(now.text)) * 1000 + 60, () =>
        setMargin((then) => (then?.id === now.id ? null : then)),
      );
      return { ...now, life: "erasing" };
    });
  }, [later]);

  const empty = !text.trim();
  useEffect(() => {
    // Typing answers the idle line, so it goes.
    if (!empty && margin?.id.startsWith("idle")) rubMargin();
    if (!empty || silent || firstQuestion) return;
    const timer = later(IDLE_MS, () => {
      const used = idle.used();
      const line = IDLE_LINES[used];
      if (used >= IDLE_MAX || !line || latestText.current.trim()) return;
      idle.spend();
      writeMargin(line, `idle:${used}`);
    });
    return () => {
      clearTimeout(timer);
      timers.current.delete(timer);
    };
  }, [empty, silent, firstQuestion, later, idle, writeMargin, rubMargin, margin?.id]);

  // Contact details wait for an accepted checkout. The first Send holds and says so; the next one sends.
  const warned = useRef<string | null>(null);
  const holdForContact = useCallback(
    (answer: string) => {
      if (!hasContactDetails(answer) || warned.current === answer) return false;
      warned.current = answer;
      writeMargin(CONTACT_LATER, `contact:${answer.length}`);
      return true;
    },
    [writeMargin],
  );

  const pasted = useCallback((words: string) => {
    look.current.pasted = true;
    if (words.trim().length > PASTE_HIGHLIGHT) setPastes((all) => [...all, words.trim()]);
  }, []);

  // On silence the marks are rubbed out like any other, so they stay in the list until that's done.
  return { marks, placed, margin, silent, pasted, holdForContact };
}
