import { BrowserRouter, Navigate, Route, Routes } from "react-router-dom";
import { AuthPage } from "../features/auth/AuthPage";
import { AuthProvider } from "../features/auth/AuthProvider";
import { RequireAuth } from "../features/auth/RequireAuth";
import { MyBookPage } from "../features/book/MyBookPage";
import { SparkPreviewPage } from "../features/book/SparkPreviewPage";
import { ShelfPage } from "../features/discovery/ShelfPage";
import { InterviewPage } from "../features/interview/InterviewPage";
import { ReadingQuestionPage } from "../features/interview/ReadingQuestionPage";
import { RemovalPage } from "../features/interview/RemovalPage";

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
            path="/interview/reading/:questionId"
            element={
              <RequireAuth>
                <ReadingQuestionPage />
              </RequireAuth>
            }
          />
          <Route
            path="/my-book"
            element={
              <RequireAuth>
                <MyBookPage />
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
      </BrowserRouter>
    </AuthProvider>
  );
}
