import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { api } from "../../api/client";
import { SparkButton } from "./SparkButton";

function show(props: Partial<Parameters<typeof SparkButton>[0]> = {}) {
  render(<SparkButton bookId="b1" chapterId="c1" chapterTitle="Two offers" {...props} />);
}

function press() {
  fireEvent.click(screen.getByRole("button", { name: "I have one like this: Two offers" }));
}

describe("SparkButton", () => {
  afterEach(() => vi.restoreAllMocks());

  it("saves on one press, sending only the book and chapter", async () => {
    const post = vi.spyOn(api, "POST").mockResolvedValue({
      data: { id: "s1" },
      response: new Response(null, { status: 200 }),
    } as never);
    show();
    press();
    expect(await screen.findByText("Saved for your next interview")).toBeTruthy();
    expect(post).toHaveBeenCalledWith("/interview/sparks", { body: { book_id: "b1", chapter_id: "c1" } });
  });

  it("starts saved when the page says so, and survives a reload that way", () => {
    show({ sparkId: "s1" });
    expect(screen.getByText("Saved for your next interview")).toBeTruthy();
    expect(screen.queryByRole("button", { name: /I have one like this/ })).toBeNull();
  });

  it("says which interview, for a member with no book yet", () => {
    show({ sparkId: "s1", hasBook: false });
    expect(screen.getByText("Saved for your interview")).toBeTruthy();
  });

  it("Undo removes it and goes back to the quiet control", async () => {
    const remove = vi.spyOn(api, "DELETE").mockResolvedValue({
      response: new Response(null, { status: 204 }),
    } as never);
    show({ sparkId: "s1" });
    fireEvent.click(screen.getByRole("button", { name: "Undo saving Two offers" }));
    expect(await screen.findByRole("button", { name: "I have one like this: Two offers" })).toBeTruthy();
    expect(remove).toHaveBeenCalledWith("/interview/sparks/s1");
  });

  it("at the limit, says what to do", async () => {
    vi.spyOn(api, "POST").mockResolvedValue({
      data: undefined,
      response: new Response(null, { status: 409 }),
    } as never);
    show();
    press();
    expect(await screen.findByText(/Remove one from My book to save this/)).toBeTruthy();
  });

  it("when saving fails, offers another try", async () => {
    vi.spyOn(api, "POST").mockRejectedValueOnce(new TypeError("Failed to fetch"));
    show();
    press();
    expect(await screen.findByText("Couldn't save that.")).toBeTruthy();
    expect(document.body.textContent).not.toMatch(/Failed to fetch/);
    vi.spyOn(api, "POST").mockResolvedValue({
      data: { id: "s1" },
      response: new Response(null, { status: 200 }),
    } as never);
    fireEvent.click(screen.getByRole("button", { name: "Try saving Two offers again" }));
    await waitFor(() => expect(screen.getByText("Saved for your next interview")).toBeTruthy());
  });

  it("shows no numbers and names no author", () => {
    show();
    expect(document.body.textContent).not.toMatch(/\d/);
  });
});
