import { ArrowLeft, Check, Plus, Save, Trash2, X } from "lucide-react";
import { FormEvent, KeyboardEvent, useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { ApiError, api } from "../api";
import { useAuth } from "../auth";
import { MyData } from "../components/MyData";
import type { Profile, ProfileInput } from "../types";

const emptyProfile: ProfileInput = { name: "", affiliation: "", location: "", expertise: [], interests: [] };

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

      <MyData />

      <form className="profile-form" onSubmit={submit}>
        {error && <div className="form-error" role="alert">{error}</div>}
        {success && <div className="form-success" role="status"><Check /> {success}</div>}
        <section className="form-section"><div className="form-section__heading"><span>01</span><div><h2>The essentials</h2><p>Start with the information people use to recognize you.</p></div></div><div className="form-grid"><label>Full name<input value={form.name} onChange={(event) => update("name", event.target.value)} placeholder="Your name" required /></label><label>Affiliation<input value={form.affiliation} onChange={(event) => update("affiliation", event.target.value)} placeholder="CWRU student, alumni, mentor…" required /></label><label className="form-grid__wide">Location<input value={form.location} onChange={(event) => update("location", event.target.value)} placeholder="City, State" required /></label></div></section>
        <section className="form-section"><div className="form-section__heading"><span>02</span><div><h2>What you know</h2><p>Add the skills and experiences others can learn from.</p></div></div><TagEditor label="Expertise" values={form.expertise} onChange={(value) => update("expertise", value)} placeholder="e.g. Fundraising" /></section>
        <section className="form-section"><div className="form-section__heading"><span>03</span><div><h2>What draws you in</h2><p>Share the fields, ideas, and problems that interest you.</p></div></div><TagEditor label="Interests" values={form.interests} onChange={(value) => update("interests", value)} placeholder="e.g. Healthcare technology" /></section>
        <div className="profile-form__actions">{saved && <button type="button" className="button button--danger" onClick={remove} disabled={saving}><Trash2 /> Delete profile</button>}<button className="button button--primary button--large" disabled={saving}><Save /> {saving ? "Saving…" : saved ? "Save changes" : "Publish profile"}</button></div>
      </form>
    </div>
  );
}
