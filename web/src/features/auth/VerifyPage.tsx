import { type FormEvent, useEffect, useState } from "react";
import { Link, useLocation, useNavigate, useSearchParams } from "react-router-dom";
import { api } from "../../api/client";
import { errorMessage } from "../../api/errors";
import { Button } from "../../ui/Button";
import { TextField } from "../../ui/TextField";
import { usePageTitle } from "../../ui/usePageTitle";
import { AuthLayout, CodeField, joiningName } from "./AuthLayout";
import { useAuth } from "./AuthProvider";

// Students confirm the code we emailed to their case.edu address (docs/trove.md §9.2).
export function VerifyPage() {
  usePageTitle("Confirm your email");
  const { verifyEmail } = useAuth();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const knownEmail = params.get("email");
  // The name joining lettered onto the book, so the book keeps it here.
  const arrival = useLocation().state as { name?: string; sendCode?: boolean } | null;
  const name = arrival?.name || joiningName();
  const [email, setEmail] = useState(knownEmail ?? "");
  const [code, setCode] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [resent, setResent] = useState(false);
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      await verifyEmail(email.trim(), code.trim());
      navigate("/");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Something went wrong.");
    } finally {
      setBusy(false);
    }
  }

  async function resend(quietly = false) {
    setError(null);
    setResent(false);
    const { response, error: problem } = await api.POST("/auth/verify/resend", {
      body: { email: email.trim() },
    });
    if (response.ok) setResent(!quietly);
    else setError(errorMessage(problem));
  }

  // Sent here from signing in or a reset, not from joining: no code was just sent, so one goes now, and the line
  // above the boxes stays true.
  const sendNow = Boolean(arrival?.sendCode && knownEmail);
  // biome-ignore lint/correctness/useExhaustiveDependencies: once, on arrival
  useEffect(() => {
    if (sendNow) resend(true);
  }, []);

  return (
    <AuthLayout
      caption="One more step"
      title="Confirm your email."
      voice="You are the author of the book you haven’t written yet."
      across={{ to: "/sign-in", label: "Sign in" }}
      author={name || undefined}
    >
      <p className="auth-sub">
        {knownEmail ? (
          <>
            We sent a 6-digit code to <strong>{knownEmail}</strong>.
          </>
        ) : (
          "Enter the 6-digit code we emailed you."
        )}{" "}
        It works for 15 minutes.
      </p>
      <form onSubmit={submit} className="auth-form">
        {!knownEmail && (
          <TextField label="Email" type="email" value={email} onChange={setEmail} autoComplete="email" />
        )}
        <CodeField value={code} onChange={setCode} />
        {error && (
          <p role="alert" className="message message-error">
            <span>!</span>
            <span>{error}</span>
          </p>
        )}
        {resent && (
          <p role="status" className="message">
            <span>✓</span>
            <span>
              If that address is waiting for a code, a new one is on its way. You can ask once a minute.
            </span>
          </p>
        )}
        <div className="auth-go">
          <Button
            type="submit"
            disabled={busy || code.trim().length !== 6 || !email.trim()}
            aria-busy={busy || undefined}
          >
            Confirm
          </Button>
          <Button variant="quiet" onClick={() => resend()} disabled={!email.trim()}>
            Send me a new code
          </Button>
        </div>
      </form>
      <p className="auth-foot">
        Wrong address? <Link to="/sign-up">Start over</Link>
      </p>
    </AuthLayout>
  );
}
