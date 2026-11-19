import type {
  BookStage,
  DraftBook,
  InterviewClient,
  InterviewState,
  LibMark,
  MyBook,
  NotebookEntry,
  NotesLook,
  NotesReply,
  Phase,
  ProposedChange,
  ReadingQuestion,
  Spark,
} from "./interviewClient";

// A stand-in for the interview API in tests: it plays a fixed script, can wait like a Claude call
// would, and keeps its state in localStorage so leaving and coming back works.

const STORAGE_KEY = "trove_fake_interview";
const CAN_FINISH_AFTER = 10;

const QUESTIONS: { phase: Phase; text: string; topic: string }[] = [
  {
    phase: "sweep",
    text: "What is something you spent years getting good at that the people around you never really saw?",
    topic: "the thing you got good at that nobody saw",
  },
  {
    phase: "sweep",
    text: "What do people come to you for, even when it isn't your job?",
    topic: "what people come to you for",
  },
  {
    phase: "sweep",
    text: "Think of a turning point in school or work. Where were you when you decided?",
    topic: "a turning point, and where you were when you decided",
  },
  {
    phase: "sweep",
    text: "What's something about your field that outsiders always get wrong?",
    topic: "what outsiders get wrong about your field",
  },
  {
    phase: "sweep",
    text: "What did you figure out the hard way?",
    topic: "what you figured out the hard way",
  },
  {
    phase: "dig",
    text: "You mentioned an offer you turned down. What was happening the week you said no?",
    topic: "the week you turned down the first offer",
  },
  {
    phase: "dig",
    text: "Who did you tell first, and what did they say back?",
    topic: "who you told first",
  },
  {
    phase: "dig",
    text: "What did you decide that week that you still stand by?",
    topic: "the decision you still stand by",
  },
  {
    phase: "dig",
    text: "You said the second offer felt different from the first. What was different about it?",
    topic: "the second offer you turned down, and what your advisor said",
  },
  {
    phase: "dig",
    text: "What do you know now that you didn't know then?",
    topic: "what you know now",
  },
  {
    phase: "dig",
    text: "If a first-year came to you facing the same choice, what would you ask them first?",
    topic: "what you'd ask a first-year facing the same choice",
  },
  {
    phase: "dig",
    text: "What would you argue about for an hour?",
    topic: "what you'd argue about for an hour",
  },
];

const PLAYBACK =
  "Here is what I heard. You walked away from graduate school twice, and both times it was because the work in front of you taught you faster. Is this you?";

const TITLES = [
  {
    id: "title-1",
    title: "Why I Turned Down Grad School Twice",
    why: "Because both times you chose the work over the title.",
  },
  {
    id: "title-2",
    title: "The Offer I Wasn't Ready For",
    why: "Because you asked what you would stop learning.",
  },
  { id: "title-3", title: "A Slower Way Up", why: "Because you took the longer road on purpose, twice." },
];

const CHAPTERS = [
  {
    id: "ch-1",
    title: "The offer I wasn't ready for",
    summary: "The first time, a lab offered a place and I said no without knowing why.",
  },
  {
    id: "ch-2",
    title: "What I told my advisor",
    summary: "The conversation where I said it out loud, and what he asked back.",
  },
  {
    id: "ch-3",
    title: "The second time",
    summary: "A different offer, a clearer reason, and what changed in how I decided.",
  },
  {
    id: "ch-4",
    title: "What I do now",
    summary: "The work that taught me faster, and what I'd tell someone standing where I stood.",
  },
];

const ADDING_QUESTIONS = [
  "The offer you turned down the second time: what did you tell the person who made it?",
  "Who noticed before you did that the work was teaching you faster?",
];

const CHANGES: ProposedChange[] = [
  {
    id: "change-1",
    kind: "improve",
    note: "Adds what your advisor asked you back.",
    title: "What I told my advisor",
    summary:
      "The conversation where I said it out loud, and what he asked back. He asked what I would do with the extra year, and I had no answer.",
    now: {
      title: "What I told my advisor",
      summary: "The conversation where I said it out loud, and what he asked back.",
    },
  },
  {
    id: "change-2",
    kind: "new",
    note: "You described who noticed first.",
    title: "The person who noticed first",
    summary: "A labmate told me I'd stopped talking about the degree, a full year before I admitted it.",
    now: null,
  },
];

interface Stored {
  id: string;
  answers: string[];
  stage: InterviewState["stage"] | "adding";
  corrected: boolean;
  book: DraftBook | null;
  addingAnswers?: number;
  canUndo?: boolean;
  offShelf?: boolean;
  previous?: DraftBook;
  sparks?: Spark[];
  reading?: ReadingQuestion[];
  /** The Librarian's notebook, and its marks on the answer being written. */
  notebook?: NotebookEntry[];
  marks?: LibMark[];
}

function scripted(index: number) {
  const question = QUESTIONS[Math.max(0, Math.min(index, QUESTIONS.length - 1))];
  if (!question) throw new Error("The fake interview has no questions.");
  return question;
}

function load(): Stored | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as Stored) : null;
  } catch {
    return null;
  }
}

function save(stored: Stored) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(stored));
}

function wait(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

// A skip takes a place in the script as an empty answer, so it moves on without counting.
function answered(stored: Stored): number {
  return stored.answers.filter(Boolean).length;
}

function view(stored: Stored, authorName: string): InterviewState {
  const { id } = stored;
  switch (stored.stage) {
    case "adding":
      return {
        id,
        stage: "asking",
        round: "adding",
        phase: "dig",
        question:
          ADDING_QUESTIONS[Math.min(stored.addingAnswers ?? 0, ADDING_QUESTIONS.length - 1)] ??
          "What else belongs in your book?",
        canFinish: (stored.addingAnswers ?? 0) > 0,
        hasAnswers: (stored.addingAnswers ?? 0) > 0,
        lastTopic: null,
      };
    case "writing":
      return { id, stage: "writing" };
    case "writeFailed":
      return { id, stage: "writeFailed" };
    case "proposing":
      return { id, stage: "proposing", changes: CHANGES, blurb: stored.book?.blurb ?? null };
    case "nothing":
      return { id, stage: "nothing" };
    case "updated":
      return { id, stage: "updated", book: stored.book ?? emptyBook(authorName), canUndo: true };
    case "asking": {
      const current = scripted(stored.answers.length);
      const previous = scripted(stored.answers.length - 1);
      return {
        id,
        stage: "asking",
        phase: current.phase,
        question: current.text,
        canFinish: answered(stored) >= CAN_FINISH_AFTER,
        nearlyDone: answered(stored) >= CAN_FINISH_AFTER,
        hasAnswers: answered(stored) > 0,
        lastTopic: stored.answers.length > 0 ? previous.topic : null,
        librarian: {
          answered: stored.answers.length,
          marks: stored.marks ?? [],
          silent: false,
          notebook: stored.notebook ?? [],
        },
      };
    }
    case "shaping":
      return {
        id,
        stage: "shaping",
        phase: "shape",
        playback: stored.corrected
          ? "Here is what I heard, with your correction. You left graduate school twice to keep learning from the work itself, and you'd do it again. Is this you?"
          : PLAYBACK,
      };
    case "choosing":
      return { id, stage: "choosing", titles: TITLES };
    case "drafting":
      return { id, stage: "drafting", about: "book" };
    case "notEnough":
      return { id, stage: "notEnough" };
    case "reviewing":
      return {
        id,
        stage: "reviewing",
        book: stored.book ?? emptyBook(authorName),
        signOff: "took some editing.",
      };
    default:
      return { id, stage: stored.stage, book: stored.book ?? emptyBook(authorName) };
  }
}

function emptyBook(authorName: string): DraftBook {
  return { title: "", authorName: authorName, blurb: null, chapters: [] };
}

const BLURB =
  "I've spent years being the person people call when the timeline slips. This book is how I find the one step that went wrong, and what I do the morning after.";

function asMyBook(stored: Stored): MyBook {
  const book = stored.book as DraftBook;
  const status = stored.stage === "reviewing" ? "draft" : stored.offShelf ? "off_shelf" : "on_shelf";
  return { ...book, status, canUndo: Boolean(stored.canUndo) };
}

function stageOf(stored: Stored | null): BookStage {
  switch (stored?.stage) {
    case undefined:
      return "none";
    case "asking":
    case "shaping":
      return "interviewing";
    case "choosing":
      return "titles";
    case "reviewing":
      return "draft";
    case "adding":
      // A round with no answers counts as closed: there's nothing to continue.
      return stored.addingAnswers ? "adding" : "shelf";
    case "writing":
      return "writing";
    case "writeFailed":
      return "writeFailed";
    case "proposing":
      return "changesWaiting";
    default:
      return "shelf";
  }
}

// A stand-in Librarian with no AI: a few fixed reactions, so the screen can be tried and tested free.
const SCRIPT: { anchor: string; move: LibMark["move"]; note: string }[] = [
  { anchor: "leveraged", move: "strike", note: "used." },
  { anchor: "everyone", move: "underline", note: "says who?" },
  { anchor: "a long time", move: "underline", note: "how long?" },
  { anchor: "stale cache", move: "circle", note: "this is the chapter." },
];

function fakeId(...parts: string[]): string {
  let hash = 0;
  for (const char of parts.join("|")) hash = (Math.imul(hash, 31) + char.charCodeAt(0)) | 0;
  return `lib-${(hash >>> 0).toString(36)}`;
}

export function fakeNotes(look: NotesLook, notebook: NotebookEntry[], turn: number): NotesReply {
  const lower = look.text.toLowerCase();
  const marks = SCRIPT.filter((line) => new RegExp(`\\b${line.anchor}\\b`).test(lower)).map(
    (line): LibMark => ({
      id: fakeId(line.move, line.anchor),
      move: line.move,
      anchor: look.text.slice(lower.indexOf(line.anchor), lower.indexOf(line.anchor) + line.anchor.length),
      occurrence: 1,
      note: line.note,
    }),
  );
  const words = look.text.match(/[A-Za-z]{5,}/g) ?? [];
  const mine = notebook.filter((entry) => entry.sourceTurns.includes(turn));
  const add: NotebookEntry[] = [];
  const first = words[0];
  if (first && words.length >= 6 && !mine.some((entry) => entry.kind === "chapter")) {
    add.push({
      id: fakeId("chapter", String(turn), first),
      kind: "chapter",
      text: `ch. ? the ${first.toLowerCase()} story`,
      anchors: [first],
      sourceTurns: [turn],
      status: "open",
      struck: [],
    });
  }
  const shown = new Set(look.shown);
  return {
    silent: false,
    marks: {
      keep: marks.filter((mark) => shown.has(mark.id)).map((mark) => mark.id),
      add: marks.filter((mark) => !shown.has(mark.id)),
    },
    notebook: {
      keep: notebook.map((entry) => entry.id).filter((id) => shown.has(id)),
      add,
      revise: [],
      erase: [],
    },
  };
}

export function createFakeInterviewClient(authorName: string, delay = 1200): InterviewClient {
  function mutate(id: string, change: (stored: Stored) => void): Promise<InterviewState> {
    return wait(delay).then(() => {
      const stored = load();
      if (!stored || stored.id !== id) throw new Error("This interview has ended. Please start again.");
      change(stored);
      save(stored);
      return view(stored, authorName);
    });
  }

  return {
    async current() {
      await wait(delay / 3);
      const stored = load();
      if (!stored) return null;
      // The background write finishes by the next look, as it does for a member who waits.
      if (stored.stage === "writing") {
        stored.stage = "proposing";
        save(stored);
      }
      return view(stored, authorName);
    },
    async start() {
      await wait(delay);
      const stored: Stored = {
        id: crypto.randomUUID(),
        answers: [],
        stage: "asking",
        corrected: false,
        book: null,
      };
      save(stored);
      return view(stored, authorName);
    },
    answer: (id, text) =>
      mutate(id, (stored) => {
        stored.marks = [];
        if (stored.stage === "adding") {
          stored.addingAnswers = (stored.addingAnswers ?? 0) + 1;
          return;
        }
        stored.answers.push(text);
        if (stored.answers.length >= QUESTIONS.length) stored.stage = "shaping";
      }),
    async notes(look) {
      await wait(delay);
      const stored = load();
      if (!stored) throw new Error("This interview has ended.");
      const notebook = stored.notebook ?? [];
      const reply = fakeNotes(look, notebook, stored.answers.length + 1);
      const kept = (stored.marks ?? []).filter((mark) => reply.marks.keep.includes(mark.id));
      stored.marks = [...kept, ...reply.marks.add];
      stored.notebook = [...notebook, ...reply.notebook.add];
      save(stored);
      return reply;
    },
    skip: (id) =>
      mutate(id, (stored) => {
        stored.marks = [];
        if (stored.stage === "adding") return;
        stored.answers.push("");
        if (stored.answers.length >= QUESTIONS.length) stored.stage = "shaping";
      }),
    askAgain: (id) => mutate(id, () => {}),
    finish: (id, answer) =>
      mutate(id, (stored) => {
        if (stored.stage === "adding") {
          stored.stage = "writing";
          return;
        }
        if (answer) stored.answers.push(answer);
        if (answered(stored) < CAN_FINISH_AFTER) throw new Error("Answer a few more questions first.");
        stored.stage = "shaping";
      }),
    confirmShape: (id) =>
      mutate(id, (stored) => {
        stored.stage = "choosing";
      }),
    correctShape: (id) =>
      mutate(id, (stored) => {
        stored.corrected = true;
      }),
    chooseTitle: (id, titleId) =>
      mutate(id, (stored) => {
        const title = TITLES.find((option) => option.id === titleId);
        if (!title) throw new Error("That title isn't one of the three.");
        stored.book = {
          title: title.title,
          authorName: authorName,
          blurb: BLURB,
          chapters: CHAPTERS.map((ch) => ({ ...ch, quotes: [`I said this about ${ch.title}.`] })),
        };
        stored.stage = "reviewing";
      }),
    otherTitles: async () => TITLES,
    changeTitle: (id, titleId) =>
      mutate(id, (stored) => {
        const title = TITLES.find((option) => option.id === titleId);
        if (title && stored.book) stored.book.title = title.title;
      }),
    rewriteBlurb: (id) =>
      mutate(id, (stored) => {
        if (stored.book) stored.book.blurb = `${BLURB} I'd start with the first offer.`;
      }),
    rewriteChapter: (id, chapterId) =>
      mutate(id, (stored) => {
        const chapter = stored.book?.chapters.find((ch) => ch.id === chapterId);
        if (chapter) chapter.summary = `${chapter.summary.replace(/\.$/, "")}, told from where I stand now.`;
      }),
    restoreChapter: (id) => mutate(id, () => {}),
    removeChapter: (id, chapterId) =>
      mutate(id, (stored) => {
        if (!stored.book) return;
        if (stored.book.chapters.length <= 3) throw new Error("A book keeps at least three chapters.");
        stored.book.chapters = stored.book.chapters.filter((ch) => ch.id !== chapterId);
      }),
    putOnShelf: (id) =>
      mutate(id, (stored) => {
        stored.stage = "done";
      }),

    stage: async () => stageOf(load()),
    myBook: async () => {
      const stored = load();
      return stored?.book ? asMyBook(stored) : null;
    },
    editBook: async (edit) => {
      const stored = load();
      if (!stored?.book) throw new Error("There's no book to edit.");
      Object.assign(stored.book, edit);
      save(stored);
      return asMyBook(stored);
    },
    editChapter: async (chapterId, edit) => {
      const stored = load();
      const chapter = stored?.book?.chapters.find((candidate) => candidate.id === chapterId);
      if (!stored || !chapter) throw new Error("That chapter isn't in your book.");
      Object.assign(chapter, edit);
      save(stored);
      return asMyBook(stored);
    },
    takeOffShelf: async () => {
      const stored = load();
      if (!stored?.book) throw new Error("There's no book to take down.");
      stored.offShelf = true;
      save(stored);
      return asMyBook(stored);
    },
    putBackOnShelf: async () => {
      const stored = load();
      if (!stored?.book) throw new Error("There's no book to put back.");
      stored.offShelf = false;
      save(stored);
      return asMyBook(stored);
    },
    reopen: () =>
      wait(delay).then(() => {
        const stored = load();
        if (!stored) throw new Error("There's no book to add to.");
        if (stored.stage !== "adding") stored.addingAnswers = 0;
        stored.stage = "adding";
        save(stored);
        return view(stored, authorName);
      }),
    retryWriting: (id) =>
      mutate(id, (stored) => {
        stored.stage = "proposing";
      }),
    retryDrafting: async () => {
      const stored = load();
      if (!stored) throw new Error("There's no interview to continue.");
      return view(stored, authorName);
    },
    saveChoices: async () => undefined,
    blurbFor: async (approved) => (approved.length ? `${BLURB} I also say who noticed first.` : null),
    applyChanges: async (approved, blurb) => {
      await wait(delay);
      const stored = load();
      if (!stored?.book) throw new Error("There's no book to change.");
      stored.stage = "done";
      if (approved.length) {
        stored.previous = structuredClone(stored.book);
        stored.canUndo = true;
        if (blurb) stored.book.blurb = blurb;
        for (const change of CHANGES) {
          if (!approved.includes(change.id)) continue;
          const existing = stored.book.chapters.find((chapter) => chapter.title === change.now?.title);
          if (existing) existing.summary = change.summary;
          else
            stored.book.chapters.push({
              id: change.id,
              title: change.title,
              summary: change.summary,
              quotes: [],
            });
        }
      }
      save(stored);
      return approved.length
        ? { id: stored.id, stage: "updated", book: stored.book, canUndo: true }
        : { id: stored.id, stage: "done", book: stored.book };
    },
    undoChanges: async () => {
      const stored = load();
      if (stored?.previous) stored.book = stored.previous;
      if (stored) {
        stored.previous = undefined;
        stored.canUndo = false;
        save(stored);
      }
    },
    blurbWithout: async () => `${BLURB} Shorter now.`,
    removeFromShelf: async (chapterId, blurb) => {
      const stored = load();
      if (!stored?.book) return;
      stored.previous = structuredClone(stored.book);
      stored.canUndo = true;
      stored.book.chapters = stored.book.chapters.filter((chapter) => chapter.id !== chapterId);
      if (blurb) stored.book.blurb = blurb;
      save(stored);
    },
    restoreBlurb: (id) => mutate(id, () => {}),
    openRemoval: async () => null,
    cancelRemoval: async () => undefined,
    lastRound: async () => ({ empty: load()?.stage === "nothing" }),
    sparks: async () => load()?.sparks ?? [],
    removeSpark: async (sparkId) => {
      const stored = load();
      if (!stored) return;
      stored.sparks = (stored.sparks ?? []).filter((spark) => spark.id !== sparkId);
      save(stored);
    },
    readingQuestions: async () => load()?.reading ?? [],
    answerReading: (questionId) =>
      wait(delay).then(() => {
        const stored = load();
        if (!stored) throw new Error("There's no book to add to.");
        stored.reading = (stored.reading ?? []).filter((question) => question.id !== questionId);
        stored.stage = "writing";
        save(stored);
        return view(stored, authorName);
      }),
    dismissReading: async (questionId) => {
      const stored = load();
      if (!stored) return;
      stored.reading = (stored.reading ?? []).filter((question) => question.id !== questionId);
      save(stored);
    },
  };
}

/** Forget the fake interview, so the next visit starts fresh. */
export function resetFakeInterview() {
  localStorage.removeItem(STORAGE_KEY);
}
