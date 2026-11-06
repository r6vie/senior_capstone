import { createContext, type ReactNode, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { api, session } from "../../api/client";
import { errorMessage } from "../../api/errors";
import type { components } from "../../api/schema";

type User = components["schemas"]["UserResponse"];

interface AuthValue {
  user: User | null;
  loading: boolean;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (firstName: string, email: string, password: string) => Promise<void>;
  signOut: () => Promise<void>;
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
      const { data, error } = await api.POST("/auth/login", { body: { email, password } });
      if (!data) throw new Error(errorMessage(error));
      session.set(data.access_token);
      await loadUser();
    },
    [loadUser],
  );

  const signUp = useCallback(
    async (firstName: string, email: string, password: string) => {
      const { error } = await api.POST("/auth/signup", { body: { first_name: firstName, email, password } });
      if (error) throw new Error(errorMessage(error));
      await signIn(email, password);
    },
    [signIn],
  );

  const signOut = useCallback(async () => {
    await api.POST("/auth/logout").catch(() => undefined);
    session.clear();
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({ user, loading, signIn, signUp, signOut }),
    [user, loading, signIn, signUp, signOut],
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthValue {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth must be used inside <AuthProvider>.");
  return value;
}
