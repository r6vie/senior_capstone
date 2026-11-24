// The API sends some times without a timezone. They are all UTC.
export function parseApiDate(value: string): Date {
  return new Date(/(Z|[+-]\d\d:\d\d)$/i.test(value) ? value : `${value}Z`);
}

export function formatDay(value: string): string {
  return parseApiDate(value).toLocaleDateString(undefined, {
    weekday: "long",
    month: "long",
    day: "numeric",
  });
}

/** A day as a library slip prints it: "Fri, Nov 27". */
export function slipDay(value: string): string {
  return parseApiDate(value).toLocaleDateString(undefined, {
    weekday: "short",
    month: "short",
    day: "numeric",
  });
}

/** A day and time for a slip: "Thu, Dec 3 · 3:00 PM", in this person's own time zone. */
export function slipWhen(value: string): string {
  const date = parseApiDate(value);
  return `${slipDay(value)} · ${date.toLocaleTimeString(undefined, { hour: "numeric", minute: "2-digit" })}`;
}
