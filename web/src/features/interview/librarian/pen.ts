// How the Librarian's pen moves (docs/LIBRARIAN_SPEC.md §5). The randomness is seeded from the text,
// so the same line always writes with the same rhythm and wobble, on every visit and every device.

export function seeded(text: string): () => number {
  // FNV-1a for the seed, then mulberry32: small, fast, and the same everywhere.
  let seed = 2166136261;
  for (let index = 0; index < text.length; index++) {
    seed ^= text.charCodeAt(index);
    seed = Math.imul(seed, 16777619);
  }
  return () => {
    seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

export interface Glyph {
  char: string;
  /** Seconds from the start of the line. */
  start: number;
  duration: number;
  /** Pen pressure. */
  opacity: number;
  /** px */
  lift: number;
  /** degrees */
  turn: number;
}

/** Letter by letter: about ten a second, each overlapping the last a little, with pauses at spaces and stops. */
export function strokes(text: string): { glyphs: Glyph[]; total: number } {
  const random = seeded(text);
  const between = (low: number, high: number) => low + (high - low) * random();
  let at = 0;
  let end = 0;
  const glyphs: Glyph[] = [];
  for (const char of text) {
    const duration = 0.1 * between(0.75, 1.25);
    glyphs.push({
      char,
      start: at,
      duration,
      opacity: between(0.86, 1),
      lift: between(-0.6, 0.6),
      turn: between(-1.2, 1.2),
    });
    end = at + duration;
    at += duration * 0.85;
    if (char === " ") at += between(0.12, 0.22);
    else if (".!?".includes(char)) at += between(0.18, 0.3);
    else if (",;:".includes(char)) at += between(0.1, 0.18);
  }
  return { glyphs, total: end };
}

/** The eraser sweeps faster over a short line than a long one. Seconds. */
export function rubDuration(characters: number): number {
  return Math.min(0.45, Math.max(0.2, characters * 0.012));
}

export function reducedMotion(): boolean {
  return (
    typeof window !== "undefined" && Boolean(window.matchMedia?.("(prefers-reduced-motion: reduce)").matches)
  );
}
