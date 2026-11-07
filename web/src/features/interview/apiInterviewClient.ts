import { api } from "../../api/client";
import { errorMessage } from "../../api/errors";
import type { components } from "../../api/schema";
import type { DraftBook, InterviewClient, InterviewState } from "./interviewClient";

// The real interview API (api/trove/interview), mapped onto the shape the screens use.
// The API keeps one interview per member, so there is no id to pass; the screens' id is a constant.

type InterviewResponse = components["schemas"]["InterviewResponse"];
type MyBookResponse = components["schemas"]["MyBookResponse"];

const ID = "me";

interface Result<T> {
  data?: T;
  error?: unknown;
}

function unwrap<T>({ data, error }: Result<T>): T {
  if (data === undefined) throw new Error(errorMessage(error));
  return data;
}

function toBook(book: MyBookResponse): DraftBook {
  return {
    title: book.title,
    authorName: book.author_name,
    chapters: book.chapters.map(({ id, title, summary }) => ({ id, title, summary })),
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
      return myBook();
    case "interviewing": {
      const { question } = response;
      if (!question) {
        if (response.ready_for_reveal) return toState(unwrap(await api.POST("/interview/finish")));
        if (retried) throw new Error("The Librarian couldn't answer just now. Please try again.");
        return toState(unwrap(await api.POST("/interview/question")), true);
      }
      if (question.phase === "shape") {
        const playback = question.playback ? `${question.playback} ${question.text}` : question.text;
        return { id: ID, stage: "shaping", phase: "shape", playback };
      }
      return {
        id: ID,
        stage: "asking",
        phase: question.phase,
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
    return toState(unwrap({ data, error }));
  },
  async start(resume) {
    const body = resume ? { resume_pdf: await readBase64(resume) } : {};
    return toState(unwrap(await api.POST("/interview", { body })));
  },
  async answer(_id, text) {
    return toState(unwrap(await api.POST("/interview/answers", { body: { answer: text } })));
  },
  async finish() {
    return toState(unwrap(await api.POST("/interview/finish")));
  },
  async confirmShape() {
    return toState(unwrap(await api.POST("/interview/shape", { body: {} })));
  },
  async correctShape(_id, correction) {
    return toState(unwrap(await api.POST("/interview/shape", { body: { correction } })));
  },
  async chooseTitle(_id, titleId) {
    return fromBook(unwrap(await api.POST("/interview/title", { body: { title: Number(titleId) } })));
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
