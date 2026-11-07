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
}

export interface DraftBook {
  title: string;
  authorName: string;
  chapters: DraftChapter[];
}

export type InterviewState =
  | {
      id: string;
      stage: "asking";
      phase: Phase;
      question: string;
      /** True once the member has answered enough to stop early ("I've said enough"). */
      canFinish: boolean;
      /** True when there are answers from an earlier visit. */
      hasAnswers: boolean;
      /** "Last time you were telling me about…", for coming back. Null on a fresh interview. */
      lastTopic: string | null;
    }
  | { id: string; stage: "shaping"; phase: "shape"; playback: string }
  | { id: string; stage: "choosing"; titles: TitleOption[] }
  | { id: string; stage: "reviewing"; book: DraftBook }
  | { id: string; stage: "done"; book: DraftBook };

export interface InterviewClient {
  /** The member's interview in progress, or null if they haven't started one. */
  current(): Promise<InterviewState | null>;
  start(resume: File | null): Promise<InterviewState>;
  answer(id: string, text: string): Promise<InterviewState>;
  /** "I've said enough. Show me my book." */
  finish(id: string): Promise<InterviewState>;
  confirmShape(id: string): Promise<InterviewState>;
  correctShape(id: string, correction: string): Promise<InterviewState>;
  chooseTitle(id: string, titleId: string): Promise<InterviewState>;
  rewriteChapter(id: string, chapterId: string): Promise<InterviewState>;
  removeChapter(id: string, chapterId: string): Promise<InterviewState>;
  putOnShelf(id: string): Promise<InterviewState>;
}
