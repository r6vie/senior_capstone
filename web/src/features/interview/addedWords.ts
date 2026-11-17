// Which words of the proposed text weren't in the text it replaces, so they can be underlined. The
// difference then shows without colour and without comparing two columns by eye.

export interface Piece {
  text: string;
  added: boolean;
}

export function addedWords(now: string, proposed: string): Piece[] {
  const before = now.split(/\s+/).filter(Boolean);
  // Words and the spaces between them, so the text comes back exactly as written.
  const after = proposed.split(/(\s+)/);
  const words = after.filter((part) => /\S/.test(part));
  // The longest run of words the two share, by the standard table.
  const table = Array.from({ length: before.length + 1 }, () => new Array<number>(words.length + 1).fill(0));
  for (let i = before.length - 1; i >= 0; i--) {
    for (let j = words.length - 1; j >= 0; j--) {
      const row = table[i] as number[];
      const below = table[i + 1] as number[];
      row[j] =
        before[i] === words[j]
          ? (below[j + 1] as number) + 1
          : Math.max(below[j] as number, row[j + 1] as number);
    }
  }
  const isNew: boolean[] = [];
  let i = 0;
  let j = 0;
  while (j < words.length) {
    if (i < before.length && before[i] === words[j]) {
      isNew.push(false);
      i++;
      j++;
    } else if (i < before.length && (table[i + 1] as number[])[j] === (table[i] as number[])[j]) {
      i++;
    } else {
      isNew.push(true);
      j++;
    }
  }
  // Mostly new text is a rewrite. Underlining nearly every word tells the member nothing.
  if (isNew.filter(Boolean).length > words.length / 2) return [{ text: proposed, added: false }];

  const pieces: Piece[] = [];
  const push = (text: string, added: boolean) => {
    const last = pieces.at(-1);
    if (last && last.added === added) last.text += text;
    else pieces.push({ text, added });
  };
  let word = 0;
  for (const part of after) {
    if (!part) continue;
    if (/\S/.test(part)) {
      push(part, isNew[word] === true);
      word++;
    } else {
      // A space between two added words is part of the addition, so the underline runs through it.
      push(part, isNew[word - 1] === true && isNew[word] === true);
    }
  }
  return pieces;
}
