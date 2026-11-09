import { addedWords } from "./addedWords";

function added(now: string, proposed: string) {
  return addedWords(now, proposed)
    .filter((piece) => piece.added)
    .map((piece) => piece.text.trim());
}

describe("addedWords", () => {
  it("finds words added at the end", () => {
    expect(added("I test the switch.", "I test the switch. Then I order the part.")).toEqual([
      "Then I order the part.",
    ]);
  });

  it("finds words added in the middle", () => {
    expect(added("I test the switch first.", "I test the coil switch first.")).toEqual(["coil"]);
  });

  it("marks nothing when the text is the same", () => {
    expect(added("Same words.", "Same words.")).toEqual([]);
  });

  it("keeps every word of the proposed text, in order", () => {
    const proposed = "A new first line. I test the switch.";
    const pieces = addedWords("I test the switch.", proposed);
    expect(pieces.map((piece) => piece.text).join("")).toBe(proposed);
  });
});
