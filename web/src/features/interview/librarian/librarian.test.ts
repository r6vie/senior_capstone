import { fold, occurrencesOf, place } from "./anchors";
import { rubDuration, strokes } from "./pen";
import { hasContactDetails, mashing, resumeSentences } from "./scripted";
import { isSilent } from "./silence";

describe("the pen", () => {
  it("writes the same line with the same rhythm every time", () => {
    expect(strokes("says who?")).toEqual(strokes("says who?"));
    expect(strokes("says who?").glyphs[0]?.start).toBe(0);
  });

  it("runs at about ten letters a second and pauses at spaces and stops", () => {
    const line = strokes("a number would help.");
    expect(line.total).toBeGreaterThan(1.4);
    expect(line.total).toBeLessThan(3.2);
    const plain = strokes("abcd").total;
    const spaced = strokes("ab cd").total;
    expect(spaced - plain).toBeGreaterThan(0.1);
    for (const glyph of line.glyphs) {
      expect(glyph.opacity).toBeGreaterThanOrEqual(0.86);
      expect(Math.abs(glyph.lift)).toBeLessThanOrEqual(0.6);
      expect(Math.abs(glyph.turn)).toBeLessThanOrEqual(1.2);
    }
  });

  it("rubs out in 0.2 to 0.45 seconds, by width", () => {
    expect(rubDuration(3)).toBe(0.2);
    expect(rubDuration(200)).toBe(0.45);
  });
});

describe("anchors", () => {
  it("finds whole words in any case, with curly quotes counted as straight", () => {
    expect(occurrencesOf("Everyone said everyone", "everyone")).toEqual([0, 14]);
    expect(occurrencesOf("the build-breaker", "build")).toEqual([4]);
    expect(occurrencesOf("rebuild it", "build")).toEqual([]);
    expect(occurrencesOf("I didn’t know", "didn't")).toEqual([2]);
    expect(fold("Didn’t").length).toBe(6);
  });

  it("places a mark on the named occurrence, and not at all once its words are gone", () => {
    const mark = { anchor: "the test", occurrence: 2 };
    expect(place("the test, then the test again", [mark])).toEqual([{ item: mark, start: 15, end: 23 }]);
    expect(place("the test, then a quiz", [mark])).toEqual([]);
  });

  it("never lets two marks overlap", () => {
    const first = { anchor: "stale cache", occurrence: 1 };
    const second = { anchor: "cache", occurrence: 1 };
    expect(place("a stale cache", [first, second]).map((p) => p.item)).toEqual([first]);
  });
});

describe("silence", () => {
  it("goes quiet on what an answer is about", () => {
    expect(isSilent("my dad died the spring I started college")).toBe(true);
    expect(isSilent("after my parents' divorce I moved twice")).toBe(true);
    expect(isSilent("we broke up the week of the demo")).toBe(true);
  });

  it("stays on for a passing word or a harmless phrase", () => {
    expect(isSilent("I miss my mom’s lasagna")).toBe(false);
    expect(isSilent("I listen to death metal while I debug")).toBe(false);
    expect(isSilent("the deadline was killing me")).toBe(false);
    expect(isSilent("the night the build broke")).toBe(false);
  });
});

describe("instant moves", () => {
  it("highlights a sentence that reads like a résumé, and leaves a plain one alone", () => {
    const text = "Spearheaded cross-functional initiatives to drive stakeholder alignment. Then I went home.";
    expect(resumeSentences(text)).toEqual([
      "Spearheaded cross-functional initiatives to drive stakeholder alignment.",
    ]);
    expect(resumeSentences("I leveraged a friend's car.")).toEqual([]);
  });

  it("notices keyboard mashing, not real words", () => {
    expect(mashing("it was asdfgh honestly")).toBe("asdfgh");
    expect(mashing("aaaaaaa")).toBe("aaaaaaa");
    expect(mashing("rhythm and strength")).toBeNull();
    expect(mashing("I fixed the pipeline")).toBeNull();
  });

  it("knows contact details when it sees them", () => {
    expect(hasContactDetails("write to me at sam@case.edu")).toBe(true);
    expect(hasContactDetails("call 216 555 0199")).toBe(true);
    expect(hasContactDetails("find me @samwrites")).toBe(true);
    expect(hasContactDetails("I found it in 11 weeks")).toBe(false);
  });
});
