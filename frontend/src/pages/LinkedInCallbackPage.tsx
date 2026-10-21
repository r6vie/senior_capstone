import { useEffect, useRef, useState } from "react";
import { Link, Navigate, useNavigate, useSearchParams } from "react-router-dom";
import { ApiError } from "../api";
import { useAuth } from "../auth";
import { Brand } from "../components/Brand";

// LinkedIn sends members back here, via our backend, with a one-time code in the address.
export function LinkedInCallbackPage() {
  const { completeLinkedInSignIn } = useAuth();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const code = params.get("code");
  const [error, setError] = useState("");
  // The code works once; React's development double-run must not spend it twice.
  const started = useRef(false);

  useEffect(() => {
    if (!code || started.current) return;
    started.current = true;
    completeLinkedInSignIn(code)
      .then((isNew) => navigate(isNew ? "/onboarding" : "/app", { replace: true }))
      .catch((caught) => setError(caught instanceof ApiError ? caught.message : "We could not complete sign-in."));
  }, [code]);

  if (!code) return <Navigate to="/signup" replace />;

  return (
    <div className="loading-screen">
      <Brand />
      {error ? (
        <>
          <div className="form-error" role="alert">{error}</div>
          <Link to="/signup">Back to sign up</Link>
        </>
      ) : (
        <>
          <span className="spinner" />Signing you in…
        </>
      )}
    </div>
  );
}
