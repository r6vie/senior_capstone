import { type ComponentType, lazy, Suspense, useEffect } from "react";
import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AuthPage } from "../features/auth/AuthPage";
import { AuthProvider } from "../features/auth/AuthProvider";
import { RequireAuth } from "../features/auth/RequireAuth";
import { VerifyPage } from "../features/auth/VerifyPage";
import { SparkPreviewPage } from "../features/book/SparkPreviewPage";
import { AppShell } from "../ui/AppShell";
import { LoadingGate, PageLoading } from "../ui/Loading";

// Signed-in pages load their code when first opened, so the first screen downloads only what it needs; the rest
// are fetched quietly once it's up, so moving between pages doesn't wait on a download.
const loaders: (() => Promise<unknown>)[] = [];
function page<K extends string>(load: () => Promise<{ [key in K]: ComponentType }>, name: K) {
  loaders.push(load);
  return lazy(() => load().then((module) => ({ default: module[name] })));
}
const SettingsPage = page(() => import("../features/account/SettingsPage"), "SettingsPage");
const MyBookPage = page(() => import("../features/book/MyBookPage"), "MyBookPage");
const CheckOutPage = page(() => import("../features/checkouts/CheckOutPage"), "CheckOutPage");
const CheckoutsPage = page(() => import("../features/checkouts/CheckoutsPage"), "CheckoutsPage");
const PastMeetsPage = page(() => import("../features/checkouts/PastMeetsPage"), "PastMeetsPage");
const ShelfPage = page(() => import("../features/discovery/ShelfPage"), "ShelfPage");
const InterviewPage = page(() => import("../features/interview/InterviewPage"), "InterviewPage");
const ReadingQuestionPage = page(
  () => import("../features/interview/ReadingQuestionPage"),
  "ReadingQuestionPage",
);
const RemovalPage = page(() => import("../features/interview/RemovalPage"), "RemovalPage");
const MeetingPage = page(() => import("../features/meetings/MeetingPage"), "MeetingPage");
const MessagesPage = page(() => import("../features/messaging/MessagesPage"), "MessagesPage");

function PreloadPages() {
  useEffect(() => {
    const start = () => {
      for (const load of loaders) load().catch(() => undefined);
    };
    const idle = window.requestIdleCallback ?? ((run: () => void) => window.setTimeout(run, 1500));
    idle(start);
  }, []);
  return null;
}

// Every page is registered here. Feature folders own their pages; this file only wires URLs.
export function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <LoadingGate>
          <PreloadPages />
          <Suspense fallback={<PageLoading />}>
            <Routes>
              <Route path="/sign-in" element={<AuthPage mode="sign-in" />} />
              <Route path="/sign-up" element={<AuthPage mode="sign-up" />} />
              <Route path="/verify" element={<VerifyPage />} />
              <Route
                element={
                  <RequireAuth>
                    <AppShell />
                  </RequireAuth>
                }
              >
                <Route path="/" element={<ShelfPage />} />
                <Route path="/books/:bookId" element={<ShelfPage />} />
                <Route path="/my-book" element={<MyBookPage />} />
                <Route path="/checkouts" element={<CheckoutsPage />} />
                <Route path="/checkouts/new/:bookId" element={<CheckOutPage />} />
                <Route path="/checkouts/:checkoutId/meeting" element={<MeetingPage />} />
                <Route path="/checkouts/:checkoutId/messages" element={<MessagesPage />} />
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
              <Route
                path="/interview/reading/:questionId"
                element={
                  <RequireAuth>
                    <ReadingQuestionPage />
                  </RequireAuth>
                }
              />
              <Route
                path="/my-book/remove/:chapterId"
                element={
                  <RequireAuth>
                    <RemovalPage />
                  </RequireAuth>
                }
              />
              {/* Dev only: SparkButton before the reader's book page mounts it. */}
              {import.meta.env.DEV && <Route path="/dev/spark" element={<SparkPreviewPage />} />}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </Suspense>
        </LoadingGate>
      </BrowserRouter>
    </AuthProvider>
  );
}
