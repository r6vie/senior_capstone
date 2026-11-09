import { api } from "../../api/client";
import { errorMessage } from "../../api/errors";
import type { components } from "../../api/schema";
import {
  type BookStage,
  type DraftBook,
  type InterviewClient,
  InterviewError,
  type InterviewState,
  LostError,
  type ProposedChange,
} from "./interviewClient";

// The real interview API (api/trove/interview), mapped onto the shape the screens use.
// The API keeps one interview per member, so there is no id to pass; the screens' id is a constant.

type MyBookResponse = components["schemas"]["MyBookResponse"];
type ChangeResponse = components["schemas"]["Change"];
type InterviewResponse = components["schemas"]["InterviewResponse"];

const ID = "me";

interface Result<T> {
  data?: T;
  error?: unknown;
  response?: Response;
}

function unwrap<T>({ data, error, response }: Result<T>): T {
  if (data !== undefined) return data;
  // Neither of these reaches a member in the API's own words: one names a database, one names a field.
  if (response?.status === 503)
    throw new InterviewError("Something's wrong on our side. Nothing you said is lost.");
  if (response?.status === 422) throw new InterviewError("That didn't go through. Check it and try again.");
  if (response?.status === 502) {
    // The API's own 502 says what happened, in `detail`: the Librarian failed, with the member's part
    // saved. A proxy's 502 has no such word, and may never have reached the API.
    if (!(error && typeof error === "object" && "detail" in error)) throw new LostError();
    throw new InterviewError(errorMessage(error), true);
  }
  throw new InterviewError(errorMessage(error), false, response?.status === 409);
}

function ended({ error, response }: Result<unknown>) {
  if (response?.ok) return;
  throw new InterviewError(errorMessage(error), response?.status === 502, response?.status === 409);
}

// Sent back with an answer or a skip, so a resend can't land on a question the member never saw.
let waitingQuestionId = "";

function toBook(book: MyBookResponse): DraftBook {
  return {
    title: book.title,
    authorName: book.author_name,
    blurb: book.blurb,
    rewriteUnchanged: book.rewrite_unchanged,
    chapters: book.chapters.map(({ id, title, summary, quotes, has_previous }) => ({
      id,
      title,
      summary,
      quotes,
      hasPrevious: has_previous,
    })),
  };
}

function fromBook(book: MyBookResponse): InterviewState {
  return { id: ID, stage: book.status === "on_shelf" ? "done" : "reviewing", book: toBook(book) };
}

function toChange(change: ChangeResponse): ProposedChange {
  return {
    id: change.id,
    kind: change.kind,
    note: change.note,
    title: change.title,
    summary: change.summary,
    now: change.current ? { title: change.current.title, summary: change.current.summary } : null,
  };
}

async function myBook(): Promise<InterviewState> {
  return fromBook(unwrap(await api.GET("/books/me")));
}

// Turns the API's flat response into one screen. Two cases need another call first: the Librarian
// has enough (go straight to the titles), or the question couldn't be written (ask for it again).
async function toState(response: InterviewResponse, retried = false): Promise<InterviewState> {
  waitingQuestionId = response.question?.question_id ?? "";
  switch (response.stage) {
    case "drafting":
      return { id: ID, stage: "drafting", about: "titles", failed: response.step_status === "failed" };
    case "finishing":
      return {
        id: ID,
        stage: "drafting",
        about: "book",
        failed: response.step_status === "failed",
        retryTitle: String(
          Math.max(
            0,
            (response.titles ?? []).findIndex((option) => option.title === response.chosen_title),
          ),
        ),
      };
    case "choosing":
      return {
        id: ID,
        stage: "choosing",
        titles: (response.titles ?? []).map((option, index) => ({ id: String(index), ...option })),
      };
    case "reviewing":
      return myBook();
    case "done":
      return response.nothing_new ? { id: ID, stage: "nothing" } : myBook();
    case "revising":
      if (!response.changes) {
        return { id: ID, stage: response.revision_status === "failed" ? "writeFailed" : "writing" };
      }
      return {
        id: ID,
        stage: "proposing",
        changes: response.changes.map(toChange),
        blurb: response.blurb,
        approved: response.approved_changes,
      };
    case "adding":
    case "interviewing": {
      // Before the question below: at the limit, whether to keep answering is the member's choice.
      if (response.at_limit) return { id: ID, stage: "notEnough" };
      const { question } = response;
      if (!question) {
        if (response.ready_for_reveal) {
          return toState(unwrap<InterviewResponse>(await api.POST("/interview/finish", {})));
        }
        if (retried) {
          throw new InterviewError("The Librarian couldn't answer just now. Please try again.", true);
        }
        return toState(unwrap<InterviewResponse>(await api.POST("/interview/question")), true);
      }
      if (question.phase === "shape") {
        const playback = question.playback ? `${question.playback} ${question.text}` : question.text;
        return { id: ID, stage: "shaping", phase: "shape", playback };
      }
      return {
        id: ID,
        stage: "asking",
        round: response.stage === "adding" ? "adding" : "first",
        // Only a round of adding has other phases, and those aren't shown.
        phase: question.phase === "dig" ? "dig" : "sweep",
        question: question.text,
        canFinish: response.can_finish,
        hasAnswers: response.has_answers,
        lastTopic: response.topic,
        needsMore: response.needs_more,
        nearlyDone: response.nearly_done,
      };
    }
  }
}

// A removal is proposed once, then confirmed like any change. The proposal may already be open from an
// earlier visit, and asking again would be refused, so look first.
const removals = new Map<string, Promise<string>>();

function removalOf(chapterId: string): Promise<string> {
  const known = removals.get(chapterId);
  if (known) return known;
  const asking = (async () => {
    const now: InterviewResponse = unwrap(await api.GET("/interview"));
    const open = now.changes?.find((change) => change.kind === "remove" && change.chapter_id === chapterId);
    if (open) return open.id;
    const proposed = unwrap(await api.POST("/interview/removal", { body: { chapter_id: chapterId } }));
    const change = proposed.changes?.find((candidate) => candidate.kind === "remove");
    if (!change) throw new InterviewError("That chapter can't be removed just now.");
    return change.id;
  })();
  asking.catch(() => removals.delete(chapterId));
  removals.set(chapterId, asking);
  return asking;
}

const BLURB_LOOK_MS = 1500;
const BLURB_GIVE_UP_MS = 110_000;
const COULD_NOT_WRITE_BLURB = "The back cover couldn't be written.";

// The back cover for a selection is written in the background. Saving the same choices keeps one that's
// already written, so a member who left during the wait gets it on their return without another write.
async function writeSelectionBlurb(approved: string[]): Promise<string | null> {
  ended(await api.PUT("/interview/revision/choices", { body: { approved } }));
  const started = Date.now();
  let asked = false;
  while (Date.now() - started < BLURB_GIVE_UP_MS) {
    const now: InterviewResponse = unwrap(await api.GET("/interview"));
    const status = now.selection_blurb_status;
    if (status === "ready") return now.selection_blurb;
    if (status === "failed" && asked) throw new InterviewError(COULD_NOT_WRITE_BLURB);
    if (status !== "writing") {
      unwrap(await api.POST("/interview/revision/blurb"));
      asked = true;
    }
    await new Promise((resolve) => setTimeout(resolve, BLURB_LOOK_MS));
  }
  throw new InterviewError(COULD_NOT_WRITE_BLURB);
}

function readBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result).replace(/^data:[^,]*,/, ""));
    reader.onerror = () =>
      reject(new Error("That file couldn't be read. Choose it again, or start without it."));
    reader.readAsDataURL(file);
  });
}

export const apiInterviewClient: InterviewClient = {
  async current() {
    const { data, error, response } = await api.GET("/interview");
    if (response.status === 404) return null;
    return toState(unwrap<InterviewResponse>({ data, error, response }));
  },
  async start(resume) {
    const body = resume ? { resume_pdf: await readBase64(resume) } : {};
    return toState(unwrap<InterviewResponse>(await api.POST("/interview", { body })));
  },
  async answer(_id, text) {
    const body = { answer: text, question_id: waitingQuestionId };
    return toState(unwrap<InterviewResponse>(await api.POST("/interview/answers", { body })));
  },
  async skip() {
    const body = { question_id: waitingQuestionId };
    return toState(unwrap<InterviewResponse>(await api.POST("/interview/skip", { body })));
  },
  async askAgain() {
    return toState(unwrap<InterviewResponse>(await api.POST("/interview/question")));
  },
  async finish(_id, answer) {
    const init = answer ? { body: { answer, question_id: waitingQuestionId } } : {};
    return toState(unwrap<InterviewResponse>(await api.POST("/interview/finish", init)));
  },
  async confirmShape() {
    return toState(unwrap<InterviewResponse>(await api.POST("/interview/shape", { body: {} })));
  },
  async correctShape(_id, correction) {
    return toState(unwrap<InterviewResponse>(await api.POST("/interview/shape", { body: { correction } })));
  },
  async chooseTitle(_id, titleId) {
    const body = { title: Number(titleId) };
    return toState(unwrap<InterviewResponse>(await api.POST("/interview/title", { body })));
  },
  async otherTitles() {
    const response: InterviewResponse = unwrap(await api.GET("/interview"));
    return (response.titles ?? []).map((option, index) => ({ id: String(index), ...option }));
  },
  async changeTitle(_id, titleId) {
    return fromBook(unwrap(await api.POST("/interview/book/title", { body: { title: Number(titleId) } })));
  },
  async rewriteBlurb() {
    return fromBook(unwrap(await api.POST("/interview/book/blurb")));
  },
  async rewriteChapter(_id, chapterId) {
    const params = { path: { chapter_id: chapterId } };
    return fromBook(unwrap(await api.POST("/interview/book/chapters/{chapter_id}/rewrite", { params })));
  },
  async restoreChapter(_id, chapterId) {
    const params = { path: { chapter_id: chapterId } };
    return fromBook(unwrap(await api.POST("/interview/book/chapters/{chapter_id}/restore", { params })));
  },
  async removeChapter(_id, chapterId) {
    const params = { path: { chapter_id: chapterId } };
    return fromBook(unwrap(await api.DELETE("/interview/book/chapters/{chapter_id}", { params })));
  },
  async putOnShelf() {
    return fromBook(unwrap(await api.POST("/interview/book/shelve")));
  },

  async stage() {
    const { data, error, response } = await api.GET("/interview");
    if (response.status === 404) {
      // A book can be on the shelf with no interview behind it, such as a sample.
      const book = await api.GET("/books/me");
      return book.data ? "shelf" : "none";
    }
    const now: InterviewResponse = unwrap({ data, error, response });
    const stages: Record<InterviewResponse["stage"], BookStage> = {
      interviewing: "interviewing",
      // A failed step is the interview page's to offer again, so My book points there.
      drafting: now.step_status === "failed" ? "interviewing" : "writingTitles",
      choosing: "titles",
      finishing: now.step_status === "failed" ? "interviewing" : "writingBook",
      reviewing: "draft",
      done: "shelf",
      // can_finish means a real answer this round. With none, there's nothing to continue.
      adding: now.can_finish ? "adding" : "shelf",
      revising: now.changes ? "changesWaiting" : now.revision_status === "failed" ? "writeFailed" : "writing",
    };
    return stages[now.stage];
  },
  async myBook() {
    const { data, error, response } = await api.GET("/books/me");
    if (response.status === 404) return null;
    const book = unwrap<MyBookResponse>({ data, error, response });
    return { ...toBook(book), canUndo: book.can_undo };
  },
  async reopen() {
    return toState(unwrap<InterviewResponse>(await api.POST("/interview/reopen")));
  },
  async retryWriting() {
    return toState(unwrap<InterviewResponse>(await api.POST("/interview/finish", {})));
  },
  async retryDrafting(about, titleId) {
    if (about === "titles")
      return toState(unwrap<InterviewResponse>(await api.POST("/interview/finish", {})));
    const body = { title: Number(titleId ?? 0) };
    return toState(unwrap<InterviewResponse>(await api.POST("/interview/title", { body })));
  },
  async saveChoices(approved) {
    ended(await api.PUT("/interview/revision/choices", { body: { approved } }));
  },
  async blurbFor(approved) {
    return writeSelectionBlurb(approved);
  },
  async applyChanges(approved, blurb) {
    // The API applies the back cover it last showed for this selection, so the text never travels back.
    const body = { approved, blurb: blurb ? ("use" as const) : ("keep" as const) };
    const book = unwrap(await api.POST("/interview/revision", { body }));
    return approved.length
      ? { id: ID, stage: "updated", book: toBook(book) }
      : { id: ID, stage: "done", book: toBook(book) };
  },
  async undoChanges() {
    ended(await api.POST("/interview/book/undo"));
  },
  async blurbWithout(chapterId) {
    return writeSelectionBlurb([await removalOf(chapterId)]);
  },
  async removeFromShelf(chapterId, blurb) {
    const change = await removalOf(chapterId);
    removals.delete(chapterId);
    const body = { approved: [change], blurb: blurb ? ("use" as const) : ("keep" as const) };
    ended(await api.POST("/interview/revision", { body }));
  },
  async sparks() {
    const sparks = unwrap(await api.GET("/interview/sparks"));
    return sparks.map(({ id, chapter_title }) => ({ id, chapterTitle: chapter_title }));
  },
  async removeSpark(sparkId) {
    ended(await api.DELETE("/interview/sparks/{spark_id}", { params: { path: { spark_id: sparkId } } }));
  },
  async readingQuestions() {
    const questions = unwrap(await api.GET("/interview/reading-questions"));
    return questions.map(({ id, question, reader_name, created_at }) => ({
      id,
      question,
      readerName: reader_name,
      createdAt: created_at,
    }));
  },
  async answerReading(questionId, answer) {
    const params = { path: { question_id: questionId } };
    return toState(
      unwrap<InterviewResponse>(
        await api.POST("/interview/reading-questions/{question_id}/answer", { params, body: { answer } }),
      ),
    );
  },
  async dismissReading(questionId) {
    const params = { path: { question_id: questionId } };
    ended(await api.POST("/interview/reading-questions/{question_id}/dismiss", { params }));
  },
};
