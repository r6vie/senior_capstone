import { render } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { usePageTitle } from "./usePageTitle";

function Page({ title }: { title: string }) {
  usePageTitle(title);
  return null;
}

describe("usePageTitle", () => {
  it("names the browser tab after the page", () => {
    render(<Page title="Checkouts" />);
    expect(document.title).toBe("Checkouts · Trove");
  });

  it("follows the page when its title changes", () => {
    const { rerender } = render(<Page title="Messages" />);
    rerender(<Page title="Messages with Sam Lee" />);
    expect(document.title).toBe("Messages with Sam Lee · Trove");
  });

  it("falls back to Trove for an empty title", () => {
    render(<Page title="" />);
    expect(document.title).toBe("Trove");
  });
});
