import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { NeedsVerification } from "./AuthProvider";
import { ResetPasswordPage } from "./ResetPasswordPage";

const api = vi.hoisted(() => ({ POST: vi.fn() }));
const auth = vi.hoisted(() => ({ signIn: vi.fn() }));

vi.mock("../../api/client", () => ({ api }));
vi.mock("./AuthProvider", async (importOriginal) => ({
  ...(await importOriginal<typeof import("./AuthProvider")>()),
  useAuth: () => auth,
}));

function renderPage(url: string | { pathname: string; state: unknown } = "/reset-password") {
  render(
    <MemoryRouter initialEntries={[url]}>
      <Routes>
        <Route path="/reset-password" element={<ResetPasswordPage />} />
        <Route path="/" element={<p>Home</p>} />
        <Route path="/sign-in" element={<p>Sign in page</p>} />
        <Route path="/verify" element={<p>Verify page</p>} />
      </Routes>
    </MemoryRouter>,
  );
}

const ok = { response: { ok: true } };

function enterCodeAndPassword() {
  fireEvent.change(screen.getByLabelText("Code"), { target: { value: "123456" } });
  fireEvent.change(screen.getByLabelText("New password"), { target: { value: "a long new passphrase" } });
  fireEvent.click(screen.getByRole("button", { name: "Reset password" }));
}

beforeEach(() => vi.resetAllMocks());

describe("ResetPasswordPage", () => {
  it("asks for the email, then says the same thing whether or not there's an account", async () => {
    api.POST.mockResolvedValue(ok);
    renderPage({ pathname: "/reset-password", state: { email: "sam@case.edu" } });
    expect((screen.getByLabelText("Email") as HTMLInputElement).value).toBe("sam@case.edu");
    fireEvent.click(screen.getByRole("button", { name: "Send me a code" }));
    expect(await screen.findByText(/has a Trove account, we sent it a 6-digit code/)).toBeTruthy();
    expect(api.POST).toHaveBeenCalledWith("/auth/password/forgot", { body: { email: "sam@case.edu" } });
  });

  it("opens straight at the code from the email's link", () => {
    renderPage("/reset-password?email=sam%40case.edu");
    expect(screen.getByText("sam@case.edu")).toBeTruthy();
    expect(screen.getByText(/Enter the 6-digit code we emailed/)).toBeTruthy();
    expect(document.activeElement).toBe(screen.getByLabelText("Code"));
  });

  it("resets the password and signs in with it", async () => {
    api.POST.mockResolvedValue(ok);
    auth.signIn.mockResolvedValue(undefined);
    renderPage("/reset-password?email=sam%40case.edu");
    enterCodeAndPassword();
    expect(await screen.findByText("Home")).toBeTruthy();
    expect(api.POST).toHaveBeenCalledWith("/auth/password/reset", {
      body: { email: "sam@case.edu", code: "123456", new_password: "a long new passphrase" },
    });
    expect(auth.signIn).toHaveBeenCalledWith("sam@case.edu", "a long new passphrase");
  });

  it("sends an account still waiting for its sign-up code to confirm it", async () => {
    api.POST.mockResolvedValue(ok);
    auth.signIn.mockRejectedValue(new NeedsVerification());
    renderPage("/reset-password?email=sam%40case.edu");
    enterCodeAndPassword();
    expect(await screen.findByText("Verify page")).toBeTruthy();
  });

  it("says why a code is refused, and keeps what was typed", async () => {
    api.POST.mockResolvedValue({
      response: { ok: false },
      error: { detail: "That code isn't right, or it has expired. You can ask for a new one." },
    });
    renderPage("/reset-password?email=sam%40case.edu");
    enterCodeAndPassword();
    expect((await screen.findByRole("alert")).textContent).toContain("isn't right");
    expect((screen.getByLabelText("New password") as HTMLInputElement).value).toBe("a long new passphrase");
    expect(auth.signIn).not.toHaveBeenCalled();
  });

  it("sends a new code on request, and Start over goes back to the email", async () => {
    api.POST.mockResolvedValue(ok);
    renderPage("/reset-password?email=sam%40case.edu");
    fireEvent.click(screen.getByRole("button", { name: "Send me a new code" }));
    await waitFor(() => expect(screen.getByRole("status")).toBeTruthy());
    fireEvent.click(screen.getByRole("button", { name: "Start over" }));
    expect(screen.getByRole("button", { name: "Send me a code" })).toBeTruthy();
  });
});
