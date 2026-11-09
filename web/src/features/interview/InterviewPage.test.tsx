import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { api, session } from "../../api/client";
import { AuthProvider } from "../auth/AuthProvider";
import { createFakeInterviewClient, resetFakeInterview } from "./fakeInterviewClient";
import { InterviewPage } from "./InterviewPage";
import { type DraftBook, type InterviewClient, InterviewError } from "./interviewClient";

function renderWith(client: InterviewClient) {
  render(
    <AuthProvider>
      <MemoryRouter>
        <InterviewPage client={client} />
      </MemoryRouter>
    </AuthProvider>,
  );
}

function bookAt(stage: "reviewing" | "done", blurb: string | null): InterviewClient {
  const book: DraftBook = {
    title: "Finding the Step That Went Wrong",
    authorName: "Hana Okafor",
    blurb,
    chapters: [{ id: "1", title: "The morning after", summary: "What I check first." }],
  };
  return { ...createFakeInterviewClient("Hana", 0), current: async () => ({ id: "me", stage, book }) };
}

function renderPage() {
  render(
    <AuthProvider>
      <MemoryRouter>
        <InterviewPage client={createFakeInterviewClient("Hana", 0)} />
      </MemoryRouter>
    </AuthProvider>,
  );
}

async function answer(text: string) {
  fireEvent.change(await screen.findByLabelText("Your answer"), { target: { value: text } });
  fireEvent.click(screen.getByRole("button", { name: "Send answer" }));
  await waitFor(() => expect(document.querySelector('main[aria-busy="true"]')).toBeNull());
}

describe("InterviewPage", () => {
  beforeEach(() => {
    resetFakeInterview();
    localStorage.clear();
  });

  it("starts with the résumé optional and then asks one question", async () => {
    renderPage();
    expect(await screen.findByText(/A résumé, if you like/)).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Start the interview" }));
    expect(await screen.findByText(/spent years getting good at/)).toBeTruthy();
    expect(screen.queryByRole("button", { name: /I've said enough/ })).toBeNull();
  });

  it("hides Speak where the browser has no speech recognition", async () => {
    renderPage();
    fireEvent.click(await screen.findByRole("button", { name: "Start the interview" }));
    await screen.findByLabelText("Your answer");
    expect(screen.queryByRole("button", { name: /Speak/ })).toBeNull();
  });

  it("offers the way out only after ten answers, without showing a count", async () => {
    renderPage();
    fireEvent.click(await screen.findByRole("button", { name: "Start the interview" }));
    for (let i = 0; i < 9; i++) await answer(`Answer ${i}`);
    expect(screen.queryByRole("button", { name: /I've said enough/ })).toBeNull();
    await answer("Answer 9");
    expect(await screen.findByRole("button", { name: /I've said enough/ })).toBeTruthy();
    expect(document.body.textContent).not.toMatch(/\b10\b/);
  });

  it("after the Librarian fails, Try again asks for the question instead of resending the answer", async () => {
    const client = createFakeInterviewClient("Hana", 0);
    await client.start(null);
    const answer = vi
      .spyOn(client, "answer")
      .mockRejectedValueOnce(
        new InterviewError("The Librarian couldn't answer just now. Please try again.", true),
      );
    const askAgain = vi.spyOn(client, "askAgain");
    render(
      <AuthProvider>
        <MemoryRouter>
          <InterviewPage client={client} />
        </MemoryRouter>
      </AuthProvider>,
    );
    fireEvent.change(await screen.findByLabelText("Your answer"), { target: { value: "An answer" } });
    fireEvent.click(screen.getByRole("button", { name: "Send answer" }));
    fireEvent.click(await screen.findByRole("button", { name: "Try again" }));
    await waitFor(() => expect(askAgain).toHaveBeenCalledTimes(1));
    expect(answer).toHaveBeenCalledTimes(1);
    await waitFor(() => expect(screen.queryByRole("alert")).toBeNull());
  });

  it("welcomes a returning member back with Continue and Continue later", async () => {
    const client = createFakeInterviewClient("Hana", 0);
    const started = await client.start(null);
    await client.answer(started.id, "An answer");
    render(
      <AuthProvider>
        <MemoryRouter>
          <InterviewPage client={client} />
        </MemoryRouter>
      </AuthProvider>,
    );
    expect(await screen.findByText(/Welcome back. Last time you were telling me about/)).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Start that part again" })).toBeNull();
    expect(screen.getByRole("link", { name: "Continue later" }).getAttribute("href")).toBe("/");
    fireEvent.click(screen.getByRole("button", { name: "Continue" }));
    expect(await screen.findByText(/What do people come to you for/)).toBeTruthy();
  });

  it.each(["reviewing", "done"] as const)("shows the blurb under the title while %s", async (stage) => {
    renderWith(bookAt(stage, "I fix schedules that slipped."));
    expect(await screen.findByText("I fix schedules that slipped.")).toBeTruthy();
    expect(screen.getAllByText("Finding the Step That Went Wrong").length).toBeGreaterThan(0);
  });

  it("shows no blurb for a book written before blurbs", async () => {
    renderWith(bookAt("reviewing", null));
    await screen.findByRole("heading", { name: "Finding the Step That Went Wrong" });
    expect(document.querySelector(".iv-blurb")).toBeNull();
  });

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
    const titles = [{ id: "0", title: "Finding the Step That Went Wrong", why: "You fix schedules." }];
    renderWith({
      ...createFakeInterviewClient("Hana", 0),
      current: async () => ({ id: "me", stage: "choosing", titles }),
    });
    expect(await screen.findByText("Alexandra Okonkwo-Brennan")).toBeTruthy();
    session.clear();
    vi.restoreAllMocks();
  });

  it("Skip goes to the next question with nothing marking it, and drops the part-written answer", async () => {
    const client = createFakeInterviewClient("Hana", 0);
    const answerCall = vi.spyOn(client, "answer");
    renderWith(client);
    fireEvent.click(await screen.findByRole("button", { name: "Start the interview" }));
    const first = (await screen.findByText(/spent years getting good at/)).textContent;
    fireEvent.change(screen.getByLabelText("Your answer"), { target: { value: "Half a thought" } });
    fireEvent.click(screen.getByRole("button", { name: "Skip" }));
    await waitFor(() => expect(screen.queryByText(first ?? "")).toBeNull());
    expect(answerCall).not.toHaveBeenCalled();
    expect((screen.getByLabelText("Your answer") as HTMLTextAreaElement).value).toBe("");
    expect(screen.getByRole("button", { name: "Skip" })).toBeTruthy();
    expect(document.body.textContent).not.toMatch(/skipped/i);
  });

  it("doesn't count skips toward the way out", async () => {
    renderPage();
    fireEvent.click(await screen.findByRole("button", { name: "Start the interview" }));
    await screen.findByLabelText("Your answer");
    for (let i = 0; i < 10; i++) {
      fireEvent.click(screen.getByRole("button", { name: "Skip" }));
      await waitFor(() => expect(document.querySelector('main[aria-busy="true"]')).toBeNull());
      await screen.findByRole("button", { name: "Skip" });
    }
    expect(screen.queryByRole("button", { name: /I've said enough/ })).toBeNull();
  });

  it("offers no Skip on the Shape step", async () => {
    renderWith({
      ...createFakeInterviewClient("Hana", 0),
      current: async () => ({ id: "me", stage: "shaping", phase: "shape", playback: "Is this you?" }),
    });
    await screen.findByText("Is this you?");
    expect(screen.queryByRole("button", { name: "Skip" })).toBeNull();
  });

  it("when the interview can't be loaded, offers Try again rather than the start screen", async () => {
    const client = createFakeInterviewClient("Hana", 0);
    vi.spyOn(client, "current")
      .mockRejectedValueOnce(new TypeError("Failed to fetch"))
      .mockResolvedValueOnce(null);
    renderWith(client);
    expect(await screen.findByRole("alert")).toBeTruthy();
    expect(screen.getByRole("alert").textContent).toMatch(/can't be reached/);
    expect(document.body.textContent).not.toMatch(/Failed to fetch/);
    expect(screen.queryByRole("button", { name: "Start the interview" })).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));
    expect(await screen.findByRole("button", { name: "Start the interview" })).toBeTruthy();
  });

  it("keeps the draft when a send can't reach the server", async () => {
    const client = createFakeInterviewClient("Hana", 0);
    await client.start(null);
    vi.spyOn(client, "answer").mockRejectedValueOnce(new TypeError("Failed to fetch"));
    renderWith(client);
    fireEvent.change(await screen.findByLabelText("Your answer"), { target: { value: "My answer" } });
    fireEvent.click(screen.getByRole("button", { name: "Send answer" }));
    expect(await screen.findByRole("alert")).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Try again" })).toBeNull();
    expect((screen.getByLabelText("Your answer") as HTMLTextAreaElement).value).toBe("My answer");
  });

  it("returns keyboard focus to the member's side after the Librarian answers", async () => {
    const client = createFakeInterviewClient("Hana", 0);
    await client.start(null);
    renderWith(client);
    await screen.findByLabelText("Your answer");
    fireEvent.click(screen.getByRole("button", { name: "Skip" }));
    await waitFor(() => expect(document.activeElement).toBe(document.querySelector(".iv-act")));
  });
});
