// What the interview screens need from the backend. The screens talk only to this interface, so the
// local fake (fakeInterviewClient.ts) and the real API client are interchangeable.

export type Phase = "sweep" | "dig" | "shape";

export interface TitleOption {
  id: string;
  title: string;
  /** One line on why this title is the member. */
  why: string;
}

export interface DraftChapter {
  id: string;
  title: string;
  summary: string;
  /** The member's own words behind this chapter. Only they ever see them. */
  quotes: string[];
  /** In review, the last rewrite can be taken back. */
  hasPrevious?: boolean;
}

export interface DraftBook {
  title: string;
  authorName: string;
  /** The back-cover blurb, in the member's own voice. Null on books written before blurbs. */
  blurb: string | null;
  chapters: DraftChapter[];
  /** The last rewrite couldn't be told better from what the member said, so nothing changed. */
  rewriteUnchanged?: boolean;
}

/** One proposed change to a book on the shelf. Nothing here is live until the member confirms. */
export interface ProposedChange {
  id: string;
  kind: "new" | "improve" | "remove";
  /** One line, to the member, on what this adds. */
  note: string;
  title: string;
  summary: string;
  /** What's in the book now. Null for a new chapter. A removal has only this. */
  now: { title: string; summary: string } | null;
}

export type InterviewState =
  | {
      id: string;
      stage: "asking";
      /** "adding" is a short new round on a shelved book: no phases, and a different way out. */
      round?: "first" | "adding";
      phase: Phase;
      question: string;
      /** True once the member has answered enough to stop early ("I've said enough"). */
      canFinish: boolean;
      /** True when there are answers from an earlier visit. */
      hasAnswers: boolean;
      /** "Last time you were telling me about…", for coming back. Null on a fresh interview. */
      lastTopic: string | null;
      /** A draft found too little, so the Librarian is asking for more. */
      needsMore?: boolean;
    }
  | { id: string; stage: "shaping"; phase: "shape"; playback: string }
  | { id: string; stage: "choosing"; titles: TitleOption[] }
  | { id: string; stage: "reviewing"; book: DraftBook }
  | { id: string; stage: "done"; book: DraftBook }
  /** The changes are being written in the background. */
  | { id: string; stage: "writing" }
  /** The first book's titles or chapters are being written, and the page was refreshed or left. */
  | { id: string; stage: "drafting"; about: "titles" | "book" }
  /** Not enough yet for three chapters. Never a dead end: the Librarian keeps asking (decision 14). */
  | { id: string; stage: "notEnough" }
  | { id: string; stage: "writeFailed" }
  | {
      id: string;
      stage: "proposing";
      changes: ProposedChange[];
      /** The back cover as it stands. */
      blurb: string | null;
    }
  /** A round that earned no changes. The book is as it was. */
  | { id: string; stage: "nothing" }
  /** Approved changes just went live. */
  | { id: string; stage: "updated"; book: DraftBook };

/** Where a member's book stands, for My book. Reading this never asks the Librarian for anything. */
export type BookStage =
  | "none"
  | "interviewing"
  | "writingTitles"
  | "titles"
  | "writingBook"
  | "draft"
  | "shelf"
  | "adding"
  | "writing"
  | "writeFailed"
  | "changesWaiting";

export interface MyBook extends DraftBook {
  /** The last approved changes can still be taken back. */
  canUndo: boolean;
}

export interface Spark {
  id: string;
  chapterTitle: string;
}

export interface ReadingQuestion {
  id: string;
  question: string;
  /** The person the reading was with. To the author only, and never sent to a prompt. */
  readerName: string | null;
  createdAt: string;
}

/** A failed call. Retryable when the Librarian (Claude) failed and nothing the member said was lost. */
export class InterviewError extends Error {
  constructor(
    message: string,
    readonly retryable = false,
    /** 409: the interview isn't where this screen thought it was. */
    readonly conflict = false,
  ) {
    super(message);
  }
}

/** The call may never have reached the API, or its reply never came back: nobody knows what was saved. */
export class LostError extends Error {}

export interface InterviewClient {
  /** The member's interview in progress, or null if they haven't started one. */
  current(): Promise<InterviewState | null>;
  start(resume: File | null): Promise<InterviewState>;
  answer(id: string, text: string): Promise<InterviewState>;
  /** Move past this question. Skips are never shown or counted. */
  skip(id: string): Promise<InterviewState>;
  /** Write the waiting question again, after an answer was saved but the next question failed. */
  askAgain(id: string): Promise<InterviewState>;
  /** "I've said enough. Show me my book." Words still in the field are saved first. */
  finish(id: string, answer?: string): Promise<InterviewState>;
  confirmShape(id: string): Promise<InterviewState>;
  correctShape(id: string, correction: string): Promise<InterviewState>;
  chooseTitle(id: string, titleId: string): Promise<InterviewState>;
  /** The titles the member can still go back to, while reviewing. */
  otherTitles(id: string): Promise<TitleOption[]>;
  /** Pick another title. This writes the book again, so chapter rewrites may be replaced. */
  changeTitle(id: string, titleId: string): Promise<InterviewState>;
  rewriteBlurb(id: string): Promise<InterviewState>;
  rewriteChapter(id: string, chapterId: string): Promise<InterviewState>;
  /** Go back to the chapter's last version. */
  restoreChapter(id: string, chapterId: string): Promise<InterviewState>;
  removeChapter(id: string, chapterId: string): Promise<InterviewState>;
  putOnShelf(id: string): Promise<InterviewState>;

  // ---------- A book that grows (trove.md §3, §4) ----------
  stage(): Promise<BookStage>;
  /** The member's book as it stands, or null. */
  myBook(): Promise<MyBook | null>;
  /** Open a short new round of questions on a shelved book. */
  reopen(): Promise<InterviewState>;
  retryWriting(id: string): Promise<InterviewState>;
  /** The back cover for exactly these approved changes. Null means there's nothing to rewrite. */
  blurbFor(approved: string[]): Promise<string | null>;
  /** `blurb` is text the member was shown and approved. Null keeps the back cover as it is. */
  applyChanges(approved: string[], blurb: string | null): Promise<InterviewState>;
  undoChanges(): Promise<void>;
  /** The back cover for the book without this chapter. */
  blurbWithout(chapterId: string): Promise<string | null>;
  removeFromShelf(chapterId: string, blurb: string | null): Promise<void>;
  sparks(): Promise<Spark[]>;
  removeSpark(sparkId: string): Promise<void>;
  readingQuestions(): Promise<ReadingQuestion[]>;
  answerReading(questionId: string, answer: string): Promise<InterviewState>;
  dismissReading(questionId: string): Promise<void>;
}
