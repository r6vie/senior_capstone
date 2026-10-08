import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuth } from "../auth";
import { Brand } from "./Brand";

export function ProtectedRoute() {
  const { token, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return <div className="loading-screen"><Brand /><span className="spinner" />Loading your network…</div>;
  }

  if (!token) return <Navigate to="/login" state={{ from: location.pathname }} replace />;
  return <Outlet />;
}
