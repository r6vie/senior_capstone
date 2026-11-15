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
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <circle cx="11" cy="11" r="7" />
              <path d="m20 20-3.5-3.5" />
            </svg>
            <input type="search" placeholder="Search by topic" aria-label="Search by topic" />
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
