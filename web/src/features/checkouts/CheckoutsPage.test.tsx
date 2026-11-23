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
  it("shows one empty state with a next step when there are no checkouts", async () => {
    renderPage();
    expect(await screen.findByText("No checkouts yet")).toBeTruthy();
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
    expect(screen.getByText("Ana Diaz · Not available")).toBeTruthy();
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

  it("shows contact details on both sides once the author has said yes", async () => {
    api.GET.mockResolvedValue({
      data: {
        lending: [
          {
            ...waitingRequest,
            status: "accepted",
            expires_at: null,
            reader_contact: { email: "sam@example.com", linkedin_url: null, phone: "216-555-0142" },
          },
        ],
        reading: [
          reading("accepted", {
            author_contact: {
              email: "ana@example.com",
              linkedin_url: "https://www.linkedin.com/in/ana-diaz",
              phone: null,
            },
          }),
        ],
      },
    });
    renderPage();
    expect(await screen.findByText("Reach Sam Lee")).toBeTruthy();
    expect(screen.getByRole("link", { name: "sam@example.com" }).getAttribute("href")).toBe(
      "mailto:sam@example.com",
    );
    expect(screen.getByRole("link", { name: "216-555-0142" }).getAttribute("href")).toBe("tel:2165550142");
    expect(screen.getByText("Reach Ana Diaz")).toBeTruthy();
    expect(screen.getByRole("link", { name: "LinkedIn profile" }).getAttribute("href")).toBe(
      "https://www.linkedin.com/in/ana-diaz",
    );
  });

  it("shows no contact details before a yes", async () => {
    api.GET.mockResolvedValue({ data: { reading: [reading("waiting")], lending: [waitingRequest] } });
    renderPage();
    expect(await screen.findByText("Sam Lee")).toBeTruthy();
    expect(screen.queryByText(/^Reach /)).toBeNull();
  });

  it("confirms a new checkout, with the day it closes if unanswered", async () => {
    renderPage({ checkedOut: "Small Town, Big Contracts", answerBy: "2026-11-22T10:00:00Z" });
    const status = (await screen.findByRole("status")).textContent ?? "";
    expect(status).toContain('"Small Town, Big Contracts"');
    expect(status).toContain("November 22");
  });

  it("links an accepted checkout to its messages, with a private label when something is unread", async () => {
    api.GET.mockResolvedValue({
      data: {
        lending: [{ ...waitingRequest, status: "accepted", expires_at: null, new_messages: true }],
        reading: [reading("accepted", { new_messages: false })],
      },
    });
    renderPage();
    const links = await screen.findAllByRole("link", { name: "Messages" });
    expect(links.map((link) => link.getAttribute("href"))).toEqual([
      "/checkouts/c1/messages",
      "/checkouts/r-accepted/messages",
    ]);
    expect(screen.getAllByText("New message")).toHaveLength(1);
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

  it('asks "Did you meet?" only once it\'s due', async () => {
    api.GET.mockResolvedValue({
      data: {
        lending: [{ ...waitingRequest, status: "accepted", expires_at: null, did_you_meet: null }],
        reading: [reading("accepted", { did_you_meet: { can_answer: true, my_answer: null } })],
      },
    });
    renderPage();
    expect(await screen.findByRole("group", { name: "Did you meet Ana Diaz?" })).toBeTruthy();
    expect(screen.queryByRole("group", { name: "Did you meet Sam Lee?" })).toBeNull();
    expect(screen.getByText("Only you see your answer. Yes or No returns the copy.")).toBeTruthy();
  });

  it("sends a Yes, says the checkout is closed, and shows it as returned", async () => {
    api.GET.mockResolvedValueOnce({
      data: {
        lending: [],
        reading: [reading("accepted", { did_you_meet: { can_answer: true, my_answer: null } })],
      },
    });
    api.GET.mockResolvedValue({
      data: {
        lending: [],
        reading: [
          reading("returned", {
            id: "r-accepted",
            author_contact: { email: "ana@example.com", linkedin_url: null, phone: null },
            did_you_meet: { can_answer: false, my_answer: "met" },
          }),
        ],
      },
    });
    renderPage();
    fireEvent.click(await screen.findByRole("button", { name: "Yes, we met" }));
    await waitFor(() =>
      expect(api.POST).toHaveBeenCalledWith("/checkouts/{checkout_id}/met", {
        params: { path: { checkout_id: "r-accepted" } },
        body: { answer: "met" },
      }),
    );
    expect(await screen.findByText(/Your checkout with Ana Diaz is closed/)).toBeTruthy();
    // It moves to Earlier, as one line.
    expect(screen.getByText("Ana Diaz · Returned")).toBeTruthy();
    expect(screen.getByRole("link", { name: "See Ana Diaz in Past meets" }).getAttribute("href")).toBe(
      "/past-meets",
    );
    expect(screen.queryByRole("group", { name: /Did you meet/ })).toBeNull();
    // Contacts and the conversation live on Past meets once it's returned.
    expect(screen.queryByText("ana@example.com")).toBeNull();
  });

  it("keeps the question after Not yet, and doesn't say it's closed", async () => {
    api.GET.mockResolvedValueOnce({
      data: {
        lending: [
          {
            ...waitingRequest,
            status: "accepted",
            expires_at: null,
            did_you_meet: { can_answer: true, my_answer: null },
          },
        ],
        reading: [],
      },
    });
    api.GET.mockResolvedValue({
      data: {
        lending: [
          {
            ...waitingRequest,
            status: "accepted",
            expires_at: null,
            did_you_meet: { can_answer: true, my_answer: "not_yet" },
          },
        ],
        reading: [],
      },
    });
    renderPage();
    fireEvent.click(await screen.findByRole("button", { name: "Not yet" }));
    expect(await screen.findByText("You said not yet. Answer again once you've met.")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Not yet" }).getAttribute("aria-pressed")).toBe("true");
    expect(screen.queryByText(/is closed/)).toBeNull();
  });

  it("shows a returned checkout with no Past meet plainly", async () => {
    api.GET.mockResolvedValue({
      data: {
        lending: [],
        reading: [reading("returned", { did_you_meet: { can_answer: false, my_answer: "no" } })],
      },
    });
    renderPage();
    expect(await screen.findByText("Ana Diaz · Returned")).toBeTruthy();
    expect(screen.queryByRole("link", { name: /Past meets/ })).toBeNull();
  });

  it("shows why an answer failed, and keeps the question", async () => {
    api.GET.mockResolvedValue({
      data: {
        lending: [],
        reading: [reading("accepted", { did_you_meet: { can_answer: true, my_answer: null } })],
      },
    });
    api.POST.mockResolvedValue({ error: { detail: "It's too early to answer that." } });
    renderPage();
    fireEvent.click(await screen.findByRole("button", { name: "No" }));
    expect(await screen.findByText("It's too early to answer that.")).toBeTruthy();
    expect(screen.getByRole("button", { name: "No" })).toBeTruthy();
  });

  it("groups checkouts by what they need from you", async () => {
    api.GET.mockResolvedValue({
      data: {
        lending: [waitingRequest],
        reading: [
          reading("waiting", { book_title: "The Night Shift Founder", author_name: "Priya Rao" }),
          reading("cancelled", { book_title: "Moving Home to Ohio", author_name: "Kara Singh" }),
        ],
      },
    });
    renderPage();
    const section = async (name: string) => (await screen.findByRole("region", { name })) as HTMLElement;
    expect((await section("Waiting on you")).textContent).toContain("Sam Lee");
    expect((await section("Under way")).textContent).toContain("The Night Shift Founder");
    expect((await section("Earlier")).textContent).toContain("Kara Singh · You cancelled it");
    expect(screen.getByText("Asks for your book")).toBeTruthy();
    expect(screen.getByText("Waiting")).toBeTruthy();
  });

  it("says when nothing is waiting on you, without hiding the rest", async () => {
    api.GET.mockResolvedValue({
      data: { lending: [], reading: [reading("accepted", { did_you_meet: null })] },
    });
    renderPage();
    expect(await screen.findByText("Nothing needs you right now.")).toBeTruthy();
    expect(screen.getByText("Accepted")).toBeTruthy();
    expect(screen.queryByText("No checkouts yet")).toBeNull();
  });
});
