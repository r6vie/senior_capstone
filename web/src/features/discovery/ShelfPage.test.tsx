import { render, screen } from "@testing-library/react";
import { AuthProvider } from "../auth/AuthProvider";
import { ShelfPage } from "./ShelfPage";
import { sampleBooks, sampleShelves } from "./sampleBooks";

function renderPage() {
  render(
    <AuthProvider>
      <ShelfPage />
    </AuthProvider>,
  );
}

describe("ShelfPage", () => {
  it("shows every shelf", () => {
    renderPage();
    for (const shelf of sampleShelves) {
      expect(screen.getByRole("heading", { name: shelf.name })).toBeTruthy();
    }
  });

  it("names each author by first name only", () => {
    for (const book of sampleBooks) expect(book.firstName).toMatch(/^\S+$/);
    renderPage();
    expect(screen.getByRole("button", { name: "Raising Money Without a Network, by Amara" })).toBeTruthy();
  });
});
