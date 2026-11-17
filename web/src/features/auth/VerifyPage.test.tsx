import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { VerifyPage } from "./VerifyPage";

const api = vi.hoisted(() => ({ POST: vi.fn() }));
const auth = vi.hoisted(() => ({ verifyEmail: vi.fn() }));

vi.mock("../../api/client", () => ({ api }));
vi.mock("./AuthProvider", () => ({ useAuth: () => auth }));

function renderPage(url = "/verify?email=sam%40case.edu") {
  render(
    <MemoryRouter initialEntries={[url]}>
      <Routes>
        <Route path="/verify" element={<VerifyPage />} />
        <Route path="/" element={<p>Home</p>} />
      </Routes>
    </MemoryRouter>,
  );
}

beforeEach(() => vi.resetAllMocks());

describe("VerifyPage", () => {
  it("names the address the code went to and doesn't ask for it again", () => {
    renderPage();
    expect(screen.getByText("sam@case.edu")).toBeTruthy();
    expect(screen.queryByLabelText("Email")).toBeNull();
  });

  it("asks for the email when the page is opened without one", () => {
    renderPage("/verify");
    expect(screen.getByLabelText("Email")).toBeTruthy();
  });

  it("only allows Confirm once there are six digits", () => {
    renderPage();
    const confirm = screen.getByRole("button", { name: "Confirm" }) as HTMLButtonElement;
    expect(confirm.disabled).toBe(true);
    fireEvent.change(screen.getByLabelText("Code"), { target: { value: "12345" } });
    expect(confirm.disabled).toBe(true);
    fireEvent.change(screen.getByLabelText("Code"), { target: { value: "123456" } });
    expect(confirm.disabled).toBe(false);
  });

  it("confirms the code and goes home", async () => {
    auth.verifyEmail.mockResolvedValue(undefined);
    renderPage();
    fireEvent.change(screen.getByLabelText("Code"), { target: { value: "123456" } });
    fireEvent.click(screen.getByRole("button", { name: "Confirm" }));
    expect(await screen.findByText("Home")).toBeTruthy();
    expect(auth.verifyEmail).toHaveBeenCalledWith("sam@case.edu", "123456");
  });

  it("shows the reason when the code is wrong", async () => {
    auth.verifyEmail.mockRejectedValue(new Error("That code isn't right, or it has expired."));
    renderPage();
    fireEvent.change(screen.getByLabelText("Code"), { target: { value: "000000" } });
    fireEvent.click(screen.getByRole("button", { name: "Confirm" }));
    expect((await screen.findByRole("alert")).textContent).toContain("isn't right");
  });

  it("sends a new code on request", async () => {
    api.POST.mockResolvedValue({ response: { ok: true } });
    renderPage();
    fireEvent.click(screen.getByRole("button", { name: "Send me a new code" }));
    await waitFor(() => expect(screen.getByRole("status")).toBeTruthy());
    expect(api.POST).toHaveBeenCalledWith("/auth/verify/resend", { body: { email: "sam@case.edu" } });
  });

  it("shows the reason when asking for codes too often", async () => {
    api.POST.mockResolvedValue({
      response: { ok: false },
      error: { detail: "Too many attempts. Please try again later." },
    });
    renderPage();
    fireEvent.click(screen.getByRole("button", { name: "Send me a new code" }));
    expect((await screen.findByRole("alert")).textContent).toContain("Too many attempts");
  });
});
