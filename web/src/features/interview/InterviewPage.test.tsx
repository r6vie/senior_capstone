import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { api, session } from "../../api/client";
import { AuthProvider } from "../auth/AuthProvider";
import { clearAllDrafts, draftKeyFor } from "./AnswerPanel";
import { createFakeInterviewClient, resetFakeInterview } from "./fakeInterviewClient";
import { InterviewPage } from "./InterviewPage";
import {
  type DraftBook,
  type DraftChapter,
  type InterviewClient,
  InterviewError,
  type InterviewState,
  LostError,
} from "./interviewClient";

function renderWith(client: InterviewClient) {
  render(
    <AuthProvider>
      <MemoryRouter>
        <InterviewPage client={client} />
      </MemoryRouter>
    </AuthProvider>,
  );
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
  fireEvent.change(await screen.findByLabelText("Your answer"), { target: { value: text } });
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

  describe("start", () => {
    it("leads with Start and keeps the résumé behind one quiet line", async () => {
      renderWith(fake());
      const start = await screen.findByRole("button", { name: "Start the interview" });
      expect(screen.getByText(/Nobody sees it until you put it on the shelf/)).toBeTruthy();
      expect(screen.getByText(/About twenty minutes/)).toBeTruthy();
      expect(screen.queryByText(/A résumé, if you like/)).toBeNull();
      fireEvent.click(screen.getByRole("button", { name: /Have a résumé\?/ }));
      expect(screen.getByText(/A résumé, if you like/)).toBeTruthy();
      expect(screen.getByText(/its text is deleted when the interview ends/)).toBeTruthy();
      expect(document.body.textContent).not.toMatch(/never stored/);
      fireEvent.click(start);
      expect(await screen.findByText(/spent years getting good at/)).toBeTruthy();
    });

    it("clears a file's error when another is picked", async () => {
      renderWith(fake());
      fireEvent.click(await screen.findByRole("button", { name: /Have a résumé\?/ }));
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
      fireEvent.click(await screen.findByRole("button", { name: /Have a résumé\?/ }));
      const cv = new File(["x"], "cv.pdf", { type: "application/pdf" });
      fireEvent.change(screen.getByLabelText("Choose a PDF"), { target: { files: [cv] } });
      fireEvent.click(screen.getByRole("button", { name: "Start the interview" }));
      fireEvent.click(await screen.findByRole("button", { name: "Start without it" }));
      expect(await screen.findByText(asking.question)).toBeTruthy();
      expect(start).toHaveBeenLastCalledWith(null);
    });

    it("turns down a résumé over the size limit in a plain sentence", async () => {
      renderWith(fake());
      fireEvent.click(await screen.findByRole("button", { name: /Have a résumé\?/ }));
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

    it("names the steps in plain words, as a list, and says when it's mostly done", async () => {
      renderWith(at({ ...asking, phase: "dig", canFinish: true }));
      await screen.findByLabelText("Your answer");
      const steps = screen.getByRole("list", { name: "Where we are" });
      expect(steps.textContent).toBe("First lookDeeperCheck");
      expect(steps.querySelector('[aria-current="step"]')?.textContent).toBe("Deeper");
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
      expect((screen.getByLabelText("Your answer") as HTMLTextAreaElement).value).toBe(long);
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

    it("isn't offered on the Shape step", async () => {
      renderWith(at({ id: "me", stage: "shaping", phase: "shape", playback: "Is this you?" }));
      await screen.findByText("Is this you?");
      expect(screen.queryByRole("button", { name: "Skip" })).toBeNull();
    });
  });

  describe("Shape", () => {
    const shaping: InterviewState = { id: "me", stage: "shaping", phase: "shape", playback: "Is this you?" };

    it("with nothing typed, offers only Yes", async () => {
      renderWith(at(shaping));
      await screen.findByText("Is this you?");
      expect(screen.getByRole("button", { name: "Yes, that's me" })).toBeTruthy();
      expect(screen.queryByRole("button", { name: "Not quite" })).toBeNull();
      expect(screen.queryByRole("button", { name: "Send my correction" })).toBeNull();
    });

    it("with a correction typed, the red button sends it", async () => {
      const client = at(shaping);
      const correct = vi.spyOn(client, "correctShape").mockResolvedValue(shaping);
      const confirm = vi.spyOn(client, "confirmShape");
      renderWith(client);
      fireEvent.change(await screen.findByLabelText(/tell me what's different/), {
        target: { value: "It was three times" },
      });
      expect(screen.queryByRole("button", { name: "Yes, that's me" })).toBeNull();
      fireEvent.click(screen.getByRole("button", { name: "Send my correction" }));
      expect(correct).toHaveBeenCalledWith("me", "It was three times");
      expect(confirm).not.toHaveBeenCalled();
    });

    it("confirming past a typed correction has to be chosen by name", async () => {
      const client = at(shaping);
      const confirm = vi.spyOn(client, "confirmShape").mockResolvedValue(shaping);
      renderWith(client);
      fireEvent.change(await screen.findByLabelText(/tell me what's different/), {
        target: { value: "Actually, never mind" },
      });
      fireEvent.click(screen.getByRole("button", { name: "Yes, that's me, ignore this" }));
      expect(confirm).toHaveBeenCalledTimes(1);
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

    const conflict = new InterviewError("There's no question waiting for an answer.", false, true);

    it("a refused resend moves to the current question and says the answer was saved", async () => {
      const client = fake();
      const next = { ...asking, question: "The next question?" };
      vi.spyOn(client, "current").mockResolvedValueOnce(asking).mockResolvedValue(next);
      vi.spyOn(client, "answer").mockRejectedValueOnce(conflict);
      renderWith(client);
      await type("My answer");
      fireEvent.click(screen.getByRole("button", { name: "Send answer" }));
      expect(await screen.findByText("The next question?")).toBeTruthy();
      expect(screen.getByText("Your answer was saved.")).toBeTruthy();
      expect(screen.queryByRole("alert")).toBeNull();
      expect(localStorage.getItem(draftKeyFor("anon", asking.question))).toBeNull();
    });

    it("a refused pick of a title shows what's true, not the refusal", async () => {
      const titles = [{ id: "0", title: "A title", why: "Because." }];
      const choosing: InterviewState = { id: "me", stage: "choosing", titles };
      const client = fake();
      vi.spyOn(client, "current").mockResolvedValueOnce(choosing).mockResolvedValue(reviewing());
      vi.spyOn(client, "chooseTitle").mockRejectedValueOnce(
        new InterviewError("You already have a book.", false, true),
      );
      renderWith(client);
      fireEvent.click(await screen.findByRole("radio"));
      fireEvent.click(screen.getByRole("button", { name: "Choose this title" }));
      expect(await screen.findByRole("heading", { name: bookWith(null).title })).toBeTruthy();
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

    it("a proxy's 502 resends the answer on Try again", async () => {
      const client = at(asking);
      const send = vi
        .spyOn(client, "answer")
        .mockRejectedValueOnce(new LostError())
        .mockResolvedValue({ ...asking, question: "The next question?" });
      renderWith(client);
      await type("My answer");
      fireEvent.click(screen.getByRole("button", { name: "Send answer" }));
      expect((await screen.findByRole("alert")).textContent).toMatch(/Your answer is still here/);
      fireEvent.click(screen.getByRole("button", { name: "Try again" }));
      expect(await screen.findByText("The next question?")).toBeTruthy();
      expect(send).toHaveBeenCalledTimes(2);
    });

    it("waits and looks again when the book is being written after a refresh", async () => {
      vi.useFakeTimers({ shouldAdvanceTime: true });
      const client = fake();
      const drafting: InterviewState = { id: "me", stage: "drafting", about: "book" };
      vi.spyOn(client, "current").mockResolvedValueOnce(drafting).mockResolvedValue(reviewing());
      renderWith(client);
      expect(await screen.findByText("The Librarian is writing your book…")).toBeTruthy();
      await act(() => vi.advanceTimersByTimeAsync(5000));
      expect(screen.getByRole("heading", { name: bookWith(null).title })).toBeTruthy();
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
      expect(await screen.findByRole("button", { name: "Start the interview" })).toBeTruthy();
    });

    it("a lost connection keeps the answer and sends it again only if it never arrived", async () => {
      const client = at(asking);
      const send = vi
        .spyOn(client, "answer")
        .mockRejectedValueOnce(new TypeError("Failed to fetch"))
        .mockResolvedValue({ ...asking, question: "The next question?" });
      renderWith(client);
      await type("My answer");
      fireEvent.click(screen.getByRole("button", { name: "Send answer" }));
      expect((await screen.findByRole("alert")).textContent).toMatch(/Your answer is still here/);
      expect(document.body.textContent).not.toMatch(/Failed to fetch/);
      expect((screen.getByLabelText("Your answer") as HTMLTextAreaElement).value).toBe("My answer");
      fireEvent.click(screen.getByRole("button", { name: "Try again" }));
      expect(await screen.findByText("The next question?")).toBeTruthy();
      expect(send).toHaveBeenCalledTimes(2);
    });

    it("a lost connection doesn't send twice when the answer did arrive", async () => {
      const client = fake();
      const next = { ...asking, question: "The next question?" };
      vi.spyOn(client, "current").mockResolvedValueOnce(asking).mockResolvedValueOnce(next);
      const send = vi.spyOn(client, "answer").mockRejectedValueOnce(new TypeError("Failed to fetch"));
      renderWith(client);
      await type("My answer");
      fireEvent.click(screen.getByRole("button", { name: "Send answer" }));
      fireEvent.click(await screen.findByRole("button", { name: "Try again" }));
      expect(await screen.findByText("The next question?")).toBeTruthy();
      expect(send).toHaveBeenCalledTimes(1);
    });
  });

  describe("waiting", () => {
    it("says it's still working once a wait runs long", async () => {
      vi.useFakeTimers({ shouldAdvanceTime: true });
      const client = at(asking);
      vi.spyOn(client, "skip").mockReturnValue(new Promise(() => {}));
      renderWith(client);
      fireEvent.click(await screen.findByRole("button", { name: "Skip" }));
      await act(() => vi.advanceTimersByTimeAsync(14_000));
      expect(screen.queryByText(/Still working/)).toBeNull();
      await act(() => vi.advanceTimersByTimeAsync(2_000));
      expect(screen.getByText("Still working. Your answers are saved.")).toBeTruthy();
      await act(() => vi.advanceTimersByTimeAsync(105_000));
      expect(screen.getByRole("button", { name: "Try again" })).toBeTruthy();
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
      expect(screen.getByRole("link", { name: "Continue later" }).getAttribute("href")).toBe("/my-book");
      fireEvent.click(screen.getByRole("button", { name: "Continue" }));
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
      expect(await screen.findByText("Alexandra Okonkwo-Brennan")).toBeTruthy();
    });

    it("reads each title once to a screen reader, under a plain line", async () => {
      renderWith(at({ id: "me", stage: "choosing", titles }));
      expect(await screen.findByText("Here are three titles for your book.")).toBeTruthy();
      expect(document.querySelector(".iv-pick .book")?.getAttribute("aria-hidden")).toBe("true");
    });
  });

  describe("reviewing the book", () => {
    it("shows the book itself, and promises only what the screen can do", async () => {
      renderWith(at(reviewing()));
      await screen.findByRole("heading", { name: bookWith(null).title });
      expect(document.querySelector(".iv-booktitle .book")).toBeTruthy();
      expect(screen.getByText(/Rewrite or remove anything that doesn't sound like you/)).toBeTruthy();
      expect(document.body.textContent).not.toMatch(/Change anything/);
    });

    it("shows the blurb, and rewrites it on request", async () => {
      const client = at(reviewing());
      const rewrite = vi.spyOn(client, "rewriteBlurb").mockResolvedValue(reviewing("A better blurb."));
      renderWith(client);
      expect(await screen.findByText("I fix schedules that slipped.")).toBeTruthy();
      fireEvent.click(screen.getByRole("button", { name: "Rewrite the back cover" }));
      expect(await screen.findByText("A better blurb.")).toBeTruthy();
      expect(rewrite).toHaveBeenCalledTimes(1);
    });

    it("says so when a removal rewrote the back cover", async () => {
      const client = at(reviewing("The old blurb."));
      vi.spyOn(client, "removeChapter").mockResolvedValue(reviewing("The shorter blurb.", 3));
      renderWith(client);
      const title = CHAPTER_TITLES[0] ?? "";
      fireEvent.click(await screen.findByRole("button", { name: `Remove ${title}` }));
      fireEvent.click(screen.getByRole("button", { name: `Remove ${title}` }));
      expect(await screen.findByText("Back cover rewritten to match.")).toBeTruthy();
    });

    it("says so on the row when a rewrite came back no better", async () => {
      const client = at(reviewing());
      const same = reviewing() as Extract<InterviewState, { stage: "reviewing" }>;
      vi.spyOn(client, "rewriteChapter").mockResolvedValue({
        ...same,
        book: { ...same.book, rewriteUnchanged: true },
      });
      renderWith(client);
      fireEvent.click(await screen.findByRole("button", { name: `Rewrite ${CHAPTER_TITLES[0]}` }));
      expect(await screen.findByText(/I couldn't tell this one better from what you said/)).toBeTruthy();
      expect(screen.getAllByText(/I couldn't tell this one better/)).toHaveLength(1);
    });

    it("goes back to a chapter's last version", async () => {
      const state = reviewing() as Extract<InterviewState, { stage: "reviewing" }>;
      const [first, ...rest] = state.book.chapters;
      const client = at({
        ...state,
        book: { ...state.book, chapters: [{ ...(first as DraftChapter), hasPrevious: true }, ...rest] },
      });
      const restore = vi.spyOn(client, "restoreChapter").mockResolvedValue(reviewing());
      renderWith(client);
      const name = `Go back to the last version of ${CHAPTER_TITLES[0]}`;
      fireEvent.click(await screen.findByRole("button", { name }));
      expect(restore).toHaveBeenCalledWith("me", "0");
      expect(await screen.findByRole("heading", { name: bookWith(null).title })).toBeTruthy();
      expect(screen.queryByRole("button", { name })).toBeNull();
    });

    it("shows no blurb or its button for a book written before blurbs", async () => {
      renderWith(at(reviewing(null)));
      await screen.findByRole("heading", { name: bookWith(null).title });
      expect(document.querySelector(".iv-blurb")).toBeNull();
      expect(screen.queryByRole("button", { name: "Rewrite the back cover" })).toBeNull();
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
      await screen.findByRole("heading", { name: "Another Title" });
      expect(change).toHaveBeenCalledWith("me", "1");
    });

    it("shows the member their own words behind a chapter, on request", async () => {
      renderWith(at(reviewing()));
      expect(await screen.findByText(/Only you see them/)).toBeTruthy();
      const quote = `I said this about ${CHAPTER_TITLES[0]}.`;
      expect(screen.queryByText(quote)).toBeNull();
      fireEvent.click(screen.getByRole("button", { name: `Show what you said for ${CHAPTER_TITLES[0]}` }));
      expect(screen.getByText(quote)).toBeTruthy();
      fireEvent.click(screen.getByRole("button", { name: `Hide what you said for ${CHAPTER_TITLES[0]}` }));
      expect(screen.queryByText(quote)).toBeNull();
    });

    it("names the chapter on each row's buttons", async () => {
      renderWith(at(reviewing()));
      for (const title of CHAPTER_TITLES) {
        expect(await screen.findByRole("button", { name: `Rewrite ${title}` })).toBeTruthy();
        expect(screen.getByRole("button", { name: `Remove ${title}` })).toBeTruthy();
      }
    });

    it("asks in place before removing a chapter", async () => {
      const client = at(reviewing());
      const remove = vi.spyOn(client, "removeChapter").mockResolvedValue(reviewing("Blurb.", 3));
      renderWith(client);
      const title = CHAPTER_TITLES[0] ?? "";
      fireEvent.click(await screen.findByRole("button", { name: `Remove ${title}` }));
      expect(remove).not.toHaveBeenCalled();
      expect(screen.getByText("Remove this chapter?")).toBeTruthy();
      fireEvent.click(screen.getByRole("button", { name: "Keep it" }));
      expect(screen.queryByText("Remove this chapter?")).toBeNull();
      fireEvent.click(screen.getByRole("button", { name: `Remove ${title}` }));
      fireEvent.click(screen.getByRole("button", { name: `Remove ${title}` }));
      expect(remove).toHaveBeenCalledWith("me", "0");
    });

    it("at three chapters, hides Remove and says why", async () => {
      renderWith(at(reviewing("Blurb.", 3)));
      expect(await screen.findByText("A book keeps at least three chapters.")).toBeTruthy();
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
