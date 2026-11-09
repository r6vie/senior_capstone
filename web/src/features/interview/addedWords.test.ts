import { addedWords } from "./addedWords";

function added(now: string, proposed: string) {
  return addedWords(now, proposed)
    .filter((piece) => piece.added)
    .map((piece) => piece.text.trim());
}

describe("addedWords", () => {
  it("finds words added at the end", () => {
    const now = "I test the switch with a meter before I do anything else.";
    expect(added(now, `${now} Then I order the part.`)).toEqual(["Then I order the part."]);
  });

  it("finds words added in the middle", () => {
    expect(added("I test the switch first.", "I test the coil switch first.")).toEqual(["coil"]);
  });

  it("marks nothing when the text is the same", () => {
    expect(added("Same words.", "Same words.")).toEqual([]);
  });

  it("keeps every word of the proposed text, in order", () => {
    const proposed = "A new line. I test the switch with a meter, always.";
    const pieces = addedWords("I test the switch with a meter, always.", proposed);
    expect(pieces.map((piece) => piece.text).join("")).toBe(proposed);
  });

  it("underlines a run of new words as one, with no gaps", () => {
    const pieces = addedWords("I test the switch first.", "I test the old coil switch first.");
    expect(pieces.filter((piece) => piece.added).map((piece) => piece.text)).toEqual(["old coil"]);
  });

  it("underlines nothing when more than half the words are new", () => {
    const proposed = "Entirely different words here and only the one same";
    expect(addedWords("The same text as before", proposed)).toEqual([{ text: proposed, added: false }]);
  });
});
