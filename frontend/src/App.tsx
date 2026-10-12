import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AuthProvider } from "./auth";
import { AppShell } from "./components/AppShell";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { AuthPage } from "./pages/AuthPage";
import { DirectoryPage } from "./pages/DirectoryPage";
import { InterviewPage } from "./pages/InterviewPage";
import { LandingPage } from "./pages/LandingPage";
import { OnboardingBasicsPage } from "./pages/OnboardingBasicsPage";
import { ProfilePage } from "./pages/ProfilePage";

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<AuthPage mode="login" />} />
          <Route path="/signup" element={<AuthPage mode="signup" />} />
          <Route element={<ProtectedRoute />}>
            <Route path="/app" element={<AppShell><DirectoryPage /></AppShell>} />
            <Route path="/app/profile" element={<AppShell><ProfilePage /></AppShell>} />
            <Route path="/onboarding" element={<AppShell><OnboardingBasicsPage /></AppShell>} />
            <Route path="/onboarding/interview" element={<AppShell><InterviewPage /></AppShell>} />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
