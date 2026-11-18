import { act, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { MessagesPage } from "./MessagesPage";

const api = vi.hoisted(() => ({ GET: vi.fn(), POST: vi.fn() }));
vi.mock("../../api/client", () => ({ api }));

const message = (id: string, extra: Record<string, unknown>) => ({
  id,
  kind: "message",
  from_me: false,
  sender_name: "Ana Diaz",
  text: "",
  sent_at: "2026-11-18T15:00:00Z",
  ...extra,
});

const thread = (extra: Record<string, unknown> = {}) => ({
  checkout_id: "c1",
  book_title: "Small Town, Big Contracts",
  other_name: "Ana Diaz",
  can_write: true,
  messages: [
    message("note-1", {
      kind: "checkout_note",
      from_me: true,
      sender_name: "Sam Lee",
      text: "Hi Ana!",
      sent_at: "2026-11-17T10:00:00Z",
    }),
    message("m1", { text: "Happy to talk!", sent_at: "2026-11-18T14:00:00Z" }),
    message("n1", {
      kind: "note",
      sender_name: "",
      text: "Ana confirmed Tuesday at 3pm",
      sent_at: "2026-11-18T15:00:00Z",
    }),
  ],
  ...extra,
});

function renderPage() {
  render(
    <MemoryRouter initialEntries={["/checkouts/c1/messages"]}>
      <Routes>
        <Route path="/checkouts/:checkoutId/messages" element={<MessagesPage />} />
      </Routes>
    </MemoryRouter>,
  );
}

function setVisibility(state: "visible" | "hidden") {
  Object.defineProperty(document, "visibilityState", { value: state, configurable: true });
}

beforeEach(() => {
  vi.resetAllMocks();
  setVisibility("visible");
  api.GET.mockResolvedValue(ok(thread()));
  api.POST.mockResolvedValue({ data: {}, response: { ok: true, status: 204 } });
});

afterEach(() => {
  setVisibility("visible");
  vi.useRealTimers();
});

function ok(data: unknown) {
  return { data, response: { ok: true, status: 200 } };
}

function failed(status: number, detail = "Something went wrong.") {
  return { error: { detail }, response: { ok: false, status } };
}

const readCalls = () => api.POST.mock.calls.filter(([path]) => path === "/messages/{checkout_id}/read");

describe("MessagesPage", () => {
  it("shows the conversation: the checkout note, people's messages and app notes", async () => {
    renderPage();
    expect(await screen.findByRole("heading", { name: "Messages with Ana Diaz" })).toBeTruthy();
    expect(screen.getByText("You, checking out")).toBeTruthy();
    expect(screen.getByText("Hi Ana!")).toBeTruthy();
    expect(screen.getByText("Ana Diaz")).toBeTruthy();
    expect(screen.getByText("Happy to talk!")).toBeTruthy();
    expect(screen.getByText("Ana confirmed Tuesday at 3pm")).toBeTruthy();
    expect(api.GET).toHaveBeenCalledWith("/messages/{checkout_id}", {
      params: { path: { checkout_id: "c1" } },
    });
  });

  it("marks read only up to the newest message it showed", async () => {
    renderPage();
    await waitFor(() =>
      expect(api.POST).toHaveBeenCalledWith("/messages/{checkout_id}/read", {
        params: { path: { checkout_id: "c1" } },
        body: { seen_up_to: "2026-11-18T15:00:00Z" },
      }),
    );
  });

  it("doesn't mark anything read while the page is hidden", async () => {
    setVisibility("hidden");
    renderPage();
    expect(await screen.findByText("Happy to talk!")).toBeTruthy();
    expect(api.POST).not.toHaveBeenCalled();
  });

  it("sends a message, clears the box and reloads the conversation", async () => {
    renderPage();
    const box = await screen.findByLabelText("Write to Ana Diaz");
    fireEvent.change(box, { target: { value: "  See you Tuesday!  " } });
    fireEvent.click(screen.getByRole("button", { name: "Send" }));
    await waitFor(() =>
      expect(api.POST).toHaveBeenCalledWith("/messages/{checkout_id}", {
        params: { path: { checkout_id: "c1" } },
        body: { text: "See you Tuesday!" },
      }),
    );
    await waitFor(() => expect((box as HTMLTextAreaElement).value).toBe(""));
    expect(api.GET).toHaveBeenCalledTimes(2);
  });

  it("needs something to send", async () => {
    renderPage();
    fireEvent.click(await screen.findByRole("button", { name: "Send" }));
    expect((await screen.findByRole("alert")).textContent).toContain("Write something first.");
    expect(api.POST).not.toHaveBeenCalledWith("/messages/{checkout_id}", expect.anything());
  });

  it("shows why a message wasn't sent, like the hourly limit", async () => {
    renderPage();
    fireEvent.change(await screen.findByLabelText("Write to Ana Diaz"), { target: { value: "Hi" } });
    api.POST.mockResolvedValue(failed(429, "You've sent a lot of messages in the last hour."));
    fireEvent.click(screen.getByRole("button", { name: "Send" }));
    expect((await screen.findByRole("alert")).textContent).toContain("in the last hour");
    expect((screen.getByLabelText("Write to Ana Diaz") as HTMLTextAreaElement).value).toBe("Hi");
  });

  it("explains a conversation that isn't open", async () => {
    api.GET.mockResolvedValue(failed(404, "We couldn't find that conversation."));
    renderPage();
    expect(await screen.findByText("This conversation isn't available.")).toBeTruthy();
    expect(screen.getByRole("link", { name: "Back to Checkouts" })).toBeTruthy();
  });

  it("is read-only once the conversation is closed", async () => {
    api.GET.mockResolvedValue(ok(thread({ can_write: false })));
    renderPage();
    expect(await screen.findByText("This conversation is closed. You can still read it.")).toBeTruthy();
    expect(screen.queryByRole("button", { name: "Send" })).toBeNull();
  });

  it("keeps the conversation on screen when a later check fails", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    renderPage();
    expect(await screen.findByText("Happy to talk!")).toBeTruthy();
    api.GET.mockResolvedValue(failed(503, "The database is unavailable."));
    await act(async () => {
      vi.advanceTimersByTime(20_000);
    });
    expect(await screen.findByText(/Couldn't check for new messages/)).toBeTruthy();
    expect(screen.getByText("Happy to talk!")).toBeTruthy();
    expect(screen.queryByText("This conversation isn't available.")).toBeNull();
  });

  it("offers to try again when the first load fails, including a dropped connection", async () => {
    api.GET.mockRejectedValueOnce(new TypeError("Failed to fetch"));
    renderPage();
    expect((await screen.findByRole("alert")).textContent).toContain("We couldn't load this conversation.");
    api.GET.mockResolvedValue(ok(thread()));
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));
    expect(await screen.findByText("Happy to talk!")).toBeTruthy();
  });

  it("tries marking read again if it didn't work the first time", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    api.POST.mockResolvedValueOnce({ error: {}, response: { ok: false, status: 503 } });
    renderPage();
    await waitFor(() => expect(readCalls()).toHaveLength(1));
    await act(async () => {
      vi.advanceTimersByTime(20_000);
    });
    await waitFor(() => expect(readCalls()).toHaveLength(2));
    await act(async () => {
      vi.advanceTimersByTime(20_000);
    });
    // Once it worked, the same newest message isn't reported again.
    await waitFor(() => expect(api.GET).toHaveBeenCalledTimes(3));
    expect(readCalls()).toHaveLength(2);
  });

  it("checks for new messages every 20 seconds only while the page is visible", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    renderPage();
    await waitFor(() => expect(api.GET).toHaveBeenCalledTimes(1));
    setVisibility("hidden");
    await act(async () => {
      vi.advanceTimersByTime(60_000);
    });
    expect(api.GET).toHaveBeenCalledTimes(1);
    setVisibility("visible");
    await act(async () => {
      document.dispatchEvent(new Event("visibilitychange"));
    });
    await waitFor(() => expect(api.GET).toHaveBeenCalledTimes(2));
  });
});
