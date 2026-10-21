import { ArrowLeft, ArrowRight, CheckCircle2, Eye, EyeOff, LockKeyhole, Mail, UserRound } from "lucide-react";
import { FormEvent, useState } from "react";
import { Link, Navigate, useLocation, useNavigate, useSearchParams } from "react-router-dom";
import { ApiError } from "../api";
import { useAuth } from "../auth";
import { Brand } from "../components/Brand";
import { LinkedInButton } from "../components/LinkedInButton";

const LINKEDIN_ERRORS: Record<string, string> = {
  not_configured: "LinkedIn sign-in is not set up yet. Ask an administrator to add the LinkedIn app credentials.",
  cancelled: "LinkedIn sign-in was cancelled. You can try again whenever you are ready.",
  invalid_state: "That sign-in attempt expired or came from a different browser. Please try again.",
  missing_email: "LinkedIn did not share an email address with us. Please allow email access and try again.",
  email_unverified: "Your LinkedIn email address is not verified. Verify it on LinkedIn, then try again.",
  account_disabled: "This account is not active. Please contact the FoundersCircle team.",
  too_many_attempts: "Too many attempts. Please wait a few minutes and try again.",
  linkedin_failed: "We could not complete sign-in with LinkedIn. Please try again.",
};

export function AuthPage({ mode }: { mode: "login" | "signup" }) {
  const { token, login, signup } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [params] = useSearchParams();
  const linkedInError = params.get("error");
  const [error, setError] = useState(
    linkedInError ? LINKEDIN_ERRORS[linkedInError] ?? LINKEDIN_ERRORS.linkedin_failed : "",
  );
  const [submitting, setSubmitting] = useState(false);

  if (token) return <Navigate to="/app" replace />;

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      if (mode === "signup") await signup(name, email, password);
      else await login(email, password);
      const destination = (location.state as { from?: string } | null)?.from;
      navigate(destination ?? (mode === "signup" ? "/onboarding" : "/app"), { replace: true });
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "We could not complete that request.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="auth-page">
      <aside className="auth-story">
        <Brand light />
        <div className="auth-story__content">
          <span className="eyebrow">A stronger circle starts here</span>
          <h1>{mode === "signup" ? "Join people who want to help ideas move forward." : "Welcome back to your network."}</h1>
          <div className="auth-benefits">
            <p><CheckCircle2 /> Discover expertise across the CWRU community</p>
            <p><CheckCircle2 /> Build a profile that reflects what you know and need</p>
            <p><CheckCircle2 /> Turn broad networks into useful connections</p>
          </div>
        </div>
        <p className="auth-story__quote">“The value of a network is knowing who can help—and why.”</p>
      </aside>

      <main className="auth-form-wrap">
        <Link className="auth-back" to="/"><ArrowLeft size={17} /> Back to home</Link>
        <div className="auth-form">
          <span className="eyebrow eyebrow--blue">{mode === "signup" ? "Join FoundersCircle" : "Member login"}</span>
          <h2>{mode === "signup" ? "Start building your circle." : "Good to see you again."}</h2>
          <p>{mode === "signup" ? "Sign up with LinkedIn. We use your LinkedIn details to set up your profile, so you never start from a blank page." : "Sign in to search the network and manage your profile."}</p>

          {error && <div className="form-error" role="alert">{error}</div>}

          <LinkedInButton>{mode === "signup" ? "Sign up with LinkedIn" : "Log in with LinkedIn"}</LinkedInButton>
          {mode === "signup" && <p className="auth-fineprint">We only receive your name, email address, and profile photo. We never post on your behalf.</p>}

          <div className="auth-divider">{mode === "signup" ? "or sign up with email" : "or use a password"}</div>
          <form onSubmit={submit}>
            {mode === "signup" && (
              <label>Name<div className="input-wrap"><UserRound /><input value={name} onChange={(event) => setName(event.target.value)} placeholder="Your full name" autoComplete="name" required /></div></label>
            )}
            <label>Email<div className="input-wrap"><Mail /><input type="email" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="you@example.com" autoComplete="email" required /></div></label>
            <label>Password<div className="input-wrap"><LockKeyhole /><input type={showPassword ? "text" : "password"} value={password} onChange={(event) => setPassword(event.target.value)} placeholder={mode === "signup" ? "At least 12 characters" : "Your password"} minLength={mode === "signup" ? 12 : 1} maxLength={128} autoComplete={mode === "signup" ? "new-password" : "current-password"} required /><button type="button" className="input-action" onClick={() => setShowPassword((value) => !value)} aria-label={showPassword ? "Hide password" : "Show password"}>{showPassword ? <EyeOff /> : <Eye />}</button></div></label>
            <button className="button button--secondary button--large button--full" disabled={submitting}>
              {submitting ? "Please wait…" : mode === "signup" ? "Create account" : "Log in"} {!submitting && <ArrowRight size={18} />}
            </button>
          </form>
          <p className="auth-switch">
            {mode === "signup" ? "Already a member?" : "New to FoundersCircle?"}{" "}
            <Link to={mode === "signup" ? "/login" : "/signup"}>{mode === "signup" ? "Log in" : "Join FoundersCircle"}</Link>
          </p>
        </div>
      </main>
    </div>
  );
}
