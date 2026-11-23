import { type RefObject, useEffect, useRef } from "react";
import { useLocation } from "react-router-dom";

const WAIT_MS = 3_000;

/**
 * After moving to another page, puts keyboard and screen-reader focus on the new page's heading, so the next Tab
 * starts in the page rather than back in the top bar. Only when nothing else has taken focus (pages that place it
 * themselves, like My book, keep theirs), not on the first load, and not for the book reader, which manages its own.
 */
export function usePageFocus(page: RefObject<HTMLElement | null>, topBar: RefObject<HTMLElement | null>) {
  const { pathname } = useLocation();
  const first = useRef(true);

  useEffect(() => {
    if (first.current) {
      first.current = false;
      return;
    }
    if (pathname.startsWith("/books/")) return;
    const started = Date.now();
    let frame = 0;
    const look = () => {
      const active = document.activeElement;
      const free = !active || active === document.body || Boolean(topBar.current?.contains(active));
      if (!free) return;
      // The heading may not exist yet, or may still be hidden while the page loads.
      const heading = page.current?.querySelector("h1");
      const visible = heading && (heading.checkVisibility?.({ visibilityProperty: true }) ?? true);
      if (heading && visible) {
        if (!heading.hasAttribute("tabindex")) heading.setAttribute("tabindex", "-1");
        heading.focus({ preventScroll: true });
        return;
      }
      if (Date.now() - started < WAIT_MS) frame = requestAnimationFrame(look);
    };
    frame = requestAnimationFrame(look);
    return () => cancelAnimationFrame(frame);
  }, [pathname, page, topBar]);
}
