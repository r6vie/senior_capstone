// Marks sit on the member's exact words. Every edit finds each anchor again; one that's gone is rubbed
// out. Matching is the server's (api/trove/interview/librarian.py): whole words, any case, and curly
// quotes and dashes counted as straight ones.

const FOLD: Record<string, string> = {
  "‘": "'",
  "’": "'",
  "“": '"',
  "”": '"',
  "–": "-",
  "—": "-",
};

/** Same length as the text, so a position in one is the same position in the other. */
export function fold(text: string): string {
  let out = "";
  for (const char of text) {
    const folded = FOLD[char] ?? char.toLowerCase();
    // A few letters change length when lowercased; keep those as they are so positions still line up.
    out += folded.length === char.length ? folded : char;
  }
  return out;
}

const WORDISH = /[\p{L}\p{N}_']/u;

/** Where each whole-word occurrence of `anchor` starts in `text`. */
export function occurrencesOf(text: string, anchor: string): number[] {
  const hay = fold(text);
  const needle = fold(anchor.trim());
  if (!needle) return [];
  const found: number[] = [];
  let from = 0;
  for (;;) {
    const at = hay.indexOf(needle, from);
    if (at < 0) return found;
    const before = hay[at - 1];
    const after = hay[at + needle.length];
    if ((!before || !WORDISH.test(before)) && (!after || !WORDISH.test(after))) found.push(at);
    from = at + 1;
  }
}

export interface Anchored {
  anchor: string;
  /** 1 is the first. */
  occurrence: number;
}

export interface Placed<T> {
  item: T;
  start: number;
  end: number;
}

/** Where each mark lands in the text now, in reading order. A mark whose words are gone, or that would
 * overlap one placed before it, isn't placed. */
export function place<T extends Anchored>(text: string, items: T[]): Placed<T>[] {
  const placed: Placed<T>[] = [];
  for (const item of items) {
    const at = occurrencesOf(text, item.anchor)[item.occurrence - 1];
    if (at === undefined) continue;
    const span = { item, start: at, end: at + item.anchor.trim().length };
    if (placed.some((other) => span.start < other.end && other.start < span.end)) continue;
    placed.push(span);
  }
  return placed.sort((a, b) => a.start - b.start);
}

export function holds(text: string, anchor: string): boolean {
  return occurrencesOf(text, anchor).length > 0;
}
