import type { CSSProperties } from "react";
import { useRef } from "react";
import type { Rect } from "./AnswerText";
import { Hand, rubTime } from "./Hand";
import { seeded } from "./pen";
import { NOTE_AFTER_S, type ShownMark } from "./useLibrarian";

// The Librarian's marks, drawn over the answer on their own layer: strokes from left to right, the note
// at pen pace after them, and rubbed out from the left, line first and then the note. A mark whose
// words were deleted is rubbed out where they last were.

const STROKED = new Set(["underline", "big", "strike", "circle", "highlight"]);

function wobble(id: string) {
  const random = seeded(id);
  return { stroke: (random() - 0.5) * 3, note: -1 - random() * 3, nudge: Math.round(random() * 6) };
}

export function Ink({ marks, rects }: { marks: ShownMark[]; rects: Map<string, Rect[]> }) {
  // Where each mark last was, so a mark can still be rubbed out after its words are gone.
  const last = useRef(new Map<string, Rect[]>());
  for (const [id, lines] of rects) if (lines.length) last.current.set(id, lines);
  for (const id of last.current.keys())
    if (!marks.some((shown) => shown.mark.id === id)) last.current.delete(id);

  return (
    <div className="lib-ink" aria-hidden="true">
      {marks.map(({ mark, life }) => {
        const lines = rects.get(mark.id)?.length ? (rects.get(mark.id) as Rect[]) : last.current.get(mark.id);
        // Nothing to draw until the field has been laid out; the mark is still there.
        const first = lines?.[0];
        if (!lines || !first)
          return <div key={mark.id} className="lib-mark" data-move={mark.move} data-life={life} />;
        const shape = wobble(mark.id);
        const style = {
          "--r": `${shape.stroke.toFixed(2)}deg`,
          "--rub": `${rubTime(mark.anchor)}s`,
        } as CSSProperties;
        const strokes =
          mark.move === "circle"
            ? [boxOf(lines)]
            : mark.move === "highlight" || mark.move === "underline" || mark.move === "big"
              ? lines
              : mark.move === "strike"
                ? [first]
                : [];
        return (
          <div key={mark.id} className="lib-mark" data-move={mark.move} data-life={life} style={style}>
            {STROKED.has(mark.move) &&
              strokes.map((line, index) => (
                <span
                  // biome-ignore lint/suspicious/noArrayIndexKey: one stroke per line of the phrase
                  key={index}
                  className="lib-stroke"
                  style={{
                    left: line.left,
                    top: line.top,
                    width: line.width,
                    height: line.height,
                  }}
                >
                  <i />
                </span>
              ))}
            {mark.note && (
              <span
                className="lib-note"
                style={
                  {
                    left: first.left + shape.nudge - 2,
                    top: first.top,
                    "--rot": `${shape.note.toFixed(2)}deg`,
                  } as CSSProperties
                }
              >
                <Hand text={mark.note} life={life} delay={mark.move === "note" ? 0 : NOTE_AFTER_S} />
              </span>
            )}
          </div>
        );
      })}
    </div>
  );
}

function boxOf(lines: Rect[]): Rect {
  const left = Math.min(...lines.map((line) => line.left));
  const top = Math.min(...lines.map((line) => line.top));
  const right = Math.max(...lines.map((line) => line.left + line.width));
  const bottom = Math.max(...lines.map((line) => line.top + line.height));
  return { left, top, width: right - left, height: bottom - top };
}
