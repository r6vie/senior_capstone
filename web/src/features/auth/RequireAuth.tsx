import type { ReactNode } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { PageLoading } from "../../ui/Loading";
import { useAuth } from "./AuthProvider";

export function RequireAuth({ children }: { children: ReactNode }) {
  const { user, loading, sessionEnded } = useAuth();
  const location = useLocation();
  // Sign-in brings the member back to this page afterwards, and says why they're there if the session ended.
  if (!loading && !user) return <Navigate to="/sign-in" replace state={{ from: location, sessionEnded }} />;
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
