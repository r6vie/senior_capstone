// Library touches for checkouts (docs/design/system.md, Additions, "Date-due slip" and "Met stamp").

/** A date-due slip: a small card with a label over one printed rule, then the date. Never red. */
export function DateSlip({ label, when }: { label: string; when: string }) {
  return (
    <p className="co-slip">
      <span className="co-slip-label">{label}</span> <span className="co-slip-date">{when}</span>
    </p>
  );
}

/**
 * The ink stamp a met checkout gets: "MET" and the day. `fresh` is the moment someone answers Yes, when it lands
 * with one short press (motion answers what the person did); on Past meets it simply sits there.
 */
export function MetStamp({ on, fresh = false }: { on: string; fresh?: boolean }) {
  return (
    <span className="co-stamp" data-fresh={fresh || undefined} role="img" aria-label={`Met, ${on}`}>
      <span className="co-stamp-word" aria-hidden="true">
        Met
      </span>
      <span className="co-stamp-date" aria-hidden="true">
        {on}
      </span>
    </span>
  );
}
