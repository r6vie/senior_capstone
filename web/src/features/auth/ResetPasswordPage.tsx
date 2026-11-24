import { type FormEvent, useState } from "react";
import { useLocation, useNavigate, useSearchParams } from "react-router-dom";
import { api } from "../../api/client";
import { errorMessage } from "../../api/errors";
import { Button } from "../../ui/Button";
import { TextField } from "../../ui/TextField";
import { usePageTitle } from "../../ui/usePageTitle";
import { AuthLayout, CodeField, PasswordField } from "./AuthLayout";
import { NeedsVerification, useAuth } from "./AuthProvider";

// "Forgot your password?" (approved by Josef 2026-11-24), in the sign-in page's two halves: the email, then the
// emailed code in six boxes with a new password, then signed in. Asking says the same thing whether or not the
// account exists. The email's link opens this page with the address filled in, straight at the code.

type Step = "ask" | "code";

export function ResetPasswordPage() {
  usePageTitle("Reset your password");
  const { signIn } = useAuth();
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const linked = params.get("email");
  // From the sign-in page, whatever was typed there comes along (in the navigation, not the address).
  const typed = (useLocation().state as { email?: string } | null)?.email;
  const [email, setEmail] = useState(linked ?? typed ?? "");
  const [step, setStep] = useState<Step>(linked ? "code" : "ask");
  const [fromLink, setFromLink] = useState(Boolean(linked));
  const [code, setCode] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [resent, setResent] = useState(false);
  const [busy, setBusy] = useState(false);

  async function ask(event?: FormEvent) {
    event?.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const { response, error: problem } = await api.POST("/auth/password/forgot", {
        body: { email: email.trim() },
      });
      if (!response.ok) {
        setError(errorMessage(problem));
        return false;
      }
      return true;
    } finally {
      setBusy(false);
    }
  }

  async function reset(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const { response, error: problem } = await api.POST("/auth/password/reset", {
        body: { email: email.trim(), code, new_password: password },
      });
      if (!response.ok) {
        setError(errorMessage(problem));
        return;
      }
      // Every session was signed out, this one too: sign in again with the new password.
      try {
        await signIn(email.trim(), password);
        navigate("/");
      } catch (caught) {
        if (caught instanceof NeedsVerification)
          navigate(`/verify?email=${encodeURIComponent(email.trim())}`);
        else navigate("/sign-in");
      }
    } finally {
      setBusy(false);
    }
  }

  const layout = {
    caption: "Sign in",
    title: "Reset your password.",
    voice: "Your book is where you left it.",
    across: { to: "/sign-in", label: "Sign in" },
  };

  if (step === "ask") {
    return (
      <AuthLayout {...layout}>
        <form
          className="auth-form"
          onSubmit={async (event) => {
            if (await ask(event)) {
              setFromLink(false);
              setStep("code");
            }
          }}
        >
          <TextField label="Email" type="email" value={email} onChange={setEmail} autoComplete="email" />
          {error && (
            <p role="alert" className="message message-error">
              <span>!</span>
              <span>{error}</span>
            </p>
          )}
          <div className="auth-go">
            <Button type="submit" disabled={busy || !email.trim()} aria-busy={busy || undefined}>
              Send me a code
            </Button>
          </div>
        </form>
      </AuthLayout>
    );
  }

  return (
    <AuthLayout {...layout}>
      <p className="auth-sub">
        {fromLink ? (
          <>
            Enter the 6-digit code we emailed to <strong>{email}</strong>.
          </>
        ) : (
          <>
            If <strong>{email}</strong> has a Trove account, we sent it a 6-digit code.
          </>
        )}{" "}
        It works for 15 minutes.
      </p>
      <form className="auth-form" onSubmit={reset}>
        <CodeField value={code} onChange={setCode} />
        <PasswordField
          label="New password"
          value={password}
          onChange={setPassword}
          autoComplete="new-password"
          hint="At least 12 characters."
        />
        {error && (
          <p role="alert" className="message message-error">
            <span>!</span>
            <span>{error}</span>
          </p>
        )}
        {resent && (
          <p role="status" className="message">
            <span>✓</span>
            <span>If that address has an account, a new code is on its way. You can ask once a minute.</span>
          </p>
        )}
        <div className="auth-go">
          <Button
            type="submit"
            disabled={busy || code.length !== 6 || !password.trim()}
            aria-busy={busy || undefined}
          >
            Reset password
          </Button>
          <Button
            variant="quiet"
            disabled={busy}
            onClick={async () => {
              setResent(false);
              if (await ask()) setResent(true);
            }}
          >
            Send me a new code
          </Button>
        </div>
      </form>
      <p className="auth-foot">
        Wrong address?{" "}
        <button
          type="button"
          className="auth-textlink"
          onClick={() => {
            setCode("");
            setError(null);
            setResent(false);
            setStep("ask");
          }}
        >
          Start over
        </button>
      </p>
    </AuthLayout>
  );
}
