import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { session } from "../../../api/client";
import { AuthProvider } from "../../auth/AuthProvider";
import { answerOf, setAnswer } from "../answerField.testing";
import { createFakeInterviewClient, resetFakeInterview } from "../fakeInterviewClient";
import { InterviewPage } from "../InterviewPage";
import type {
  InterviewClient,
  InterviewState,
  LibrarianView,
  NotebookEntry,
  NotesLook,
  NotesReply,
} from "../interviewClient";

const QUIET: NotesReply = {
  silent: false,
  marks: { keep: [], add: [], revise: [], erase: [] },
  notebook: { keep: [], add: [], revise: [], erase: [] },
};

function entry(
  id: string,
  kind: NotebookEntry["kind"],
  text: string,
  extra: Partial<NotebookEntry> = {},
): NotebookEntry {
  return { id, kind, text, anchors: [], sourceTurns: [1], status: "open", struck: [], ...extra };
}

function asking(librarian: LibrarianView, questionId = "q2"): InterviewState {
  return {
    id: "me",
    stage: "asking",
    phase: "sweep",
    question: "Tell me about a time something you built broke.",
    questionId,
    canFinish: false,
    hasAnswers: true,
    lastTopic: null,
    librarian,
  };
}

const SECOND: LibrarianView = { answered: 1, marks: [], silent: false, notebook: [] };

function client(overrides: Partial<InterviewClient> = {}, state: InterviewState = asking(SECOND)) {
  const base = createFakeInterviewClient("Hana", 0);
  return { ...base, current: async () => state, ...overrides } as InterviewClient;
}

function renderWith(interview: InterviewClient) {
  render(
    <AuthProvider>
      <MemoryRouter>
        <InterviewPage client={interview} />
      </MemoryRouter>
    </AuthProvider>,
  );
}

const field = () => screen.findByLabelText("Your answer");
const spoken = () => document.querySelector('[aria-live="polite"].iv-visually-hidden')?.textContent ?? "";

describe("the Librarian", () => {
  beforeEach(() => {
    resetFakeInterview();
    localStorage.clear();
    sessionStorage.clear();
  });
  afterEach(() => {
    vi.restoreAllMocks();
    vi.useRealTimers();
    session.clear();
  });

  it("marks the answer and writes in its notebook once a sentence is finished", async () => {
    const notes = vi.fn(
      async (_look: NotesLook): Promise<NotesReply> => ({
        silent: false,
        marks: {
          keep: [],
          add: [{ id: "m1", move: "strike", anchor: "leveraged", occurrence: 1, note: "used." }],
          revise: [],
          erase: [],
        },
        notebook: {
          keep: [],
          add: [
            entry("e1", "chapter", "ch. ? the night the build broke", {
              anchors: ["build"],
              sourceTurns: [2],
            }),
          ],
          revise: [],
          erase: [],
        },
      }),
    );
    renderWith(client({ notes }));
    setAnswer(await field(), "I leveraged my skills to fix the build.");
    await waitFor(() => expect(notes).toHaveBeenCalledTimes(1));
    expect(notes.mock.calls[0]?.[0]).toMatchObject({
      questionId: "q2",
      text: "I leveraged my skills to fix the build.",
    });
    await waitFor(() => expect(document.querySelector('.lib-mark[data-move="strike"]')).toBeTruthy());
    expect(spoken()).toContain("Librarian crossed out leveraged, wrote used.");
    expect(spoken()).toContain("ch. ? the night the build broke");
    // The handwriting is ink only; the words reach screen readers once, through the live region.
    expect(document.querySelector(".lib-ink")?.getAttribute("aria-hidden")).toBe("true");
    expect(screen.getByRole("region", { name: "The Librarian’s notebook" }).textContent).toContain(
      "ch. ? the night the build broke",
    );
    // Its line opens for the note; the member's words are untouched.
    expect(document.querySelector('span[data-mk="m1"]')?.textContent).toBe("leveraged");
    expect(answerOf(await field())).toBe("I leveraged my skills to fix the build.");
  });

  it("rubs a mark out, and the entry built on those words, when the words go", async () => {
    const notes = vi.fn(
      async (_look: NotesLook): Promise<NotesReply> => ({
        ...QUIET,
        marks: {
          keep: [],
          add: [{ id: "m1", move: "underline", anchor: "Everyone", occurrence: 1, note: "says who?" }],
          revise: [],
          erase: [],
        },
        notebook: {
          ...QUIET.notebook,
          add: [
            entry("e1", "saving", "ask: what did everyone say?", { anchors: ["Everyone"], sourceTurns: [2] }),
          ],
        },
      }),
    );
    renderWith(client({ notes }));
    setAnswer(await field(), "Everyone blamed the test runner.");
    await waitFor(() => expect(document.querySelector('.lib-mark[data-move="underline"]')).toBeTruthy());
    setAnswer(await field(), "I blamed the test runner.");
    await waitFor(() =>
      expect(document.querySelector('.lib-mark[data-move="underline"]')?.getAttribute("data-life")).toBe(
        "erasing",
      ),
    );
    expect(document.querySelector('.lib-en[data-kind="saving"]')?.getAttribute("data-life")).toBe("erasing");
    await waitFor(() => expect(document.querySelector(".lib-mark")).toBeNull());
  });

  it("goes quiet on a silent answer, before any call", async () => {
    const notes = vi.fn(async (_look: NotesLook) => QUIET);
    renderWith(client({ notes }));
    setAnswer(await field(), "My dad died the spring I started building robots.");
    await new Promise((resolve) => setTimeout(resolve, 1300));
    expect(notes).not.toHaveBeenCalled();
  });

  it("never looks per keystroke: one look after a pause", async () => {
    const notes = vi.fn(async (_look: NotesLook) => QUIET);
    renderWith(client({ notes }));
    const answer = await field();
    for (const text of ["The", "The build", "The build kept", "The build kept failing"])
      setAnswer(answer, text);
    expect(notes).not.toHaveBeenCalled();
    await waitFor(() => expect(notes).toHaveBeenCalledTimes(1), { timeout: 2000 });
    expect(notes.mock.calls[0]?.[0]).toMatchObject({ text: "The build kept failing" });
  });

  it("highlights a long paste at once, with no AI, and the member can still send", async () => {
    const answer = vi.fn(async () => asking(SECOND, "q3"));
    renderWith(client({ answer, notes: async () => QUIET }));
    const box = await field();
    const pasted = "Responsible for the end to end ownership of the deployment pipeline.";
    fireEvent.paste(box, { clipboardData: { getData: () => pasted } });
    await waitFor(() => expect(answerOf(box)).toBe(pasted));
    await waitFor(() => expect(document.querySelector('.lib-mark[data-move="highlight"]')).toBeTruthy());
    expect(spoken()).toContain("Librarian: in your own words?");
    fireEvent.click(screen.getByRole("button", { name: "Send answer" }));
    await waitFor(() => expect(answer).toHaveBeenCalled());
  });

  it("holds the first Send on contact details, and lets the second one through", async () => {
    const answer = vi.fn(async () => asking(SECOND, "q3"));
    renderWith(client({ answer, notes: async () => QUIET }));
    setAnswer(await field(), "Write to me at sam@case.edu about it");
    fireEvent.click(screen.getByRole("button", { name: "Send answer" }));
    expect(answer).not.toHaveBeenCalled();
    expect(spoken()).toContain("contact details come after a yes.");
    fireEvent.click(screen.getByRole("button", { name: "Send answer" }));
    await waitFor(() => expect(answer).toHaveBeenCalled());
  });

  it("writes an idle line after a long quiet on an empty answer, but never on the first question", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    renderWith(client({ notes: async () => QUIET }));
    await field();
    await act(async () => {
      vi.advanceTimersByTime(25_000);
    });
    expect(spoken()).toContain("start with what you’d say out loud.");
  });

  it("stays quiet when idle on the first question", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    renderWith(client({ notes: async () => QUIET }, asking({ ...SECOND, answered: 0 }, "q1")));
    await field();
    await act(async () => {
      vi.advanceTimersByTime(25_000);
    });
    expect(document.querySelector(".lib-margin")).toBeNull();
  });

  it("circles the entry the next question was built on, and ticks a saving", async () => {
    const before = [
      entry("c1", "chapter", "ch. ? the night the build broke"),
      entry("s1", "saving", "ask: what did the PI say?"),
    ];
    let state = asking({ ...SECOND, notebook: before });
    const answer = vi.fn(async () => {
      state = asking(
        {
          answered: 2,
          marks: [],
          silent: false,
          notebook: [before[0] as NotebookEntry, { ...(before[1] as NotebookEntry), status: "ticked" }],
        },
        "q3",
      );
      return state;
    });
    renderWith(client({ answer, notes: async () => QUIET, current: async () => state }));
    setAnswer(await field(), "It took eleven weeks");
    fireEvent.click(screen.getByRole("button", { name: "Send answer" }));
    await waitFor(() => expect(document.querySelector('.lib-en[data-status="ticked"]')).toBeTruthy());
    expect(document.querySelector('.lib-en[data-status="ticked"]')?.hasAttribute("data-marking")).toBe(true);
    expect(spoken()).toContain("Librarian ticked off: ask: what did the PI say?");
  });

  it("signs the finished book under its title", async () => {
    const reviewing: InterviewState = {
      id: "me",
      stage: "reviewing",
      signOff: "took some editing.",
      book: { title: "Eleven Weeks, One Stale Cache", authorName: "Hana", blurb: null, chapters: [] },
    };
    renderWith(client({}, reviewing));
    expect(await screen.findByText("Librarian: took some editing.")).toBeTruthy();
  });

  it("credits an edit: its old note struck in place, the credit written above", async () => {
    let look = 0;
    const notes = vi.fn(async (_look: NotesLook): Promise<NotesReply> => {
      look++;
      const mark = {
        id: "m1",
        move: "underline" as const,
        anchor: "a long time",
        occurrence: 1,
        note: "how long?",
      };
      return look === 1
        ? { ...QUIET, marks: { ...QUIET.marks, add: [mark] } }
        : {
            ...QUIET,
            marks: {
              ...QUIET.marks,
              revise: [{ ...mark, anchor: "11 weeks", note: "there it is.", struckNote: "how long?" }],
            },
          };
    });
    renderWith(client({ notes }));
    setAnswer(await field(), "It took a long time to find.");
    await waitFor(() => expect(spoken()).toContain("Librarian: how long?"));
    setAnswer(await field(), "It took 11 weeks to find.");
    await waitFor(
      () => expect(spoken()).toContain("Librarian crossed out its note how long?, wrote there it is."),
      {
        timeout: 4000,
      },
    );
    expect(document.querySelector('span[data-mk="m1"]')?.textContent).toBe("11 weeks");
  });

  it("draws the running bit with its count, and the back-cover line as a double underline", async () => {
    const notes = vi.fn(
      async (_look: NotesLook): Promise<NotesReply> => ({
        ...QUIET,
        marks: {
          ...QUIET.marks,
          add: [
            {
              id: "m1",
              move: "circle",
              anchor: "whiteboard",
              occurrence: 1,
              note: "the whiteboard has tenure.",
              count: 3,
            },
            { id: "m2", move: "back_cover", anchor: "Nobody reads the README.", occurrence: 1, note: null },
          ],
        },
      }),
    );
    renderWith(client({ notes }));
    setAnswer(await field(), "The whiteboard again. Nobody reads the README.");
    await waitFor(() => expect(spoken()).toContain("Librarian: ×3. the whiteboard has tenure."));
    expect(document.querySelector('.lib-mark[data-move="back_cover"]')).toBeTruthy();
  });

  it("settles a bet from an earlier answer: called and ticked, or lost and struck", async () => {
    const bet = entry("b1", "bet", "betting this ends in a spreadsheet.", { anchors: ["tests"] });
    const notes = vi.fn(
      async (_look: NotesLook): Promise<NotesReply> => ({
        ...QUIET,
        notebook: {
          ...QUIET.notebook,
          keep: ["b1"],
          revise: [{ ...bet, status: "called", outcomeNote: "called it." }],
        },
      }),
    );
    renderWith(client({ notes }, asking({ ...SECOND, notebook: [bet] })));
    setAnswer(await field(), "So I built a spreadsheet of every failure.");
    await waitFor(() => expect(document.querySelector('.lib-en[data-status="called"]')).toBeTruthy());
    expect(document.querySelector('.lib-en[data-status="called"] .lib-tick')).toBeTruthy();
    expect(spoken()).toContain("Librarian's bet, betting this ends in a spreadsheet.: called it.");
    expect(screen.getByRole("region", { name: "The Librarian’s notebook" }).textContent).toContain(
      "called it.",
    );
  });
});
