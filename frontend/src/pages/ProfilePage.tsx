import { ArrowLeft, Check, Plus, Save, Trash2, X } from "lucide-react";
import { FormEvent, KeyboardEvent, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ApiError, api } from "../api";
import { useAuth } from "../auth";
import type { Profile, ProfileInput } from "../types";

const emptyProfile: ProfileInput = {
  name: "",
  affiliation: "",
  location: "",
  expertise: [],
  interests: [],
  role: "student",
  industry: "",
  background: "",
  help_offered: [],
  help_needed: [],
  availability: "available",
  meeting_preference: "either",
  graduation_year: null,
};

function TagEditor({ label, values, onChange, placeholder }: { label: string; values: string[]; onChange: (value: string[]) => void; placeholder: string }) {
  const [draft, setDraft] = useState("");

  function addTag() {
    const value = draft.trim();
    if (value && !values.some((item) => item.toLowerCase() === value.toLowerCase())) onChange([...values, value]);
    setDraft("");
  }

  function keyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (event.key === "Enter" || event.key === ",") {
      event.preventDefault();
      addTag();
    }
  }

  return (
    <label className="tag-field">{label}<div className="tag-editor">{values.map((value) => <span className="tag tag--editable" key={value}>{value}<button type="button" onClick={() => onChange(values.filter((item) => item !== value))} aria-label={`Remove ${value}`}><X /></button></span>)}<div className="tag-editor__input"><input value={draft} onChange={(event) => setDraft(event.target.value)} onKeyDown={keyDown} onBlur={addTag} placeholder={values.length ? "Add another" : placeholder} /><Plus /></div></div><small>Press Enter or type a comma to add each item.</small></label>
  );
}

export function ProfilePage() {
  const { token, user } = useAuth();
  const navigate = useNavigate();
  const [saved, setSaved] = useState<Profile | null>(null);
  const [form, setForm] = useState<ProfileInput>({ ...emptyProfile });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    if (!token) return;
    api.myProfile(token)
      .then((profile) => { setSaved(profile); setForm(profile); })
      .catch((caught) => {
        if (caught instanceof ApiError && caught.status === 404) setForm({ ...emptyProfile, name: user?.name ?? "" });
        else setError(caught instanceof ApiError ? caught.message : "Unable to load your profile.");
      })
      .finally(() => setLoading(false));
  }, [token, user?.name]);

  function update<K extends keyof ProfileInput>(field: K, value: ProfileInput[K]) {
    setForm((current) => ({ ...current, [field]: value }));
    setSuccess("");
  }

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!token) return;
    setSaving(true); setError(""); setSuccess("");
    try {
      const profile = saved ? await api.updateProfile(token, saved.id, form) : await api.createProfile(token, form);
      setSaved(profile); setForm(profile); setSuccess(saved ? "Your profile has been updated." : "Your profile is now part of the network.");
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Unable to save your profile.");
    } finally { setSaving(false); }
  }

  async function remove() {
    if (!token || !saved || !window.confirm("Delete your network profile? Your account will remain active.")) return;
    setSaving(true); setError("");
    try { await api.deleteProfile(token, saved.id); navigate("/app"); }
    catch (caught) { setError(caught instanceof ApiError ? caught.message : "Unable to delete your profile."); setSaving(false); }
  }

  if (loading) return <div className="page-wrap"><div className="loading-panel"><span className="spinner" />Loading your profile…</div></div>;

  return (
    <div className="page-wrap profile-page">
      <Link className="back-link" to="/app"><ArrowLeft /> Back to directory</Link>
      <div className="profile-page__heading"><div><span className="eyebrow eyebrow--blue">Your place in the network</span><h1>{saved ? "Edit your profile" : "Create your profile"}</h1><p>Help the community understand what you know, what you care about, and where you are.</p></div><span className={`profile-status ${saved ? "profile-status--complete" : ""}`}>{saved && <Check />} {saved ? "Profile active" : "Profile not published"}</span></div>

      <form className="profile-form" onSubmit={submit}>
        {error && <div className="form-error" role="alert">{error}</div>}
        {success && <div className="form-success" role="status"><Check /> {success}</div>}
        <section className="form-section">
          <div className="form-section__heading"><span>01</span><div><h2>The essentials</h2><p>Start with the information people use to recognize you.</p></div></div>
          <div className="form-grid">
            <label>Full name<input value={form.name} onChange={(event) => update("name", event.target.value)} placeholder="Your name" required /></label>
            <label>Member type<select value={form.role} onChange={(event) => update("role", event.target.value as ProfileInput["role"])}><option value="student">Current student</option><option value="alumni">Alumni</option></select></label>
            <label>Affiliation<input value={form.affiliation} onChange={(event) => update("affiliation", event.target.value)} placeholder="CWRU program, company, or role" required /></label>
            <label>Graduation year<input type="number" min="1900" max="2100" value={form.graduation_year ?? ""} onChange={(event) => update("graduation_year", event.target.value ? Number(event.target.value) : null)} placeholder="2027" /></label>
            <label>Location<input value={form.location} onChange={(event) => update("location", event.target.value)} placeholder="City, State" required /></label>
            <label>Industry<input value={form.industry} onChange={(event) => update("industry", event.target.value)} placeholder="Healthcare, software, finance…" /></label>
            <label className="form-grid__wide">Background<textarea value={form.background} onChange={(event) => update("background", event.target.value)} placeholder="A short summary of your experience, goals, or current work." rows={4} /></label>
          </div>
        </section>
        <section className="form-section">
          <div className="form-section__heading"><span>02</span><div><h2>Knowledge and interests</h2><p>Give the matching system useful context about your experience and goals.</p></div></div>
          <div className="profile-form__stack">
            <TagEditor label="Expertise" values={form.expertise} onChange={(value) => update("expertise", value)} placeholder="e.g. Fundraising" />
            <TagEditor label="Interests" values={form.interests} onChange={(value) => update("interests", value)} placeholder="e.g. Healthcare technology" />
          </div>
        </section>
        <section className="form-section">
          <div className="form-section__heading"><span>03</span><div><h2>How you want to connect</h2><p>Students can describe what they need; alumni can describe how they can help.</p></div></div>
          <div className="profile-form__stack">
            <TagEditor label="I can help with" values={form.help_offered} onChange={(value) => update("help_offered", value)} placeholder="e.g. Pitch feedback" />
            <TagEditor label="I would like help with" values={form.help_needed} onChange={(value) => update("help_needed", value)} placeholder="e.g. Finding a co-founder" />
            <div className="form-grid">
              <label>Availability<select value={form.availability} onChange={(event) => update("availability", event.target.value as ProfileInput["availability"])}><option value="available">Available</option><option value="limited">Limited availability</option><option value="unavailable">Not currently available</option></select></label>
              <label>Meeting preference<select value={form.meeting_preference} onChange={(event) => update("meeting_preference", event.target.value as ProfileInput["meeting_preference"])}><option value="either">Remote or in person</option><option value="remote">Remote</option><option value="in_person">In person</option></select></label>
            </div>
          </div>
        </section>
        <div className="profile-form__actions">{saved && <button type="button" className="button button--danger" onClick={remove} disabled={saving}><Trash2 /> Delete profile</button>}<button className="button button--primary button--large" disabled={saving}><Save /> {saving ? "Saving…" : saved ? "Save changes" : "Publish profile"}</button></div>
      </form>
    </div>
  );
}
