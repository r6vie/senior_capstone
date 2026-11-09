import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { AuthProvider } from "../auth/AuthProvider";
import { createFakeInterviewClient, resetFakeInterview } from "./fakeInterviewClient";
import { InterviewPage } from "./InterviewPage";
import type { InterviewClient, InterviewState, MyBook, ProposedChange } from "./interviewClient";
import { ReadingQuestionPage } from "./ReadingQuestionPage";
import { RemovalPage } from "./RemovalPage";

const changes: ProposedChange[] = [
  {
    id: "c1",
    kind: "improve",
    note: "Adds what the collector showed you.",
    title: "Selling the Ones I Couldn't Fix",
    summary: "I kept them for a year. He showed me how to test a board.",
    now: { title: "Selling the Ones I Couldn't Fix", summary: "I kept them for a year." },
  },
  {
    id: "c2",
    kind: "new",
    note: "You described what you gave up.",
    title: "What I Gave Up for the Garage",
    summary: "I go every Saturday.",
    now: null,
  },
];
const proposing: InterviewState = { id: "me", stage: "proposing", changes, blurb: "The old back cover." };

function client(state: InterviewState | null, overrides: Partial<InterviewClient> = {}): InterviewClient {
  return { ...createFakeInterviewClient("Nora", 0), current: async () => state, ...overrides };
}

function show(c: InterviewClient, url = "/interview") {
  render(
    <AuthProvider>
      <MemoryRouter initialEntries={[url]}>
        <Routes>
          <Route path="/interview" element={<InterviewPage client={c} />} />
          <Route path="/interview/reading/:questionId" element={<ReadingQuestionPage client={c} />} />
          <Route path="/my-book/remove/:chapterId" element={<RemovalPage client={c} />} />
          <Route path="/my-book" element={<p>The My book page</p>} />
        </Routes>
      </MemoryRouter>
    </AuthProvider>,
  );
}

function press(name: string) {
  fireEvent.click(screen.getByRole("button", { name }));
}

describe("adding to a book", () => {
  beforeEach(() => {
    resetFakeInterview();
    localStorage.clear();
  });
  afterEach(() => {
    vi.restoreAllMocks();
    vi.useRealTimers();
  });

  const done: InterviewState = {
    id: "me",
    stage: "done",
    book: { title: "T", authorName: "N", blurb: null, chapters: [] },
  };

  it("sends an earlier visit's finished book to My book", async () => {
    show(client(done));
    expect(await screen.findByText("The My book page")).toBeTruthy();
  });

  it("opens nothing until the member presses Start, and says the shelf doesn't change", async () => {
    const reopen = vi.fn(
      async (): Promise<InterviewState> => ({
        id: "me",
        stage: "asking",
        round: "adding",
        phase: "dig",
        question: "What did you stop doing?",
        canFinish: false,
        hasAnswers: false,
        lastTopic: null,
      }),
    );
    show(client(done, { reopen }), "/interview?add");
    expect(await screen.findByText(/A few more questions/)).toBeTruthy();
    expect(screen.getByText(/Nothing changes on the shelf until you approve it/)).toBeTruthy();
    expect(reopen).not.toHaveBeenCalled();
    press("Start the questions");
    expect(await screen.findByText("What did you stop doing?")).toBeTruthy();
  });

  it("mentions sparks only when there are some, with no number", async () => {
    show(client(done, { sparks: async () => [{ id: "s", chapterTitle: "Two offers" }] }), "/interview?add");
    expect(await screen.findByText(/will shape some of the questions/)).toBeTruthy();
    expect(document.body.textContent).not.toMatch(/Two offers/);
  });

  const inRound: InterviewState = {
    id: "me",
    stage: "asking",
    round: "adding",
    phase: "dig",
    question: "What did you stop doing?",
    canFinish: true,
    hasAnswers: true,
    lastTopic: null,
  };

  it("shows no phases in a round, and its own way out that keeps typed words", async () => {
    localStorage.setItem("trove_interview_seen:anon", String(Date.now()));
    const finish = vi.fn(async (): Promise<InterviewState> => ({ id: "me", stage: "writing" }));
    show(client(inRound, { finish }));
    fireEvent.click(await screen.findByRole("button", { name: "That's enough. Write the changes" }));
    expect(finish).toHaveBeenCalledWith("me", undefined);
    expect(await screen.findByText("Writing your changes.")).toBeTruthy();
    expect(screen.queryByRole("list", { name: "Where we are" })).toBeNull();
  });

  it("with words in the field, the way out says it sends them", async () => {
    localStorage.setItem("trove_interview_seen:anon", String(Date.now()));
    const finish = vi.fn(async (): Promise<InterviewState> => ({ id: "me", stage: "writing" }));
    show(client(inRound, { finish }));
    fireEvent.change(await screen.findByLabelText("Your answer"), { target: { value: "My words" } });
    press("Send this, then write the changes");
    expect(finish).toHaveBeenCalledWith("me", "My words");
  });

  it("the wait moves on by itself, and says the member can leave", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const states: InterviewState[] = [{ id: "me", stage: "writing" }, proposing];
    show(client(null, { current: async () => states.shift() ?? proposing }));
    expect(await screen.findByText(/You can leave/)).toBeTruthy();
    expect(screen.getByRole("link", { name: "Back to my book" })).toBeTruthy();
    await act(() => vi.advanceTimersByTimeAsync(5000));
    expect(screen.getByText("Here is what I would change in your book.")).toBeTruthy();
  });

  it("failed writing says the answers are saved, and tries again", async () => {
    const retry = vi.fn(async () => proposing);
    show(client({ id: "me", stage: "writeFailed" }, { retryWriting: retry }));
    expect(await screen.findByText(/Your answers are saved/)).toBeTruthy();
    press("Try again");
    expect(await screen.findByText("Here is what I would change in your book.")).toBeTruthy();
  });

  it("nothing usable says so without blaming the member", async () => {
    show(client({ id: "me", stage: "nothing" }));
    expect(await screen.findByText("Nothing here changes your book.")).toBeTruthy();
    expect(screen.getByText("What you said is saved, and the next questions can use it.")).toBeTruthy();
    expect(document.body.textContent).not.toMatch(/round/i);
  });
});

describe("proposed changes", () => {
  beforeEach(() => localStorage.clear());
  afterEach(() => vi.restoreAllMocks());

  it("shows what's there now, what would replace it and what was added, undecided at first", async () => {
    show(client(proposing));
    expect(await screen.findByText("Changed chapter")).toBeTruthy();
    expect(screen.getByText("New chapter")).toBeTruthy();
    expect(screen.queryByText(/Improved/)).toBeNull();
    expect(screen.getByText("Not in your book yet.")).toBeTruthy();
    expect(screen.getAllByText("Not decided")).toHaveLength(2);
    expect(document.querySelector("ins")?.textContent).toMatch(/He showed me how to test a board/);
  });

  it("names the chapter on each decision, and the choice is never red", async () => {
    show(client(proposing));
    const approve = await screen.findByRole("button", { name: "Approve: What I Gave Up for the Garage" });
    fireEvent.click(approve);
    expect(approve.getAttribute("aria-pressed")).toBe("true");
    expect(approve.className).not.toMatch(/primary/);
    expect(screen.getByText("Approved")).toBeTruthy();
  });

  it("keeps choices after leaving, so Decide later means it", async () => {
    show(client(proposing));
    fireEvent.click(await screen.findByRole("button", { name: "Decline: What I Gave Up for the Garage" }));
    await screen.findByText("Declined");
    expect(screen.getByRole("link", { name: "Decide later" }).getAttribute("href")).toBe("/my-book");
    document.body.innerHTML = "";
    show(client(proposing));
    expect(await screen.findByText("Declined")).toBeTruthy();
  });

  it("nothing goes live until the member confirms, and they see the back cover first", async () => {
    const blurbFor = vi.fn(async () => "The new back cover.");
    const apply = vi.fn(
      async (): Promise<InterviewState> => ({
        id: "me",
        stage: "updated",
        book: { title: "T", authorName: "N", blurb: null, chapters: [] },
      }),
    );
    show(client(proposing, { blurbFor, applyChanges: apply }));
    fireEvent.click(await screen.findByRole("button", { name: "Approve: What I Gave Up for the Garage" }));
    press("Review your choices");
    expect(await screen.findByText("Here is what changes on the shelf.")).toBeTruthy();
    expect(blurbFor).toHaveBeenCalledWith(["c2"]);
    expect(apply).not.toHaveBeenCalled();
    expect(screen.getByText("Will change on the shelf")).toBeTruthy();
    expect(screen.getByText("Not decided")).toBeTruthy();
    expect(screen.getByText("The old back cover.")).toBeTruthy();
    expect(document.body.textContent).toContain("The new back cover.");
    press("Update my book on the shelf");
    await waitFor(() => expect(apply).toHaveBeenCalledWith(["c2"], "The new back cover."));
    expect(await screen.findByText("Your book on the shelf is updated.")).toBeTruthy();
    expect(screen.getByRole("link", { name: "See my book" })).toBeTruthy();
  });

  it("declining the back cover keeps the old one", async () => {
    const apply = vi.fn(async (): Promise<InterviewState> => proposing);
    show(client(proposing, { blurbFor: async () => "The new back cover.", applyChanges: apply }));
    fireEvent.click(await screen.findByRole("button", { name: "Approve: What I Gave Up for the Garage" }));
    press("Review your choices");
    fireEvent.click(await screen.findByRole("button", { name: "Decline: the back cover" }));
    press("Update my book on the shelf");
    await waitFor(() => expect(apply).toHaveBeenCalledWith(["c2"], null));
  });

  it("a back cover that can't be written doesn't block confirming, and is never sent", async () => {
    const blurbFor = vi.fn().mockRejectedValueOnce(new Error("no")).mockResolvedValue("Second try.");
    const apply = vi.fn(async (): Promise<InterviewState> => proposing);
    show(client(proposing, { blurbFor, applyChanges: apply }));
    fireEvent.click(await screen.findByRole("button", { name: "Approve: What I Gave Up for the Garage" }));
    press("Review your choices");
    expect(await screen.findByText(/The old one stays unless you try again/)).toBeTruthy();
    press("Update my book on the shelf");
    await waitFor(() => expect(apply).toHaveBeenCalledWith(["c2"], null));
  });

  it("with nothing approved, the button says what will happen and offers no back cover", async () => {
    const blurbFor = vi.fn(async () => "Never.");
    const apply = vi.fn(async (): Promise<InterviewState> => proposing);
    show(client(proposing, { blurbFor, applyChanges: apply }));
    fireEvent.click(await screen.findByRole("button", { name: "Decline: What I Gave Up for the Garage" }));
    press("Review your choices");
    expect(await screen.findByText("Nothing will change on the shelf.")).toBeTruthy();
    expect(blurbFor).not.toHaveBeenCalled();
    press("Leave my book as it is");
    await waitFor(() => expect(apply).toHaveBeenCalledWith([], null));
  });

  it("offers undo once the changes are live", async () => {
    const undo = vi.fn(async () => undefined);
    show(
      client(
        { id: "me", stage: "updated", book: { title: "T", authorName: "N", blurb: null, chapters: [] } },
        { undoChanges: undo },
      ),
    );
    fireEvent.click(await screen.findByRole("button", { name: "Undo these changes" }));
    await waitFor(() => expect(undo).toHaveBeenCalledTimes(1));
    expect(await screen.findByText("Your book is back as it was.")).toBeTruthy();
  });
});

describe("removing a chapter from the shelf", () => {
  const book: MyBook = {
    title: "T",
    authorName: "N",
    blurb: "The old back cover.",
    canUndo: false,
    chapters: ["One", "Two", "Three", "Four"].map((title, index) => ({
      id: String(index),
      title,
      summary: `About ${title}.`,
      quotes: [],
    })),
  };

  it("goes through the same confirm step, with the back cover shown", async () => {
    const remove = vi.fn(async () => undefined);
    show(
      client(null, {
        myBook: async () => book,
        blurbWithout: async () => "The shorter back cover.",
        removeFromShelf: remove,
      }),
      "/my-book/remove/3",
    );
    expect(await screen.findByText("You asked to remove a chapter.")).toBeTruthy();
    expect(screen.getByText("Comes out of your book.")).toBeTruthy();
    expect(document.body.textContent).toContain("The shorter back cover.");
    expect(remove).not.toHaveBeenCalled();
    press("Update my book on the shelf");
    await waitFor(() => expect(remove).toHaveBeenCalledWith("3", "The shorter back cover."));
    expect(await screen.findByText("The My book page")).toBeTruthy();
  });

  it("isn't reachable at three chapters", async () => {
    show(
      client(null, { myBook: async () => ({ ...book, chapters: book.chapters.slice(0, 3) }) }),
      "/my-book/remove/0",
    );
    expect(await screen.findByText("The My book page")).toBeTruthy();
  });
});

describe("the reading question", () => {
  const question = {
    id: "r1",
    question: "What did they ask you about that surprised you?",
    readerName: "Sam Okafor",
    createdAt: "2026-11-06T12:00:00Z",
  };
  beforeEach(() => localStorage.clear());

  it("names the reader, asks for names to be left out, and has no Skip", async () => {
    show(client(null, { readingQuestions: async () => [question] }), "/interview/reading/r1");
    expect(await screen.findByText("After your reading with Sam Okafor, Nov 6")).toBeTruthy();
    expect(screen.getByText("Leave names out. This can become part of your book.")).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Skip" })).toBeNull();
  });

  it("Not now only goes back: it doesn't dismiss", async () => {
    const dismiss = vi.fn(async () => undefined);
    show(
      client(null, { readingQuestions: async () => [question], dismissReading: dismiss }),
      "/interview/reading/r1",
    );
    const notNow = await screen.findByRole("link", { name: "Not now" });
    expect(notNow.getAttribute("href")).toBe("/my-book");
    expect(dismiss).not.toHaveBeenCalled();
  });

  it("sends the answer, then waits with its own words, and a thin one says so plainly", async () => {
    const answer = vi.fn(async (): Promise<InterviewState> => ({ id: "me", stage: "writing" }));
    show(
      client(
        { id: "me", stage: "writing" },
        { readingQuestions: async () => [question], answerReading: answer },
      ),
      "/interview/reading/r1",
    );
    fireEvent.change(await screen.findByLabelText("Your answer"), { target: { value: "They asked why." } });
    press("Send answer");
    expect(await screen.findByText("Reading your answer against your book.")).toBeTruthy();
    expect(answer).toHaveBeenCalledWith("r1", "They asked why.");
  });

  it("says so when the question isn't waiting any more", async () => {
    show(client(null, { readingQuestions: async () => [] }), "/interview/reading/r1");
    expect(await screen.findByText("That question isn't waiting any more.")).toBeTruthy();
  });
});
