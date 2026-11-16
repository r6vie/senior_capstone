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
