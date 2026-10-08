import { ArrowLeft, ArrowRight, CheckCircle2, Eye, EyeOff, LockKeyhole, Mail, UserRound } from "lucide-react";
import { FormEvent, useState } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";
import { ApiError } from "../api";
import { useAuth } from "../auth";
import { Brand } from "../components/Brand";

export function AuthPage({ mode }: { mode: "login" | "signup" }) {
  const { token, login, signup } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
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
      navigate(destination ?? (mode === "signup" ? "/app/profile" : "/app"), { replace: true });
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
        <form className="auth-form" onSubmit={submit}>
          <span className="eyebrow eyebrow--blue">{mode === "signup" ? "Create your account" : "Member login"}</span>
          <h2>{mode === "signup" ? "Start building your circle." : "Good to see you again."}</h2>
          <p>{mode === "signup" ? "Your account gives you access to the FoundersCircle network." : "Sign in to search the network and manage your profile."}</p>

          {error && <div className="form-error" role="alert">{error}</div>}

          {mode === "signup" && (
            <label>Name<div className="input-wrap"><UserRound /><input value={name} onChange={(event) => setName(event.target.value)} placeholder="Your full name" autoComplete="name" required /></div></label>
          )}
          <label>Email<div className="input-wrap"><Mail /><input type="email" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="you@example.com" autoComplete="email" required /></div></label>
          <label>Password<div className="input-wrap"><LockKeyhole /><input type={showPassword ? "text" : "password"} value={password} onChange={(event) => setPassword(event.target.value)} placeholder={mode === "signup" ? "At least 12 characters" : "Your password"} minLength={mode === "signup" ? 12 : 1} maxLength={128} autoComplete={mode === "signup" ? "new-password" : "current-password"} required /><button type="button" className="input-action" onClick={() => setShowPassword((value) => !value)} aria-label={showPassword ? "Hide password" : "Show password"}>{showPassword ? <EyeOff /> : <Eye />}</button></div></label>
          <button className="button button--primary button--large button--full" disabled={submitting}>
            {submitting ? "Please wait…" : mode === "signup" ? "Create account" : "Log in"} {!submitting && <ArrowRight size={18} />}
          </button>
          <p className="auth-switch">
            {mode === "signup" ? "Already have an account?" : "New to FoundersCircle?"}{" "}
            <Link to={mode === "signup" ? "/login" : "/signup"}>{mode === "signup" ? "Log in" : "Create an account"}</Link>
          </p>
        </form>
      </main>
    </div>
  );
}
