import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { AuthProvider } from "../features/auth/AuthProvider";
import { AppShell, NAV_ITEMS } from "./AppShell";

function renderAt(path: string) {
  render(
    <AuthProvider>
      <MemoryRouter initialEntries={[path]}>
        <Routes>
          <Route element={<AppShell />}>
            <Route path="/" element={<p>shelf page</p>} />
            <Route path="/my-book" element={<p>book page</p>} />
            <Route path="/settings" element={<p>settings page</p>} />
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
});
