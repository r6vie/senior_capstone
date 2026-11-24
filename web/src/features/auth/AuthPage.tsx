import { type FormEvent, useEffect, useState } from "react";
import { Link, type Location, useLocation, useNavigate, useSearchParams } from "react-router-dom";
import { api } from "../../api/client";
import { errorMessage } from "../../api/errors";
import { Button } from "../../ui/Button";
import { TextField } from "../../ui/TextField";
import { usePageTitle } from "../../ui/usePageTitle";
import { AuthLayout, PasswordField } from "./AuthLayout";
import { NeedsVerification, useAuth } from "./AuthProvider";

type Invite = { inviter: string } | { problem: string } | null;

export function AuthPage({ mode }: { mode: "sign-in" | "sign-up" }) {
  usePageTitle(mode === "sign-up" ? "Join" : "Sign in");
  const { signIn, signUp } = useAuth();
  const navigate = useNavigate();
  // Sent here from a page (RequireAuth): go back to it after signing in.
  const arrival = useLocation().state as { from?: Location; sessionEnded?: boolean } | null;
  const back = arrival?.from ? `${arrival.from.pathname}${arrival.from.search}${arrival.from.hash}` : "/";
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
      // The confirm page keeps the name on the book, so it travels in the navigation, not the address.
      if (next === "verify")
        navigate(`/verify?email=${encodeURIComponent(email)}`, {
          state: { name: `${firstName.trim()} ${lastName.trim()}`.trim() },
        });
      else navigate(signingUp ? "/" : back);
    } catch (caught) {
      if (caught instanceof NeedsVerification) navigate(`/verify?email=${encodeURIComponent(email)}`);
      else setError(caught instanceof Error ? caught.message : "Something went wrong.");
    } finally {
      setBusy(false);
    }
  }

  const invited = inviteCheck !== null && "inviter" in inviteCheck;

  return (
    <AuthLayout
      caption={signingUp ? "Join" : "Sign in"}
      title={signingUp ? "Join Trove." : "Welcome back."}
      voice={
        signingUp
          ? "You are the author of the book you haven’t written yet."
          : arrival?.sessionEnded
            ? "Your session ended. Sign in to pick up where you left off."
            : "Your book is where you left it."
      }
      across={
        signingUp ? { to: "/sign-in", label: "Sign in" } : { to: "/sign-up", label: "Create an account" }
      }
      author={signingUp ? `${firstName.trim()} ${lastName.trim()}`.trim() : undefined}
      invitedBy={inviteCheck && "inviter" in inviteCheck ? inviteCheck.inviter : null}
    >
      {signingUp && inviteCheck && "problem" in inviteCheck && (
        <p role="alert" className="message message-error">
          <span>!</span>
          <span>{`${inviteCheck.problem} You can still join with a case.edu email.`}</span>
        </p>
      )}
      <form onSubmit={submit} className="auth-form">
        {signingUp && (
          <div className="auth-names">
            <TextField
              label="First name"
              value={firstName}
              onChange={setFirstName}
              autoComplete="given-name"
            />
            <TextField label="Last name" value={lastName} onChange={setLastName} autoComplete="family-name" />
          </div>
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
        <PasswordField
          value={password}
          onChange={setPassword}
          autoComplete={signingUp ? "new-password" : "current-password"}
          hint={signingUp ? "At least 12 characters." : undefined}
        />
        {error && (
          <p role="alert" className="message message-error">
            <span>!</span>
            <span>{error}</span>
          </p>
        )}
        <div className="auth-go">
          <Button type="submit" disabled={busy} aria-busy={busy || undefined}>
            {signingUp ? "Create account" : "Sign in"}
          </Button>
          {!signingUp && (
            <Link to="/reset-password" state={{ email: email.trim() }} className="button button-quiet">
              Forgot your password?
            </Link>
          )}
        </div>
      </form>
    </AuthLayout>
  );
}
