import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { AuthProvider } from "../auth/AuthProvider";
import { createFakeInterviewClient, resetFakeInterview } from "./fakeInterviewClient";
import { InterviewPage } from "./InterviewPage";
import { InterviewError } from "./interviewClient";

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
});
