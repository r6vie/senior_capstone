import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { artFor } from "../../ui/art/bookArt";
import { AuthProvider } from "../auth/AuthProvider";
import { createFakeInterviewClient } from "../interview/fakeInterviewClient";
import type {
  BookStage,
  InterviewClient,
  MyBook,
  ReadingQuestion,
  Spark,
} from "../interview/interviewClient";
import { leaveWords } from "../interview/LeftoverWords";
import { MyBookPage } from "./MyBookPage";

// The book's id, which chooses its cover art, comes from /books/me.
vi.mock("../discovery/bookPreload", () => ({ loadOwnBook: async () => ({ id: "nora-book" }) }));

const book: MyBook = {
  title: "The Coil Was Never the Problem",
  authorName: "Nora Valdez",
  blurb: "I've restored about thirty pinball machines.",
  canUndo: false,
  status: "on_shelf",
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
    <AuthProvider>
      <MemoryRouter>
        <MyBookPage client={c} />
      </MemoryRouter>
    </AuthProvider>,
  );
}

function linkTo(name: string) {
  return screen.getByRole("link", { name }).getAttribute("href");
}

describe("my book's cover", () => {
  it("shows the book's own cover art, at both sizes, with the type in the art's ink", async () => {
    show(client("shelf"));
    await screen.findByRole("heading", { level: 1, name: book.title });
    const art = artFor("nora-book");
    const covers = [...document.querySelectorAll(".mb-head .book-cover")] as HTMLElement[];
    expect(covers).toHaveLength(2);
    for (const cover of covers) {
      expect(cover.querySelector("img.book-art")?.getAttribute("src")).toBe(art.cover);
      expect(cover.style.getPropertyValue("--art-ink")).toBe(art.ink);
    }
  });
});

describe("editing my book", () => {
  beforeEach(() => localStorage.clear());

  it("edits the title and back cover in place, saving only what changed", async () => {
    let current: MyBook = book;
    const edit = vi.fn(async () => {
      current = { ...book, title: "My own title" };
      return current;
    });
    show(client("shelf", { editBook: edit, myBook: async () => current }));
    fireEvent.click(await screen.findByRole("button", { name: "Edit the title and back cover" }));
    fireEvent.change(screen.getByLabelText("Title"), { target: { value: "My own title" } });
    fireEvent.click(screen.getByRole("button", { name: "Save" }));
    await waitFor(() => expect(edit).toHaveBeenCalledWith({ title: "My own title" }));
    expect(await screen.findByRole("heading", { name: "My own title" })).toBeTruthy();
  });

  it("shows the server's reason and keeps what was typed", async () => {
    const { InterviewError } = await import("../interview/interviewClient");
    const refuse = vi.fn(async () => {
      throw new InterviewError(
        "Contact details are shared only when you accept a checkout, so they can't go on your book.",
      );
    });
    show(client("shelf", { editChapter: refuse }));
    fireEvent.click(await screen.findByRole("button", { name: "Edit One" }));
    fireEvent.change(screen.getByLabelText("What it's about"), { target: { value: "Email me at a@b.com" } });
    fireEvent.click(screen.getByRole("button", { name: "Save" }));
    expect((await screen.findByRole("alert")).textContent).toMatch(/Contact details are shared only/);
    expect((screen.getByLabelText("What it's about") as HTMLTextAreaElement).value).toBe(
      "Email me at a@b.com",
    );
  });

  it("keeps an edit under way through a refresh", async () => {
    show(client("shelf"));
    fireEvent.click(await screen.findByRole("button", { name: "Edit One" }));
    fireEvent.change(screen.getByLabelText("Chapter title"), { target: { value: "Half typed" } });
    document.body.innerHTML = "";
    show(client("shelf"));
    expect(((await screen.findByLabelText("Chapter title")) as HTMLInputElement).value).toBe("Half typed");
  });

  it("never cuts a paste: past the limit it says so and waits", async () => {
    show(client("shelf"));
    fireEvent.click(await screen.findByRole("button", { name: "Edit the title and back cover" }));
    const long = "x".repeat(81);
    fireEvent.change(screen.getByLabelText("Title"), { target: { value: long } });
    expect(screen.getByText(/80 characters at most/)).toBeTruthy();
    expect((screen.getByRole("button", { name: "Save" }) as HTMLButtonElement).disabled).toBe(true);
    expect((screen.getByLabelText("Title") as HTMLInputElement).value).toBe(long);
  });

  it("refuses an empty field without sending it", async () => {
    const edit = vi.fn();
    show(client("shelf", { editBook: edit }));
    fireEvent.click(await screen.findByRole("button", { name: "Edit the title and back cover" }));
    fireEvent.change(screen.getByLabelText("Title"), { target: { value: "  " } });
    expect((screen.getByRole("button", { name: "Save" }) as HTMLButtonElement).disabled).toBe(true);
    expect(edit).not.toHaveBeenCalled();
  });

  it("takes the book off the shelf only after asking, with focus on keeping it", async () => {
    const down = vi.fn(async () => ({ ...book, status: "off_shelf" as const }));
    show(client("shelf", { takeOffShelf: down }));
    fireEvent.click(await screen.findByRole("button", { name: "Take off the shelf" }));
    expect(down).not.toHaveBeenCalled();
    expect(
      screen.getByText(/no new checkouts can start. Anything already arranged still happens/),
    ).toBeTruthy();
    await waitFor(() => expect(document.activeElement?.textContent).toBe("Keep it on the shelf"));
    fireEvent.click(screen.getByRole("button", { name: "Take it off" }));
    await waitFor(() => expect(down).toHaveBeenCalledTimes(1));
  });

  it("says plainly when the book is off the shelf, and puts it back", async () => {
    const back = vi.fn(async () => ({ ...book, status: "on_shelf" as const }));
    show(client("shelf", { myBook: async () => ({ ...book, status: "off_shelf" }), putBackOnShelf: back }));
    expect(await screen.findByText("Off the shelf")).toBeTruthy();
    expect(screen.getByText(/Other members can't find it or ask to check it out/)).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Take off the shelf" })).toBeNull();
    expect(document.querySelectorAll(".button-primary")).toHaveLength(1);
    fireEvent.click(screen.getByRole("button", { name: "Put back on the shelf" }));
    await waitFor(() => expect(back).toHaveBeenCalledTimes(1));
  });
});

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

  it.each([
    ["writingTitles", "I'm finding your titles."],
    ["writingBook", "I'm writing your book."],
  ] as const)("while %s, says so and has nothing to press", async (stage, words) => {
    show(client(stage, { myBook: async () => null }));
    expect(await screen.findByText(words)).toBeTruthy();
    expect(document.querySelectorAll(".button-primary")).toHaveLength(0);
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

  it("asks before undoing, says what it did, and gives the date", async () => {
    const undo = vi.fn(async () => undefined);
    let canUndo = true;
    undo.mockImplementation(async () => {
      canUndo = false;
    });
    show(
      client("shelf", {
        myBook: async () => ({ ...book, canUndo, changedAt: "2026-11-09T12:00:00Z" }),
        undoChanges: undo,
      }),
    );
    expect(await screen.findByText(/Your book was updated on Nov 9/)).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Undo these changes" }));
    expect(undo).not.toHaveBeenCalled();
    expect(screen.getByText("Undo these changes? Your book goes back to how it was.")).toBeTruthy();
    // A second Enter lands on the safe answer.
    await waitFor(() => expect(document.activeElement?.textContent).toBe("Keep them"));
    fireEvent.click(screen.getByRole("button", { name: "Undo" }));
    expect(await screen.findByText("Your book is back as it was.")).toBeTruthy();
    expect(undo).toHaveBeenCalledTimes(1);
  });

  it("a second press while undoing does nothing", async () => {
    let finish: () => void = () => {};
    const undo = vi.fn(() => new Promise<void>((resolve) => (finish = resolve)));
    show(client("shelf", { myBook: async () => ({ ...book, canUndo: true }), undoChanges: undo }));
    fireEvent.click(await screen.findByRole("button", { name: "Undo these changes" }));
    const press = screen.getByRole("button", { name: "Undo" });
    fireEvent.click(press);
    fireEvent.click(press);
    expect(undo).toHaveBeenCalledTimes(1);
    await act(async () => finish());
  });

  it("says when the last round changed nothing", async () => {
    show(client("shelf", { lastRound: async () => ({ empty: true }) }));
    expect(await screen.findByText(/Your last answers didn't change your book/)).toBeTruthy();
  });

  it("says which words were left out, and answering again starts from what was said", async () => {
    localStorage.clear();
    show(
      client("shelf", {
        readingQuestions: async () => reading,
        lastRound: async () => ({
          empty: true,
          droppedForNames: true,
          droppedWords: ["Geauga", "Fair"],
          readingQuestionId: "r1",
          readingAnswer: "They asked about the Geauga Fair.",
        }),
      }),
    );
    expect(await screen.findByText(/named someone or somewhere: Geauga, Fair/)).toBeTruthy();
    fireEvent.click(screen.getAllByRole("link", { name: "Answer" })[0] as HTMLElement);
    expect(localStorage.getItem("trove_interview_draft:anon:reading:r1")).toBe(
      "They asked about the Geauga Fair.",
    );
  });

  it("draws the next step once, with what it needs: a removal never flashes as changes", async () => {
    let finish: (value: { chapterId: string; title: string } | null) => void = () => {};
    show(
      client("changesWaiting", {
        openRemoval: () => new Promise((resolve) => (finish = resolve)),
      }),
    );
    await act(async () => {});
    expect(screen.queryByRole("link", { name: "Review the proposed changes" })).toBeNull();
    await act(async () => finish({ chapterId: "3", title: "Four" }));
    expect(await screen.findByRole("link", { name: "Finish removing" })).toBeTruthy();
  });

  it("shows words that couldn't be used, until the member says they've got them", async () => {
    localStorage.clear();
    leaveWords("anon", "Your last words weren't saved. Here they are:", "My careful words");
    show(client("shelf"));
    expect(await screen.findByText("My careful words")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "I've got them" }));
    // The page may still be loading its book; the words go once the update lands.
    await waitFor(() => expect(screen.queryByText("My careful words")).toBeNull());
    expect(localStorage.getItem("trove_interview_draft:leftover:anon")).toBeNull();
  });

  it("says the book stays as it is after declining everything", async () => {
    render(
      <AuthProvider>
        <MemoryRouter initialEntries={[{ pathname: "/my-book", state: { leftAsIs: true } }]}>
          <MyBookPage client={client("shelf")} />
        </MemoryRouter>
      </AuthProvider>,
    );
    expect(await screen.findByText("Your book stays as it is.")).toBeTruthy();
  });

  it("a removal left open offers to finish or keep the chapter", async () => {
    const cancel = vi.fn(async () => undefined);
    show(
      client("changesWaiting", {
        openRemoval: async () => ({ chapterId: "3", title: "Four" }),
        cancelRemoval: cancel,
      }),
    );
    expect(await screen.findByText("You started removing Four.")).toBeTruthy();
    expect(linkTo("Finish removing")).toBe("/my-book/remove/3?finish");
    expect(screen.queryByRole("link", { name: "Review the proposed changes" })).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Keep it" }));
    await waitFor(() => expect(cancel).toHaveBeenCalledTimes(1));
  });

  it("re-reads when an action is refused, and shows no error if the page was just out of date", async () => {
    const stages: BookStage[] = ["writeFailed", "changesWaiting"];
    show(
      client("writeFailed", {
        stage: async () => stages.shift() ?? "changesWaiting",
        retryWriting: async () => {
          throw new Error("refused");
        },
      }),
    );
    fireEvent.click(await screen.findByRole("button", { name: "Try again" }));
    expect(await screen.findByRole("link", { name: "Review the proposed changes" })).toBeTruthy();
    expect(screen.queryByRole("alert")).toBeNull();
  });

  it("shows the page while it loads, then starts the keyboard at the heading", async () => {
    show(client("shelf"));
    expect(screen.getByRole("heading", { name: "My book" })).toBeTruthy();
    const heading = await screen.findByRole("heading", { name: book.title });
    await waitFor(() => expect(document.activeElement).toBe(heading));
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

  it("after removing a spark, the keyboard goes on to the next one", async () => {
    const two = [...sparks, { id: "s2", chapterTitle: "The question I stopped asking" }];
    show(client("draft", { stage: async () => "none", myBook: async () => null, sparks: async () => two }));
    fireEvent.click(await screen.findByRole("button", { name: `Remove ${sparks[0]?.chapterTitle}` }));
    const next = await screen.findByRole("button", { name: "Remove The question I stopped asking" });
    await waitFor(() => expect(screen.queryByText(sparks[0]?.chapterTitle ?? "")).toBeNull());
    expect(next).toBeTruthy();
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
