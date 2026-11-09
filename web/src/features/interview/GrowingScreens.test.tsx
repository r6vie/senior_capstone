import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { AuthProvider } from "../auth/AuthProvider";
import { createFakeInterviewClient, resetFakeInterview } from "./fakeInterviewClient";
import { InterviewPage } from "./InterviewPage";
import {
  type InterviewClient,
  InterviewError,
  type InterviewState,
  type MyBook,
  type ProposedChange,
} from "./interviewClient";
import { ReadingQuestionPage } from "./ReadingQuestionPage";
import { RemovalPage } from "./RemovalPage";

const changes: ProposedChange[] = [
  {
    id: "c1",
    kind: "improve",
    note: "Adds what the collector showed you.",
    title: "Selling the Ones I Couldn't Fix",
    summary: "I kept them for a year, hoping I would learn how. He showed me a test.",
    now: {
      title: "Selling the Ones I Couldn't Fix",
      summary: "I kept them for a year, hoping I would learn how.",
    },
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

function press2(name: string) {
  return screen.findByRole("button", { name }).then((button) => fireEvent.click(button));
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
    expect(await screen.findByText("I'm writing the changes.")).toBeTruthy();
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
    expect(document.querySelector("ins")?.textContent).toMatch(/He showed me a test/);
  });

  it("names the chapter on each decision, and the choice is never red", async () => {
    show(client(proposing));
    const approve = await screen.findByRole("button", { name: "Approve: What I Gave Up for the Garage" });
    fireEvent.click(approve);
    expect(approve.getAttribute("aria-pressed")).toBe("true");
    expect(approve.className).not.toMatch(/primary/);
    expect(screen.getByText("Approved")).toBeTruthy();
  });

  it("saves each choice as it's pressed, and shows what was approved on another visit", async () => {
    const saved = vi.fn(async () => undefined);
    show(client({ ...proposing, approved: ["c1"] } as InterviewState, { saveChoices: saved }));
    expect(await screen.findByText("Approved")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Approve: What I Gave Up for the Garage" }));
    expect(saved).toHaveBeenCalledWith(["c1", "c2"]);
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

  it("shows a removal left open from My book as a removal", async () => {
    const removal: ProposedChange = {
      id: "r",
      kind: "remove",
      note: "You asked to take this chapter out of your book.",
      title: "Four",
      summary: "",
      now: { title: "Four", summary: "About four." },
    };
    show(client({ id: "me", stage: "proposing", changes: [removal], blurb: null }));
    expect(await screen.findByText("Removing")).toBeTruthy();
    expect(screen.getByText("Comes out of your book.")).toBeTruthy();
  });

  it("nothing goes live until the member confirms, and they see the back cover first", async () => {
    const blurbFor = vi.fn(async () => "The new back cover.");
    const apply = vi.fn(
      async (): Promise<InterviewState> => ({
        id: "me",
        stage: "updated",
        book: { title: "T", authorName: "N", blurb: null, chapters: [] },
        canUndo: true,
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
        {
          id: "me",
          stage: "updated",
          book: { title: "T", authorName: "N", blurb: null, chapters: [] },
          canUndo: true,
        },
        { undoChanges: undo },
      ),
    );
    fireEvent.click(await screen.findByRole("button", { name: "Undo these changes" }));
    expect(undo).not.toHaveBeenCalled();
    expect(screen.getByText(/Your book goes back to how it was/)).toBeTruthy();
    press("Undo");
    await waitFor(() => expect(undo).toHaveBeenCalledTimes(1));
    expect(await screen.findByText("Your book is back as it was.")).toBeTruthy();
  });
});

describe("words that can't go where they were meant", () => {
  beforeEach(() => localStorage.clear());
  afterEach(() => vi.restoreAllMocks());

  const stale = new InterviewError("That isn't the question waiting.", false, true, false);
  const inRound: InterviewState = {
    id: "me",
    stage: "asking",
    round: "adding",
    phase: "dig",
    question: "What did you stop doing?",
    canFinish: false,
    hasAnswers: false,
    lastTopic: null,
  };
  const moved = (now: InterviewState) => {
    const c = client(null);
    vi.spyOn(c, "current").mockResolvedValueOnce(inRound).mockResolvedValue(now);
    vi.spyOn(c, "answer").mockRejectedValueOnce(stale);
    return c;
  };
  const screens: [string, InterviewState][] = [
    ["writing", { id: "me", stage: "writing" }],
    ["proposing", proposing],
    ["drafting", { id: "me", stage: "drafting", about: "titles" }],
    ["shaping", { id: "me", stage: "shaping", phase: "shape", playback: "Is this you?" }],
  ];

  it.each(screens)(
    "another screen ended the questions, and this lands on %s: the words stay",
    async (_, now) => {
      localStorage.setItem("trove_interview_seen:anon", String(Date.now()));
      show(moved(now));
      fireEvent.change(await screen.findByLabelText("Your answer"), {
        target: { value: "My careful words" },
      });
      press("Send answer");
      expect(await screen.findByText("My careful words")).toBeTruthy();
      expect(
        screen.getByText(/Your last words weren't saved, because the questions had already ended/),
      ).toBeTruthy();
      await act(async () => {});
      fireEvent.click(screen.getByRole("button", { name: "I've got them" }));
      await waitFor(() => expect(screen.queryByText("My careful words")).toBeNull());
    },
  );

  it("the words stay usable during a wait, and the wait doesn't claim everything was saved", async () => {
    localStorage.setItem("trove_interview_seen:anon", String(Date.now()));
    show(moved({ id: "me", stage: "drafting", about: "titles" }));
    fireEvent.change(await screen.findByLabelText("Your answer"), { target: { value: "My careful words" } });
    press("Send answer");
    const words = await screen.findByText("My careful words");
    expect(words.closest("[inert]")).toBeNull();
    expect(await screen.findByText("Everything else you've said is saved.")).toBeTruthy();
    expect(screen.queryByText("Everything you've said is saved.")).toBeNull();
  });

  it("an edit after a lost reply, when the questions have since ended, stays visible", async () => {
    localStorage.setItem("trove_interview_seen:anon", String(Date.now()));
    const c = client(null);
    vi.spyOn(c, "current").mockResolvedValueOnce(inRound).mockResolvedValue({ id: "me", stage: "writing" });
    const answer = vi.spyOn(c, "answer").mockRejectedValueOnce(new TypeError("Failed to fetch"));
    show(c);
    fireEvent.change(await screen.findByLabelText("Your answer"), { target: { value: "First." } });
    press("Send answer");
    await screen.findByRole("alert");
    fireEvent.change(screen.getByLabelText("Your answer"), { target: { value: "Better." } });
    press("Send answer");
    expect(await screen.findByText("Better.")).toBeTruthy();
    expect(screen.getByText(/Your first version was saved/)).toBeTruthy();
    expect(answer).toHaveBeenCalledTimes(1);
  });

  it("a draft left behind by another screen comes back on arrival", async () => {
    localStorage.setItem("trove_interview_seen:anon", String(Date.now()));
    localStorage.setItem("trove_interview_draft:anon:An earlier question", "Unsent words");
    localStorage.setItem("trove_interview_draft:anon:reading:r1", "A reading draft");
    show(client(inRound));
    expect(await screen.findByText("Unsent words")).toBeTruthy();
    expect(screen.queryByText("A reading draft")).toBeNull();
    expect(localStorage.getItem("trove_interview_draft:anon:reading:r1")).toBe("A reading draft");
  });

  describe("on Is this you?", () => {
    const shaping: InterviewState = { id: "me", stage: "shaping", phase: "shape", playback: "Is this you?" };
    const correct = (text: string) =>
      fireEvent.change(screen.getByLabelText(/tell me what's different/), { target: { value: text } });

    it("after a lost reply there's no Try again, and an edit is what gets sent", async () => {
      const c = client(shaping);
      const send = vi
        .spyOn(c, "correctShape")
        .mockRejectedValueOnce(new TypeError("Failed to fetch"))
        .mockResolvedValue({ id: "me", stage: "nothing" });
      show(c);
      await screen.findByText("Is this you?");
      correct("OLD correction");
      press("Send my correction");
      await screen.findByRole("alert");
      expect(screen.queryByRole("button", { name: "Try again" })).toBeNull();
      correct("NEW correction");
      press("Send my correction");
      await screen.findByText("Nothing here changes your book.");
      expect(send).toHaveBeenLastCalledWith("me", "NEW correction");
    });

    it("if the first correction did arrive, an edit stays visible instead of vanishing", async () => {
      const c = client(null);
      vi.spyOn(c, "current")
        .mockResolvedValueOnce(shaping)
        .mockResolvedValue({ id: "me", stage: "drafting", about: "titles" });
      const send = vi.spyOn(c, "correctShape").mockRejectedValueOnce(new TypeError("Failed to fetch"));
      show(c);
      await screen.findByText("Is this you?");
      correct("OLD correction");
      press("Send my correction");
      await screen.findByRole("alert");
      correct("NEW correction");
      press("Send my correction");
      expect(await screen.findByText("NEW correction")).toBeTruthy();
      expect(send).toHaveBeenCalledTimes(1);
    });

    it("Yes, that's me looks first too, so it isn't sent twice", async () => {
      const c = client(null);
      vi.spyOn(c, "current")
        .mockResolvedValueOnce(shaping)
        .mockResolvedValue({ id: "me", stage: "drafting", about: "titles" });
      const confirm = vi.spyOn(c, "confirmShape").mockRejectedValueOnce(new TypeError("Failed to fetch"));
      show(c);
      fireEvent.click(await screen.findByRole("button", { name: "Yes, that's me" }));
      await screen.findByRole("alert");
      press("Yes, that's me");
      await screen.findByText("The Librarian is finding your titles…");
      expect(confirm).toHaveBeenCalledTimes(1);
    });

    it("keeps a typed correction through a refresh", async () => {
      const key = "trove_interview_draft:anon:shape:Is this you?";
      localStorage.setItem(key, "Half a correction");
      show(client(shaping));
      await screen.findByText("Is this you?");
      expect((screen.getByLabelText(/tell me what's different/) as HTMLTextAreaElement).value).toBe(
        "Half a correction",
      );
    });
  });

  it("holds the Librarian's last line on the band during the wait", async () => {
    show(
      client({
        id: "me",
        stage: "drafting",
        about: "titles",
        closingLine: "That's enough for your book. I'll keep it as plain as you told it.",
      }),
    );
    expect(await screen.findByText(/I'll keep it as plain as you told it/)).toBeTruthy();
  });
});

describe("how a round ends", () => {
  beforeEach(() => localStorage.clear());

  const book = { title: "T", authorName: "N", blurb: null, chapters: [] };
  const done: InterviewState = { id: "me", stage: "done", book };

  it("hides undo on the updated screen when it can't be undone", async () => {
    show(client({ id: "me", stage: "updated", book, canUndo: false }));
    await screen.findByText("Your book on the shelf is updated.");
    expect(screen.queryByRole("button", { name: "Undo these changes" })).toBeNull();
  });

  it("declining everything goes to My book, not the first-publication screen", async () => {
    show(client(proposing, { applyChanges: async () => done }));
    fireEvent.click(await screen.findByRole("button", { name: "Decline: What I Gave Up for the Garage" }));
    press("Review your choices");
    await press2("Leave my book as it is");
    expect(await screen.findByText("The My book page")).toBeTruthy();
    expect(screen.queryByText(/Your book is on the shelf/)).toBeNull();
  });

  it("a round that changes nothing says so, rather than offering more questions", async () => {
    const reopened: InterviewState = {
      id: "me",
      stage: "asking",
      round: "adding",
      phase: "dig",
      question: "What did you stop doing?",
      canFinish: true,
      hasAnswers: false,
      lastTopic: null,
    };
    const finish = vi.fn(async (): Promise<InterviewState> => ({ id: "me", stage: "nothing" }));
    show(client(done, { reopen: async () => reopened, finish }), "/interview?add");
    fireEvent.click(await screen.findByRole("button", { name: "Start the questions" }));
    fireEvent.click(await screen.findByRole("button", { name: "That's enough. Write the changes" }));
    expect(await screen.findByText("Nothing here changes your book.")).toBeTruthy();
    expect(screen.queryByText(/A few more questions/)).toBeNull();
  });

  it("says why when an answer was left out for naming someone, and offers another go", async () => {
    show(client({ id: "me", stage: "nothing", droppedForNames: true, readingQuestionId: "r1" }));
    expect(await screen.findByText(/I left this out because it named someone or somewhere/)).toBeTruthy();
    expect(screen.getByRole("link", { name: "Say it again" }).getAttribute("href")).toBe(
      "/interview/reading/r1",
    );
  });

  it("names what was caught, and Say it again opens with the member's words", async () => {
    show(
      client({
        id: "me",
        stage: "nothing",
        droppedForNames: true,
        readingQuestionId: "r1",
        droppedWords: ["Geauga", "County", "Fair"],
        readingAnswer: "They asked about the Geauga County Fair.",
      }),
    );
    expect(
      await screen.findByText(/named someone or somewhere: Geauga, County, Fair. Change those/),
    ).toBeTruthy();
    fireEvent.click(screen.getByRole("link", { name: "Say it again" }));
    expect(localStorage.getItem("trove_interview_draft:anon:reading:r1")).toBe(
      "They asked about the Geauga County Fair.",
    );
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
    await press2("Remove");
    expect(await screen.findByText("You asked to remove a chapter.")).toBeTruthy();
    expect(screen.getByText("Comes out of your book.")).toBeTruthy();
    expect(document.body.textContent).toContain("Rewritten without this chapter.");
    expect(document.body.textContent).not.toContain("to include what you approved");
    expect(document.body.textContent).toContain("The shorter back cover.");
    expect(remove).not.toHaveBeenCalled();
    press("Update my book on the shelf");
    await waitFor(() => expect(remove).toHaveBeenCalledWith("3", "The shorter back cover."));
    expect(await screen.findByText("The My book page")).toBeTruthy();
  });

  it("looking costs nothing: nothing starts until Remove", async () => {
    const write = vi.fn(async () => "Shorter.");
    show(client(null, { myBook: async () => book, blurbWithout: write }), "/my-book/remove/3");
    expect(await screen.findByText("Remove this chapter?")).toBeTruthy();
    expect(write).not.toHaveBeenCalled();
    expect(screen.getByRole("link", { name: "Keep it" }).getAttribute("href")).toBe("/my-book");
  });

  it("backing out after starting cancels it", async () => {
    const cancel = vi.fn(async () => undefined);
    show(
      client(null, { myBook: async () => book, blurbWithout: async () => "S.", cancelRemoval: cancel }),
      "/my-book/remove/3",
    );
    await press2("Remove");
    await screen.findByText("You asked to remove a chapter.");
    await press2("Back to my book");
    await waitFor(() => expect(cancel).toHaveBeenCalledTimes(1));
    expect(await screen.findByText("The My book page")).toBeTruthy();
  });

  it("coming back to finish skips the question", async () => {
    show(
      client(null, { myBook: async () => book, blurbWithout: async () => "S." }),
      "/my-book/remove/3?finish",
    );
    expect(await screen.findByText("You asked to remove a chapter.")).toBeTruthy();
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
    expect(await screen.findByText("I'm checking whether this belongs in your book.")).toBeTruthy();
    expect(answer).toHaveBeenCalledWith("r1", "They asked why.");
  });

  it("when the reply is lost but the answer arrived, goes on and says it was saved", async () => {
    const asked = vi.fn().mockResolvedValueOnce([question]).mockResolvedValue([]);
    show(
      client(
        { id: "me", stage: "writing" },
        {
          readingQuestions: asked,
          answerReading: async () => {
            throw new TypeError("Failed to fetch");
          },
        },
      ),
      "/interview/reading/r1",
    );
    fireEvent.change(await screen.findByLabelText("Your answer"), { target: { value: "They asked why." } });
    press("Send answer");
    expect(await screen.findByText("Your answer was saved.")).toBeTruthy();
    expect(screen.getByText("I'm checking whether this belongs in your book.")).toBeTruthy();
  });

  it("a first send refused because another screen answered doesn't claim it was saved", async () => {
    const asked = vi.fn().mockResolvedValueOnce([question]).mockResolvedValue([]);
    show(
      client(null, {
        readingQuestions: asked,
        answerReading: async () => {
          throw new InterviewError("That question isn't waiting for you.", false, true);
        },
      }),
      "/interview/reading/r1",
    );
    fireEvent.change(await screen.findByLabelText("Your answer"), { target: { value: "My words." } });
    press("Send answer");
    expect((await screen.findByRole("alert")).textContent).toMatch(/these words weren't saved/);
    expect(screen.queryByText("Your answer was saved.")).toBeNull();
    expect((screen.getByLabelText("Your answer") as HTMLTextAreaElement).value).toBe("My words.");
  });

  it("an edit after a lost reply that did arrive stays visible", async () => {
    const asked = vi
      .fn()
      .mockResolvedValueOnce([question])
      .mockResolvedValueOnce([question])
      .mockResolvedValue([]);
    const answer = vi
      .fn()
      .mockRejectedValueOnce(new TypeError("Failed to fetch"))
      .mockRejectedValue(new InterviewError("That question isn't waiting for you.", false, true));
    show(
      client({ id: "me", stage: "writing" }, { readingQuestions: asked, answerReading: answer }),
      "/interview/reading/r1",
    );
    fireEvent.change(await screen.findByLabelText("Your answer"), { target: { value: "First." } });
    press("Send answer");
    await screen.findByRole("alert");
    fireEvent.change(screen.getByLabelText("Your answer"), { target: { value: "Better." } });
    press("Send answer");
    expect(await screen.findByText("Better.")).toBeTruthy();
    expect(screen.getByText(/Your first version was saved/)).toBeTruthy();
  });

  it("when the send failed and it's still waiting, keeps the answer", async () => {
    show(
      client(null, {
        readingQuestions: async () => [question],
        answerReading: async () => {
          throw new TypeError("Failed to fetch");
        },
      }),
      "/interview/reading/r1",
    );
    fireEvent.change(await screen.findByLabelText("Your answer"), { target: { value: "They asked why." } });
    press("Send answer");
    expect((await screen.findByRole("alert")).textContent).toMatch(/Your answer is still here/);
    expect((screen.getByLabelText("Your answer") as HTMLTextAreaElement).value).toBe("They asked why.");
  });

  it("says so when the question isn't waiting any more", async () => {
    show(client(null, { readingQuestions: async () => [] }), "/interview/reading/r1");
    expect(await screen.findByText("That question isn't waiting any more.")).toBeTruthy();
  });
});
