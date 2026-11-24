import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { api, session } from "../../api/client";
import type { MemberContext } from "../account/MemberContextFields";
import { AuthProvider } from "../auth/AuthProvider";
import { clearAllDrafts, draftKeyFor } from "./AnswerPanel";
import { answerOf, setAnswer } from "./answerField.testing";
import { createFakeInterviewClient, resetFakeInterview } from "./fakeInterviewClient";
import { InterviewPage } from "./InterviewPage";
import { type DraftBook, type InterviewClient, InterviewError, type InterviewState } from "./interviewClient";

function renderWith(
  client: InterviewClient,
  saveMemberContext: (context: MemberContext) => Promise<void> = async () => undefined,
) {
  render(
    <AuthProvider>
      <MemoryRouter>
        <InterviewPage client={client} saveMemberContext={saveMemberContext} />
      </MemoryRouter>
    </AuthProvider>,
  );
}

/** Reduced motion: the screens that type or rise show their end state at once. */
function stillMotion() {
  vi.stubGlobal("matchMedia", (query: string) => ({ matches: query === "(prefers-reduced-motion: reduce)" }));
}

/** The intro book (StartInterview) types its lines first; Skip goes straight to its questions and Start. */
async function skipIntro() {
  await screen.findByText("I’ll ask you one question at a time.");
  // With reduced motion the book opens on its end, with nothing to skip.
  const skip = screen.queryByRole("button", { name: "Skip" });
  if (skip) fireEvent.click(skip);
}

async function chooseStudent() {
  await skipIntro();
  fireEvent.click(await screen.findByLabelText("Current student"));
}

function fake() {
  return createFakeInterviewClient("Hana", 0);
}

function at(state: InterviewState | null, base = fake()): InterviewClient {
  return { ...base, current: async () => state };
}

const CHAPTER_TITLES = ["The morning after", "When the schedule slips", "Reading the chart", "Saying no"];

function bookWith(blurb: string | null, chapters = 4): DraftBook {
  return {
    title: "Finding the Step That Went Wrong",
    authorName: "Hana Okafor",
    blurb,
    chapters: CHAPTER_TITLES.slice(0, chapters).map((title, index) => ({
      id: String(index),
      title,
      summary: "What I check first.",
      quotes: [`I said this about ${title}.`],
    })),
  };
}

function reviewing(blurb: string | null = "I fix schedules that slipped.", chapters = 4): InterviewState {
  return { id: "me", stage: "reviewing", book: bookWith(blurb, chapters) };
}

const asking: InterviewState = {
  id: "me",
  stage: "asking",
  phase: "sweep",
  question: "What do people come to you for?",
  canFinish: false,
  hasAnswers: false,
  lastTopic: null,
};

function settled() {
  return waitFor(() => expect(document.querySelector('main[aria-busy="true"]')).toBeNull());
}

async function type(text: string) {
  setAnswer(await screen.findByLabelText("Your answer"), text);
}

async function answer(text: string) {
  await type(text);
  fireEvent.click(screen.getByRole("button", { name: "Send answer" }));
  await settled();
}

function stubHover(hover: boolean) {
  vi.stubGlobal("matchMedia", (query: string) => ({ matches: hover && query === "(hover: hover)" }));
}

describe("InterviewPage", () => {
  beforeEach(() => {
    resetFakeInterview();
    localStorage.clear();
  });
  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
    vi.useRealTimers();
    session.clear();
  });

  describe("the opening (StartOpen)", () => {
    function signIn() {
      session.set("token");
      vi.spyOn(api, "GET").mockResolvedValue({
        data: {
          id: "u1",
          first_name: "Ingrid",
          last_name: "Solberg",
          full_name: "Ingrid Solberg",
          email: "i@example.com",
          created_at: "2026-11-07T00:00:00Z",
        },
        response: new Response(null, { status: 200 }),
      } as never);
    }
    async function chooseAndStart() {
      await chooseStudent();
      fireEvent.click(screen.getByRole("button", { name: "Start the interview" }));
    }
    function stubMotion(reduce: boolean) {
      vi.stubGlobal("matchMedia", (query: string) => ({
        matches: query === "(hover: hover)" || (reduce && query === "(prefers-reduced-motion: reduce)"),
      }));
    }

    it("writes the hello in the notebook while the first question types in", async () => {
      signIn();
      stubMotion(false);
      renderWith(fake());
      await chooseAndStart();
      expect(await screen.findAllByText("hello, ingrid.")).not.toHaveLength(0);
      // Option A (Josef): the hello alone, no other welcome lines.
      expect(screen.queryByText("nobody sees any of it till you shelve it.")).toBeNull();
      // The question's place keeps two lines while its letters type in; readers get it whole at once.
      const question = document.querySelector(".iv-q");
      expect(question?.hasAttribute("data-typing")).toBe(true);
      expect(question?.querySelector(".iv-caret")).toBeTruthy();
      expect(screen.getByText(/spent years getting good at/)).toBeTruthy();
    });

    it("with reduced motion, shows the hello and the whole question at once", async () => {
      signIn();
      stubMotion(true);
      renderWith(fake());
      await chooseAndStart();
      expect(await screen.findAllByText("hello, ingrid.")).not.toHaveLength(0);
      const question = document.querySelector(".iv-q");
      expect(question?.hasAttribute("data-typing")).toBe(false);
      expect(question?.querySelector(".iv-caret")).toBeNull();
      expect(question?.textContent).toMatch(/spent years getting good at/);
      await waitFor(() => expect(document.activeElement).toBe(screen.getByLabelText("Your answer")));
    });

    it("leaves the keyboard where the member put it when the question finishes typing", async () => {
      signIn();
      stubMotion(false);
      renderWith(fake());
      await chooseAndStart();
      const skip = await screen.findByRole("button", { name: "Skip" });
      skip.focus();
      await waitFor(() => expect(document.querySelector(".iv-q")?.hasAttribute("data-typing")).toBe(false), {
        timeout: 6000,
      });
      expect(document.activeElement).toBe(skip);
    });

    it("skips the welcome when the member comes back to an interview under way", async () => {
      signIn();
      stubMotion(false);
      renderWith(at(asking));
      expect(await screen.findByText(asking.question)).toBeTruthy();
      expect(screen.queryByText("hello, ingrid.")).toBeNull();
      expect(document.querySelector(".iv-q")?.hasAttribute("data-typing")).toBe(false);
    });
  });

  describe("start", () => {
    it("opens as the empty book, then asks the member's place at CWRU before Start", async () => {
      const saveContext = vi.fn(async () => undefined);
      renderWith(fake(), saveContext);
      // The three lines are in the book from the start, for screen readers; the questions wait for them.
      expect(await screen.findByText("I’ll ask you one question at a time.")).toBeTruthy();
      expect(screen.getByText(/Nobody sees it until you put it on the shelf/)).toBeTruthy();
      expect(screen.queryByRole("button", { name: "Start the interview" })).toBeNull();
      await skipIntro();
      const start = await screen.findByRole("button", { name: "Start the interview" });
      expect((start as HTMLButtonElement).disabled).toBe(true);
      expect(screen.getByText("About 10 minutes")).toBeTruthy();
      // Josef dropped both helper lines.
      expect(screen.queryByText(/Choose both when both apply/)).toBeNull();
      expect(screen.queryByText(/not shown on your book/)).toBeNull();
      // The résumé is one optional line in the book, sent with Start.
      expect(screen.getByText("A résumé, if you like")).toBeTruthy();
      expect(screen.getByText("Drop a PDF here")).toBeTruthy();
      fireEvent.click(screen.getByLabelText("Current student"));
      fireEvent.click(screen.getByLabelText("Alumni"));
      fireEvent.click(screen.getByLabelText("I am a founder"));
      fireEvent.click(start);
      expect(await screen.findByText(/spent years getting good at/)).toBeTruthy();
      expect(saveContext).toHaveBeenCalledWith({
        affiliations: ["current_student", "alumni"],
        founder: true,
      });
    });

    it("clears a file's error when another is picked", async () => {
      renderWith(fake());
      await skipIntro();
      const picker = screen.getByLabelText("Choose a PDF");
      fireEvent.change(picker, { target: { files: [new File(["x"], "notes.txt", { type: "text/plain" })] } });
      expect(screen.getByText(/isn't a PDF/)).toBeTruthy();
      fireEvent.change(picker, {
        target: { files: [new File(["x"], "cv.pdf", { type: "application/pdf" })] },
      });
      expect(screen.queryByText(/isn't a PDF/)).toBeNull();
    });

    it("offers to start without a résumé that failed", async () => {
      const client = fake();
      const start = vi
        .spyOn(client, "start")
        .mockRejectedValueOnce(new InterviewError("That PDF couldn't be read."))
        .mockResolvedValue(asking);
      renderWith(client);
      await chooseStudent();
      const cv = new File(["x"], "cv.pdf", { type: "application/pdf" });
      fireEvent.change(screen.getByLabelText("Choose a PDF"), { target: { files: [cv] } });
      fireEvent.click(screen.getByRole("button", { name: "Start the interview" }));
      fireEvent.click(await screen.findByRole("button", { name: "Start without it" }));
      expect(await screen.findByText(asking.question)).toBeTruthy();
      expect(start).toHaveBeenLastCalledWith(null);
    });

    it("when the first question fails, offers only Try again, not a second Start", async () => {
      const client = fake();
      vi.spyOn(client, "start").mockRejectedValueOnce(
        new InterviewError("The Librarian couldn't answer just now. Please try again.", true),
      );
      const askAgain = vi.spyOn(client, "askAgain").mockResolvedValue(asking);
      renderWith(client);
      await chooseStudent();
      fireEvent.click(await screen.findByRole("button", { name: "Start the interview" }));
      const retry = await screen.findByRole("button", { name: "Try again" });
      expect(screen.queryByRole("button", { name: "Start the interview" })).toBeNull();
      expect(screen.queryByText("Choose a PDF")).toBeNull();
      fireEvent.click(retry);
      expect(await screen.findByText(asking.question)).toBeTruthy();
      expect(askAgain).toHaveBeenCalledTimes(1);
    });

    it("when an earlier Start already got through, opens that interview instead of refusing", async () => {
      const client = fake();
      vi.spyOn(client, "start").mockRejectedValueOnce(
        new InterviewError("You've already started your interview.", false, true),
      );
      vi.spyOn(client, "current").mockResolvedValueOnce(null).mockResolvedValue(asking);
      renderWith(client);
      await chooseStudent();
      fireEvent.click(await screen.findByRole("button", { name: "Start the interview" }));
      expect(await screen.findByText(asking.question)).toBeTruthy();
      expect(document.body.textContent).not.toMatch(/already started/);
    });

    it("turns down a résumé over the size limit in a plain sentence", async () => {
      renderWith(fake());
      await skipIntro();
      const big = new File([new Uint8Array(5 * 1024 * 1024 + 1)], "big.pdf", { type: "application/pdf" });
      fireEvent.change(screen.getByLabelText("Choose a PDF"), { target: { files: [big] } });
      expect(screen.getByText(/over 5 MB/)).toBeTruthy();
      expect(screen.queryByText("big.pdf")).toBeNull();
    });
  });

  describe("answering", () => {
    it("hides Speak where the browser has no speech recognition", async () => {
      renderWith(at(asking));
      await screen.findByLabelText("Your answer");
      expect(screen.queryByRole("button", { name: /Speak/ })).toBeNull();
    });

    it("offers the way out only after ten answers, without showing a count", async () => {
      const client = fake();
      await client.start(null);
      renderWith(client);
      await screen.findByLabelText("Your answer");
      for (let i = 0; i < 9; i++) await answer(`Answer ${i}`);
      expect(screen.queryByRole("button", { name: /I've said enough/ })).toBeNull();
      await answer("Answer 9");
      expect(await screen.findByRole("button", { name: /I've said enough/ })).toBeTruthy();
      expect(document.body.textContent).not.toMatch(/\b10\b/);
    }, 20_000);

    it("asks on a plain page: the question as words, the answer card, and when it's mostly done", async () => {
      renderWith(at({ ...asking, phase: "dig", canFinish: true, nearlyDone: true }));
      await screen.findByLabelText("Your answer");
      // LibDesktop: no band and no step names on the question screen.
      expect(screen.queryByRole("list", { name: "Where we are" })).toBeNull();
      expect(screen.getByText("Question")).toBeTruthy();
      expect(screen.getByRole("heading", { level: 1, name: asking.question })).toBeTruthy();
      expect(screen.getByText("Most of the way there.")).toBeTruthy();
    });

    it("finishing with words in the field says so and sends them, never drops them", async () => {
      const client = at({ ...asking, canFinish: true });
      const finish = vi.spyOn(client, "finish").mockResolvedValue(asking);
      renderWith(client);
      await screen.findByRole("button", { name: "I've said enough. Show me my book" });
      await type("My last thought");
      expect(screen.queryByRole("button", { name: "I've said enough. Show me my book" })).toBeNull();
      fireEvent.click(screen.getByRole("button", { name: "Send this, then show me my book" }));
      expect(finish).toHaveBeenCalledWith("me", "My last thought");
    });

    it("finishing with an empty field sends nothing", async () => {
      const client = at({ ...asking, canFinish: true });
      const finish = vi.spyOn(client, "finish").mockResolvedValue(asking);
      renderWith(client);
      fireEvent.click(await screen.findByRole("button", { name: "I've said enough. Show me my book" }));
      expect(finish).toHaveBeenCalledWith("me", undefined);
    });

    it("asks for more, with the question still there, when a draft found too little", async () => {
      renderWith(at({ ...asking, needsMore: true }));
      expect(await screen.findByText(/I need a little more before I can write your book/)).toBeTruthy();
      expect(screen.getByText(asking.question)).toBeTruthy();
      expect(screen.queryByRole("button", { name: "Try again" })).toBeNull();
    });

    it("doesn't say it's mostly done early on", async () => {
      renderWith(at(asking));
      await screen.findByLabelText("Your answer");
      expect(screen.queryByText("Most of the way there.")).toBeNull();
    });

    it("blocks an answer past the limit without losing it", async () => {
      renderWith(at(asking));
      const long = "x".repeat(5001);
      await type(long);
      expect(screen.getByText(/longer than I can take in one go/)).toBeTruthy();
      const send = screen.getByRole("button", { name: "Send answer" }) as HTMLButtonElement;
      expect(send.disabled).toBe(true);
      expect(answerOf(screen.getByLabelText("Your answer"))).toBe(long);
    });

    it("sends with Ctrl or Cmd and Enter", async () => {
      const client = at(asking);
      const send = vi.spyOn(client, "answer").mockResolvedValue(asking);
      renderWith(client);
      await type("My answer");
      fireEvent.keyDown(screen.getByLabelText("Your answer"), { key: "Enter", ctrlKey: true });
      expect(send).toHaveBeenCalledWith("me", "My answer");
    });

    it("shows Saved only after this draft is saved, not because of earlier answers", async () => {
      renderWith(at({ ...asking, hasAnswers: true }));
      await screen.findByLabelText("Your answer");
      expect(screen.queryByText("Saved")).toBeNull();
      await type("A draft");
      expect(await screen.findByText("Saved", {}, { timeout: 1500 })).toBeTruthy();
    });

    it("keeps each member's drafts apart, and sign-out can clear them", () => {
      const first = draftKeyFor("member-1", "Same question?");
      const second = draftKeyFor("member-2", "Same question?");
      expect(first).not.toBe(second);
      localStorage.setItem(first, "Private words");
      localStorage.setItem("something-else", "Stays");
      clearAllDrafts();
      expect(localStorage.getItem(first)).toBeNull();
      expect(localStorage.getItem("something-else")).toBe("Stays");
    });
  });

  describe("Skip", () => {
    it("goes to the next question with nothing marking it", async () => {
      const client = fake();
      await client.start(null);
      const send = vi.spyOn(client, "answer");
      renderWith(client);
      const first = (await screen.findByText(/spent years getting good at/)).textContent ?? "";
      fireEvent.click(screen.getByRole("button", { name: "Skip" }));
      await waitFor(() => expect(screen.queryByText(first)).toBeNull());
      await settled();
      expect(send).not.toHaveBeenCalled();
      expect(screen.getByRole("button", { name: "Skip" })).toBeTruthy();
      expect(document.body.textContent).not.toMatch(/skipped/i);
    });

    it("is there only while the field is empty, so it can't cost a typed answer", async () => {
      renderWith(at(asking));
      await type("Half a thought");
      expect(screen.queryByRole("button", { name: "Skip" })).toBeNull();
      await type("   ");
      expect(screen.getByRole("button", { name: "Skip" })).toBeTruthy();
    });

    it("doesn't count toward the way out", async () => {
      const client = fake();
      await client.start(null);
      renderWith(client);
      await screen.findByLabelText("Your answer");
      for (let i = 0; i < 10; i++) {
        fireEvent.click(screen.getByRole("button", { name: "Skip" }));
        await settled();
        await screen.findByRole("button", { name: "Skip" });
      }
      expect(screen.queryByRole("button", { name: /I've said enough/ })).toBeNull();
    });
  });

  describe("Shape", () => {
    it("is an ordinary question, with nothing played back to confirm", async () => {
      const question = "What do the two offers have in common, if anything?";
      const client = at({ ...asking, phase: "shape", question });
      const send = vi.spyOn(client, "answer");
      renderWith(client);
      await screen.findByText(question);
      expect(screen.queryByRole("button", { name: "Yes, that's me" })).toBeNull();
      await type("Both paid more than they taught");
      fireEvent.click(screen.getByRole("button", { name: "Send answer" }));
      expect(send).toHaveBeenCalledWith("me", "Both paid more than they taught");
    });
  });

  describe("when something fails", () => {
    const stuck = new InterviewError("The Librarian couldn't answer just now. Please try again.", true);

    it("after a saved answer, says so and asks for the next question instead of resending", async () => {
      const client = at(asking);
      const send = vi.spyOn(client, "answer").mockRejectedValueOnce(stuck);
      const askAgain = vi
        .spyOn(client, "askAgain")
        .mockResolvedValue({ ...asking, question: "The next question?" });
      renderWith(client);
      await type("An answer");
      fireEvent.click(screen.getByRole("button", { name: "Send answer" }));
      expect(
        await screen.findByText(/Your answer is saved. The next question didn't come through/),
      ).toBeTruthy();
      expect(screen.queryByRole("button", { name: "Send answer" })).toBeNull();
      expect(localStorage.getItem(draftKeyFor("anon", asking.question))).toBeNull();
      fireEvent.click(screen.getByRole("button", { name: "Ask me the next question" }));
      expect(await screen.findByText("The next question?")).toBeTruthy();
      expect(askAgain).toHaveBeenCalledTimes(1);
      expect(send).toHaveBeenCalledTimes(1);
    });

    const next = { ...asking, question: "The next question?" };
    const stale = (alreadySaved: boolean) =>
      new InterviewError("That isn't the question waiting.", false, true, alreadySaved);
    const moved = (error: InterviewError) => {
      const client = fake();
      vi.spyOn(client, "current").mockResolvedValueOnce(asking).mockResolvedValue(next);
      vi.spyOn(client, "answer").mockRejectedValueOnce(error);
      return client;
    };

    it("a refused resend moves to the current question and says the answer was saved", async () => {
      renderWith(moved(stale(true)));
      await type("My answer");
      fireEvent.click(screen.getByRole("button", { name: "Send answer" }));
      expect(await screen.findByText("The next question?")).toBeTruthy();
      expect(screen.getByText("Your answer was saved.")).toBeTruthy();
      expect(screen.queryByRole("alert")).toBeNull();
      expect(answerOf(screen.getByLabelText("Your answer"))).toBe("");
      expect(localStorage.getItem(draftKeyFor("anon", asking.question))).toBeNull();
    });

    it("answering a question another screen already answered keeps the words", async () => {
      renderWith(moved(stale(false)));
      await type("My careful answer");
      fireEvent.click(screen.getByRole("button", { name: "Send answer" }));
      expect(await screen.findByText("The next question?")).toBeTruthy();
      expect(screen.getByText(/already moved past that question on another screen/)).toBeTruthy();
      expect(screen.queryByText("Your answer was saved.")).toBeNull();
      expect(answerOf(screen.getByLabelText("Your answer"))).toBe("My careful answer");
      expect(localStorage.getItem(draftKeyFor("anon", next.question))).toBe("My careful answer");
    });

    it("finishing from a stale screen keeps the words and doesn't finish", async () => {
      const client = fake();
      const open = { ...asking, canFinish: true };
      vi.spyOn(client, "current")
        .mockResolvedValueOnce(open)
        .mockResolvedValue({ ...next, canFinish: true });
      vi.spyOn(client, "finish").mockRejectedValueOnce(stale(false));
      renderWith(client);
      await type("My last words");
      fireEvent.click(screen.getByRole("button", { name: "Send this, then show me my book" }));
      expect(await screen.findByText("The next question?")).toBeTruthy();
      expect(answerOf(screen.getByLabelText("Your answer"))).toBe("My last words");
    });

    const lost = () => new TypeError("Failed to fetch");

    it("after a lost reply there's no Try again: Send sends what's in the field now", async () => {
      const client = at(asking);
      const send = vi.spyOn(client, "answer").mockRejectedValueOnce(lost()).mockResolvedValue(next);
      renderWith(client);
      await type("Old words");
      fireEvent.click(screen.getByRole("button", { name: "Send answer" }));
      expect((await screen.findByRole("alert")).textContent).toMatch(/Your answer is still here/);
      expect(screen.queryByRole("button", { name: "Try again" })).toBeNull();
      await type("New better words");
      fireEvent.click(screen.getByRole("button", { name: "Send answer" }));
      expect(await screen.findByText("The next question?")).toBeTruthy();
      expect(send).toHaveBeenLastCalledWith("me", "New better words");
    });

    const arrivedAnyway = () => {
      const client = fake();
      vi.spyOn(client, "current").mockResolvedValueOnce(asking).mockResolvedValue(next);
      const send = vi.spyOn(client, "answer").mockRejectedValueOnce(lost());
      return { client, send };
    };

    it("if the first try did arrive and the words are the same, says it was saved", async () => {
      const { client, send } = arrivedAnyway();
      renderWith(client);
      await type("My answer");
      fireEvent.click(screen.getByRole("button", { name: "Send answer" }));
      await screen.findByRole("alert");
      fireEvent.click(screen.getByRole("button", { name: "Send answer" }));
      expect(await screen.findByText("The next question?")).toBeTruthy();
      expect(screen.getByText("Your answer was saved.")).toBeTruthy();
      expect(send).toHaveBeenCalledTimes(1);
    });

    it("if the first try did arrive and the words were edited, keeps the edit", async () => {
      const { client, send } = arrivedAnyway();
      renderWith(client);
      await type("Old words");
      fireEvent.click(screen.getByRole("button", { name: "Send answer" }));
      await screen.findByRole("alert");
      await type("New better words");
      fireEvent.click(screen.getByRole("button", { name: "Send answer" }));
      expect(await screen.findByText("The next question?")).toBeTruthy();
      expect(screen.getByText(/Your first version was saved. Your changes are still here/)).toBeTruthy();
      expect(answerOf(screen.getByLabelText("Your answer"))).toBe("New better words");
      expect(send).toHaveBeenCalledTimes(1);
    });

    it("a repeated question opens with an empty field, thanks to its id", async () => {
      const client = at({ ...asking, questionId: "q1" });
      vi.spyOn(client, "answer").mockResolvedValue({ ...asking, questionId: "q2" });
      renderWith(client);
      await type("My answer");
      fireEvent.click(screen.getByRole("button", { name: "Send answer" }));
      await waitFor(() => expect(answerOf(screen.getByLabelText("Your answer"))).toBe(""));
    });

    it("says so when asking for the next question fails again", async () => {
      const client = at(asking);
      vi.spyOn(client, "skip").mockRejectedValueOnce(stuck);
      vi.spyOn(client, "askAgain").mockRejectedValueOnce(stuck);
      renderWith(client);
      fireEvent.click(await screen.findByRole("button", { name: "Skip" }));
      fireEvent.click(await screen.findByRole("button", { name: "Ask me the next question" }));
      expect(await screen.findByText("That didn't work either. Try again in a moment.")).toBeTruthy();
    });

    it("a refused pick of a title shows what's true, not the refusal", async () => {
      const titles = [{ id: "0", title: "A title", why: "Because." }];
      const choosing: InterviewState = { id: "me", stage: "choosing", titles };
      const client = fake();
      vi.spyOn(client, "current").mockResolvedValueOnce(choosing).mockResolvedValue(reviewing());
      vi.spyOn(client, "chooseTitle").mockRejectedValueOnce(
        new InterviewError("You already have a book.", false, true),
      );
      stillMotion();
      renderWith(client);
      fireEvent.click(await screen.findByRole("button", { name: /A title/ }));
      fireEvent.click(screen.getByRole("button", { name: "Choose this title" }));
      expect(await screen.findByDisplayValue(bookWith(null).title)).toBeTruthy();
      expect(document.body.textContent).not.toMatch(/already have a book/);
    });

    it("a 409 where nothing has moved still says why", async () => {
      const client = at(reviewing("Blurb.", 4));
      vi.spyOn(client, "putOnShelf").mockRejectedValueOnce(
        new InterviewError("A book needs at least 3 chapters.", false, true),
      );
      renderWith(client);
      fireEvent.click(await screen.findByRole("button", { name: "Put it on the shelf" }));
      expect((await screen.findByRole("alert")).textContent).toMatch(/at least 3 chapters/);
    });

    it("waits and looks again when the book is being written after a refresh", async () => {
      vi.useFakeTimers({ shouldAdvanceTime: true });
      const client = fake();
      const drafting: InterviewState = { id: "me", stage: "drafting", about: "book" };
      vi.spyOn(client, "current").mockResolvedValueOnce(drafting).mockResolvedValue(reviewing());
      renderWith(client);
      expect(await screen.findByText("The Librarian is writing your book…")).toBeTruthy();
      await act(() => vi.advanceTimersByTimeAsync(5000));
      expect(screen.getByDisplayValue(bookWith(null).title)).toBeTruthy();
    });

    it("when writing failed twice, offers the same step again", async () => {
      const client = at({ id: "me", stage: "drafting", about: "book", failed: true, retryTitle: "2" });
      const retry = vi.spyOn(client, "retryDrafting").mockResolvedValue(reviewing());
      renderWith(client);
      expect(await screen.findByText("I couldn't finish writing your book.")).toBeTruthy();
      expect(screen.getByText("Everything you've said is saved.")).toBeTruthy();
      fireEvent.click(screen.getByRole("button", { name: "Try again" }));
      expect(retry).toHaveBeenCalledWith("book", "2");
      expect(await screen.findByDisplayValue(bookWith(null).title)).toBeTruthy();
    });

    it("not enough yet is never a dead end", async () => {
      const client = at({ id: "me", stage: "notEnough" });
      const ask = vi.spyOn(client, "askAgain").mockResolvedValue(asking);
      renderWith(client);
      expect(await screen.findByText(/I don't have enough yet for three chapters/)).toBeTruthy();
      fireEvent.click(screen.getByRole("button", { name: "Keep answering" }));
      expect(await screen.findByText(asking.question)).toBeTruthy();
      expect(ask).toHaveBeenCalledTimes(1);
    });

    it("after a skip, doesn't claim an answer was saved", async () => {
      const client = at(asking);
      vi.spyOn(client, "skip").mockRejectedValueOnce(stuck);
      renderWith(client);
      fireEvent.click(await screen.findByRole("button", { name: "Skip" }));
      expect(await screen.findByText(/The next question didn't come through/)).toBeTruthy();
      expect(screen.queryByText(/Your answer is saved/)).toBeNull();
    });

    it("on a developer's machine, says why the interview couldn't be loaded", async () => {
      vi.stubEnv("DEV", true);
      const client = fake();
      vi.spyOn(client, "current").mockRejectedValueOnce(
        new InterviewError("AI_MODE=scripted only runs on a trove_dev database, not alvisa."),
      );
      renderWith(client);
      expect(await screen.findByText(/only runs on a trove_dev database/)).toBeTruthy();
      vi.unstubAllEnvs();
    });

    it("never shows a member the reason behind a failed load", async () => {
      vi.stubEnv("DEV", false);
      const client = fake();
      vi.spyOn(client, "current").mockRejectedValueOnce(new InterviewError("database connection failed"));
      renderWith(client);
      expect(await screen.findByText(/Nothing you've said is lost/)).toBeTruthy();
      expect(document.body.textContent).not.toMatch(/database connection failed/);
      vi.unstubAllEnvs();
    });

    it("when the interview can't be loaded, offers Try again rather than the start screen", async () => {
      const client = fake();
      vi.spyOn(client, "current")
        .mockRejectedValueOnce(new TypeError("Failed to fetch"))
        .mockResolvedValueOnce(null);
      renderWith(client);
      expect(await screen.findByText(/Nothing you've said is lost/)).toBeTruthy();
      expect(document.body.textContent).not.toMatch(/Failed to fetch/);
      expect(screen.queryByRole("button", { name: "Start the interview" })).toBeNull();
      fireEvent.click(screen.getByRole("button", { name: "Try again" }));
      await skipIntro();
      expect(await screen.findByRole("button", { name: "Start the interview" })).toBeTruthy();
    });
  });

  describe("waiting", () => {
    it("shows no waiting line for a reply that comes back at once", async () => {
      vi.useFakeTimers({ shouldAdvanceTime: true });
      const client = at(asking);
      let reply: (state: InterviewState) => void = () => undefined;
      vi.spyOn(client, "skip").mockReturnValue(new Promise((done) => (reply = done)));
      renderWith(client);
      fireEvent.click(await screen.findByRole("button", { name: "Skip" }));
      await act(() => vi.advanceTimersByTimeAsync(200));
      expect(screen.queryByText("The Librarian is thinking…")).toBeNull();
      expect(screen.getByRole("heading", { name: asking.question })).toBeTruthy();
      await act(async () => reply({ ...asking, question: "The next question?" }));
      expect(await screen.findByText("The next question?")).toBeTruthy();
    });

    it("writes the Librarian's last look at the answer into the notebook while the next question comes", async () => {
      const client = at(asking);
      vi.spyOn(client, "skip").mockReturnValue(new Promise(() => {}));
      vi.spyOn(client, "finalNotes").mockResolvedValue({
        status: "done",
        silent: false,
        marks: { keep: [], add: [], revise: [], erase: [] },
        notebook: {
          keep: [],
          add: [
            {
              id: "n1",
              kind: "note",
              text: "reads the room before the chart",
              anchors: [],
              sourceTurns: [1],
              status: "open",
              struck: [],
            },
          ],
          revise: [],
          erase: [],
        },
      });
      renderWith(client);
      fireEvent.click(await screen.findByRole("button", { name: "Skip" }));
      expect(await screen.findAllByText("reads the room before the chart")).not.toHaveLength(0);
    });

    it("shows a returning member's notebook at rest, not written out again", async () => {
      const entry = {
        id: "n1",
        kind: "note" as const,
        text: "fixes what others won't touch",
        anchors: [],
        sourceTurns: [1],
        status: "open" as const,
        struck: [],
      };
      renderWith(at({ ...asking, librarian: { answered: 1, marks: [], silent: false, notebook: [entry] } }));
      expect(await screen.findAllByText(entry.text)).not.toHaveLength(0);
      expect(document.querySelector('.lib-en[data-life="writing"]')).toBeNull();
    });

    it("drops a late look at an answer once the next question is here", async () => {
      const client = at(asking);
      vi.spyOn(client, "skip").mockResolvedValue({ ...asking, question: "The next question?" });
      let land: (reply: Awaited<ReturnType<InterviewClient["finalNotes"]>>) => void = () => undefined;
      vi.spyOn(client, "finalNotes").mockReturnValue(new Promise((done) => (land = done)));
      renderWith(client);
      fireEvent.click(await screen.findByRole("button", { name: "Skip" }));
      expect(await screen.findByText("The next question?")).toBeTruthy();
      await act(async () =>
        land({
          status: "done",
          silent: false,
          marks: { keep: [], add: [], revise: [], erase: [] },
          notebook: {
            keep: [],
            add: [
              {
                id: "late",
                kind: "note",
                text: "too late",
                anchors: [],
                sourceTurns: [1],
                status: "open",
                struck: [],
              },
            ],
            revise: [],
            erase: [],
          },
        }),
      );
      expect(screen.queryByText("too late")).toBeNull();
    });

    it("keeps the note an answer brought when the next question arrives without it", async () => {
      const client = at({ ...asking, librarian: { answered: 0, marks: [], silent: false, notebook: [] } });
      let next: (state: InterviewState) => void = () => undefined;
      vi.spyOn(client, "skip").mockReturnValue(new Promise((done) => (next = done)));
      vi.spyOn(client, "finalNotes").mockResolvedValue({
        status: "done",
        silent: false,
        marks: { keep: [], add: [], revise: [], erase: [] },
        notebook: {
          keep: [],
          add: [
            {
              id: "ask1",
              kind: "saving",
              text: "ask: what came after the reseat?",
              anchors: [],
              sourceTurns: [1],
              status: "open",
              struck: [],
            },
          ],
          revise: [],
          erase: [],
        },
      });
      renderWith(client);
      fireEvent.click(await screen.findByRole("button", { name: "Skip" }));
      expect(await screen.findAllByText("ask: what came after the reseat?")).not.toHaveLength(0);
      await act(async () =>
        next({
          ...asking,
          question: "What came after the reseat?",
          librarian: { answered: 1, marks: [], silent: false, notebook: [] },
        }),
      );
      expect(await screen.findByText("What came after the reseat?")).toBeTruthy();
      await act(() => new Promise((done) => setTimeout(done, 700)));
      // Still there, now ticked: the question took it up.
      expect(screen.getAllByText(/ask: what came after the reseat\? \(ticked off/)).not.toHaveLength(0);
    });

    it("sends once on a double press", async () => {
      const client = at(asking);
      const skip = vi.spyOn(client, "skip").mockReturnValue(new Promise(() => {}));
      renderWith(client);
      const button = await screen.findByRole("button", { name: "Skip" });
      fireEvent.click(button);
      fireEvent.click(button);
      expect(skip).toHaveBeenCalledTimes(1);
    });

    it("says it's still working once a wait runs long", async () => {
      vi.useFakeTimers({ shouldAdvanceTime: true });
      const client = at(asking);
      vi.spyOn(client, "skip").mockReturnValue(new Promise(() => {}));
      renderWith(client);
      fireEvent.click(await screen.findByRole("button", { name: "Skip" }));
      await act(() => vi.advanceTimersByTimeAsync(9_000));
      expect(screen.queryByText(/Still working/)).toBeNull();
      await act(() => vi.advanceTimersByTimeAsync(2_000));
      expect(screen.getByText("Still working. Your answers are saved.")).toBeTruthy();
      await act(() => vi.advanceTimersByTimeAsync(110_000));
      expect(screen.getByRole("alert")).toBeTruthy();
      expect(screen.queryByText(/Still working/)).toBeNull();
    });
  });

  describe("focus", () => {
    const next = { ...asking, question: "The next question?" };

    it("puts a keyboard user straight into the field on a new question", async () => {
      stubHover(true);
      const client = at(asking);
      vi.spyOn(client, "skip").mockResolvedValue(next);
      renderWith(client);
      fireEvent.click(await screen.findByRole("button", { name: "Skip" }));
      await screen.findByText("The next question?");
      await waitFor(() => expect(document.activeElement).toBe(screen.getByLabelText("Your answer")));
    });

    it("on a phone, goes to the question rather than opening the keyboard over it", async () => {
      stubHover(false);
      const client = at(asking);
      vi.spyOn(client, "skip").mockResolvedValue(next);
      renderWith(client);
      fireEvent.click(await screen.findByRole("button", { name: "Skip" }));
      const question = await screen.findByText("The next question?");
      await waitFor(() => expect(document.activeElement).toBe(question));
    });

    it("starts a new question at the top of the page", async () => {
      const client = at(asking);
      vi.spyOn(client, "skip").mockResolvedValue(next);
      renderWith(client);
      fireEvent.click(await screen.findByRole("button", { name: "Skip" }));
      document.documentElement.scrollTop = 400;
      await screen.findByText("The next question?");
      await waitFor(() => expect(document.documentElement.scrollTop).toBe(0));
    });
  });

  describe("coming back", () => {
    const returning = { ...asking, hasAnswers: true, lastTopic: "the machining schedule" };

    it("welcomes a member back after time away, with one way forward", async () => {
      renderWith(at(returning));
      expect(await screen.findByText(/Welcome back. Last time you were telling me about/)).toBeTruthy();
      expect(screen.queryByText("Continue later")).toBeNull();
      fireEvent.click(screen.getByRole("button", { name: "Back to the question" }));
      expect(await screen.findByText(asking.question)).toBeTruthy();
    });

    it("doesn't on a refresh moments later", async () => {
      localStorage.setItem("trove_interview_seen:anon", String(Date.now() - 60_000));
      renderWith(at(returning));
      expect(await screen.findByText(asking.question)).toBeTruthy();
      expect(screen.queryByText(/Welcome back/)).toBeNull();
    });

    it("does once more than an hour has passed", async () => {
      localStorage.setItem("trove_interview_seen:anon", String(Date.now() - 2 * 60 * 60 * 1000));
      renderWith(at(returning));
      expect(await screen.findByText(/Welcome back/)).toBeTruthy();
    });
  });

  describe("the title reveal", () => {
    const titles = [{ id: "0", title: "Finding the Step That Went Wrong", why: "You fix schedules." }];

    it("signs the title choices with the member's full name", async () => {
      session.set("token");
      vi.spyOn(api, "GET").mockResolvedValue({
        data: {
          id: "u1",
          first_name: "Alexandra",
          last_name: "Okonkwo-Brennan",
          full_name: "Alexandra Okonkwo-Brennan",
          email: "a@example.com",
          created_at: "2026-11-07T00:00:00Z",
        },
        response: new Response(null, { status: 200 }),
      } as never);
      renderWith(at({ id: "me", stage: "choosing", titles }));
      expect(await screen.findAllByText("Alexandra Okonkwo-Brennan")).not.toHaveLength(0);
    });

    it("makes each white book the choice, with its reason", async () => {
      stillMotion();
      renderWith(at({ id: "me", stage: "choosing", titles }));
      expect(await screen.findByText("Here are three titles for your book.")).toBeTruthy();
      const book = screen.getByRole("button", { name: /Finding the Step That Went Wrong/ });
      expect(book.getAttribute("aria-pressed")).toBe("false");
      fireEvent.click(book);
      expect(book.getAttribute("aria-pressed")).toBe("true");
      expect(screen.getAllByText("Your pick")).not.toHaveLength(0);
      expect((screen.getByRole("button", { name: "Choose this title" }) as HTMLButtonElement).disabled).toBe(
        false,
      );
    });
  });

  describe("reviewing the book", () => {
    async function openChapter(index: number) {
      fireEvent.click(await screen.findByRole("button", { name: new RegExp(CHAPTER_TITLES[index] ?? "") }));
    }

    it("is the open book, every word a field, and promises only what it does", async () => {
      renderWith(at(reviewing()));
      expect(await screen.findByDisplayValue(bookWith(null).title)).toBeTruthy();
      // Josef removed Rewrite chapter and Rewrite back cover (2026-11-23).
      expect(screen.queryByRole("button", { name: /^Rewrite/ })).toBeNull();
      expect(screen.getByText(/Edit or remove anything that doesn't sound like you/)).toBeTruthy();
      for (const title of CHAPTER_TITLES)
        expect(screen.getByRole("button", { name: new RegExp(title) })).toBeTruthy();
      // The back cover is the last entry in the contents.
      expect(screen.getAllByRole("button", { name: "Back cover" })).not.toHaveLength(0);
    });

    it("saves the title as the member types it", async () => {
      const client = at(reviewing());
      const edit = vi.spyOn(client, "editBook").mockResolvedValue({
        ...bookWith("I fix schedules that slipped."),
        title: "My Own Title",
        canUndo: false,
        status: "draft",
      });
      renderWith(client);
      const title = await screen.findByLabelText("Title");
      fireEvent.focus(title);
      fireEvent.change(title, { target: { value: "My Own Title" } });
      fireEvent.blur(title);
      await waitFor(() => expect(edit).toHaveBeenCalledWith({ title: "My Own Title" }));
    });

    it("opens a chapter to its title and text, and saves its words", async () => {
      const client = at(reviewing());
      const edit = vi.spyOn(client, "editChapter").mockResolvedValue({
        ...bookWith("I fix schedules that slipped."),
        chapters: bookWith(null).chapters.map((chapter, index) =>
          index === 0 ? { ...chapter, summary: "In my own words." } : chapter,
        ),
        canUndo: false,
        status: "draft",
      });
      renderWith(client);
      await openChapter(0);
      const text = screen.getByLabelText("Chapter 1 text");
      fireEvent.focus(text);
      fireEvent.change(text, { target: { value: "In my own words." } });
      fireEvent.blur(text);
      await waitFor(() => expect(edit).toHaveBeenCalledWith("0", { summary: "In my own words." }));
      expect(screen.getByLabelText("Chapter 1 title")).toBeTruthy();
    });

    it("an edit refused while changes wait keeps the words and says why", async () => {
      const client = at(reviewing());
      vi.spyOn(client, "editBook").mockRejectedValue(
        new InterviewError("Decide on the waiting changes first.", false, true),
      );
      renderWith(client);
      const [backTab] = await screen.findAllByRole("button", { name: "Back cover" });
      if (backTab) fireEvent.click(backTab);
      const back = screen.getByLabelText("Back cover");
      fireEvent.focus(back);
      fireEvent.change(back, { target: { value: "My blurb" } });
      fireEvent.blur(back);
      expect((await screen.findByRole("alert")).textContent).toMatch(/waiting changes/);
      expect((screen.getByLabelText("Back cover") as HTMLTextAreaElement).value).toBe("My blurb");
    });

    it("says so when a removal rewrote the back cover", async () => {
      const client = at(reviewing("The old blurb."));
      vi.spyOn(client, "removeChapter").mockResolvedValue(reviewing("The shorter blurb.", 3));
      renderWith(client);
      const title = CHAPTER_TITLES[0] ?? "";
      await openChapter(0);
      fireEvent.click(screen.getByRole("button", { name: `Remove ${title}` }));
      fireEvent.click(screen.getByRole("button", { name: `Remove ${title}` }));
      expect(await screen.findByText("Back cover rewritten to match.")).toBeTruthy();
    });

    it("has no back cover entry for a book written before blurbs", async () => {
      renderWith(at(reviewing(null)));
      await screen.findByDisplayValue(bookWith(null).title);
      expect(screen.queryByRole("button", { name: "Back cover" })).toBeNull();
    });

    it("goes back to the other titles, warning that rewrites may change", async () => {
      const client = at(reviewing());
      vi.spyOn(client, "otherTitles").mockResolvedValue([
        { id: "0", title: bookWith(null).title, why: "The one you have." },
        { id: "1", title: "Another Title", why: "Because." },
      ]);
      const change = vi.spyOn(client, "changeTitle").mockResolvedValue({
        id: "me",
        stage: "reviewing",
        book: { ...bookWith(null), title: "Another Title" },
      });
      renderWith(client);
      fireEvent.click(await screen.findByRole("button", { name: "See the other titles" }));
      expect(await screen.findByText(/rewrites your chapters to fit the new title/)).toBeTruthy();
      expect(screen.queryByText("The one you have.")).toBeNull();
      fireEvent.click(screen.getByRole("button", { name: /Another Title/ }));
      expect(await screen.findByDisplayValue("Another Title")).toBeTruthy();
      expect(change).toHaveBeenCalledWith("me", "1");
    });

    it("asks on the chapter's page before removing it", async () => {
      const client = at(reviewing());
      const remove = vi.spyOn(client, "removeChapter").mockResolvedValue(reviewing("Blurb.", 3));
      renderWith(client);
      const title = CHAPTER_TITLES[0] ?? "";
      await openChapter(0);
      fireEvent.click(screen.getByRole("button", { name: `Remove ${title}` }));
      expect(remove).not.toHaveBeenCalled();
      expect(screen.getByText("Remove this chapter?")).toBeTruthy();
      fireEvent.click(screen.getByRole("button", { name: "Keep it" }));
      expect(screen.queryByText("Remove this chapter?")).toBeNull();
      fireEvent.click(screen.getByRole("button", { name: `Remove ${title}` }));
      fireEvent.click(screen.getByRole("button", { name: `Remove ${title}` }));
      await waitFor(() => expect(remove).toHaveBeenCalledWith("me", "0"));
    });

    it("at three chapters, a chapter's page has no Remove", async () => {
      renderWith(at(reviewing("Blurb.", 3)));
      await openChapter(0);
      expect(screen.queryByRole("button", { name: /^Remove / })).toBeNull();
    });
  });

  it("the done screen answers what happens now", async () => {
    const client = at(reviewing());
    vi.spyOn(client, "putOnShelf").mockResolvedValue({
      id: "me",
      stage: "done",
      book: bookWith("I fix schedules."),
    });
    renderWith(client);
    fireEvent.click(await screen.findByRole("button", { name: "Put it on the shelf" }));
    expect(await screen.findByText(/you say yes or no/)).toBeTruthy();
    expect(screen.getByText(/Your contact details stay private until you say yes/)).toBeTruthy();
    expect(screen.getByRole("link", { name: "See my book" }).getAttribute("href")).toBe("/my-book");
    expect(screen.getByRole("link", { name: "Go to the shelf" }).getAttribute("href")).toBe("/");
  });
});
