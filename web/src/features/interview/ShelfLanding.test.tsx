import { act, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { artFor } from "../../ui/art/bookArt";
import { ShelfLanding } from "./ShelfLanding";

const book = { id: "mine", title: "Check the slats first", authorName: "Ingrid Solberg" };
const neighbours = ["Above the Tree Line", "Room to Grow", "After Hours", "The High Desert"].map(
  (title, index) => ({
    id: `n${index}`,
    title,
    authorName: "Someone Else",
  }),
);

function reduceMotion(reduce: boolean) {
  Object.defineProperty(window, "matchMedia", {
    configurable: true,
    value: (query: string) => ({ matches: reduce && query.includes("reduce"), media: query }),
  });
}

const root = () => document.querySelector(".shelf-landing") as HTMLElement;
const clip = () => document.querySelector("video");

beforeEach(() => {
  reduceMotion(false);
  vi.spyOn(HTMLMediaElement.prototype, "play").mockResolvedValue(undefined);
});

afterEach(() => {
  vi.useRealTimers();
  vi.restoreAllMocks();
});

describe("ShelfLanding", () => {
  it("stands the member's book in the middle of the row, between its neighbours, on one ledge", () => {
    render(<ShelfLanding book={book} neighbours={neighbours} from={null} />);
    const row = document.querySelector(".sl-row") as HTMLElement;
    const order = [...row.querySelectorAll(".book")].map((element) => element.textContent);
    expect(order).toEqual([
      "Above the Tree LineSomeone Else",
      "Room to GrowSomeone Else",
      "Check the slats firstIngrid Solberg",
      "After HoursSomeone Else",
      "The High DesertSomeone Else",
    ]);
    expect(
      screen.getByRole("img", { name: "Check the slats first, by Ingrid Solberg, on the shelf" }),
    ).toBeTruthy();
    expect(document.querySelectorAll(".ledge")).toHaveLength(1);
  });

  it("paints the cover in with its quick clip, inside the cover under the type, then shows the still cover", async () => {
    const landed = vi.fn();
    render(<ShelfLanding book={book} neighbours={neighbours} from={null} onLanded={landed} />);
    // White until the clip can play.
    expect(root().dataset.phase).toBe("white");
    const video = clip() as HTMLVideoElement;
    expect(video.closest(".sl-mine .book-cover")).toBeTruthy();
    expect(video.muted).toBe(true);
    expect(video.hasAttribute("playsinline")).toBe(true);
    expect(video.hasAttribute("controls")).toBe(false);
    const sources = [...video.querySelectorAll("source")].map((source) => source.getAttribute("src"));
    expect(sources).toEqual([artFor(book.id).anim?.webm, artFor(book.id).anim?.mp4]);

    await act(async () => {
      fireEvent.canPlay(video);
    });
    expect(HTMLMediaElement.prototype.play).toHaveBeenCalled();
    // Still white until the clip really plays: the title's ink change is timed from then.
    expect(root().dataset.phase).toBe("white");
    await act(async () => {
      fireEvent.playing(video);
    });
    expect(root().dataset.phase).toBe("paint");
    expect(landed).not.toHaveBeenCalled();

    await act(async () => {
      fireEvent.ended(video);
    });
    expect(root().dataset.phase).toBe("done");
    expect(clip()).toBeNull();
    // The still cover was there all along, under the clip; nothing fades it in (that's only for a clip that failed).
    expect(document.querySelector(".sl-mine img.book-art")?.getAttribute("src")).toBe(artFor(book.id).cover);
    expect(root().dataset.fallback).toBeUndefined();
    expect(landed).toHaveBeenCalledTimes(1);
  });

  it("with reduced motion, shows the finished shelf at once with the still cover, and says it has landed", () => {
    reduceMotion(true);
    const landed = vi.fn();
    const from = new DOMRect(100, 0, 236, 344);
    render(<ShelfLanding book={book} neighbours={neighbours} from={from} onLanded={landed} />);
    expect(root().dataset.phase).toBe("done");
    expect(root().dataset.reduced).toBe("true");
    expect(clip()).toBeNull();
    expect(document.querySelector(".sl-mine img.book-art")?.getAttribute("src")).toBe(artFor(book.id).cover);
    expect(landed).toHaveBeenCalledTimes(1);
  });

  it("shows the still cover if the clip can't start in time, and still says it has landed", () => {
    vi.useFakeTimers();
    const landed = vi.fn();
    render(<ShelfLanding book={book} neighbours={neighbours} from={null} onLanded={landed} />);
    expect(root().dataset.phase).toBe("white");
    act(() => {
      vi.advanceTimersByTime(2600);
    });
    expect(root().dataset.phase).toBe("done");
    expect(root().dataset.fallback).toBe("true");
    expect(clip()).toBeNull();
    expect(landed).toHaveBeenCalledTimes(1);
  });

  it("shows the still cover if the browser refuses to play the clip", async () => {
    vi.mocked(HTMLMediaElement.prototype.play).mockRejectedValue(new Error("NotAllowedError"));
    render(<ShelfLanding book={book} neighbours={neighbours} from={null} />);
    await act(async () => {
      fireEvent.canPlay(clip() as HTMLVideoElement);
    });
    expect(root().dataset.phase).toBe("done");
    expect(root().dataset.fallback).toBe("true");
  });

  it("flies in from where the closed book was, then waits white on the shelf for its clip", async () => {
    const finished = Promise.resolve();
    const animate = vi.fn(() => ({ finished, cancel: vi.fn() }));
    Object.defineProperty(HTMLElement.prototype, "animate", { configurable: true, value: animate });
    try {
      render(<ShelfLanding book={book} neighbours={neighbours} from={new DOMRect(400, 0, 236, 344)} />);
      expect(root().dataset.phase).toBe("flight");
      // The book's flight, its turn, and each group of neighbours sliding apart.
      expect(animate).toHaveBeenCalledTimes(4);
      const [frames, timing] = animate.mock.calls[0] as unknown as [Keyframe[], KeyframeAnimationOptions];
      expect(String(frames[0]?.transform)).toContain("translate(400px, 0px)");
      expect(frames.at(-1)?.transform).toBe("none");
      expect(timing.duration).toBe(1600);
      await act(async () => {
        await finished;
      });
      expect(root().dataset.phase).toBe("white");
    } finally {
      delete (HTMLElement.prototype as { animate?: unknown }).animate;
    }
  });
});
