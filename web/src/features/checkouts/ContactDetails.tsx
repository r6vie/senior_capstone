import type { components } from "../../api/schema";

type Contact = components["schemas"]["Contact"];

// The reveal (C2): shown only once the author has said yes, to the two people in the checkout, and kept
// on Past meets afterwards (C4).
export function ContactDetails({ name, contact }: { name: string; contact: Contact }) {
  return (
    <div className="checkout-contact">
      <span className="caption">How to reach {name}</span>
      <ul>
        <li>
          <a href={`mailto:${contact.email}`}>{contact.email}</a>
        </li>
        {contact.linkedin_url && (
          <li>
            <a href={contact.linkedin_url} target="_blank" rel="noreferrer">
              LinkedIn profile
            </a>
          </li>
        )}
        {contact.phone && (
          <li>
            {/* Shown as typed; dialled as digits only (and a leading +), which every phone understands. */}
            <a href={`tel:${contact.phone.replace(/(?!^\+)[^\d]/g, "")}`}>{contact.phone}</a>
          </li>
        )}
      </ul>
    </div>
  );
}
