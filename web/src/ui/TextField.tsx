import { useId } from "react";

interface Props {
  label: string;
  value: string;
  onChange: (value: string) => void;
  type?: "text" | "email" | "password";
  hint?: string;
  autoComplete?: string;
}

export function TextField({ label, value, onChange, type = "text", hint, autoComplete }: Props) {
  const id = useId();
  return (
    <label htmlFor={id} className="field">
      <span>{label}</span>
      <input
        id={id}
        type={type}
        value={value}
        autoComplete={autoComplete}
        onChange={(event) => onChange(event.target.value)}
      />
      {hint && <small className="muted">{hint}</small>}
    </label>
  );
}
