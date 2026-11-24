import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { artFor, BOOK_ARTS } from "../../ui/art/bookArt";
import { AuthProvider } from "../auth/AuthProvider";
import { createFakeInterviewClient } from "../interview/fakeInterviewClient";
import type { BookStage, InterviewClient, MyBook } from "../interview/interviewClient";
import { leaveWords } from "../interview/LeftoverWords";
import { MyBookPage } from "./MyBookPage";

// The book's id, which chooses its cover art, comes from /books/me.
vi.mock("../discovery/bookPreload", () => ({
  loadOwnBook: async () => ({ id: "nora-book" }),
  forgetOwnBook: () => undefined,
}));

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

function client(stage: BookStage, overrides: Partial<InterviewClient> = {}): InterviewClient {
  return {
    ...createFakeInterviewClient("Nora", 0),
    stage: async () => stage,
    myBook: async () => (stage === "none" || stage === "interviewing" || stage === "titles" ? null : book),
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

const titleField = async () => (await screen.findByLabelText("Title")) as HTMLTextAreaElement;

describe("my book, open", () => {
  beforeEach(() => localStorage.clear());
  afterEach(() => vi.useRealTimers());

  it("is the open book: the title page carries the book's art, the contents end with the back cover", async () => {
    show(client("shelf"));
    expect((await titleField()).value).toBe(book.title);
    expect(screen.getByText(`by ${book.authorName}`)).toBeTruthy();
    const art = artFor("nora-book");
    expect(document.querySelector("img.mb-page-art")?.getAttribute("src")).toBe(art.page);
    const rows = [...document.querySelectorAll(".rv-toc li")].map(
      (row) => row.querySelector(".rv-toc-t")?.textContent,
    );
    expect(rows).toEqual(["One", "Two", "Three", "Four", "Back cover"]);
  });

  it("saves the title as it's typed, with no Save button", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const edit = vi.fn(async () => ({ ...book, title: "My own title" }));
    show(client("shelf", { editBook: edit }));
    fireEvent.change(await titleField(), { target: { value: "My own title" } });
    expect(screen.queryByRole("button", { name: "Save" })).toBeNull();
    await act(() => vi.advanceTimersByTimeAsync(1000));
    expect(edit).toHaveBeenCalledWith({ title: "My own title" });
  });

  it("opens a chapter with its title and text as fields, the contents beside it", async () => {
    const edit = vi.fn(async () => book);
    show(client("shelf", { editChapter: edit }));
    fireEvent.click(await screen.findByRole("button", { name: "Chapter 2" }));
    const title = screen.getByLabelText("Chapter 2 title") as HTMLTextAreaElement;
    expect(title.value).toBe("Two");
    expect((screen.getByLabelText("Chapter 2 text") as HTMLTextAreaElement).value).toBe("About Two.");
    expect(document.querySelector('.rv-toc button[aria-current="page"]')?.textContent).toContain("Two");
    fireEvent.change(title, { target: { value: "Two, again" } });
    fireEvent.blur(title);
    await waitFor(() => expect(edit).toHaveBeenCalledWith("1", { title: "Two, again" }));
  });

  it("opens the back cover as one field that saves itself", async () => {
    const edit = vi.fn(async () => book);
    show(client("shelf", { editBook: edit }));
    fireEvent.click(await screen.findByRole("button", { name: "Back cover" }));
    const field = screen.getByLabelText("Back cover") as HTMLTextAreaElement;
    expect(field.value).toBe(book.blurb);
    fireEvent.change(field, { target: { value: "Thirty machines, and counting." } });
    fireEvent.blur(field);
    await waitFor(() => expect(edit).toHaveBeenCalledWith({ blurb: "Thirty machines, and counting." }));
  });

  it("shows the server's reason when a save is refused, and keeps what was typed", async () => {
    const { InterviewError } = await import("../interview/interviewClient");
    const refuse = vi.fn(async () => {
      throw new InterviewError(
        "Contact details are shared only when you accept a checkout, so they can't go on your book.",
      );
    });
    show(client("shelf", { editChapter: refuse }));
    fireEvent.click(await screen.findByRole("button", { name: "Chapter 1" }));
    const text = screen.getByLabelText("Chapter 1 text") as HTMLTextAreaElement;
    fireEvent.change(text, { target: { value: "Email me at a@b.com" } });
    fireEvent.blur(text);
    expect((await screen.findByRole("alert")).textContent).toMatch(/Contact details are shared only/);
    expect(text.value).toBe("Email me at a@b.com");
  });

  it("removes a chapter after asking, keeping the back cover", async () => {
    const remove = vi.fn(async () => undefined);
    show(client("shelf", { removeFromShelf: remove }));
    fireEvent.click(await screen.findByRole("button", { name: "Chapter 4" }));
    fireEvent.click(screen.getByRole("button", { name: "Remove this chapter" }));
    expect(remove).not.toHaveBeenCalled();
    fireEvent.click(screen.getByRole("button", { name: "Remove Four" }));
    await waitFor(() => expect(remove).toHaveBeenCalledWith("3", null));
  });

  it("can't remove a chapter at three chapters, or from a draft", async () => {
    show(client("shelf", { myBook: async () => ({ ...book, chapters: book.chapters.slice(0, 3) }) }));
    fireEvent.click(await screen.findByRole("button", { name: "Chapter 1" }));
    expect(screen.queryByRole("button", { name: "Remove this chapter" })).toBeNull();
  });
});

describe("on the shelf", () => {
  it("is a switch: off takes the book down, on puts it back", async () => {
    const down = vi.fn(async () => ({ ...book, status: "off_shelf" as const }));
    const back = vi.fn(async () => ({ ...book, status: "on_shelf" as const }));
    show(client("shelf", { takeOffShelf: down, putBackOnShelf: back }));
    const toggle = await screen.findByRole("switch", { name: "On the shelf" });
    expect(toggle.getAttribute("aria-checked")).toBe("true");
    fireEvent.click(toggle);
    await waitFor(() => expect(toggle.getAttribute("aria-checked")).toBe("false"));
    expect(down).toHaveBeenCalledTimes(1);
    fireEvent.click(toggle);
    await waitFor(() => expect(toggle.getAttribute("aria-checked")).toBe("true"));
    expect(back).toHaveBeenCalledTimes(1);
  });

  it("isn't there for a draft, which isn't on the shelf yet", async () => {
    show(client("draft"));
    expect(await titleField()).toBeTruthy();
    expect(screen.queryByRole("switch")).toBeNull();
    expect(linkTo("Review your book")).toBe("/interview");
  });
});

describe("changing the design", () => {
  it("closes the book and shows the designs of its kind, the current one chosen", async () => {
    show(client("shelf"));
    fireEvent.click(await screen.findByRole("button", { name: "Change the design" }));
    expect(await screen.findByRole("heading", { name: "Choose a design" })).toBeTruthy();
    const art = artFor("nora-book");
    const kind = screen.getByRole("tab", { selected: true });
    expect(kind.textContent).toBe(art.category === "strata" ? "Mosaic" : "Watercolour");
    const options = screen
      .getAllByRole("button", { pressed: false })
      .filter((b) => b.classList.contains("mb-design-opt"));
    expect(options).toHaveLength(9);
    expect(screen.getByRole("button", { name: art.name, pressed: true })).toBeTruthy();
  });

  it("saves the chosen design to the book and shows it on the title page", async () => {
    const save = vi.fn(async (edit: { design?: string }) => ({ ...book, design: edit.design ?? null }));
    show(client("shelf", { editBook: save }));
    fireEvent.click(await screen.findByRole("button", { name: "Change the design" }));
    fireEvent.click(screen.getByRole("tab", { name: "Watercolour" }));
    const next = BOOK_ARTS.find((art) => art.category === "watercolor" && art.id !== artFor("nora-book").id);
    fireEvent.click(screen.getByRole("button", { name: next?.name }));
    fireEvent.click(screen.getByRole("button", { name: "Use this design" }));
    expect(await titleField()).toBeTruthy();
    expect(save).toHaveBeenCalledWith({ design: next?.id });
    expect(document.querySelector("img.mb-page-art")?.getAttribute("src")).toBe(next?.page);
  });

  it("goes back to the book as it was", async () => {
    show(client("shelf"));
    fireEvent.click(await screen.findByRole("button", { name: "Change the design" }));
    fireEvent.click(screen.getByRole("button", { name: "Back to my book" }));
    expect(await titleField()).toBeTruthy();
    expect(document.querySelector("img.mb-page-art")?.getAttribute("src")).toBe(artFor("nora-book").page);
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
    show(client("interviewing"));
    expect(await screen.findByText("Your interview is in progress.")).toBeTruthy();
    expect(screen.queryByText(/haven't started/)).toBeNull();
    expect(linkTo("Continue your interview")).toBe("/interview");
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

  it("on the shelf, the Librarian's block is the one way on", async () => {
    show(client("shelf"));
    expect(await screen.findByRole("region", { name: "The Librarian" })).toBeTruthy();
    expect(linkTo("Continue with the Librarian")).toBe("/interview?add");
    expect(document.querySelectorAll(".button-primary")).toHaveLength(1);
  });

  it("has no Undo, sparks, reading question or 'what you said'", async () => {
    show(client("shelf", { myBook: async () => ({ ...book, canUndo: true }) }));
    await titleField();
    expect(screen.queryByRole("button", { name: /Undo/ })).toBeNull();
    expect(screen.queryByText("For your next questions")).toBeNull();
    expect(screen.queryByText(/what you said/i)).toBeNull();
  });

  it("says when the last round changed nothing", async () => {
    show(client("shelf", { lastRound: async () => ({ empty: true }) }));
    expect(await screen.findByText(/Your last answers didn't change your book/)).toBeTruthy();
  });

  it("says which words were left out", async () => {
    show(
      client("shelf", {
        lastRound: async () => ({ empty: true, droppedForNames: true, droppedWords: ["Geauga", "Fair"] }),
      }),
    );
    expect(await screen.findByText(/named someone or somewhere: Geauga, Fair/)).toBeTruthy();
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
    await titleField();
    const heading = screen.getByRole("heading", { level: 1, name: "My book" });
    await waitFor(() => expect(document.activeElement).toBe(heading));
  });

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
    expect(await screen.findByRole("switch", { name: "On the shelf" })).toBeTruthy();
  });

  it("shows no performance numbers", async () => {
    show(client("shelf"));
    await titleField();
    const text = document.body.textContent ?? "";
    expect(text).not.toMatch(/cop(y|ies)|checkouts?\b|views?\b/i);
  });
});
