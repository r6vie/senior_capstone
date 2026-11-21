import type { CSSProperties } from "react";
import manifest from "./strata/manifest.json";

// Book art, strata set 1 (docs/design/art/strata/set-1/README.md, approved by Josef 2026-11-21). Each book gets one
// of the ten, chosen from its id, so the same book has the same art on every screen and after every reload, and its
// cover and its opened title page always match. Front end only: the book has no art field.

const covers = import.meta.glob<string>("./strata/covers/*.webp", {
  eager: true,
  query: "?url",
  import: "default",
});
const pages = import.meta.glob<string>("./strata/pages/*.webp", {
  eager: true,
  query: "?url",
  import: "default",
});

export type BookArt = {
  key: string;
  /** The colour of the title and name on this cover: art data, not a UI colour. */
  ink: string;
  cover: string;
  page: string;
};

export const BOOK_ARTS: BookArt[] = manifest.arts.map((art) => ({
  key: art.key,
  ink: art.ink,
  cover: covers[`./strata/${art.cover}`] ?? "",
  page: pages[`./strata/${art.page}`] ?? "",
}));

/** The book's art: a stable hash of its id (FNV-1a), modulo the set. */
export function artFor(bookId: string): BookArt {
  let hash = 0x811c9dc5;
  for (let index = 0; index < bookId.length; index++) {
    hash ^= bookId.charCodeAt(index);
    hash = Math.imul(hash, 0x01000193);
  }
  return BOOK_ARTS[(hash >>> 0) % BOOK_ARTS.length] as BookArt;
}

/** Put on a `.book-cover`: its type takes the art's ink. */
export function coverInk(art: BookArt): CSSProperties {
  return { "--art-ink": art.ink } as CSSProperties;
}

const decoded = new Set<string>();
const decoding = new Map<string, Promise<void>>();

/** Fetches and decodes both of a book's pictures, once; it settles even if one fails, so nothing waits for ever. */
export function loadArt(art: BookArt): Promise<void> {
  const kept = decoding.get(art.key);
  if (kept) return kept;
  const decode = (src: string) => {
    if (typeof Image === "undefined" || !src) return Promise.resolve();
    const image = new Image();
    image.src = src;
    return typeof image.decode === "function" ? image.decode().catch(() => undefined) : Promise.resolve();
  };
  const done = Promise.all([decode(art.cover), decode(art.page)]).then(() => {
    decoded.add(art.key);
  });
  decoding.set(art.key, done);
  return done;
}

/** Whether a book's pictures are already decoded, so it can open at once. */
export function artReady(art: BookArt): boolean {
  return decoded.has(art.key);
}
