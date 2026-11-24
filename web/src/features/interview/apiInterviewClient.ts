import { api } from "../../api/client";
import { errorMessage } from "../../api/errors";
import type { components } from "../../api/schema";
import {
  type BookStage,
  type DraftBook,
  type InterviewClient,
  InterviewError,
  type InterviewState,
  type LibMark,
  type LibrarianView,
  LostError,
  type NotebookEntry,
  type ProposedChange,
} from "./interviewClient";

// The real interview API (api/trove/interview), mapped onto the shape the screens use.
// The API keeps one interview per member, so there is no id to pass; the screens' id is a constant.

type MyBookResponse = components["schemas"]["MyBookResponse"];
type ChangeResponse = components["schemas"]["Change"];
type InterviewResponse = components["schemas"]["InterviewResponse"];
type MarkResponse = components["schemas"]["Mark"];
type EntryResponse = components["schemas"]["Entry"];
type LibrarianResponse = components["schemas"]["LibrarianState"];

function toMark(mark: MarkResponse): LibMark {
  return {
    id: mark.id,
    move: mark.move,
    anchor: mark.anchor,
    occurrence: mark.occurrence,
    note: mark.note,
    count: mark.count ?? null,
    struckNote: mark.struck_note ?? null,
  };
}

function toEntry(entry: EntryResponse): NotebookEntry {
  return {
    id: entry.id,
    kind: entry.kind,
    text: entry.text,
    anchors: entry.anchors,
    sourceTurns: entry.source_turns,
    status: entry.status,
    struck: entry.struck,
    outcomeNote: entry.outcome_note ?? null,
  };
}

// The notebook in the response already carries the new question's circle or tick (`builds_on`).
function toLibrarian(librarian: LibrarianResponse | null | undefined): LibrarianView | null {
  if (!librarian) return null;
  return {
    answered: librarian.turns.length,
    marks: librarian.current_marks.map(toMark),
    silent: librarian.current_silent,
    notebook: librarian.notebook.map(toEntry),
  };
}

const ID = "me";

const SOMETHING_WRONG = "Something's wrong on our side. Nothing you said is lost.";

interface Result<T> {
  data?: T;
  error?: unknown;
  response?: Response;
}

function unwrap<T>({ data, error, response }: Result<T>): T {
  if (data !== undefined) return data;
  const detail = error && typeof error === "object" && "detail" in error ? error.detail : undefined;
  // A member never sees the API's own words for a 503, which can name a database. A developer does: on their
  // machine it's usually a missing ANTHROPIC_API_KEY, and the API says exactly that.
  if (response?.status === 503) {
    const why = import.meta.env.DEV && typeof detail === "string" ? detail : SOMETHING_WRONG;
    throw new InterviewError(why);
  }
  // A list here is a schema error, which names fields. A sentence is the API talking to the member.
  if (response?.status === 422 && typeof detail !== "string") {
    throw new InterviewError("That didn't go through. Check it and try again.");
  }
  if (response?.status === 502) {
    // The API's own 502 says what happened, in `detail`: the Librarian failed, with the member's part
    // saved. A proxy's 502 has no such word, and may never have reached the API.
    if (!(error && typeof error === "object" && "detail" in error)) throw new LostError();
    throw new InterviewError(errorMessage(error), true);
  }
  const alreadySaved = Boolean(
    error && typeof error === "object" && "already_saved" in error && error.already_saved,
  );
  throw new InterviewError(errorMessage(error), false, response?.status === 409, alreadySaved);
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
    hasPreviousBlurb: book.has_previous_blurb,
    chapters: book.chapters.map(({ id, title, summary, quotes, has_previous }) => ({
      id,
      title,
      summary,
      quotes,
      hasPrevious: has_previous,
    })),
  };
}

function toMyBook(book: MyBookResponse) {
  return { ...toBook(book), status: book.status, canUndo: book.can_undo, changedAt: book.revised_at };
}

function fromBook(book: MyBookResponse): InterviewState {
  return { id: ID, stage: book.status === "draft" ? "reviewing" : "done", book: toBook(book) };
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

// Both answer null before the member has started, or has a book: an answer, not an error.
async function readInterview(): Promise<InterviewResponse | null> {
  return unwrap(await api.GET("/interview"));
}

async function readBook(): Promise<MyBookResponse | null> {
  return unwrap(await api.GET("/books/me"));
}

// For a step that only makes sense once the interview exists.
async function openInterview(): Promise<InterviewResponse> {
  const now = await readInterview();
  if (!now) throw new InterviewError("You haven't started your interview yet.");
  return now;
}

async function myBook(): Promise<InterviewState> {
  const book = await readBook();
  if (!book) throw new InterviewError("You don't have a book yet.");
  return fromBook(book);
}

// Turns the API's flat response into one screen. Two cases need another call first: the Librarian
// has enough (go straight to the titles), or the question couldn't be written (ask for it again).
async function toState(response: InterviewResponse, retried = false): Promise<InterviewState> {
  waitingQuestionId = response.question?.question_id ?? "";
  switch (response.stage) {
    case "drafting":
      return {
        id: ID,
        stage: "drafting",
        about: "titles",
        failed: response.step_status === "failed",
        closingLine: response.closing_line ?? undefined,
      };
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
    case "reviewing": {
      // The Librarian's sign-off comes only on the interview, under the title at the reveal.
      const state = await myBook();
      return state.stage === "reviewing" ? { ...state, signOff: response.sign_off ?? null } : state;
    }
    case "done":
      return response.nothing_new
        ? {
            id: ID,
            stage: "nothing",
            droppedForNames: response.dropped_for_names,
            readingQuestionId: response.reading_question_id ?? undefined,
            droppedWords: response.dropped_words ?? undefined,
            readingAnswer: response.reading_answer ?? undefined,
          }
        : myBook();
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
      return {
        id: ID,
        stage: "asking",
        round: response.stage === "adding" ? "adding" : "first",
        // Only a round of adding has other phases, and those aren't shown.
        phase: question.phase === "dig" || question.phase === "shape" ? question.phase : "sweep",
        question: question.text,
        questionId: question.question_id,
        canFinish: response.can_finish,
        hasAnswers: response.has_answers,
        lastTopic: response.topic,
        needsMore: response.needs_more,
        nearlyDone: response.nearly_done,
        librarian: toLibrarian(response.librarian),
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
    const now = await openInterview();
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
    const now = await openInterview();
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
    const now = await readInterview();
    return now ? toState(now) : null;
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
  // Never an error for want of AI: past the limits the API keeps what holds and adds nothing. A 409 (the
  // question moved on) or a dropped call is the same to the screen: nothing new to draw.
  async notes(look, signal) {
    const { data } = await api.POST("/interview/notes", {
      body: {
        question_id: look.questionId,
        text: look.text,
        previous_text: look.previousText,
        pasted: look.pasted,
        shown: look.shown,
      },
      signal,
    });
    if (!data) throw new InterviewError("The Librarian had nothing to add.");
    return {
      silent: data.silent,
      marks: {
        keep: data.marks.keep,
        add: data.marks.add.map(toMark),
        revise: data.marks.revise.map(toMark),
        erase: data.marks.erase,
      },
      notebook: {
        keep: data.notebook.keep,
        add: data.notebook.add.map(toEntry),
        revise: data.notebook.revise.map(toEntry),
        erase: data.notebook.erase,
      },
    };
  },
  async askAgain() {
    return toState(unwrap<InterviewResponse>(await api.POST("/interview/question")));
  },
  async finish(_id, answer) {
    const init = answer ? { body: { answer, question_id: waitingQuestionId } } : {};
    return toState(unwrap<InterviewResponse>(await api.POST("/interview/finish", init)));
  },
  async chooseTitle(_id, titleId) {
    const body = { title: Number(titleId) };
    return toState(unwrap<InterviewResponse>(await api.POST("/interview/title", { body })));
  },
  async otherTitles() {
    const response = await openInterview();
    return (response.titles ?? []).map((option, index) => ({ id: String(index), ...option }));
  },
  async changeTitle(_id, titleId) {
    return fromBook(unwrap(await api.POST("/interview/book/title", { body: { title: Number(titleId) } })));
  },
  async rewriteBlurb() {
    return fromBook(unwrap(await api.POST("/interview/book/blurb")));
  },
  async restoreBlurb() {
    return fromBook(unwrap(await api.POST("/interview/book/blurb/restore")));
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
    const now = await readInterview();
    // A book can be on the shelf with no interview behind it, such as a sample.
    if (!now) return (await readBook()) ? "shelf" : "none";
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
    const book = await readBook();
    return book ? toMyBook(book) : null;
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
      ? { id: ID, stage: "updated", book: toBook(book), canUndo: book.can_undo }
      : { id: ID, stage: "done", book: toBook(book) };
  },
  async undoChanges() {
    const result = await api.POST("/interview/book/undo");
    if (result.response.status === 409) {
      // A double press, or another screen: if the book is already back as it was, that's success.
      const book = await apiInterviewClient.myBook();
      if (book && !book.canUndo) return;
    }
    ended(result);
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
  async editBook(edit) {
    return toMyBook(unwrap(await api.PATCH("/books/me", { body: edit })));
  },
  async editChapter(chapterId, edit) {
    const params = { path: { chapter_id: chapterId } };
    return toMyBook(unwrap(await api.PATCH("/books/me/chapters/{chapter_id}", { params, body: edit })));
  },
  async takeOffShelf() {
    return toMyBook(unwrap(await api.POST("/books/me/take-down")));
  },
  async putBackOnShelf() {
    return toMyBook(unwrap(await api.POST("/books/me/put-back")));
  },
  async openRemoval() {
    const { data } = await api.GET("/interview");
    if (!data) return null;
    const [only, ...rest] = data.changes ?? [];
    if (!only || rest.length || only.kind !== "remove" || !only.chapter_id) return null;
    return { chapterId: only.chapter_id, title: only.current?.title ?? only.title };
  },
  async cancelRemoval() {
    removals.clear();
    ended(await api.POST("/interview/removal/cancel"));
  },
  async lastRound() {
    const { data } = await api.GET("/interview");
    const now = data;
    return {
      empty: Boolean(now?.nothing_new),
      droppedForNames: now?.dropped_for_names,
      droppedWords: now?.dropped_words ?? undefined,
      readingQuestionId: now?.reading_question_id ?? undefined,
      readingAnswer: now?.reading_answer ?? undefined,
    };
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
