import { api } from "../../api/client";
import { errorMessage } from "../../api/errors";
import type { components } from "../../api/schema";
import { type DraftBook, type InterviewClient, InterviewError, type InterviewState } from "./interviewClient";

// The real interview API (api/trove/interview), mapped onto the shape the screens use.
// The API keeps one interview per member, so there is no id to pass; the screens' id is a constant.

type InterviewResponse = components["schemas"]["InterviewResponse"];
type MyBookResponse = components["schemas"]["MyBookResponse"];

const ID = "me";

interface Result<T> {
  data?: T;
  error?: unknown;
  response?: Response;
}

function unwrap<T>({ data, error, response }: Result<T>): T {
  // Neither of these reaches a member in the API's own words: one names a database, one names a field.
  if (data === undefined && response?.status === 503)
    throw new InterviewError("Something's wrong on our side. Nothing you said is lost.");
  if (data === undefined && response?.status === 422)
    throw new InterviewError("That didn't go through. Check it and try again.");
  // 502 is the API's "the Librarian couldn't answer just now": safe to try again.
  if (data === undefined) throw new InterviewError(errorMessage(error), response?.status === 502);
  return data;
}

// Routes Trove API is adding (R1-19). Their paths can't be typed until schema.ts is regenerated.
const postUntyped = api.POST as unknown as (
  path: string,
  init?: { body: unknown },
) => Promise<Result<MyBookResponse>>;

function toBook(book: MyBookResponse): DraftBook {
  return {
    title: book.title,
    authorName: book.author_name,
    blurb: book.blurb,
    chapters: book.chapters.map(({ id, title, summary, quotes }) => ({ id, title, summary, quotes })),
  };
}

function fromBook(book: MyBookResponse): InterviewState {
  return { id: ID, stage: book.status === "on_shelf" ? "done" : "reviewing", book: toBook(book) };
}

async function myBook(): Promise<InterviewState> {
  return fromBook(unwrap(await api.GET("/books/me")));
}

// Turns the API's flat response into one screen. Two cases need another call first: the Librarian
// has enough (go straight to the titles), or the question couldn't be written (ask for it again).
async function toState(response: InterviewResponse, retried = false): Promise<InterviewState> {
  switch (response.stage) {
    case "choosing":
      return {
        id: ID,
        stage: "choosing",
        titles: (response.titles ?? []).map((option, index) => ({ id: String(index), ...option })),
      };
    case "reviewing":
    case "done":
    // No screens yet for growing a book: the member sees their book, which hasn't changed.
    case "adding":
    case "revising":
      return myBook();
    case "interviewing": {
      const { question } = response;
      if (!question) {
        if (response.ready_for_reveal) return toState(unwrap(await api.POST("/interview/finish")));
        if (retried)
          throw new InterviewError("The Librarian couldn't answer just now. Please try again.", true);
        return toState(unwrap(await api.POST("/interview/question")), true);
      }
      if (question.phase === "shape") {
        const playback = question.playback ? `${question.playback} ${question.text}` : question.text;
        return { id: ID, stage: "shaping", phase: "shape", playback };
      }
      return {
        id: ID,
        stage: "asking",
        // Only a round of adding has other phases, and that stage is handled above.
        phase: question.phase === "dig" ? "dig" : "sweep",
        question: question.text,
        canFinish: response.can_finish,
        hasAnswers: response.has_answers,
        lastTopic: response.topic,
      };
    }
  }
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
    return toState(unwrap({ data, error, response }));
  },
  async start(resume) {
    const body = resume ? { resume_pdf: await readBase64(resume) } : {};
    return toState(unwrap(await api.POST("/interview", { body })));
  },
  async answer(_id, text) {
    return toState(unwrap(await api.POST("/interview/answers", { body: { answer: text } })));
  },
  async skip() {
    return toState(unwrap(await api.POST("/interview/skip")));
  },
  async askAgain() {
    return toState(unwrap(await api.POST("/interview/question")));
  },
  async finish(_id, answer) {
    // Trove API's finish doesn't take `answer` on this branch yet. Saving it as an answer first loses
    // nothing, and only costs a question that's never shown. Swap for the body once it lands.
    if (answer) unwrap(await api.POST("/interview/answers", { body: { answer } }));
    return toState(unwrap(await api.POST("/interview/finish")));
  },
  async confirmShape() {
    return toState(unwrap(await api.POST("/interview/shape", { body: {} })));
  },
  async correctShape(_id, correction) {
    return toState(unwrap(await api.POST("/interview/shape", { body: { correction } })));
  },
  async chooseTitle(_id, titleId) {
    const result = await api.POST("/interview/title", { body: { title: Number(titleId) } });
    // Already chosen, by a press before a refresh: go on to where the interview really is.
    if (result.response.status === 409) {
      const now = await apiInterviewClient.current();
      if (now) return now;
    }
    return fromBook(unwrap(result));
  },
  async otherTitles() {
    const response = unwrap(await api.GET("/interview"));
    return (response.titles ?? []).map((option, index) => ({ id: String(index), ...option }));
  },
  async changeTitle(_id, titleId) {
    return fromBook(unwrap(await postUntyped("/interview/book/title", { body: { title: Number(titleId) } })));
  },
  async rewriteBlurb() {
    return fromBook(unwrap(await postUntyped("/interview/book/blurb")));
  },
  async rewriteChapter(_id, chapterId) {
    const params = { path: { chapter_id: chapterId } };
    return fromBook(unwrap(await api.POST("/interview/book/chapters/{chapter_id}/rewrite", { params })));
  },
  async removeChapter(_id, chapterId) {
    const params = { path: { chapter_id: chapterId } };
    return fromBook(unwrap(await api.DELETE("/interview/book/chapters/{chapter_id}", { params })));
  },
  async putOnShelf() {
    return fromBook(unwrap(await api.POST("/interview/book/shelve")));
  },
};
