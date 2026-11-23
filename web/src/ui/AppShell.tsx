import { useEffect, useRef } from "react";
import { NavLink, Outlet } from "react-router-dom";
import { useAuth } from "../features/auth/AuthProvider";
import { SearchControl } from "../features/discovery/SearchControl";
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
          <SearchControl triggerRef={search} />
          <NavLink to="/settings" className="avatar" aria-label="Settings">
            {user?.first_name.charAt(0)}
          </NavLink>
        </div>
      </header>
      <Outlet />
    </div>
  );
}
