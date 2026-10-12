import { Check, Eye, EyeOff, Lock, Pencil, Trash2, Users, X } from "lucide-react";
import { FormEvent, useState } from "react";
import type { Coverage, Fact, FactEdit, FactKind, Visibility } from "../types";

export const KIND_LABELS: Record<FactKind, string> = {
  need: "Needs", offer: "Can offer", experience: "Experience", goal: "Goals",
  background: "Background", preference: "Preferences", availability: "Availability", other: "Other",
};

export const VISIBILITY_OPTIONS: { value: Visibility; label: string; hint: string }[] = [
  { value: "public", label: "Everyone", hint: "Shown on your profile" },
  { value: "matches_only", label: "Matches only", hint: "Shown to people you're matched or connected with" },
  { value: "private", label: "Only me", hint: "Never shown, but still helps us find you good matches" },
];

const VISIBILITY_ICONS: Record<Visibility, typeof Eye> = { public: Eye, matches_only: Users, private: Lock };

export function CoverageMeter({ coverage }: { coverage: Coverage }) {
  return (
    <div className="coverage">
      <div className="coverage__top">
        <strong>Profile strength</strong>
        <span>{coverage.percent}%</span>
      </div>
      <div className="coverage__bar" role="progressbar" aria-valuenow={coverage.percent} aria-valuemin={0} aria-valuemax={100} aria-label="Profile strength">
        <span style={{ width: `${coverage.percent}%` }} />
      </div>
      <ul className="coverage__areas">
        {coverage.areas.map((area) => (
          <li key={area.area} className={`coverage__area coverage__area--${area.status}`}>
            <span className="coverage__dot" aria-hidden="true" />
            {area.label}
            {!area.important && <small>optional</small>}
            <span className="sr-only">: {area.status}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

interface FactCardProps {
  fact: Fact;
  onEdit: (fact: Fact, edit: FactEdit) => Promise<void>;
  onDelete: (fact: Fact) => Promise<void>;
}

export function FactCard({ fact, onEdit, onDelete }: FactCardProps) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(fact.text);
  const [busy, setBusy] = useState(false);
  const VisibilityIcon = VISIBILITY_ICONS[fact.visibility];

  async function run(action: () => Promise<void>) {
    setBusy(true);
    try { await action(); } finally { setBusy(false); }
  }

  function save(event: FormEvent) {
    event.preventDefault();
    const text = draft.trim();
    if (!text) return;
    void run(async () => { await onEdit(fact, { text }); setEditing(false); });
  }

  return (
    <article className={`fact-card ${fact.confirmed ? "" : "fact-card--new"}`}>
      {!fact.confirmed && <span className="fact-card__badge">New</span>}
      {editing ? (
        <form className="fact-card__edit" onSubmit={save}>
          <textarea value={draft} onChange={(event) => setDraft(event.target.value)} maxLength={400} rows={3} aria-label="Fact text" autoFocus />
          <div>
            <button type="button" className="button button--quiet" onClick={() => { setEditing(false); setDraft(fact.text); }} disabled={busy}><X size={16} /> Cancel</button>
            <button className="button button--primary" disabled={busy || !draft.trim()}><Check size={16} /> Save</button>
          </div>
        </form>
      ) : (
        <p className="fact-card__text">{fact.text}</p>
      )}
      {fact.links.length > 0 && !editing && (
        <div className="tags">{fact.links.map((key) => <span className="tag tag--link" key={key}>{key.split(":")[1].replaceAll("-", " ")}</span>)}</div>
      )}
      {!editing && (
        <div className="fact-card__actions">
          <label className="fact-card__visibility">
            <VisibilityIcon size={15} aria-hidden="true" />
            <span className="sr-only">Who can see this</span>
            <select
              value={fact.visibility}
              disabled={busy}
              onChange={(event) => void run(() => onEdit(fact, { visibility: event.target.value as Visibility }))}
              title={VISIBILITY_OPTIONS.find((option) => option.value === fact.visibility)?.hint}
            >
              {VISIBILITY_OPTIONS.map((option) => <option key={option.value} value={option.value}>{option.label}</option>)}
            </select>
          </label>
          <div className="fact-card__buttons">
            {!fact.confirmed && (
              <button className="icon-button" onClick={() => void run(() => onEdit(fact, { confirmed: true }))} disabled={busy} aria-label="Looks right" title="Looks right"><Check size={17} /></button>
            )}
            <button className="icon-button" onClick={() => setEditing(true)} disabled={busy} aria-label="Edit" title="Edit"><Pencil size={16} /></button>
            <button className="icon-button icon-button--danger" onClick={() => void run(() => onDelete(fact))} disabled={busy} aria-label="Delete" title="Delete"><Trash2 size={16} /></button>
          </div>
        </div>
      )}
    </article>
  );
}

interface FactListProps extends Omit<FactCardProps, "fact"> {
  facts: Fact[];
  empty: string;
}

export function FactList({ facts, onEdit, onDelete, empty }: FactListProps) {
  if (!facts.length) return <p className="fact-list__empty"><EyeOff size={16} /> {empty}</p>;
  const kinds = (Object.keys(KIND_LABELS) as FactKind[]).filter((kind) => facts.some((fact) => fact.kind === kind));
  return (
    <div className="fact-list">
      {kinds.map((kind) => (
        <section key={kind}>
          <h3>{KIND_LABELS[kind]}</h3>
          {facts.filter((fact) => fact.kind === kind).map((fact) => (
            <FactCard key={`${fact.id}-${fact.updated_at}`} fact={fact} onEdit={onEdit} onDelete={onDelete} />
          ))}
        </section>
      ))}
    </div>
  );
}
