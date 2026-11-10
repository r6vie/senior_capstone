import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { SettingsPage } from "../features/account/SettingsPage";
import { AuthPage } from "../features/auth/AuthPage";
import { AuthProvider } from "../features/auth/AuthProvider";
import { RequireAuth } from "../features/auth/RequireAuth";
import { ShelfPage } from "../features/discovery/ShelfPage";
import { InterviewPage } from "../features/interview/InterviewPage";

// Every page is registered here. Feature folders own their pages; this file only wires URLs.
export function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/sign-in" element={<AuthPage mode="sign-in" />} />
          <Route path="/sign-up" element={<AuthPage mode="sign-up" />} />
          <Route
            path="/"
            element={
              <RequireAuth>
                <ShelfPage />
              </RequireAuth>
            }
          />
          <Route
            path="/interview"
            element={
              <RequireAuth>
                <InterviewPage />
              </RequireAuth>
            }
          />
          <Route
            path="/settings"
            element={
              <RequireAuth>
                <SettingsPage />
              </RequireAuth>
            }
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
