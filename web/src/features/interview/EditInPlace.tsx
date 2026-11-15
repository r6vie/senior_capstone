import { useEffect, useId, useRef, useState } from "react";
import { InterviewError } from "./interviewClient";

// Editing the book's own text in place (spec-editing.md §4): a quiet Edit turns the text into fields with
// Save and Cancel. What the member types is kept as a draft while they type, so a refresh, a failed save or
// a refusal never loses it, and the server's reason for refusing is shown as it was written.

export interface EditField {
  key: string;
  label: string;
  value: string;
  /** The API's limit. Typing past it is allowed, so a paste is never cut; Save waits until it fits. */
  max: number;
  multiline?: boolean;
}

const PREFIX = "trove_interview_draft:";

function readEdit(key: string): Record<string, string> | null {
  try {
    const stored = localStorage.getItem(PREFIX + key);
    return stored ? (JSON.parse(stored) as Record<string, string>) : null;
  } catch {
    return null;
  }
}

function writeEdit(key: string, values: Record<string, string> | null) {
  try {
    if (values) localStorage.setItem(PREFIX + key, JSON.stringify(values));
    else localStorage.removeItem(PREFIX + key);
  } catch {
    // Without storage the edit lasts as long as the screen does.
  }
}

/** An edit was under way here before a refresh, so it should open again with the member's words. */
export function hasEditDraft(key: string): boolean {
  return readEdit(key) !== null;
}

export function editKeyFor(userId: string, what: string): string {
  return `${userId}:edit:${what}`;
}

export function EditForm({
  fields,
  draftKey,
  onSave,
  onClose,
}: {
  fields: EditField[];
  draftKey: string;
  /** Saves only what changed. Throws with a sentence for the member when it can't. */
  onSave: (changed: Record<string, string>) => Promise<void>;
  onClose: () => void;
}) {
  const [values, setValues] = useState<Record<string, string>>(() => {
    const saved = readEdit(draftKey);
    return Object.fromEntries(fields.map((field) => [field.key, saved?.[field.key] ?? field.value]));
  });
  const [saving, setSaving] = useState(false);
  const [problem, setProblem] = useState<string | null>(null);
  const baseId = useId();
  const first = useRef<HTMLInputElement & HTMLTextAreaElement>(null);

  useEffect(() => {
    first.current?.focus();
  }, []);

  useEffect(() => {
    const changed = fields.some((field) => values[field.key] !== field.value);
    writeEdit(draftKey, changed ? values : null);
  }, [draftKey, fields, values]);

  const tooLong = fields.find((field) => (values[field.key] ?? "").trim().length > field.max);
  const empty = fields.find((field) => !(values[field.key] ?? "").trim());

  async function save() {
    if (saving || tooLong || empty) return;
    const changed = Object.fromEntries(
      fields
        .filter((field) => (values[field.key] ?? "").trim() !== field.value.trim())
        .map((field) => [field.key, (values[field.key] ?? "").trim()]),
    );
    if (!Object.keys(changed).length) {
      writeEdit(draftKey, null);
      onClose();
      return;
    }
    setSaving(true);
    setProblem(null);
    try {
      await onSave(changed);
      writeEdit(draftKey, null);
      onClose();
    } catch (reason) {
      // The words stay in the fields, whatever happened.
      setProblem(
        reason instanceof InterviewError && reason.message
          ? reason.message
          : "That didn't reach Trove. What you wrote is still here.",
      );
    } finally {
      setSaving(false);
    }
  }

  function cancel() {
    writeEdit(draftKey, null);
    onClose();
  }

  return (
    <form
      className="ed-form"
      onSubmit={(event) => {
        event.preventDefault();
        save();
      }}
    >
      {fields.map((field, index) => {
        const id = `${baseId}-${field.key}`;
        const value = values[field.key] ?? "";
        const over = value.trim().length > field.max;
        const control = {
          id,
          value,
          ref: index === 0 ? first : undefined,
          "aria-invalid": over || undefined,
          onChange: (event: { target: { value: string } }) =>
            setValues((now) => ({ ...now, [field.key]: event.target.value })),
          onKeyDown: (event: React.KeyboardEvent) => {
            if (event.key === "Enter" && (event.metaKey || event.ctrlKey)) {
              event.preventDefault();
              save();
            }
            if (event.key === "Escape") cancel();
          },
        };
        return (
          <div key={field.key} className="field" data-invalid={over || undefined}>
            <label htmlFor={id}>{field.label}</label>
            {field.multiline ? <textarea {...control} rows={4} /> : <input type="text" {...control} />}
            {over && (
              <span className="hint" role="status">
                That's longer than fits here: {field.max} characters at most.
              </span>
            )}
          </div>
        );
      })}
      {problem && (
        <p className="message" role="alert">
          {problem}
        </p>
      )}
      <div className="iv-row">
        <button
          type="submit"
          className="button button-secondary iv-sm"
          aria-busy={saving}
          disabled={Boolean(tooLong || empty) || saving}
          aria-keyshortcuts="Meta+Enter Control+Enter"
        >
          Save
        </button>
        <button type="button" className="button button-quiet iv-sm" onClick={cancel}>
          Cancel
        </button>
      </div>
      {empty && !tooLong && <p className="iv-note">Write something here, or cancel.</p>}
    </form>
  );
}
