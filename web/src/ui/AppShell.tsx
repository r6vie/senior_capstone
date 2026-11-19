import { useEffect, useRef } from "react";
import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../features/auth/AuthProvider";
import "./AppShell.css";

// The signed-in frame: top bar, navigation and the page's room. Settings is reached from the avatar,
// so the nav keeps the design's four items (docs/design/system.md, "Navigation").
export const NAV_ITEMS = [
  { to: "/", label: "Shelf" },
  { to: "/my-book", label: "My book" },
  { to: "/checkouts", label: "Checkouts" },
  { to: "/past-meets", label: "Past meets" },
];

export function AppShell() {
  const { user } = useAuth();
  const search = useRef<HTMLInputElement>(null);

  // "/" goes to the search, as the key hint in the field says, unless the member is already typing.
  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (event.key !== "/" || event.metaKey || event.ctrlKey || event.altKey) return;
      const target = event.target as HTMLElement | null;
      if (target?.closest("input, textarea, select, [contenteditable]")) return;
      event.preventDefault();
      search.current?.focus();
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, []);

  return (
    <div className="app-shell">
      <header className="top-bar">
        <span className="wordmark">Trove</span>
        <nav className="nav" aria-label="Main">
          {NAV_ITEMS.map((item) => (
            <NavLink key={item.to} to={item.to} end={item.to === "/"}>
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="top-bar-end">
          {/* Drawn only: topic search is wired up by the discovery feature (D2). */}
          <label className="search">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <circle cx="11" cy="11" r="7" />
              <path d="m20 20-3.5-3.5" />
            </svg>
            <input
              ref={search}
              type="search"
              placeholder="Search topics and questions"
              aria-label="Search topics and questions"
              aria-keyshortcuts="/"
            />
            <span className="search-key" aria-hidden="true">
              /
            </span>
          </label>
          <NavLink to="/settings" className="avatar" aria-label="Settings">
            {user?.first_name.charAt(0)}
          </NavLink>
        </div>
      </header>
      <Outlet />
    </div>
  );
}
