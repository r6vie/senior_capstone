import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { api, ApiError } from "./api";
import type { User } from "./types";

interface AuthContextValue {
  token: string | null;
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (name: string, email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);
const SESSION_KEY = "founderscircle_session";

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => sessionStorage.getItem(SESSION_KEY));
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(Boolean(token));

  useEffect(() => {
    if (!token) {
      setLoading(false);
      setUser(null);
      return;
    }

    setLoading(true);
    api.me(token)
      .then(setUser)
      .catch((error: unknown) => {
        if (error instanceof ApiError && error.status === 401) {
          sessionStorage.removeItem(SESSION_KEY);
          setToken(null);
        }
      })
      .finally(() => setLoading(false));
  }, [token]);

  async function login(email: string, password: string) {
    const session = await api.login(email, password);
    sessionStorage.setItem(SESSION_KEY, session.access_token);
    setToken(session.access_token);
    setUser(await api.me(session.access_token));
  }

  async function signup(name: string, email: string, password: string) {
    await api.signup(name, email, password);
    await login(email, password);
  }

  async function logout() {
    const currentToken = token;
    sessionStorage.removeItem(SESSION_KEY);
    setToken(null);
    setUser(null);
    if (currentToken) await api.logout(currentToken).catch(() => undefined);
  }

  const value = useMemo(
    () => ({ token, user, loading, login, signup, logout }),
    [token, user, loading],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth must be used inside AuthProvider");
  return value;
}
