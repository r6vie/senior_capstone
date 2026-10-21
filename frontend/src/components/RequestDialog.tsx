import { Briefcase, Check, GraduationCap, Lightbulb, Send, Sparkles, UserPlus, X } from "lucide-react";
import { FormEvent, useEffect, useState, type ComponentType } from "react";
import { ApiError, api } from "../api";
import { useAuth } from "../auth";
import type { Connection, Profile, RequestType, RequestTypeOption } from "../types";

const typeIcons: Record<RequestType, ComponentType<{ size?: number }>> = {
  mentorship: GraduationCap,
  career_advice: Briefcase,
  introduction: UserPlus,
  collaboration: Lightbulb,
  other: Sparkles,
};

export function RequestDialog({
  profile, onClose, onSent,
}: { profile: Profile; onClose: () => void; onSent?: (connection: Connection) => void }) {
  const { token } = useAuth();
  const [types, setTypes] = useState<RequestTypeOption[]>([]);
  const [type, setType] = useState<RequestType | null>(null);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [sending, setSending] = useState(false);
  const [sent, setSent] = useState(false);

  useEffect(() => {
    if (!token) return;
    api.requestTypes(token).then(setTypes).catch(() => setError("Unable to load request types."));
  }, [token]);

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => { if (event.key === "Escape") onClose(); };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!token || !type) return;
    setSending(true); setError("");
    try {
      const connection = await api.sendRequest(token, profile.id, type, message.trim());
      onSent?.(connection);
      setSent(true);
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : "Unable to send your request.");
    } finally {
      setSending(false);
    }
  }

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" role="dialog" aria-modal="true" aria-label={`Connect with ${profile.name}`} onClick={(event) => event.stopPropagation()}>
        <button type="button" className="modal__close" onClick={onClose} aria-label="Close"><X /></button>
        {sent ? (
          <div className="modal__done">
            <div className="form-success" role="status"><Check /> Request sent to {profile.name}. They'll get an email.</div>
            <button type="button" className="button button--secondary" onClick={onClose}>Close</button>
          </div>
        ) : (
          <form className="profile-form" onSubmit={submit}>
            <div>
              <span className="eyebrow eyebrow--blue">New request</span>
              <h2>Connect with {profile.name}</h2>
              <p className="modal__sub">{profile.affiliation} · {profile.location}</p>
            </div>
            {error && <div className="form-error" role="alert">{error}</div>}

            <div className="bubble-field">
              <span id="purpose-label" className="bubble-field__label">What's this about?</span>
              <div className="bubble-picker" role="radiogroup" aria-labelledby="purpose-label">
                {types.map((option) => {
                  const Icon = typeIcons[option.value];
                  const selected = type === option.value;
                  return (
                    <button
                      type="button" key={option.value} role="radio" aria-checked={selected}
                      className={`type-bubble type-bubble--${option.value} ${selected ? "type-bubble--selected" : ""}`}
                      onClick={() => setType(option.value)}
                    >
                      {selected ? <Check size={16} /> : <Icon size={16} />} {option.label}
                    </button>
                  );
                })}
              </div>
            </div>

            <label>Your message
              <textarea value={message} onChange={(event) => setMessage(event.target.value)} maxLength={1000} rows={5} required
                placeholder="Introduce yourself and say what you're hoping for" />
              <small>{message.length}/1000</small>
            </label>
            <button className="button button--primary" disabled={sending || !type || !message.trim()}>
              <Send /> {sending ? "Sending…" : "Send request"}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
