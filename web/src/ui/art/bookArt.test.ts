import { describe, expect, it } from "vitest";
import { artFor, BOOK_ARTS } from "./bookArt";

describe("book art", () => {
  it("pools both categories, each art named by category and key", () => {
    expect(BOOK_ARTS.filter((art) => art.category === "strata")).toHaveLength(10);
    expect(BOOK_ARTS.filter((art) => art.category === "watercolor")).toHaveLength(10);
    expect(new Set(BOOK_ARTS.map((art) => art.id)).size).toBe(BOOK_ARTS.length);
    expect(BOOK_ARTS.map((art) => art.id)).toContain("watercolor/lake");
    expect(BOOK_ARTS.map((art) => art.id)).toContain("strata/lake");
    for (const art of BOOK_ARTS) {
      expect(art.cover).not.toBe("");
      expect(art.page).not.toBe("");
    }
  });

  it("gives a book the same art every time, and reaches every art", () => {
    expect(artFor("book-1")).toBe(artFor("book-1"));
    const seen = new Set<string>();
    for (let index = 0; index < 2000; index++) seen.add(artFor(`book-${index}`).id);
    expect(seen.size).toBe(BOOK_ARTS.length);
  });

  it("gives every cover its quick paint-in clip, its own and in both formats", () => {
    for (const art of BOOK_ARTS) {
      expect(art.anim?.webm).toMatch(new RegExp(`${art.key}-quick.*\\.webm`));
      expect(art.anim?.mp4).toMatch(new RegExp(`${art.key}-quick.*\\.mp4`));
    }
  });

  it("keeps the knockout behind the name on strata covers only", () => {
    for (const art of BOOK_ARTS) expect(art.knockout).toBe(art.category === "strata");
  });

  it("uses the design an author chose, and the id's own art when there is none or it's unknown", () => {
    const chosen = BOOK_ARTS.find((art) => art.id !== artFor("nora-book").id);
    expect(artFor("nora-book", chosen?.id)).toBe(chosen);
    expect(artFor("nora-book", null)).toBe(artFor("nora-book"));
    expect(artFor("nora-book", "mosaic/nowhere")).toBe(artFor("nora-book"));
  });
});
