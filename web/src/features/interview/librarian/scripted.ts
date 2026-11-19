// The Librarian's instant moves, with no AI (docs/librarian-plan.md, Scope; LIBRARIAN_SPEC.md §8):
// pasted or résumé-speak text is highlighted with "in your own words?", keyboard mashing gets
// "a classic.", and contact details get a line on Send. They run in the browser the moment they apply.

export const OWN_WORDS = "in your own words?";
export const MASHING = "a classic.";
export const CONTACT_LATER = "contact details come after a yes.";

/** A paste longer than this is highlighted. A short phrase is just quoting yourself. */
export const PASTE_HIGHLIGHT = 40;

// Stock résumé phrases. One alone is often fair; two in a sentence is a résumé talking.
const STOCK = [
  "leverag(e|ed|ing)",
  "spearhead(ed|ing)?",
  "cross-functional",
  "synerg(y|ies|istic)",
  "stakeholders?",
  "results-driven",
  "detail-oriented",
  "team player",
  "self-starter",
  "go-getter",
  "proven track record",
  "track record of",
  "passionate about",
  "drive (impact|results|growth|alignment)",
  "drove (impact|results|growth|alignment)",
  "driving (impact|results|growth|alignment)",
  "to drive",
  "operational excellence",
  "best practices",
  "value-add(ed)?",
  "thought leader(ship)?",
  "fast-paced environment",
  "deliverables",
  "actionable insights",
  "key initiatives",
  "initiatives",
  "alignment",
  "optimi[sz](e|ed|ing) (processes|workflows|operations)",
  "utiliz(e|ed|ing)",
  "facilitat(e|ed|ing)",
  "orchestrat(e|ed|ing)",
  "end-to-end",
  "high-impact",
  "excellence",
];
const STOCK_PATTERN = new RegExp(`\\b(${STOCK.join("|")})\\b`, "gi");

/** Sentences that read like a résumé: two stock phrases or more. Returned exactly as written. */
export function resumeSentences(text: string): string[] {
  const sentences = text.match(/[^.!?\n]+[.!?]?/g) ?? [];
  return sentences
    .map((sentence) => sentence.trim())
    .filter((sentence) => (sentence.match(STOCK_PATTERN) ?? []).length >= 2);
}

const ROWS = ["qwertyuiop", "asdfghjkl;", "zxcvbnm,./", "1234567890"];

function isMash(word: string): boolean {
  const lower = word.toLowerCase();
  if (lower.length < 5) return false;
  if (/(.)\1{4,}/.test(lower)) return true;
  // Four or more keys in a row along one row of the keyboard, either way.
  for (const row of ROWS) {
    for (let index = 0; index + 4 <= lower.length; index++) {
      const run = lower.slice(index, index + 4);
      if (row.includes(run) || row.includes([...run].reverse().join(""))) return true;
    }
  }
  // Six letters or more and not a vowel among them is nobody's word.
  return /^[a-z]{6,}$/.test(lower) && !/[aeiouy]/.test(lower);
}

/** The first run of keyboard mashing, exactly as typed. */
export function mashing(text: string): string | null {
  for (const word of text.split(/\s+/)) {
    const bare = word.replace(/^[^\p{L}\p{N}]+|[^\p{L}\p{N};,./]+$/gu, "");
    if (isMash(bare)) return bare;
  }
  return null;
}

const CONTACT = [
  /[\w.+-]+\s*(@|\(at\)|\[at\])\s*[\w-]+(\.|\s*\(dot\)\s*)[a-z]{2,}/i,
  /(\+?\d[\d\s().-]{8,}\d)/,
  /\bhttps?:\/\/\S+/i,
  /\bwww\.\S+/i,
  /\b[\w-]+\.(com|org|net|io|edu|me|dev|co)\b/i,
  /(^|\s)@[A-Za-z0-9_]{2,}/,
];

export function hasContactDetails(text: string): boolean {
  return CONTACT.some((pattern) => pattern.test(text));
}
