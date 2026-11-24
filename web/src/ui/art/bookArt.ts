import type { CSSProperties } from "react";
import strata from "./strata/manifest.json";
import watercolor from "./watercolor/manifest.json";

// Book art in two categories, each approved by Josef: strata set 1 (docs/design/art/strata/set-1/README.md,
// 2026-11-21) and watercolor set 1 (docs/design/art/watercolor/set-1/README.md, 2026-11-23). A book's art is chosen
// from its id out of every art in every category, so each art is equally likely, the same book has the same art on
// every screen and after every reload, and its cover and its opened title page always match. Front end only: the
// book has no art field. The category is on each art so the design chooser can group by it.

const covers = import.meta.glob<string>(["./strata/covers/*.webp", "./watercolor/covers/*.webp"], {
  eager: true,
  query: "?url",
  import: "default",
});
const pages = import.meta.glob<string>(["./strata/pages/*.webp", "./watercolor/pages/*.webp"], {
  eager: true,
  query: "?url",
  import: "default",
});

// The quick paint-in clip of each cover (about 4 seconds, 472x688 like the cover; Josef, 2026-11-23), played once when a
// member's book first lands on the shelf. Its first frame is the white cover and its last is the cover itself.
// URLs only: a clip is downloaded when a <video> asks for it.
const clips = import.meta.glob<string>(
  [
    "./strata/anim/*-quick.webm",
    "./strata/anim/*-quick.mp4",
    "./watercolor/anim/*-quick.webm",
    "./watercolor/anim/*-quick.mp4",
  ],
  { eager: true, query: "?url", import: "default" },
);

export type ArtCategory = "strata" | "watercolor";

export type BookArt = {
  /** Category and key together: keys repeat across categories (both have a lake). */
  id: string;
  category: ArtCategory;
  key: string;
  name: string;
  /** The colour of the title and name on this cover: art data, not a UI colour. */
  ink: string;
  /** The colour of the opened book's title, which sits on paper. */
  pageInk: string;
  /** Strata covers set the name on a white knockout; watercolour covers set it on the paint. */
  knockout: boolean;
  cover: string;
  page: string;
  /** The cover painting itself in, as WebM and MP4 (the browser picks one). Null if this art has no clip. */
  anim: { webm: string; mp4: string } | null;
};

function clipOf(category: ArtCategory, key: string): BookArt["anim"] {
  const webm = clips[`./${category}/anim/${key}-quick.webm`];
  const mp4 = clips[`./${category}/anim/${key}-quick.mp4`];
  return webm && mp4 ? { webm, mp4 } : null;
}

type Entry = { key: string; name: string; cover: string; page: string };

function arts<T extends Entry>(
  category: ArtCategory,
  list: T[],
  inks: (art: T) => [string, string],
): BookArt[] {
  return list.map((art) => {
    const [ink, pageInk] = inks(art);
    return {
      id: `${category}/${art.key}`,
      category,
      key: art.key,
      name: art.name,
      ink,
      pageInk,
      knockout: category === "strata",
      cover: covers[`./${category}/${art.cover}`] ?? "",
      page: pages[`./${category}/${art.page}`] ?? "",
      anim: clipOf(category, art.key),
    };
  });
}

/** Every art, in a fixed order: a book's art depends on it, so new sets go on the end. */
export const BOOK_ARTS: BookArt[] = [
  // A strata title page has always been set in the UI's ink.
  ...arts("strata", strata.arts, (art) => [art.ink, "var(--ink)"]),
  ...arts("watercolor", watercolor.arts, (art) => [art.coverInk, art.pageInk]),
];

/** The book's art: a stable hash of its id (FNV-1a), modulo every art. */
export function artFor(bookId: string): BookArt {
  let hash = 0x811c9dc5;
  for (let index = 0; index < bookId.length; index++) {
    hash ^= bookId.charCodeAt(index);
    hash = Math.imul(hash, 0x01000193);
  }
  return BOOK_ARTS[(hash >>> 0) % BOOK_ARTS.length] as BookArt;
}

/** Put on a `.book-cover`: its type takes the art's ink, and a watercolour cover drops the name's knockout. */
export function coverInk(art: BookArt): CSSProperties {
  return {
    "--art-ink": art.ink,
    "--art-knockout": art.knockout ? "var(--white)" : "transparent",
  } as CSSProperties;
}

/** Put on the opened book's title page. */
export function pageInk(art: BookArt): CSSProperties {
  return { "--page-ink": art.pageInk } as CSSProperties;
}

const decoded = new Set<string>();
const decoding = new Map<string, Promise<void>>();

/** Fetches and decodes both of a book's pictures, once; it settles even if one fails, so nothing waits for ever. */
export function loadArt(art: BookArt): Promise<void> {
  const kept = decoding.get(art.id);
  if (kept) return kept;
  const decode = (src: string) => {
    if (typeof Image === "undefined" || !src) return Promise.resolve();
    const image = new Image();
    image.src = src;
    return typeof image.decode === "function" ? image.decode().catch(() => undefined) : Promise.resolve();
  };
  const done = Promise.all([decode(art.cover), decode(art.page)]).then(() => {
    decoded.add(art.id);
  });
  decoding.set(art.id, done);
  return done;
}

/** Whether a book's pictures are already decoded, so it can open at once. */
export function artReady(art: BookArt): boolean {
  return decoded.has(art.id);
}
