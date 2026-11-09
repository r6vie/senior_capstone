import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { createFakeInterviewClient } from "../interview/fakeInterviewClient";
import type {
  BookStage,
  InterviewClient,
  MyBook,
  ReadingQuestion,
  Spark,
} from "../interview/interviewClient";
import { MyBookPage } from "./MyBookPage";

const book: MyBook = {
  title: "The Coil Was Never the Problem",
  authorName: "Nora Valdez",
  blurb: "I've restored about thirty pinball machines.",
  canUndo: false,
  chapters: ["One", "Two", "Three", "Four"].map((title, index) => ({
    id: String(index),
    title,
    summary: `About ${title}.`,
    quotes: [`I said ${title}.`],
  })),
};
const sparks: Spark[] = [{ id: "s1", chapterTitle: "How I decided between two offers" }];
const reading: ReadingQuestion[] = [
  {
    id: "r1",
    question: "What did they ask you about that surprised you?",
    readerName: "Sam Okafor",
    createdAt: "2026-11-06T12:00:00Z",
  },
];

function client(stage: BookStage, overrides: Partial<InterviewClient> = {}): InterviewClient {
  return {
    ...createFakeInterviewClient("Nora", 0),
    stage: async () => stage,
    myBook: async () => (stage === "none" || stage === "interviewing" || stage === "titles" ? null : book),
    sparks: async () => [],
    readingQuestions: async () => [],
    ...overrides,
  };
}

function show(c: InterviewClient) {
  render(
    <MemoryRouter>
      <MyBookPage client={c} />
    </MemoryRouter>,
  );
}

function linkTo(name: string) {
  return screen.getByRole("link", { name }).getAttribute("href");
}

describe("MyBookPage", () => {
  afterEach(() => vi.useRealTimers());

  it("with no book, points to the interview and says nobody sees it", async () => {
    show(client("none"));
    expect(await screen.findByText("You haven't started your book yet.")).toBeTruthy();
    expect(screen.getByText(/Nobody sees your book until you put it on the shelf/)).toBeTruthy();
    expect(linkTo("Start the interview")).toBe("/interview");
  });

  it("never tells someone with saved answers they haven't started", async () => {
    show(client("interviewing", { sparks: async () => sparks }));
    expect(await screen.findByText("Your interview is in progress.")).toBeTruthy();
    expect(screen.queryByText(/haven't started/)).toBeNull();
    expect(linkTo("Continue your interview")).toBe("/interview");
    expect(await screen.findByText("How I decided between two offers")).toBeTruthy();
  });

  it("shows sparks saved before a first interview too", async () => {
    show(client("none", { sparks: async () => sparks }));
    expect(await screen.findByText("For your next questions")).toBeTruthy();
  });

  it("with titles waiting, goes to them", async () => {
    show(client("titles"));
    expect(await screen.findByText("Your three titles are ready.")).toBeTruthy();
    expect(linkTo("See your titles")).toBe("/interview");
  });

  it("a draft points to review, with no reading question or sparks", async () => {
    show(client("draft", { sparks: async () => sparks, readingQuestions: async () => reading }));
    expect(await screen.findByText("Draft, not on the shelf yet")).toBeTruthy();
    expect(linkTo("Review your book")).toBe("/interview");
    expect(screen.queryByText(/What did they ask you/)).toBeNull();
    expect(screen.queryByText("For your next questions")).toBeNull();
    expect(screen.queryByRole("link", { name: /Remove this chapter/ })).toBeNull();
  });

  it("on the shelf, offers adding as the one primary action, and removing a chapter", async () => {
    show(client("shelf"));
    expect(await screen.findByText("On the shelf")).toBeTruthy();
    expect(linkTo("Add to your book")).toBe("/interview?add");
    expect(document.querySelectorAll(".button-primary")).toHaveLength(1);
    expect(linkTo("Remove this chapter: One")).toBe("/my-book/remove/0");
    expect(screen.queryByText("Undo these changes")).toBeNull();
  });

  it("hides removing at three chapters", async () => {
    const three = { ...book, chapters: book.chapters.slice(0, 3) };
    show(client("shelf", { myBook: async () => three }));
    await screen.findByText("On the shelf");
    expect(screen.queryByRole("link", { name: /Remove this chapter/ })).toBeNull();
  });

  it("shows the author's own words on request", async () => {
    show(client("shelf"));
    await screen.findByText("On the shelf");
    expect(screen.queryByText("I said One.")).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Show what you said for One" }));
    expect(screen.getByText("I said One.")).toBeTruthy();
  });

  it("offers undo right after an update, and it restores the book", async () => {
    const undo = vi.fn(async () => undefined);
    show(client("shelf", { myBook: async () => ({ ...book, canUndo: true }), undoChanges: undo }));
    expect(await screen.findByText(/You can undo these changes/)).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Undo these changes" }));
    await waitFor(() => expect(undo).toHaveBeenCalledTimes(1));
  });

  it("names the reader to the author, and No thanks dismisses it", async () => {
    const dismiss = vi.fn(async () => undefined);
    show(client("shelf", { readingQuestions: async () => reading, dismissReading: dismiss }));
    const captions = await screen.findAllByText("After your reading with Sam Okafor, Nov 6");
    expect(captions.length).toBeGreaterThan(0);
    expect(screen.getAllByRole("link", { name: "Answer" })[0]?.getAttribute("href")).toBe(
      "/interview/reading/r1",
    );
    fireEvent.click(screen.getAllByRole("button", { name: "No thanks" })[0] as HTMLElement);
    await waitFor(() => expect(dismiss).toHaveBeenCalledWith("r1"));
    await waitFor(() => expect(screen.queryByText(/What did they ask you/)).toBeNull());
  });

  it.each(["adding", "writing", "writeFailed", "changesWaiting"] as const)(
    "hides the reading question and removing while %s",
    async (stage) => {
      show(client(stage, { readingQuestions: async () => reading, sparks: async () => sparks }));
      expect(await screen.findAllByText(/These are shaping the questions/)).toBeTruthy();
      expect(screen.queryByText(/What did they ask you/)).toBeNull();
      expect(screen.queryByRole("link", { name: /Remove this chapter/ })).toBeNull();
    },
  );

  it("names the next step for a growing book", async () => {
    show(client("adding"));
    expect(await screen.findByText(/You have questions in progress/)).toBeTruthy();
    expect(linkTo("Continue adding to your book")).toBe("/interview");
  });

  it("while writing, has nothing to press", async () => {
    show(client("writing"));
    expect(await screen.findByText(/I'm writing your changes/)).toBeTruthy();
    expect(document.querySelectorAll(".button-primary")).toHaveLength(0);
  });

  it("while writing, moves on by itself when the changes are ready", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const stages: BookStage[] = ["writing", "changesWaiting"];
    show(client("writing", { stage: async () => stages.shift() ?? "changesWaiting" }));
    await screen.findByText(/I'm writing your changes/);
    await act(() => vi.advanceTimersByTimeAsync(5000));
    expect(screen.getByRole("link", { name: "Review the proposed changes" })).toBeTruthy();
  });

  it("when writing failed, says the answers are safe and tries again", async () => {
    const retry = vi.fn(async () => ({ id: "me", stage: "writing" as const }));
    show(client("writeFailed", { retryWriting: retry }));
    expect(await screen.findByText(/Your answers are saved/)).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));
    await waitFor(() => expect(retry).toHaveBeenCalledTimes(1));
  });

  it("removes a spark", async () => {
    const remove = vi.fn(async () => undefined);
    show(client("shelf", { sparks: async () => sparks, removeSpark: remove }));
    const buttons = await screen.findAllByRole("button", { name: `Remove ${sparks[0]?.chapterTitle}` });
    fireEvent.click(buttons[0] as HTMLElement);
    await waitFor(() => expect(remove).toHaveBeenCalledWith("s1"));
    await waitFor(() => expect(screen.queryByText("For your next questions")).toBeNull());
  });

  it("when it can't load, doesn't say the member has no book", async () => {
    let fail = true;
    show(
      client("shelf", {
        stage: async () => {
          if (fail) throw new TypeError("Failed to fetch");
          return "shelf";
        },
      }),
    );
    expect(await screen.findByText("I couldn't find your book just now.")).toBeTruthy();
    expect(screen.queryByText(/haven't started/)).toBeNull();
    fail = false;
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));
    expect(await screen.findByText("On the shelf")).toBeTruthy();
  });

  it("shows no performance numbers", async () => {
    show(client("shelf", { sparks: async () => sparks }));
    await screen.findByText("On the shelf");
    const text = document.body.textContent ?? "";
    expect(text).not.toMatch(/cop(y|ies)|checkouts?\b|views?\b/i);
  });
});
