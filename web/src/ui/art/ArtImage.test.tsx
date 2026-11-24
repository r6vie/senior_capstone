import { fireEvent, render } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ArtImage } from "./ArtImage";

const image = (container: HTMLElement) => container.querySelector("img") as HTMLImageElement;

describe("ArtImage", () => {
  it("stays hidden until the picture has fully arrived", () => {
    const { container } = render(<ArtImage className="book-art" src="/a.webp" />);
    expect(image(container).dataset.pending).toBe("true");
    fireEvent.load(image(container));
    expect(image(container).dataset.pending).toBeUndefined();
  });

  it("hides again while a different picture arrives", () => {
    const { container, rerender } = render(<ArtImage className="book-art" src="/a.webp" />);
    fireEvent.load(image(container));
    rerender(<ArtImage className="book-art" src="/b.webp" />);
    expect(image(container).dataset.pending).toBe("true");
  });

  it("doesn't hide one that failed, so it can't hold anything back", () => {
    const { container } = render(<ArtImage className="book-art" src="/missing.webp" />);
    fireEvent.error(image(container));
    expect(image(container).dataset.pending).toBeUndefined();
  });
});
