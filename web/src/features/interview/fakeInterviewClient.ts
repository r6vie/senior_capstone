import type { DraftBook, InterviewClient, InterviewState, Phase } from "./interviewClient";

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

interface Stored {
  id: string;
  answers: string[];
  stage: InterviewState["stage"];
  corrected: boolean;
  book: DraftBook | null;
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

function view(stored: Stored, authorName: string): InterviewState {
  const { id } = stored;
  switch (stored.stage) {
    case "asking": {
      const current = scripted(stored.answers.length);
      const previous = scripted(stored.answers.length - 1);
      return {
        id,
        stage: "asking",
        phase: current.phase,
        question: current.text,
        canFinish: stored.answers.length >= CAN_FINISH_AFTER,
        hasAnswers: stored.answers.length > 0,
        lastTopic: stored.answers.length > 0 ? previous.topic : null,
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
    default:
      return { id, stage: stored.stage, book: stored.book ?? emptyBook(authorName) };
  }
}

function emptyBook(authorName: string): DraftBook {
  return { title: "", authorName: authorName, blurb: null, chapters: [] };
}

const BLURB =
  "I've spent years being the person people call when the timeline slips. This book is how I find the one step that went wrong, and what I do the morning after.";

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
      return stored ? view(stored, authorName) : null;
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
        stored.answers.push(text);
        if (stored.answers.length >= QUESTIONS.length) stored.stage = "shaping";
      }),
    askAgain: (id) => mutate(id, () => {}),
    finish: (id) =>
      mutate(id, (stored) => {
        if (stored.answers.length < CAN_FINISH_AFTER) throw new Error("Answer a few more questions first.");
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
          chapters: CHAPTERS.map((ch) => ({ ...ch })),
        };
        stored.stage = "reviewing";
      }),
    rewriteChapter: (id, chapterId) =>
      mutate(id, (stored) => {
        const chapter = stored.book?.chapters.find((ch) => ch.id === chapterId);
        if (chapter) chapter.summary = `${chapter.summary.replace(/\.$/, "")}, told from where I stand now.`;
      }),
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
  };
}

/** Forget the fake interview, so the next visit starts fresh. */
export function resetFakeInterview() {
  localStorage.removeItem(STORAGE_KEY);
}
