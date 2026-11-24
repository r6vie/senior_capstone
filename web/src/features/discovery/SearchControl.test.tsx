import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { createRef } from "react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { SearchControl } from "./SearchControl";

const api = vi.hoisted(() => ({ GET: vi.fn() }));
vi.mock("../../api/client", () => ({ api }));
vi.mock("./BookReader", () => ({
  BookReader: ({ card, onDismiss }: { card: { title: string }; onDismiss: () => void }) => (
    <section role="dialog" aria-label={`Open book: ${card.title}`}>
      <button type="button" onClick={onDismiss}>
        Close the book
      </button>
    </section>
  ),
}));

const result = {
  book: {
    id: "career-change",
    title: "Engineering a Career Change",
    author_name: "Maya Chen",
    cover_style: "cover-1",
    blurb: "A story about turning technical skills toward a new purpose.",
  },
  excerpt: "What engineering taught me about beginning a new career.",
};

function renderSearch() {
  const triggerRef = createRef<HTMLInputElement>();
  render(
    <MemoryRouter>
      <Routes>
        <Route path="/" element={<SearchControl triggerRef={triggerRef} />} />
        <Route path="/books/:bookId" element={<p>Opened search result</p>} />
      </Routes>
    </MemoryRouter>,
  );
  return triggerRef;
}

beforeEach(() => {
  vi.resetAllMocks();
  Object.defineProperty(HTMLDialogElement.prototype, "showModal", {
    configurable: true,
    writable: true,
    value(this: HTMLDialogElement) {
      this.setAttribute("open", "");
    },
  });
  Object.defineProperty(HTMLDialogElement.prototype, "close", {
    configurable: true,
    writable: true,
    value(this: HTMLDialogElement) {
      this.removeAttribute("open");
      this.dispatchEvent(new Event("close"));
    },
  });
  vi.spyOn(HTMLElement.prototype, "getBoundingClientRect").mockReturnValue({
    x: 10,
    y: 20,
    left: 10,
    top: 20,
    right: 130,
    bottom: 200,
    width: 120,
    height: 180,
    toJSON: () => ({}),
  });
  api.GET.mockResolvedValue({ data: { results: [result] }, response: { status: 200, ok: true } });
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("D2 search overlay", () => {
  it("opens from the existing header field and restores focus when closed", async () => {
    const triggerRef = renderSearch();
    fireEvent.focus(screen.getByRole("searchbox", { name: "Search stories, topics, and people" }));

    expect(screen.getByRole("dialog", { name: "Search books" })).toBeTruthy();
    expect(screen.getByRole("heading", { name: "Find a story worth opening" })).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Close search" }));

    await waitFor(() => expect(screen.queryByRole("dialog")).toBeNull());
    expect(document.activeElement).toBe(triggerRef.current);
    expect(screen.queryByRole("dialog")).toBeNull();
  });

  it("opens a result above the search and returns to the same results", async () => {
    renderSearch();
    fireEvent.click(screen.getByRole("searchbox", { name: "Search stories, topics, and people" }));
    const field = screen.getByRole("searchbox", { name: "Search Trove" });

    fireEvent.change(field, { target: { value: "e" } });
    await new Promise((resolve) => setTimeout(resolve, 250));
    expect(api.GET).not.toHaveBeenCalled();

    fireEvent.change(field, { target: { value: "engineering" } });
    const cover = await screen.findByRole("button", {
      name: "Engineering a Career Change, by Maya Chen",
    });
    expect(screen.getByText(result.excerpt)).toBeTruthy();
    expect(api.GET).toHaveBeenCalledWith("/discovery/search", {
      params: { query: { q: "engineering" } },
    });

    fireEvent.click(cover);
    expect(screen.getByRole("dialog", { name: "Open book: Engineering a Career Change" })).toBeTruthy();
    expect(screen.getByRole("dialog", { name: "Search books" })).toBeTruthy();
    expect(cover.hasAttribute("data-out")).toBe(true);

    fireEvent.click(screen.getByRole("button", { name: "Close the book" }));
    expect(screen.queryByRole("dialog", { name: /Open book/ })).toBeNull();
    expect(screen.getByRole("dialog", { name: "Search books" })).toBeTruthy();
    expect((screen.getByRole("searchbox", { name: "Search Trove" }) as HTMLInputElement).value).toBe(
      "engineering",
    );
    expect(cover.hasAttribute("data-out")).toBe(false);
  });

  it("runs immediately when Search is pressed", async () => {
    renderSearch();
    fireEvent.click(screen.getByRole("searchbox", { name: "Search stories, topics, and people" }));
    fireEvent.change(screen.getByRole("searchbox", { name: "Search Trove" }), {
      target: { value: "Maya Chen" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Search" }));

    await waitFor(() => expect(api.GET).toHaveBeenCalledTimes(1));
    expect(api.GET).toHaveBeenCalledWith("/discovery/search", {
      params: { query: { q: "Maya Chen" } },
    });
  });
});
