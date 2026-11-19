import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { ShelfPage } from "./ShelfPage";

const api = vi.hoisted(() => ({ GET: vi.fn() }));
vi.mock("../../api/client", () => ({ api }));
vi.mock("../book/SparkButton", () => ({ SparkButton: () => <button type="button">Save a spark</button> }));
const book = {
  id: "real-book",
  title: "Learning to listen",
  author_name: "Maya Chen",
  cover_style: "cover-1",
  blurb: "What I learned from conversations.",
  chapters: Array.from({ length: 7 }, (_, index) => ({
    id: `chapter-${index}`,
    title: `Conversation ${index + 1}`,
    summary: `The story behind conversation ${index + 1}.`,
    quotes: ["Private interview answer"],
  })),
  contacts: { email: "private@example.com" },
  copies: 3,
};
const second = { ...book, id: "second", title: "Starting again" };
function response(data: unknown, status = 200) {
  return { data, response: { status, ok: status < 400 } };
}
function renderShelf(path = "/") {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/" element={<ShelfPage />} />
        <Route path="/books/:bookId" element={<ShelfPage />} />
        <Route path="/checkouts/new/:bookId" element={<p>Checkout form</p>} />
      </Routes>
    </MemoryRouter>,
  );
}
beforeEach(() => {
  vi.resetAllMocks();
  // jsdom does not implement the browser's native modal methods.
  Object.defineProperty(HTMLDialogElement.prototype, "showModal", {
    configurable: true,
    writable: true,
    value() {},
  });
  Object.defineProperty(HTMLDialogElement.prototype, "close", {
    configurable: true,
    writable: true,
    value() {},
  });
  vi.spyOn(HTMLDialogElement.prototype, "showModal").mockImplementation(function (this: HTMLDialogElement) {
    this.setAttribute("open", "");
  });
  vi.spyOn(HTMLDialogElement.prototype, "close").mockImplementation(function (this: HTMLDialogElement) {
    this.removeAttribute("open");
  });
  // Two entries fit; a real browser uses ResizeObserver to measure the wrapped titles.
  vi.spyOn(HTMLElement.prototype, "clientHeight", "get").mockImplementation(function (this: HTMLElement) {
    return this.classList.contains("reader-contents-space") ? 170 : 0;
  });
  // Layout height differs from the transformed size during the opening animation.
  vi.spyOn(HTMLElement.prototype, "offsetHeight", "get").mockReturnValue(80);
  vi.spyOn(HTMLElement.prototype, "getBoundingClientRect").mockReturnValue({
    x: 0,
    y: 0,
    left: 0,
    top: 0,
    right: 300,
    bottom: 40,
    width: 300,
    height: 40,
    toJSON: () => ({}),
  });
  api.GET.mockImplementation(async (path: string) => {
    if (path === "/books") return response({ books: [book], next: null });
    if (path === "/books/{book_id}") return response(book);
    if (path === "/books/me") return response(null, 404);
    if (path === "/interview/sparks") return response([]);
    throw new Error(`Unexpected path ${path}`);
  });
});
afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});
async function openBook() {
  const trigger = await screen.findByRole("button", { name: `${book.title}, by ${book.author_name}` });
  trigger.focus();
  fireEvent.click(trigger);
  const dialog = await screen.findByRole("dialog", { name: book.title });
  await within(dialog).findByRole("button", { name: "Conversation 1" });
  return { dialog, trigger };
}

describe("D1 shelf and reader", () => {
  it("loads real books and retains the Librarian example", async () => {
    renderShelf();
    expect(await screen.findByRole("button", { name: `${book.title}, by ${book.author_name}` })).toBeTruthy();
    expect(screen.getByText("The Librarian recommends")).toBeTruthy();
    expect(screen.getByRole("heading", { name: "Why I Turned Down Grad School Twice" })).toBeTruthy();
    expect(screen.queryByRole("heading", { name: "Changing course" })).toBeNull();
    expect(api.GET).toHaveBeenCalledWith("/books", { params: { query: { limit: 20 } } });
  });
  it("turns contents pages and reads a chapter without revealing private fields", async () => {
    renderShelf();
    const { dialog } = await openBook();
    const reader = within(dialog);
    expect(document.body.style.overflow).toBe("hidden");
    expect(reader.getByRole("button", { name: "Conversation 2" })).toBeTruthy();
    expect(reader.queryByRole("button", { name: "Conversation 3" })).toBeNull();
    fireEvent.click(reader.getByRole("button", { name: "Next page" }));
    fireEvent.click(reader.getByRole("button", { name: "Conversation 3" }));
    expect(reader.getByRole("heading", { name: "Conversation 3" })).toBeTruthy();
    expect(reader.getByText("The story behind conversation 3.")).toBeTruthy();
    expect(reader.queryByText("Private interview answer")).toBeNull();
    expect(reader.queryByText("private@example.com")).toBeNull();
    fireEvent.click(reader.getByRole("button", { name: "Back to contents" }));
    expect(reader.getByRole("button", { name: "Conversation 3" })).toBeTruthy();
    expect(reader.getByRole("heading", { name: "Contents" })).toBe(document.activeElement);
  });
  it("closes with Escape, restores focus and unlocks the shelf", async () => {
    renderShelf();
    const { dialog, trigger } = await openBook();
    fireEvent(dialog, new Event("cancel", { bubbles: false, cancelable: true }));
    await waitFor(() => expect(screen.queryByRole("dialog")).toBeNull());
    expect(document.body.style.overflow).not.toBe("hidden");
    expect(document.activeElement).toBe(trigger);
  });
  it("opens a direct link and reaches the existing checkout form", async () => {
    renderShelf("/books/real-book");
    const dialog = await screen.findByRole("dialog", { name: book.title });
    const checkout = await within(dialog).findByRole("link", { name: "Ask to check out" });
    expect(checkout.getAttribute("href")).toBe("/checkouts/new/real-book");
    fireEvent.click(checkout);
    expect(await screen.findByText("Checkout form")).toBeTruthy();
    expect(document.body.style.overflow).not.toBe("hidden");
  });
  it("retries pagination without losing or duplicating books", async () => {
    let calls = 0;
    api.GET.mockImplementation(async () => {
      calls += 1;
      if (calls === 1) return response({ books: [book], next: "cursor" });
      if (calls === 2) throw new Error("Connection lost");
      return response({ books: [book, second], next: null });
    });
    renderShelf();
    fireEvent.click(await screen.findByRole("button", { name: "Load more books" }));
    expect(await screen.findByRole("alert")).toBeTruthy();
    expect(screen.getByRole("button", { name: `${book.title}, by ${book.author_name}` })).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));
    expect(
      await screen.findByRole("button", { name: `${second.title}, by ${second.author_name}` }),
    ).toBeTruthy();
    expect(screen.getAllByRole("button", { name: `${book.title}, by ${book.author_name}` })).toHaveLength(1);
    expect(api.GET).toHaveBeenLastCalledWith("/books", { params: { query: { limit: 20, after: "cursor" } } });
    expect(screen.queryByRole("button", { name: "Load more books" })).toBeNull();
  });
  it("refreshes an empty shelf", async () => {
    api.GET.mockResolvedValue(response({ books: [], next: null }));
    renderShelf();
    expect(await screen.findByText("No books on the shelf yet.")).toBeTruthy();
    api.GET.mockResolvedValue(response({ books: [book], next: null }));
    fireEvent.click(screen.getByRole("button", { name: "Refresh shelf" }));
    expect(await screen.findByRole("button", { name: `${book.title}, by ${book.author_name}` })).toBeTruthy();
  });
  it("shows an unavailable book without a checkout action", async () => {
    const original = api.GET.getMockImplementation();
    api.GET.mockImplementation(async (path: string) =>
      path === "/books/{book_id}" ? response(null, 404) : original?.(path),
    );
    renderShelf("/books/gone");
    const dialog = await screen.findByRole("dialog");
    expect(await within(dialog).findByText("This book isn't on the shelf anymore.")).toBeTruthy();
    expect(within(dialog).queryByRole("link", { name: "Ask to check out" })).toBeNull();
  });
  it("retries a failed book request", async () => {
    let calls = 0;
    const original = api.GET.getMockImplementation();
    api.GET.mockImplementation(async (path: string) => {
      if (path !== "/books/{book_id}") return original?.(path);
      if (++calls === 1) throw new Error("Offline");
      return response(book);
    });
    renderShelf("/books/real-book");
    const dialog = await screen.findByRole("dialog");
    fireEvent.click(await within(dialog).findByRole("button", { name: "Try again" }));
    expect(await within(dialog).findByRole("button", { name: "Conversation 1" })).toBeTruthy();
  });
  it("previews the example without fabricating summaries or a checkout", async () => {
    renderShelf();
    await screen.findByRole("button", { name: `${book.title}, by ${book.author_name}` });
    fireEvent.click(
      screen.getByRole("button", { name: "Why I Turned Down Grad School Twice, by Hana Sato" }),
    );
    const dialog = screen.getByRole("dialog");
    expect(within(dialog).getByText("Example book")).toBeTruthy();
    expect(within(dialog).queryByRole("link", { name: "Ask to check out" })).toBeNull();
    fireEvent.click(within(dialog).getByRole("button", { name: "The first offer" }));
    const chapter = within(dialog).getByRole("article", { name: "The first offer" });
    expect(within(chapter).getByText("This example includes chapter titles only.")).toBeTruthy();
    expect(api.GET.mock.calls.some(([path]) => path === "/books/{book_id}")).toBe(false);
  });
});
