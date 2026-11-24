import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { CheckOutPage } from "./CheckOutPage";

const api = vi.hoisted(() => ({ GET: vi.fn(), POST: vi.fn() }));
vi.mock("../../api/client", () => ({ api }));

const book = {
  id: "b1",
  title: "Small Town, Big Contracts",
  author_name: "Ana Diaz",
  cover_style: "cover-1",
  blurb: "How I won my first contract.",
  chapters: [],
};

function renderPage() {
  render(
    <MemoryRouter initialEntries={["/checkouts/new/b1"]}>
      <Routes>
        <Route path="/checkouts/new/:bookId" element={<CheckOutPage />} />
        <Route path="/checkouts" element={<p>Checkouts list</p>} />
      </Routes>
    </MemoryRouter>,
  );
}

beforeEach(() => {
  vi.resetAllMocks();
  api.GET.mockResolvedValue({ data: book });
});

describe("CheckOutPage", () => {
  it("sends the note and goes to the checkouts list", async () => {
    api.POST.mockResolvedValue({ data: { book_title: book.title }, response: { status: 201 } });
    renderPage();
    expect(await screen.findByRole("heading", { name: book.title })).toBeTruthy();
    expect(api.GET).toHaveBeenCalledWith("/books/{book_id}", { params: { path: { book_id: "b1" } } });

    fireEvent.change(screen.getByLabelText("Your note to Ana Diaz"), { target: { value: "  Hi Ana!  " } });
    fireEvent.click(screen.getByRole("button", { name: "Ask to check out" }));

    expect(api.POST).toHaveBeenCalledWith("/checkouts", { body: { book_id: "b1", message: "Hi Ana!" } });
    expect(await screen.findByText("Checkouts list")).toBeTruthy();
  });

  it("needs a note before sending", async () => {
    renderPage();
    fireEvent.click(await screen.findByRole("button", { name: "Ask to check out" }));
    expect((await screen.findByRole("alert")).textContent).toContain("Write a short note");
    expect(api.POST).not.toHaveBeenCalled();
    // Typing clears it.
    fireEvent.change(screen.getByLabelText("Your note to Ana Diaz"), { target: { value: "Hi" } });
    expect(screen.queryByRole("alert")).toBeNull();
  });

  it("points a member without a book on the shelf to their book", async () => {
    api.POST.mockResolvedValue({
      error: { detail: "Put your own book on the shelf before you check one out." },
      response: { status: 403 },
    });
    renderPage();
    fireEvent.change(await screen.findByLabelText("Your note to Ana Diaz"), { target: { value: "Hi" } });
    fireEvent.click(screen.getByRole("button", { name: "Ask to check out" }));
    await waitFor(() => expect(screen.getByRole("link", { name: "Go to my book" })).toBeTruthy());
  });

  it("says a book off the shelf isn't available", async () => {
    api.GET.mockResolvedValue({
      error: { detail: "This book isn't on the shelf." },
      response: { status: 404 },
    });
    renderPage();
    expect(await screen.findByText("This book isn't available right now.")).toBeTruthy();
  });

  it("offers to try again when the book couldn't be loaded, instead of calling it unavailable", async () => {
    api.GET.mockResolvedValueOnce({ error: { detail: "Unavailable" }, response: { status: 503 } });
    renderPage();
    expect((await screen.findByRole("alert")).textContent).toContain("couldn't load this book");
    expect(screen.queryByText("This book isn't available right now.")).toBeNull();
    api.GET.mockRejectedValueOnce(new TypeError("Failed to fetch"));
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));
    expect((await screen.findByRole("alert")).textContent).toContain("couldn't load this book");
    fireEvent.click(screen.getByRole("button", { name: "Try again" }));
    expect(await screen.findByLabelText(/Your note to/)).toBeTruthy();
  });

  it("keeps the note and frees the button when the connection drops on sending", async () => {
    renderPage();
    const box = await screen.findByLabelText(/Your note to/);
    fireEvent.change(box, { target: { value: "Hi there" } });
    api.POST.mockRejectedValueOnce(new TypeError("Failed to fetch"));
    fireEvent.click(screen.getByRole("button", { name: "Ask to check out" }));
    expect((await screen.findByRole("alert")).textContent).toContain("couldn't reach Trove");
    expect((box as HTMLTextAreaElement).value).toBe("Hi there");
    expect((screen.getByRole("button", { name: "Ask to check out" }) as HTMLButtonElement).disabled).toBe(
      false,
    );
  });
});
