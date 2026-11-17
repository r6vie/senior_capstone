import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { InviteSection } from "./InviteSection";

const api = vi.hoisted(() => ({ GET: vi.fn(), POST: vi.fn(), DELETE: vi.fn() }));
vi.mock("../../api/client", () => ({ api }));

const open = { id: "i1", created_at: "2026-11-17T10:00:00Z", expires_at: "2026-12-01T10:00:00Z" };

beforeEach(() => {
  vi.resetAllMocks();
  api.GET.mockResolvedValue({ data: [] });
});

describe("InviteSection", () => {
  it("lists open invites without their links", async () => {
    api.GET.mockResolvedValue({ data: [open] });
    render(<InviteSection />);
    expect(await screen.findByText(/Open until/)).toBeTruthy();
    expect(screen.queryByLabelText(/Your new link/)).toBeNull();
  });

  it("makes a link and shows it once, ready to copy", async () => {
    api.POST.mockResolvedValue({ data: { ...open, id: "i2", link: "http://x/sign-up?invite=tok" } });
    const writeText = vi.fn().mockResolvedValue(undefined);
    Object.assign(navigator, { clipboard: { writeText } });
    render(<InviteSection />);
    fireEvent.click(screen.getByRole("button", { name: "Make an invite link" }));
    const field = (await screen.findByLabelText(/Your new link/)) as HTMLInputElement;
    expect(field.value).toBe("http://x/sign-up?invite=tok");
    expect(await screen.findByText(/Open until/)).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: "Copy link" }));
    await waitFor(() => expect(screen.getByRole("button", { name: "Copied" })).toBeTruthy());
    expect(writeText).toHaveBeenCalledWith("http://x/sign-up?invite=tok");
  });

  it("says why when there are already five open", async () => {
    api.POST.mockResolvedValue({ error: { detail: "You have 5 open invites. Cancel one or wait." } });
    render(<InviteSection />);
    fireEvent.click(screen.getByRole("button", { name: "Make an invite link" }));
    expect((await screen.findByRole("alert")).textContent).toContain("5 open invites");
  });

  it("cancels an invite", async () => {
    api.GET.mockResolvedValue({ data: [open] });
    api.DELETE.mockResolvedValue({ response: { ok: true } });
    render(<InviteSection />);
    fireEvent.click(await screen.findByRole("button", { name: "Cancel" }));
    await waitFor(() => expect(screen.queryByText(/Open until/)).toBeNull());
    expect(api.DELETE).toHaveBeenCalledWith("/auth/invites/{invite_id}", {
      params: { path: { invite_id: "i1" } },
    });
  });
});
