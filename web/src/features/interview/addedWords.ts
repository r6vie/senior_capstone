// Which words of the proposed text weren't in the text it replaces, so they can be underlined. The
// difference then shows without colour and without comparing two columns by eye.

export interface Piece {
  text: string;
  added: boolean;
}

export function addedWords(now: string, proposed: string): Piece[] {
  const before = now.split(/(\s+)/);
  const after = proposed.split(/(\s+)/);
  // The longest run the two share, by the standard table.
  const table = Array.from({ length: before.length + 1 }, () => new Array<number>(after.length + 1).fill(0));
  for (let i = before.length - 1; i >= 0; i--) {
    for (let j = after.length - 1; j >= 0; j--) {
      const row = table[i] as number[];
      const below = table[i + 1] as number[];
      row[j] =
        before[i] === after[j]
          ? (below[j + 1] as number) + 1
          : Math.max(below[j] as number, row[j + 1] as number);
    }
  }
  const pieces: Piece[] = [];
  const push = (text: string, added: boolean) => {
    const last = pieces.at(-1);
    if (last && last.added === added) last.text += text;
    else pieces.push({ text, added });
  };
  let i = 0;
  for (let j = 0; j < after.length; j++) {
    const word = after[j] as string;
    while (
      i < before.length &&
      before[i] !== word &&
      (table[i + 1] as number[])[j] === (table[i] as number[])[j]
    ) {
      i++;
    }
    if (i < before.length && before[i] === word) {
      push(word, false);
      i++;
    } else {
      // A space between two added words reads as part of the addition.
      push(word, /\S/.test(word) || pieces.at(-1)?.added === true);
    }
  }
  return pieces;
}
