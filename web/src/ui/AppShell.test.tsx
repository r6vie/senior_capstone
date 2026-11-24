import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { vi } from "vitest";
import { AuthProvider } from "../features/auth/AuthProvider";
import { AppShell, NAV_ITEMS } from "./AppShell";

function Broken(): never {
  throw new Error("This page has a bug.");
}

function renderAt(path: string) {
  render(
    <AuthProvider>
      <MemoryRouter initialEntries={[path]}>
        <Routes>
          <Route element={<AppShell />}>
            <Route path="/" element={<p>shelf page</p>} />
            <Route path="/my-book" element={<p>book page</p>} />
            <Route path="/settings" element={<p>settings page</p>} />
            <Route path="/checkouts" element={<h1>Checkouts</h1>} />
            <Route path="/past-meets" element={<Broken />} />
          </Route>
        </Routes>
      </MemoryRouter>
    </AuthProvider>,
  );
}

describe("AppShell", () => {
  it("links to every main page", () => {
    renderAt("/");
    const nav = screen.getByRole("navigation", { name: "Main" });
    for (const item of NAV_ITEMS) {
      const link = nav.querySelector(`a[href="${item.to}"]`);
      expect(link?.textContent).toBe(item.label);
    }
  });

  it("marks only the current page", () => {
    renderAt("/my-book");
    expect(screen.getByRole("link", { name: "My book" }).getAttribute("aria-current")).toBe("page");
    expect(screen.getByRole("link", { name: "Shelf" }).getAttribute("aria-current")).toBeNull();
    expect(screen.getByText("book page")).toBeTruthy();
  });

  it("reaches Settings from the avatar", () => {
    renderAt("/");
    expect(screen.getByRole("link", { name: "Settings" }).getAttribute("href")).toBe("/settings");
  });

  it("puts focus on the new page's heading after moving to another page", async () => {
    renderAt("/");
    const link = screen.getByRole("link", { name: "Checkouts" });
    link.focus();
    fireEvent.click(link);
    const heading = await screen.findByRole("heading", { name: "Checkouts" });
    await waitFor(() => expect(document.activeElement).toBe(heading));
  });

  it("doesn't move focus on the first page", async () => {
    renderAt("/checkouts");
    await new Promise((done) => setTimeout(done, 50));
    expect(document.activeElement).toBe(document.body);
  });

  it("keeps the top bar when a page breaks, and offers a way on", () => {
    const quiet = vi.spyOn(console, "error").mockImplementation(() => undefined);
    renderAt("/past-meets");
    expect(screen.getByRole("alert").textContent).toContain("Something went wrong on this page");
    expect(screen.getByRole("navigation", { name: "Main" })).toBeTruthy();
    expect(screen.getByRole("link", { name: "Go to the shelf" }).getAttribute("href")).toBe("/");
    quiet.mockRestore();
  });

  it("clears a broken page when the member moves on", () => {
    const quiet = vi.spyOn(console, "error").mockImplementation(() => undefined);
    renderAt("/past-meets");
    fireEvent.click(screen.getByRole("link", { name: "Shelf" }));
    expect(screen.queryByRole("alert")).toBeNull();
    expect(screen.getByText("shelf page")).toBeTruthy();
    quiet.mockRestore();
  });
});
