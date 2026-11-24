import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { PastMeetsPage } from "./PastMeetsPage";

const api = vi.hoisted(() => ({ GET: vi.fn(), POST: vi.fn() }));
vi.mock("../../api/client", () => ({ api }));

const meet = (extra = {}) => ({
  checkout_id: "c1",
  book_title: "Small Town, Big Contracts",
  you_were: "reader",
  other_name: "Ana Diaz",
  other_book: { id: "b1", title: "Small Town, Big Contracts" },
  contact: { email: "ana@example.com", linkedin_url: "https://www.linkedin.com/in/ana", phone: null },
  met_on: "2026-11-17T15:00:00Z",
  did_you_meet: { can_answer: false, my_answer: "met" },
  ...extra,
});

function renderPage() {
  render(
    <MemoryRouter>
      <PastMeetsPage />
    </MemoryRouter>,
  );
}

beforeEach(() => {
  vi.resetAllMocks();
  api.GET.mockResolvedValue({ data: [] });
  api.POST.mockResolvedValue({ data: {} });
});

describe("PastMeetsPage", () => {
  it("shows an empty state that points to Checkouts", async () => {
    renderPage();
    expect(await screen.findByText("Nothing here yet")).toBeTruthy();
    expect(screen.getByRole("link", { name: "Go to Checkouts" }).getAttribute("href")).toBe("/checkouts");
    expect(api.GET).toHaveBeenCalledWith("/checkouts/past-meets");
  });

  it("shows who you met, their book, how to reach them and the conversation", async () => {
    api.GET.mockResolvedValue({ data: [meet()] });
    renderPage();
    expect(await screen.findByText("Ana Diaz")).toBeTruthy();
    expect(screen.getByText('Author of "Small Town, Big Contracts"')).toBeTruthy();
    expect(screen.getByText(/You checked out "Small Town, Big Contracts"\./)).toBeTruthy();
    expect(screen.getByRole("link", { name: "ana@example.com" }).getAttribute("href")).toBe(
      "mailto:ana@example.com",
    );
    expect(screen.getByRole("link", { name: "LinkedIn profile" })).toBeTruthy();
    expect(screen.getByRole("link", { name: "Your conversation" }).getAttribute("href")).toBe(
      "/checkouts/c1/messages",
    );
    expect(screen.queryByRole("group", { name: /Did you meet/ })).toBeNull();
    expect(screen.getByRole("img", { name: /^Met, / })).toBeTruthy();
  });

  it("words it for the author too", async () => {
    api.GET.mockResolvedValue({
      data: [
        meet({ you_were: "author", other_name: "Sam Lee", other_book: null, book_title: "Maya's book" }),
      ],
    });
    renderPage();
    expect(await screen.findByText(/Sam Lee checked out your book, "Maya's book"\./)).toBeTruthy();
    expect(screen.queryByText(/Author of/)).toBeNull();
  });

  it("lets the other person still answer, then reloads the list", async () => {
    api.GET.mockResolvedValueOnce({ data: [meet({ did_you_meet: { can_answer: true, my_answer: null } })] });
    api.GET.mockResolvedValue({ data: [] });
    renderPage();
    expect(await screen.findByText("Only you see your answer.")).toBeTruthy();
    // The copy is already back, so "Not yet" isn't offered.
    expect(screen.queryByRole("button", { name: "Not yet" })).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "No" }));
    await waitFor(() =>
      expect(api.POST).toHaveBeenCalledWith("/checkouts/{checkout_id}/met", {
        params: { path: { checkout_id: "c1" } },
        body: { answer: "no" },
      }),
    );
    expect(await screen.findByText("Nothing here yet")).toBeTruthy();
  });

  it("says when the connection drops, and lets you answer again", async () => {
    api.GET.mockResolvedValue({ data: [meet({ did_you_meet: { can_answer: true, my_answer: null } })] });
    api.POST.mockRejectedValue(new TypeError("Failed to fetch"));
    renderPage();
    fireEvent.click(await screen.findByRole("button", { name: "Yes, we met" }));
    expect(
      await screen.findByText("We couldn't send your answer. Check your connection and try again."),
    ).toBeTruthy();
    expect((screen.getByRole("button", { name: "Yes, we met" }) as HTMLButtonElement).disabled).toBe(false);
  });

  it("says when the list can't load because the connection dropped", async () => {
    api.GET.mockRejectedValue(new TypeError("Failed to fetch"));
    renderPage();
    expect(await screen.findByText("We couldn't load your past meets. Please refresh.")).toBeTruthy();
  });

  it("says when the list couldn't load", async () => {
    api.GET.mockResolvedValue({ error: { detail: "nope" } });
    renderPage();
    expect(await screen.findByText("We couldn't load your past meets. Please refresh.")).toBeTruthy();
  });
});
