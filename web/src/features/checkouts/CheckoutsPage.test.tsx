import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { CheckoutsPage } from "./CheckoutsPage";

const api = vi.hoisted(() => ({ GET: vi.fn(), POST: vi.fn() }));
vi.mock("../../api/client", () => ({ api }));

const waitingRequest = {
  id: "c1",
  book_id: "maya-book",
  book_title: "Maya's book",
  reader_name: "Sam Lee",
  reader_book: { id: "sam-book", title: "Learning to sell" },
  message: "I'd love to hear about your first year.",
  status: "waiting",
  created_at: "2026-11-15T10:00:00",
  expires_at: "2026-11-22T10:00:00",
};

const reading = (status: string, extra = {}) => ({
  id: `r-${status}`,
  book_id: "b1",
  book_title: "Small Town, Big Contracts",
  author_name: "Ana Diaz",
  message: "Hello",
  status,
  created_at: "2026-11-15T10:00:00",
  expires_at: null,
  ...extra,
});

function renderPage(state?: unknown) {
  render(
    <MemoryRouter initialEntries={[{ pathname: "/checkouts", state }]}>
      <CheckoutsPage />
    </MemoryRouter>,
  );
}

beforeEach(() => {
  vi.resetAllMocks();
  api.GET.mockResolvedValue({ data: { reading: [], lending: [] } });
  api.POST.mockResolvedValue({ data: {} });
});

describe("CheckoutsPage", () => {
  it("shows an empty state with one next step for each list", async () => {
    renderPage();
    expect(await screen.findByText("Nobody has asked to check out your book yet.")).toBeTruthy();
    expect(screen.getByRole("link", { name: "Browse the shelf" })).toBeTruthy();
  });

  it("lets the author accept a request", async () => {
    api.GET.mockResolvedValue({ data: { reading: [], lending: [waitingRequest] } });
    renderPage();
    expect(await screen.findByText("Sam Lee")).toBeTruthy();
    expect(screen.getByText('Author of "Learning to sell"')).toBeTruthy();
    expect(screen.getByText("I'd love to hear about your first year.")).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: "Accept" }));
    await waitFor(() =>
      expect(api.POST).toHaveBeenCalledWith("/checkouts/{checkout_id}/accept", {
        params: { path: { checkout_id: "c1" } },
      }),
    );
    expect(api.GET).toHaveBeenCalledTimes(2);
  });

  it("asks once before declining", async () => {
    api.GET.mockResolvedValue({ data: { reading: [], lending: [waitingRequest] } });
    renderPage();
    fireEvent.click(await screen.findByRole("button", { name: "Decline" }));
    expect(api.POST).not.toHaveBeenCalled();
    expect(screen.getByText(/Decline Sam Lee's checkout\?/)).toBeTruthy();

    fireEvent.click(screen.getByRole("button", { name: "Decline" }));
    await waitFor(() =>
      expect(api.POST).toHaveBeenCalledWith("/checkouts/{checkout_id}/decline", {
        params: { path: { checkout_id: "c1" } },
      }),
    );
  });

  it("shows the reader each checkout's state, and only a waiting one can be cancelled", async () => {
    api.GET.mockResolvedValue({
      data: {
        lending: [],
        reading: [reading("waiting", { expires_at: "2026-11-22T10:00:00" }), reading("unavailable")],
      },
    });
    renderPage();
    expect(await screen.findByText(/Waiting for an answer/)).toBeTruthy();
    expect(screen.getByText("This book isn't available right now.")).toBeTruthy();
    expect(screen.getAllByRole("button", { name: "Cancel checkout" })).toHaveLength(1);

    fireEvent.click(screen.getByRole("button", { name: "Cancel checkout" }));
    await waitFor(() =>
      expect(api.POST).toHaveBeenCalledWith("/checkouts/{checkout_id}/cancel", {
        params: { path: { checkout_id: "r-waiting" } },
      }),
    );
  });

  it("shows why an action failed", async () => {
    api.GET.mockResolvedValue({ data: { reading: [], lending: [waitingRequest] } });
    api.POST.mockResolvedValue({ error: { detail: "This checkout has already been answered or closed." } });
    renderPage();
    fireEvent.click(await screen.findByRole("button", { name: "Accept" }));
    expect((await screen.findByRole("alert")).textContent).toContain("already been answered");
  });

  it("confirms a new checkout, with the day it closes if unanswered", async () => {
    renderPage({ checkedOut: "Small Town, Big Contracts", answerBy: "2026-11-22T10:00:00Z" });
    const status = (await screen.findByRole("status")).textContent ?? "";
    expect(status).toContain('"Small Town, Big Contracts"');
    expect(status).toContain("November 22");
  });

  it("links an accepted checkout to arranging the reading, for both people", async () => {
    api.GET.mockResolvedValue({
      data: {
        lending: [{ ...waitingRequest, status: "accepted", expires_at: null }],
        reading: [reading("accepted")],
      },
    });
    renderPage();
    const links = await screen.findAllByRole("link", { name: "Arrange the reading" });
    expect(links.map((link) => link.getAttribute("href"))).toEqual([
      "/checkouts/c1/meeting",
      "/checkouts/r-accepted/meeting",
    ]);
  });
});
