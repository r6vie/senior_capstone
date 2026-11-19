import { useLayoutEffect, useRef, useState } from "react";
import type { components } from "../../api/schema";
import { Button } from "../../ui/Button";

type Chapter = components["schemas"]["Chapter"];

// Measure the actual wrapped titles, not a fixed number of chapters. A very long single entry
// gets its own scrollable page; resizing or loading a font repaginates without dropping anything.
export function paginateContents(heights: number[], available: number): number[][] {
  const pages: number[][] = [[]];
  let used = 0;
  heights.forEach((height, index) => {
    let page = pages[pages.length - 1] as number[];
    if (page.length && used + height > available) {
      page = [];
      pages.push(page);
      used = 0;
    }
    page.push(index);
    used += height;
  });
  return pages;
}

export function ContentsPage({
  chapters,
  onSelect,
  onTurn,
}: {
  chapters: Chapter[];
  onSelect: (index: number) => void;
  onTurn: () => void;
}) {
  const space = useRef<HTMLDivElement>(null);
  const probe = useRef<HTMLOListElement>(null);
  const [pages, setPages] = useState<number[][]>([chapters.map((_, i) => i)]);
  const [anchor, setAnchor] = useState(0);
  const current = Math.max(
    0,
    pages.findIndex((page) => page.includes(anchor)),
  );
  const page = pages[current] ?? [];

  useLayoutEffect(() => {
    const container = space.current;
    const list = probe.current;
    if (!container || !list) return;
    let cancelled = false;
    function measure() {
      if (cancelled || !container || !list || container.clientHeight === 0) return;
      // Layout heights stay stable while the opening animation scales the book.
      const heights = [...list.children].map((item) => (item as HTMLElement).offsetHeight);
      const next = paginateContents(heights, container.clientHeight);
      setPages((previous) => (JSON.stringify(previous) === JSON.stringify(next) ? previous : next));
    }
    measure();
    const observer = typeof ResizeObserver === "undefined" ? null : new ResizeObserver(measure);
    observer?.observe(container);
    observer?.observe(list);
    document.fonts?.ready.then(measure);
    return () => {
      cancelled = true;
      observer?.disconnect();
    };
  }, []);

  function turn(to: number) {
    setAnchor(pages[to]?.[0] ?? 0);
    onTurn();
    space.current?.scrollTo?.(0, 0);
  }

  return (
    <>
      <div className="reader-contents-space" ref={space}>
        <ol className="reader-contents" aria-label="Chapters">
          {page.map((index) => {
            const chapter = chapters[index];
            if (!chapter) return null;
            return (
              <li key={chapter.id}>
                <button type="button" onClick={() => onSelect(index)}>
                  <span className="reader-chapter-number" aria-hidden="true">
                    {index + 1}
                  </span>
                  <span>{chapter.title}</span>
                  <span className="reader-leader" aria-hidden="true" />
                </button>
              </li>
            );
          })}
        </ol>
        <ol className="reader-contents reader-measure" ref={probe} aria-hidden="true" inert>
          {chapters.map((chapter, index) => (
            <li key={chapter.id}>
              <span className="reader-measure-entry">
                <span className="reader-chapter-number">{index + 1}</span>
                <span>{chapter.title}</span>
                <span className="reader-leader" />
              </span>
            </li>
          ))}
        </ol>
        {!chapters.length && <p>No chapters are available yet.</p>}
      </div>
      <nav className="reader-pagination" aria-label="Contents pages">
        <Button variant="quiet" disabled={current === 0} onClick={() => turn(current - 1)}>
          Previous page
        </Button>
        <span className="reader-page-number" role="status">
          {current + 1} / {pages.length}
        </span>
        <Button variant="quiet" disabled={current === pages.length - 1} onClick={() => turn(current + 1)}>
          Next page
        </Button>
      </nav>
    </>
  );
}
