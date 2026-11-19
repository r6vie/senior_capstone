import { describe, expect, it } from "vitest";
import { paginateContents } from "./ContentsPage";

describe("contents pagination", () => {
  it("fits all chapters when there is room", () => {
    expect(paginateContents([44, 44, 70], 200)).toEqual([[0, 1, 2]]);
  });
  it("continues wrapped titles without dropping entries", () => {
    expect(paginateContents([44, 110, 80, 90, 44], 160)).toEqual([[0, 1], [2], [3, 4]]);
  });
  it("keeps an oversized entry on a page by itself", () => {
    expect(paginateContents([220, 44, 44], 100)).toEqual([[0], [1, 2]]);
  });
  it("handles an empty book", () => {
    expect(paginateContents([], 100)).toEqual([[]]);
  });
});
