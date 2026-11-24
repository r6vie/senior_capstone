import { useEffect } from "react";

/** Names the browser tab after the page, "<title> · Trove", so tabs, history and screen readers can tell pages apart. */
export function usePageTitle(title: string) {
  useEffect(() => {
    document.title = title ? `${title} · Trove` : "Trove";
  }, [title]);
}
