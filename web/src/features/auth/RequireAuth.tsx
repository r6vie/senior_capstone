import type { ReactNode } from "react";
import { Navigate } from "react-router-dom";
import { PageLoading } from "../../ui/Loading";
import { useAuth } from "./AuthProvider";

export function RequireAuth({ children }: { children: ReactNode }) {
  const { user, loading } = useAuth();
  if (!loading && !user) return <Navigate to="/sign-in" replace />;
  // Signed in on this device: the page starts fetching now, alongside the account check, rather than after
  // it. The screen stays hidden until both are back (ui/Loading.tsx). The same shape either way, so the page
  // isn't rebuilt (and doesn't fetch again) when the check comes back.
  return (
    <>
      {loading && <PageLoading />}
      {children}
    </>
  );
}
