import { createContext, type ReactNode, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { api, session } from "../../api/client";
import { errorMessage } from "../../api/errors";
import type { components } from "../../api/schema";

type User = components["schemas"]["UserResponse"];

// Signing in with the right password before the case.edu code is entered (the API answers 403).
export class NeedsVerification extends Error {
  constructor() {
    super("Please confirm your case.edu email first.");
  }
}

interface AuthValue {
  user: User | null;
  loading: boolean;
  signIn: (email: string, password: string) => Promise<void>;
  // "verify" when a code was sent to a case.edu address; "signed-in" when the account is ready (an invite).
  signUp: (
    firstName: string,
    lastName: string,
    email: string,
    password: string,
    invite?: string,
  ) => Promise<"verify" | "signed-in">;
  verifyEmail: (email: string, code: string) => Promise<void>;
  signOut: () => Promise<void>;
  // Re-reads the account, for pages that change it (settings).
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(Boolean(session.get()));

  const loadUser = useCallback(async () => {
    const { data, response } = await api.GET("/auth/me");
    if (response.status === 401) session.clear();
    setUser(data ?? null);
  }, []);

  useEffect(() => {
    if (!session.get()) return;
    loadUser().finally(() => setLoading(false));
  }, [loadUser]);

  const signIn = useCallback(
    async (email: string, password: string) => {
      const { data, error, response } = await api.POST("/auth/login", { body: { email, password } });
      if (!data) {
        if (response?.status === 403) throw new NeedsVerification();
        throw new Error(errorMessage(error));
      }
      session.set(data.access_token);
      await loadUser();
    },
    [loadUser],
  );

  const signUp = useCallback(
    async (firstName: string, lastName: string, email: string, password: string, invite?: string) => {
      const { data, error } = await api.POST("/auth/signup", {
        body: { first_name: firstName, last_name: lastName, email, password, invite },
      });
      if (!data) throw new Error(errorMessage(error));
      if (!data.verified) return "verify";
      await signIn(email, password);
      return "signed-in";
    },
    [signIn],
  );

  const verifyEmail = useCallback(
    async (email: string, code: string) => {
      const { data, error } = await api.POST("/auth/verify", { body: { email, code } });
      if (!data) throw new Error(errorMessage(error));
      session.set(data.access_token);
      await loadUser();
    },
    [loadUser],
  );

  const signOut = useCallback(async () => {
    await api.POST("/auth/logout").catch(() => undefined);
    session.clear();
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({ user, loading, signIn, signUp, verifyEmail, signOut, refreshUser: loadUser }),
    [user, loading, signIn, signUp, verifyEmail, signOut, loadUser],
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthValue {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth must be used inside <AuthProvider>.");
  return value;
}
