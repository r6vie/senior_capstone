import { type FormEvent, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { api } from "../../api/client";
import { errorMessage } from "../../api/errors";
import { Button } from "../../ui/Button";
import { TextField } from "../../ui/TextField";
import { useAuth } from "./AuthProvider";

// Students confirm the code we emailed to their case.edu address (docs/trove.md §9.2).
export function VerifyPage() {
  const { verifyEmail } = useAuth();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const knownEmail = params.get("email");
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

  async function resend() {
    setError(null);
    setResent(false);
    const { response, error: problem } = await api.POST("/auth/verify/resend", {
      body: { email: email.trim() },
    });
    if (response.ok) setResent(true);
    else setError(errorMessage(problem));
  }

  return (
    <main className="narrow-page">
      <h1>Confirm your email</h1>
      <p className="muted">
        {knownEmail ? (
          <>
            We sent a 6-digit code to <strong>{knownEmail}</strong>.
          </>
        ) : (
          "Enter the 6-digit code we emailed you."
        )}{" "}
        It works for 15 minutes.
      </p>
      <form onSubmit={submit} className="stack">
        {!knownEmail && (
          <TextField label="Email" type="email" value={email} onChange={setEmail} autoComplete="email" />
        )}
        <TextField
          label="Code"
          value={code}
          onChange={setCode}
          autoComplete="one-time-code"
          inputMode="numeric"
        />
        {error && (
          <p role="alert" className="error">
            {error}
          </p>
        )}
        {resent && (
          <p role="status" className="muted">
            If that address is waiting for a code, a new one is on its way. You can ask once a minute.
          </p>
        )}
        <Button type="submit" disabled={busy || code.trim().length !== 6 || !email.trim()}>
          Confirm
        </Button>
        <div>
          <Button variant="quiet" onClick={resend} disabled={!email.trim()}>
            Send me a new code
          </Button>
        </div>
      </form>
      <p className="muted">
        Wrong address? <Link to="/sign-up">Start over</Link>
      </p>
    </main>
  );
}
