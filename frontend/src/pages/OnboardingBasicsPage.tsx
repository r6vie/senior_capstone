import { ArrowRight, HandHeart, HandHelping, Handshake } from "lucide-react";
import { FormEvent, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { ApiError, api } from "../api";
import { useAuth } from "../auth";
import type { BasicsForm, Role, Seeking } from "../types";

const ROLES: { value: Role; label: string }[] = [
  { value: "student", label: "Student" },
  { value: "alum", label: "Alum" },
  { value: "faculty", label: "Faculty" },
  { value: "staff", label: "Staff" },
  { value: "other", label: "Other" },
];

const SEEKING: { value: Seeking; label: string; hint: string; icon: typeof HandHeart }[] = [
  { value: "get_help", label: "I'm looking for help", hint: "Advice, mentorship, introductions", icon: HandHelping },
  { value: "give_help", label: "I want to help others", hint: "Mentor, advise, open doors", icon: HandHeart },
  { value: "both", label: "Both", hint: "Learn from some, help others", icon: Handshake },
];

// Suggestions only; members can type anything.
const CWRU_SCHOOLS = [
  "College of Arts and Sciences", "Case School of Engineering", "Weatherhead School of Management",
  "Frances Payne Bolton School of Nursing", "School of Medicine", "School of Law", "School of Dental Medicine",
  "Mandel School of Applied Social Sciences", "School of Graduate Studies",
];

const EMPTY: BasicsForm = { role: "student", school: "", grad_year: null, majors: [], seeking: "both", location: "" };

export function OnboardingBasicsPage() {
  const { token } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState<BasicsForm>(EMPTY);
  const [majors, setMajors] = useState("");
  const [returning, setReturning] = useState(false);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!token) return;
    api.onboardingStatus(token)
      .then((status) => {
        if (status.basics) {
          setForm(status.basics);
          setMajors(status.basics.majors.join(", "));
          setReturning(true);
        }
      })
      .catch((caught) => setError(caught instanceof ApiError ? caught.message : "Unable to load your details."))
      .finally(() => setLoading(false));
  }, [token]);

  const needsYear = form.role === "student" || form.role === "alum";

  function update<K extends keyof BasicsForm>(field: K, value: BasicsForm[K]) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!token) return;
    setSaving(true);
    setError("");
    const basics: BasicsForm = {
      ...form,
      school: form.school.trim(),
      location: form.location.trim(),
      grad_year: form.grad_year,
      majors: majors.split(",").map((major) => major.trim()).filter(Boolean).slice(0, 4),
    };
    try {
      await api.submitBasics(token, basics);
      navigate("/onboarding/interview");
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Unable to save your details.");
      setSaving(false);
    }
  }

  if (loading) return <div className="page-wrap"><div className="loading-panel"><span className="spinner" />Loading…</div></div>;

  return (
    <div className="page-wrap onboarding-page">
      <div className="onboarding-steps" aria-label="Onboarding progress">
        <span className="onboarding-steps__item onboarding-steps__item--active">1 · The basics</span>
        <span className="onboarding-steps__item">2 · A short conversation</span>
      </div>
      <div className="profile-page__heading">
        <div>
          <span className="eyebrow eyebrow--blue">{returning ? "Update your basics" : "Welcome to FoundersCircle"}</span>
          <h1>Let's start with the basics.</h1>
          <p>Thirty seconds, then a short conversation about what you're looking for and what you can offer.</p>
        </div>
      </div>

      <form className="profile-form" onSubmit={submit}>
        {error && <div className="form-error" role="alert">{error}</div>}

        <section className="form-section">
          <fieldset className="choice-group">
            <legend>I'm a…</legend>
            <div className="choice-row">
              {ROLES.map((role) => (
                <label key={role.value} className={`choice-pill ${form.role === role.value ? "choice-pill--active" : ""}`}>
                  <input type="radio" name="role" value={role.value} checked={form.role === role.value} onChange={() => update("role", role.value)} />
                  {role.label}
                </label>
              ))}
            </div>
          </fieldset>

          <div className="form-grid">
            <label>
              CWRU school or department
              <input list="cwru-schools" value={form.school} onChange={(event) => update("school", event.target.value)} placeholder="e.g. Case School of Engineering" maxLength={120} required />
              <datalist id="cwru-schools">{CWRU_SCHOOLS.map((school) => <option key={school} value={school} />)}</datalist>
            </label>
            <label>
              Graduation year{needsYear ? "" : " (optional)"}
              <input
                type="number" inputMode="numeric" min={1940} max={2040}
                value={form.grad_year ?? ""}
                onChange={(event) => update("grad_year", event.target.value ? Number(event.target.value) : null)}
                placeholder="e.g. 2027" required={needsYear}
              />
            </label>
            <label>
              Major(s)
              <input value={majors} onChange={(event) => setMajors(event.target.value)} placeholder="Separate with commas" maxLength={300} />
            </label>
            <label>
              Where you're based
              <input value={form.location} onChange={(event) => update("location", event.target.value)} placeholder="City, State" maxLength={120} required />
            </label>
          </div>
        </section>

        <section className="form-section">
          <fieldset className="choice-group">
            <legend>What brings you here?</legend>
            <div className="seeking-grid">
              {SEEKING.map(({ value, label, hint, icon: Icon }) => (
                <label key={value} className={`seeking-card ${form.seeking === value ? "seeking-card--active" : ""}`}>
                  <input type="radio" name="seeking" value={value} checked={form.seeking === value} onChange={() => update("seeking", value)} />
                  <Icon size={22} aria-hidden="true" />
                  <strong>{label}</strong>
                  <small>{hint}</small>
                </label>
              ))}
            </div>
          </fieldset>
        </section>

        <div className="profile-form__actions">
          <button className="button button--primary button--large" disabled={saving}>
            {saving ? "Saving…" : "Continue to the conversation"} {!saving && <ArrowRight size={18} />}
          </button>
        </div>
      </form>
    </div>
  );
}
