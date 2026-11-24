import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes, useLocation } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { AuthPage } from "./AuthPage";
import { NeedsVerification } from "./AuthProvider";

const api = vi.hoisted(() => ({ POST: vi.fn() }));
const auth = vi.hoisted(() => ({ signIn: vi.fn(), signUp: vi.fn() }));

vi.mock("../../api/client", () => ({ api }));
vi.mock("./AuthProvider", async (importOriginal) => ({
  ...(await importOriginal<typeof import("./AuthProvider")>()),
  useAuth: () => auth,
}));

function Where() {
  const location = useLocation();
  return (
    <p>
      at {location.pathname}
      {location.search}
    </p>
  );
}

function renderPage(mode: "sign-in" | "sign-up", url: string | { pathname: string; state: unknown } = "/") {
  render(
    <MemoryRouter initialEntries={[url]}>
      <Routes>
        <Route path="*" element={<AuthPage mode={mode} />} />
        <Route path="/verify" element={<Where />} />
        <Route path="/done" element={<Where />} />
        <Route path="/interview" element={<Where />} />
      </Routes>
    </MemoryRouter>,
  );
}

function fillIn(email: string) {
  fireEvent.change(screen.getByLabelText("First name"), { target: { value: "Sam" } });
  fireEvent.change(screen.getByLabelText("Last name"), { target: { value: "Lee" } });
  fireEvent.change(screen.getByLabelText(/^Email/), { target: { value: email } });
  fireEvent.change(screen.getByLabelText(/^Password/), { target: { value: "a long test passphrase" } });
  fireEvent.click(screen.getByRole("button", { name: "Create account" }));
}

beforeEach(() => vi.resetAllMocks());

function linkHref(name: string) {
  return screen.getByRole("link", { name }).getAttribute("href");
}

describe("AuthPage", () => {
  it("asks for a first and last name when signing up", () => {
    renderPage("sign-up");
    expect(screen.getByLabelText("First name")).toBeTruthy();
    expect(screen.getByLabelText("Last name")).toBeTruthy();
  });

  it("letters the name onto the book's cover as it's typed", () => {
    renderPage("sign-up");
    fireEvent.change(screen.getByLabelText("First name"), { target: { value: "Ingrid" } });
    fireEvent.change(screen.getByLabelText("Last name"), { target: { value: "Solberg" } });
    expect(document.querySelector(".auth-author")?.textContent).toBe("Ingrid Solberg");
  });

  it("shows the password on request", () => {
    renderPage("sign-in");
    const field = screen.getByLabelText(/^Password/) as HTMLInputElement;
    expect(field.type).toBe("password");
    const show = screen.getByRole("button", { name: "Show password" });
    fireEvent.click(show);
    expect(field.type).toBe("text");
    expect(show.getAttribute("aria-pressed")).toBe("true");
    fireEvent.click(show);
    expect(field.type).toBe("password");
  });

  it("offers a way back in for a forgotten password", () => {
    renderPage("sign-in");
    expect(linkHref("Forgot your password?")).toBe("/reset-password");
  });

  it("doesn't ask for a name when signing in", () => {
    renderPage("sign-in");
    expect(screen.queryByLabelText("First name")).toBeNull();
    expect(screen.queryByLabelText("Last name")).toBeNull();
  });

  it("tells students to use case.edu and alumni to ask for an invite", () => {
    renderPage("sign-up");
    expect(screen.getByText(/your case\.edu email/)).toBeTruthy();
    expect(screen.getByText(/ask a Trove member for an invite link/)).toBeTruthy();
  });

  it("sends a student to the code page after signing up", async () => {
    auth.signUp.mockResolvedValue("verify");
    renderPage("sign-up");
    fillIn("sam@case.edu");
    expect(await screen.findByText("at /verify?email=sam%40case.edu")).toBeTruthy();
    expect(auth.signUp).toHaveBeenCalledWith(
      "Sam",
      "Lee",
      "sam@case.edu",
      "a long test passphrase",
      undefined,
    );
  });

  it("says the session ended and goes back to the page the member was on", async () => {
    auth.signIn.mockResolvedValue(undefined);
    renderPage("sign-in", {
      pathname: "/sign-in",
      state: { from: { pathname: "/interview", search: "", hash: "" }, sessionEnded: true },
    });
    expect(screen.getByText("Your session ended. Sign in to pick up where you left off.")).toBeTruthy();
    expect(screen.queryByText("Your book is where you left it.")).toBeNull();
    fireEvent.change(screen.getByLabelText(/^Email/), { target: { value: "sam@case.edu" } });
    fireEvent.change(screen.getByLabelText(/^Password/), { target: { value: "a long test passphrase" } });
    fireEvent.click(screen.getByRole("button", { name: "Sign in" }));
    expect(await screen.findByText("at /interview")).toBeTruthy();
  });

  it("sends someone who signs in before confirming to the code page", async () => {
    auth.signIn.mockRejectedValue(new NeedsVerification());
    renderPage("sign-in");
    fireEvent.change(screen.getByLabelText(/^Email/), { target: { value: "sam@case.edu" } });
    fireEvent.change(screen.getByLabelText(/^Password/), { target: { value: "a long test passphrase" } });
    fireEvent.click(screen.getByRole("button", { name: "Sign in" }));
    expect(await screen.findByText("at /verify?email=sam%40case.edu")).toBeTruthy();
  });

  it("names who invited you and sends the invite along", async () => {
    api.POST.mockResolvedValue({ data: { inviter_name: "Maya Lee" } });
    auth.signUp.mockResolvedValue("signed-in");
    renderPage("sign-up", "/?invite=abc123");
    // The invite is a library card behind the book.
    expect(await screen.findByText("Maya Lee")).toBeTruthy();
    expect(screen.getByText("Invited by")).toBeTruthy();
    expect(screen.queryByText(/ask a Trove member/)).toBeNull();
    fillIn("ada@gmail.com");
    await screen.findByRole("button", { name: "Create account" });
    expect(auth.signUp).toHaveBeenCalledWith(
      "Sam",
      "Lee",
      "ada@gmail.com",
      "a long test passphrase",
      "abc123",
    );
  });

  it("explains a used or expired invite and still lets a student join", async () => {
    api.POST.mockResolvedValue({
      error: { detail: "This invite link has already been used or has expired." },
    });
    renderPage("sign-up", "/?invite=old");
    const alert = await screen.findByRole("alert");
    expect(alert.textContent).toContain("already been used or has expired");
    expect(alert.textContent).toContain("case.edu email");
    expect(screen.getByRole("button", { name: "Create account" })).toBeTruthy();
  });

  it("shows the reason when sign-up is refused", async () => {
    auth.signUp.mockRejectedValue(new Error("Sign up with your case.edu email, or use an invite link."));
    renderPage("sign-up");
    fillIn("ada@gmail.com");
    expect((await screen.findByRole("alert")).textContent).toContain("Sign up with your case.edu email");
  });
});
