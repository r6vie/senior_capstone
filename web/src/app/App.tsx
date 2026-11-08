import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { SettingsPage } from "../features/account/SettingsPage";
import { AuthPage } from "../features/auth/AuthPage";
import { AuthProvider } from "../features/auth/AuthProvider";
import { RequireAuth } from "../features/auth/RequireAuth";
import { MyBookPage } from "../features/book/MyBookPage";
import { CheckoutsPage } from "../features/checkouts/CheckoutsPage";
import { PastMeetsPage } from "../features/checkouts/PastMeetsPage";
import { ShelfPage } from "../features/discovery/ShelfPage";
import { InterviewPage } from "../features/interview/InterviewPage";
import { AppShell } from "../ui/AppShell";

// Every page is registered here. Feature folders own their pages; this file only wires URLs.
export function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/sign-in" element={<AuthPage mode="sign-in" />} />
          <Route path="/sign-up" element={<AuthPage mode="sign-up" />} />
          <Route
            element={
              <RequireAuth>
                <AppShell />
              </RequireAuth>
            }
          >
            <Route path="/" element={<ShelfPage />} />
            <Route path="/my-book" element={<MyBookPage />} />
            <Route path="/checkouts" element={<CheckoutsPage />} />
            <Route path="/past-meets" element={<PastMeetsPage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Route>
          <Route
            path="/interview"
            element={
              <RequireAuth>
                <InterviewPage />
              </RequireAuth>
            }
          />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
