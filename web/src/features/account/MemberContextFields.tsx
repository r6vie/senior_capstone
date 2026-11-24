import type { components } from "../../api/schema";
import "./MemberContextFields.css";

export type MemberContext = components["schemas"]["MemberContextUpdate"];
export type Affiliation = MemberContext["affiliations"][number];

const AFFILIATIONS: { value: Affiliation; label: string }[] = [
  { value: "current_student", label: "Current student" },
  { value: "alumni", label: "Alumni" },
];

export function MemberContextFields({
  affiliations,
  founder,
  onAffiliationsChange,
  onFounderChange,
}: {
  affiliations: Affiliation[];
  founder: boolean;
  onAffiliationsChange: (affiliations: Affiliation[]) => void;
  onFounderChange: (founder: boolean) => void;
}) {
  function change(value: Affiliation, checked: boolean) {
    onAffiliationsChange(
      AFFILIATIONS.map((option) => option.value).filter((option) =>
        option === value ? checked : affiliations.includes(option),
      ),
    );
  }

  return (
    <fieldset className="member-context">
      <legend>Your place in the CWRU community</legend>
      <p className="muted">Choose both when both apply.</p>
      <div className="member-context-choices">
        {AFFILIATIONS.map(({ value, label }) => (
          <label className="choice" key={value}>
            <input
              type="checkbox"
              checked={affiliations.includes(value)}
              onChange={(event) => change(value, event.target.checked)}
            />
            <span>{label}</span>
          </label>
        ))}
        <label className="choice">
          <input
            type="checkbox"
            checked={founder}
            onChange={(event) => onFounderChange(event.target.checked)}
          />
          <span>I am a founder</span>
        </label>
      </div>
      <p className="muted">This is not shown on your book and does not limit who you can meet.</p>
    </fieldset>
  );
}
