import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { forgetLoadedBooks } from "./bookPreload";
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
const changingCourse = {
  ...book,
  id: "changing-course",
  title: "From Pre-Med to Product",
  author_name: "Kofi Mensah",
};
const startingOver = {
  ...book,
  id: "starting-over",
  title: "Growing Food in the City",
  author_name: "Leah Szabo",
};
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
        <Route path="/interview" element={<p>Book interview</p>} />
        <Route path="/my-book" element={<p>My book page</p>} />
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
    if (path === "/books") {
      return response({ books: [book, changingCourse, startingOver], next: null });
    }
    if (path === "/books/{book_id}") return response(book);
    if (path === "/books/me") return response(null);
    if (path === "/discovery/recommendation")
      return response({ state: "create_book", book: null, reason: null });
    if (path === "/interview/sparks") return response([]);
    throw new Error(`Unexpected path ${path}`);
  });
});
afterEach(() => {
  cleanup();
  forgetLoadedBooks();
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
  it("asks a member mid-interview to continue it, on the cover and on their book card", async () => {
    const original = api.GET.getMockImplementation();
    api.GET.mockImplementation(async (path: string) =>
      path === "/discovery/recommendation"
        ? response({ state: "continue_interview", book: null, reason: null })
        : original?.(path),
    );
    renderShelf();
    expect(await screen.findByRole("heading", { name: "Your book is underway" })).toBeTruthy();
    expect(screen.getByRole("button", { name: "Continue your interview" })).toBeTruthy();
    const card = await screen.findByRole("region", { name: "Your book" });
    expect(within(card).getByText("In progress")).toBeTruthy();
    expect(within(card).getByRole("link", { name: "Continue" }).getAttribute("href")).toBe("/interview");
    expect(screen.queryByText("Your story belongs here")).toBeNull();
    expect(screen.queryByText("Not written yet")).toBeNull();
  });

  it("loads real books and invites a member without a book to create one", async () => {
    renderShelf();
    expect(await screen.findByRole("button", { name: `${book.title}, by ${book.author_name}` })).toBeTruthy();
    expect(screen.getByText("The Librarian recommends")).toBeTruthy();
    expect(screen.getByRole("heading", { name: "Your story belongs here" })).toBeTruthy();
    const changing = screen.getByRole("region", { name: "Changing course" });
    expect(
      within(changing).getByRole("button", {
        name: `${changingCourse.title}, by ${changingCourse.author_name}`,
      }),
    ).toBeTruthy();
    const starting = screen.getByRole("region", { name: "Starting over" });
    expect(
      within(starting).getByRole("button", {
        name: `${startingOver.title}, by ${startingOver.author_name}`,
      }),
    ).toBeTruthy();
    expect(screen.getByRole("region", { name: "Recently added" })).toBeTruthy();
    expect(api.GET).toHaveBeenCalledWith("/books", { params: { query: { limit: 20 } } });
    fireEvent.click(screen.getByRole("button", { name: "Create your book" }));
    expect(await screen.findByText("Book interview")).toBeTruthy();
  });
  it("takes out only the copy that was opened when a book stands on two shelves", async () => {
    renderShelf();
    const name = `${changingCourse.title}, by ${changingCourse.author_name}`;
    const onCategory = within(await screen.findByRole("region", { name: "Changing course" })).getByRole(
      "button",
      {
        name,
      },
    );
    const onRecent = within(screen.getByRole("region", { name: "Recently added" })).getByRole("button", {
      name,
    });
    fireEvent.click(onRecent);
    await screen.findByRole("dialog");
    expect(onRecent.hasAttribute("data-out")).toBe(true);
    expect(onCategory.hasAttribute("data-out")).toBe(false);
  });
  it("turns to a chapter and back to the contents, without revealing private fields", async () => {
    renderShelf();
    const { dialog } = await openBook();
    const reader = within(dialog);
    expect(document.documentElement.style.overflow).toBe("hidden");
    // Everything for the book is in the book: Close, the page tabs, and no helper sentences.
    expect(reader.getByRole("button", { name: "Close the book" })).toBeTruthy();
    expect(reader.getByRole("navigation", { name: "Pages of this book" })).toBeTruthy();
    expect(reader.queryByText(/I have one like this/)).toBeNull();
    expect(reader.queryByText(/video call|conversation with the author|Esc to close/i)).toBeNull();
    fireEvent.click(reader.getByRole("button", { name: "Conversation 3" }));
    const chapter = await reader.findByRole("article", { name: "Conversation 3" });
    expect(within(chapter).getByRole("heading", { name: "Conversation 3" })).toBeTruthy();
    expect(within(chapter).getByText("The story behind conversation 3.")).toBeTruthy();
    // Ask to check out sits under the contents, never under the chapter.
    expect(within(chapter).queryByRole("link", { name: "Ask to check out" })).toBeNull();
    expect(reader.getByRole("link", { name: "Ask to check out" })).toBeTruthy();
    expect(reader.queryByText("Private interview answer")).toBeNull();
    expect(reader.queryByText("private@example.com")).toBeNull();
    await waitFor(() => expect(dialog.querySelector(".br-leaf")).toBeNull());
    fireEvent.click(reader.getByRole("button", { name: "Contents" }));
    await waitFor(() =>
      expect(reader.getByRole("heading", { name: "Contents" })).toBe(document.activeElement),
    );
    expect(reader.queryByRole("article", { name: "Conversation 3" })).toBeNull();
  });
  it("turns with the arrow keys", async () => {
    renderShelf();
    const { dialog } = await openBook();
    fireEvent.keyDown(dialog, { key: "ArrowRight" });
    expect(await within(dialog).findByRole("article", { name: "Conversation 1" })).toBeTruthy();
    // A turn takes its time; a key pressed mid-turn waits for the next one.
    await waitFor(() => expect(dialog.querySelector(".br-leaf")).toBeNull());
    fireEvent.keyDown(dialog, { key: "ArrowLeft" });
    await waitFor(() => expect(within(dialog).queryByRole("article")).toBeNull());
  });
  it("closes with Escape, restores focus and unlocks the shelf", async () => {
    renderShelf();
    const { dialog, trigger } = await openBook();
    fireEvent(dialog, new Event("cancel", { bubbles: false, cancelable: true }));
    await waitFor(() => expect(screen.queryByRole("dialog")).toBeNull());
    expect(document.documentElement.style.overflow).not.toBe("hidden");
    expect(document.activeElement).toBe(trigger);
  });
  it("opens a direct link and reaches the existing checkout form", async () => {
    renderShelf("/books/real-book");
    const dialog = await screen.findByRole("dialog", { name: book.title });
    const checkout = await within(dialog).findByRole("link", { name: "Ask to check out" });
    expect(checkout.getAttribute("href")).toBe("/checkouts/new/real-book");
    fireEvent.click(checkout);
    expect(await screen.findByText("Checkout form")).toBeTruthy();
    expect(document.documentElement.style.overflow).not.toBe("hidden");
  });
  it("retries pagination without losing or duplicating books", async () => {
    let calls = 0;
    api.GET.mockImplementation(async (path: string) => {
      if (path === "/discovery/recommendation")
        return response({ state: "create_book", book: null, reason: null });
      if (path !== "/books") return response(null, 404);
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
    expect(api.GET.mock.calls.filter(([path]) => path === "/books").at(-1)).toEqual([
      "/books",
      { params: { query: { limit: 20, after: "cursor" } } },
    ]);
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
  it("opens a real Librarian recommendation in the existing reader", async () => {
    const original = api.GET.getMockImplementation();
    api.GET.mockImplementation(async (path: string) => {
      if (path === "/discovery/recommendation")
        return response({
          state: "recommendation",
          book: {
            id: second.id,
            title: second.title,
            author_name: second.author_name,
            cover_style: second.cover_style,
            blurb: second.blurb,
          },
          reason: "You both learned how to begin again without discarding what came before.",
        });
      if (path === "/books/{book_id}") return response(second);
      return original?.(path);
    });
    renderShelf();
    expect(await screen.findByRole("heading", { name: second.title })).toBeTruthy();
    expect(screen.getByText(/begin again without discarding/)).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: `${second.title}, by ${second.author_name}` }));
    const dialog = await screen.findByRole("dialog", { name: second.title });
    expect(await within(dialog).findByRole("button", { name: "Conversation 1" })).toBeTruthy();
    expect(within(dialog).getByRole("link", { name: "Ask to check out" })).toBeTruthy();
  });
  it("sends a member with a draft back to finish their book", async () => {
    const original = api.GET.getMockImplementation();
    api.GET.mockImplementation(async (path: string) =>
      path === "/discovery/recommendation"
        ? response({ state: "finish_book", book: null, reason: null })
        : original?.(path),
    );
    renderShelf();
    expect(await screen.findByRole("heading", { name: "Your story is almost ready" })).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Finish your book" }));
    expect(await screen.findByText("My book page")).toBeTruthy();
  });
  it("puts the one request waiting on you, and your own book, under the cover", async () => {
    api.GET.mockImplementation(async (path: string) => {
      if (path === "/checkouts")
        return response({
          reading: [],
          lending: [
            { id: "c2", reader_name: "Priya Nair", status: "waiting", created_at: "2026-11-18T10:00:00Z" },
            { id: "c1", reader_name: "Sam Okafor", status: "waiting", created_at: "2026-11-17T10:00:00Z" },
            { id: "c0", reader_name: "Jonah Reyes", status: "accepted", created_at: "2026-11-10T10:00:00Z" },
          ],
        });
      if (path === "/books/me")
        return response({ title: "The Coil Was Never the Problem", author_name: "Nora Valdez" });
      return response({ books: [book], next: null });
    });
    renderShelf();
    const waiting = await screen.findByRole("region", { name: "Waiting on you" });
    // The oldest request, by name, and never a count.
    expect(waiting.textContent).toContain("Sam Okafor asked to check out your book.");
    expect(within(waiting).getByRole("link", { name: "Review request" }).getAttribute("href")).toBe(
      "/checkouts",
    );
    const mine = await screen.findByRole("region", { name: "Your book" });
    expect(mine.textContent).toContain("The Coil Was Never the Problem");
    expect(within(mine).getByRole("link", { name: "Open" }).getAttribute("href")).toBe("/my-book");
  });
  it("leaves the request block out when nothing is waiting", async () => {
    api.GET.mockImplementation(async (path: string) => {
      if (path === "/checkouts") return response({ reading: [], lending: [] });
      if (path === "/books/me") return response(null);
      return response({ books: [book], next: null });
    });
    renderShelf();
    expect(await screen.findByRole("region", { name: "Your book" })).toBeTruthy();
    expect(screen.queryByRole("region", { name: "Waiting on you" })).toBeNull();
  });
  it("gives each shelf arrows that move it in place, with the start arrow off at the start", async () => {
    api.GET.mockResolvedValue(response({ books: [book], next: null }));
    renderShelf();
    await screen.findByRole("button", { name: `${book.title}, by ${book.author_name}` });
    expect(
      (screen.getByRole("button", { name: "Earlier books on Recently added" }) as HTMLButtonElement).disabled,
    ).toBe(true);
    expect(screen.getByRole("button", { name: "More books on Recently added" })).toBeTruthy();
    expect(screen.queryByText(/See the whole shelf/)).toBeNull();
  });
});
