import { StrictMode, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import { artFor, BOOK_ARTS } from "../../ui/art/bookArt";
import "../../ui/styles.css";
import { type LandingBook, ShelfLanding } from "./ShelfLanding";

// Development only (shelf-landing.html): ShelfLanding on its own, replayable, with any cover art.

const NEIGHBOURS: LandingBook[] = [
  { id: "n-above", title: "Above the Tree Line", authorName: "Ingrid Solberg" },
  { id: "n-room", title: "Room to Grow", authorName: "Noah Bergstrom" },
  { id: "n-after", title: "After Hours", authorName: "Marcus Bell" },
  { id: "n-desert", title: "The High Desert", authorName: "Lucia Navarro" },
  { id: "n-edge", title: "Notes From the Edge", authorName: "Callum O'Donnell" },
  { id: "n-field", title: "Long Days in the Field", authorName: "Priya Raman" },
];

/** A book id whose art (chosen from its id) is the one asked for. */
function idFor(artId: string): string {
  for (let index = 0; index < 5000; index++) if (artFor(`demo-${index}`).id === artId) return `demo-${index}`;
  return "demo-0";
}

function Harness() {
  const [artId, setArtId] = useState("watercolor/lake");
  const [run, setRun] = useState<{ key: number; from: DOMRect | null } | null>(null);
  const [landed, setLanded] = useState(0);
  const start = useRef<HTMLDivElement>(null);
  const book = { id: idFor(artId), title: "Check the slats first", authorName: "Ingrid Solberg" };
  return (
    <main style={{ padding: "var(--s-5) 0", minHeight: "100vh", background: "var(--paper)" }}>
      <div style={{ display: "flex", gap: 12, alignItems: "center", flexWrap: "wrap", padding: "0 16px" }}>
        <select value={artId} onChange={(event) => setArtId(event.target.value)} aria-label="Cover art">
          {BOOK_ARTS.map((art) => (
            <option key={art.id} value={art.id}>
              {art.id}
            </option>
          ))}
        </select>
        <button
          type="button"
          onClick={() => setRun({ key: Date.now(), from: start.current?.getBoundingClientRect() ?? null })}
        >
          Land from the review book
        </button>
        <button type="button" onClick={() => setRun({ key: Date.now(), from: null })}>
          Land in place
        </button>
        <span data-testid="landed">landed: {landed}</span>
      </div>
      {/* Where the closed white book sits before it flies: roughly where the review book closes. */}
      <div
        ref={start}
        style={{ width: 236, height: 344, margin: "24px auto 0", border: "2px dashed var(--ink-3)" }}
      />
      {run && (
        <ShelfLanding
          key={run.key}
          book={book}
          neighbours={NEIGHBOURS}
          from={run.from}
          onLanded={() => setLanded((count) => count + 1)}
        />
      )}
    </main>
  );
}

const root = document.getElementById("root");
if (root)
  createRoot(root).render(
    <StrictMode>
      <Harness />
    </StrictMode>,
  );
