import { Compass, LogOut, Menu, MessageSquareText, UserRound, X } from "lucide-react";
import { useState, type ReactNode } from "react";
import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../auth";
import { Brand } from "./Brand";

export function AppShell({ children }: { children: ReactNode }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);

  async function signOut() {
    await logout();
    navigate("/");
  }

  return (
    <div className="app-shell">
      <header className="app-header">
        <Brand />
        <button className="icon-button app-menu" onClick={() => setOpen((value) => !value)} aria-label="Toggle navigation">
          {open ? <X size={22} /> : <Menu size={22} />}
        </button>
        <nav className={`app-nav ${open ? "app-nav--open" : ""}`} aria-label="Application navigation">
          <NavLink to="/app" end onClick={() => setOpen(false)}>
            <Compass size={18} /> Discover
          </NavLink>
          <NavLink to="/app/connections" onClick={() => setOpen(false)}>
            <MessageSquareText size={18} /> Requests
          </NavLink>
          <NavLink to="/app/profile" onClick={() => setOpen(false)}>
            <UserRound size={18} /> My profile
          </NavLink>
          <span className="app-nav__user">{user?.name}</span>
          <button className="button button--quiet" onClick={signOut}>
            <LogOut size={17} /> Sign out
          </button>
        </nav>
      </header>
      <main>{children}</main>
    </div>
  );
}
