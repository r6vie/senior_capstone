import { type FormEvent, useEffect, useState } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { api } from "../../api/client";
import { errorMessage } from "../../api/errors";
import { Button } from "../../ui/Button";
import { TextField } from "../../ui/TextField";
import { NeedsVerification, useAuth } from "./AuthProvider";

type Invite = { inviter: string } | { problem: string } | null;

export function AuthPage({ mode }: { mode: "sign-in" | "sign-up" }) {
  const { signIn, signUp } = useAuth();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const invite = params.get("invite");
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [inviteCheck, setInviteCheck] = useState<Invite>(null);
  const signingUp = mode === "sign-up";

  // Say who the link came from, or why it won't work, before the person fills anything in.
  useEffect(() => {
    if (!signingUp || !invite) return;
    let stale = false;
    api.POST("/auth/invites/check", { body: { invite } }).then(({ data, error: problem }) => {
      if (stale) return;
      setInviteCheck(data ? { inviter: data.inviter_name } : { problem: errorMessage(problem) });
    });
    return () => {
      stale = true;
    };
  }, [signingUp, invite]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      let next = "signed-in";
      if (signingUp) next = await signUp(firstName, lastName, email, password, invite ?? undefined);
      else await signIn(email, password);
      navigate(next === "verify" ? `/verify?email=${encodeURIComponent(email)}` : "/");
    } catch (caught) {
      if (caught instanceof NeedsVerification) navigate(`/verify?email=${encodeURIComponent(email)}`);
      else setError(caught instanceof Error ? caught.message : "Something went wrong.");
    } finally {
      setBusy(false);
    }
  }

  const invited = inviteCheck !== null && "inviter" in inviteCheck;

  return (
    <main className="narrow-page">
      <h1>{signingUp ? "Join Trove" : "Sign in to Trove"}</h1>
      {signingUp && inviteCheck && (
        <p role={invited ? "status" : "alert"} className={invited ? "message" : "message message-error"}>
          <span>{invited ? "✓" : "!"}</span>
          <span>
            {"inviter" in inviteCheck
              ? `${inviteCheck.inviter} invited you to Trove.`
              : `${inviteCheck.problem} You can still join with a case.edu email.`}
          </span>
        </p>
      )}
      <form onSubmit={submit} className="stack">
        {signingUp && (
          <>
            <TextField
              label="First name"
              value={firstName}
              onChange={setFirstName}
              autoComplete="given-name"
            />
            <TextField label="Last name" value={lastName} onChange={setLastName} autoComplete="family-name" />
          </>
        )}
        <TextField
          label="Email"
          type="email"
          value={email}
          onChange={setEmail}
          autoComplete="email"
          hint={
            signingUp && !invited
              ? "Students: your case.edu email. Alumni: ask a Trove member for an invite link."
              : undefined
          }
        />
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
