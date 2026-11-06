import { type FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Button } from "../../ui/Button";
import { TextField } from "../../ui/TextField";
import { useAuth } from "./AuthProvider";

export function AuthPage({ mode }: { mode: "sign-in" | "sign-up" }) {
  const { signIn, signUp } = useAuth();
  const navigate = useNavigate();
  const [firstName, setFirstName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const signingUp = mode === "sign-up";

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      if (signingUp) await signUp(firstName, email, password);
      else await signIn(email, password);
      navigate("/");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Something went wrong.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="narrow-page">
      <h1>{signingUp ? "Join Trove" : "Sign in to Trove"}</h1>
      <form onSubmit={submit} className="stack">
        {signingUp && (
          <TextField label="First name" value={firstName} onChange={setFirstName} autoComplete="given-name" />
        )}
        <TextField label="Email" type="email" value={email} onChange={setEmail} autoComplete="email" />
        <TextField
          label="Password"
          type="password"
          value={password}
          onChange={setPassword}
          autoComplete={signingUp ? "new-password" : "current-password"}
          hint={signingUp ? "At least 12 characters." : undefined}
        />
        {error && (
          <p role="alert" className="error">
            {error}
          </p>
        )}
        <Button type="submit" disabled={busy}>
          {signingUp ? "Create account" : "Sign in"}
        </Button>
      </form>
      <p className="muted">
        {signingUp ? (
          <>
            Already have an account? <Link to="/sign-in">Sign in</Link>
          </>
        ) : (
          <>
            New here? <Link to="/sign-up">Create an account</Link>
          </>
        )}
      </p>
    </main>
  );
}
