import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { SettingsPage } from "./SettingsPage";

const api = vi.hoisted(() => ({ GET: vi.fn(), PUT: vi.fn(), DELETE: vi.fn() }));
const auth = vi.hoisted(() => ({
  user: { id: "u1", email: "maya@example.com", email_notifications: true },
  signOut: vi.fn(),
  refreshUser: vi.fn(),
}));

vi.mock("../../api/client", () => ({ api }));
vi.mock("../auth/AuthProvider", () => ({ useAuth: () => auth }));

const contact = { email: "maya@example.com", linkedin_url: null, phone: null };

beforeEach(() => {
  vi.resetAllMocks();
  auth.user = { id: "u1", email: "maya@example.com", email_notifications: true };
  api.GET.mockResolvedValue({ data: contact });
});

describe("SettingsPage", () => {
  it("shows the sign-in email as always shared and fills in saved details", async () => {
    api.GET.mockResolvedValue({
      data: { ...contact, phone: "216-555-0142", linkedin_url: "https://www.linkedin.com/in/maya" },
    });
    render(<SettingsPage />);
    expect(screen.getByText("Always shared")).toBeTruthy();
    expect(await screen.findByDisplayValue("216-555-0142")).toBeTruthy();
    expect(screen.getByDisplayValue("https://www.linkedin.com/in/maya")).toBeTruthy();
  });

  it("saves contact details, sending a cleared field as nothing", async () => {
    api.PUT.mockResolvedValue({ data: { ...contact, phone: "216-555-0142" } });
    render(<SettingsPage />);
    const save = screen.getByRole("button", { name: "Save contact details" });
    await waitFor(() => expect((save as HTMLButtonElement).disabled).toBe(false));

    fireEvent.change(screen.getByLabelText(/Phone/), { target: { value: "216-555-0142" } });
    fireEvent.click(save);

    expect(api.PUT).toHaveBeenCalledWith("/auth/me/contact", {
      body: { linkedin_url: null, phone: "216-555-0142" },
    });
    expect(await screen.findByText("Contact details saved.")).toBeTruthy();
  });

  it("shows the server's reason when a detail is rejected", async () => {
    api.PUT.mockResolvedValue({ error: { detail: "Enter a phone number with 7 to 15 digits." } });
    render(<SettingsPage />);
    const save = screen.getByRole("button", { name: "Save contact details" });
    await waitFor(() => expect((save as HTMLButtonElement).disabled).toBe(false));
    fireEvent.click(save);
    expect((await screen.findByRole("alert")).textContent).toContain("7 to 15 digits");
  });

  it("turns email notifications off", async () => {
    api.PUT.mockResolvedValue({ data: { email_notifications: false } });
    render(<SettingsPage />);
    fireEvent.click(screen.getByLabelText("Email me about checkouts and messages"));
    expect(api.PUT).toHaveBeenCalledWith("/auth/me/notifications", { body: { email_notifications: false } });
    expect(await screen.findByText("Email notifications are off.")).toBeTruthy();
    expect(auth.refreshUser).toHaveBeenCalled();
  });

  it("only offers to delete once the member has typed their email", async () => {
    api.DELETE.mockResolvedValue({ response: { ok: true } });
    render(<SettingsPage />);
    const remove = screen.getByRole("button", { name: "Delete my account" }) as HTMLButtonElement;
    expect(remove.disabled).toBe(true);

    fireEvent.change(screen.getByLabelText("Your email address"), { target: { value: "wrong@example.com" } });
    expect(remove.disabled).toBe(true);
    fireEvent.change(screen.getByLabelText("Your email address"), { target: { value: "" } });
    fireEvent.change(screen.getByLabelText("Your email address"), { target: { value: "Maya@Example.com" } });
    expect(remove.disabled).toBe(false);

    fireEvent.click(remove);
    expect(api.DELETE).toHaveBeenCalledWith("/auth/me", { body: { email: "Maya@Example.com" } });
    await waitFor(() => expect(auth.signOut).toHaveBeenCalled());
  });

  it("stays signed in when deleting fails", async () => {
    api.DELETE.mockResolvedValue({ response: { ok: false }, error: { detail: "Please sign in again." } });
    render(<SettingsPage />);
    fireEvent.change(screen.getByLabelText("Your email address"), { target: { value: "maya@example.com" } });
    fireEvent.click(screen.getByRole("button", { name: "Delete my account" }));
    expect((await screen.findByRole("alert")).textContent).toContain("Please sign in again.");
    expect(auth.signOut).not.toHaveBeenCalled();
  });
});
