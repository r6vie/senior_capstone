import { type CSSProperties, useEffect, useId, useState } from "react";
import { reducedMotion, rubDuration, strokes } from "./pen";

// The Librarian's handwriting: written letter by letter at pen pace, resting, or rubbed out from the
// left. While it's being written each letter is drawn, not faded in: the ink follows the pen along the
// letter's own outline (Caveat SemiBold, the approved hand), so the stroke appears in writing order. At
// rest it's ordinary text in the same face. Screen readers get the words elsewhere, announced once; this
// is ink only.

export type Life = "writing" | "resting" | "erasing";

/** Seconds a line takes to write. */
export function writeTime(text: string): number {
  return strokes(text).total;
}

/** Seconds a line takes to rub out. */
export function rubTime(text: string): number {
  return rubDuration(text.length);
}

type Glyphs = typeof import("./caveatGlyphs").CAVEAT;

// The outlines are loaded once, on the first line the Librarian writes, and never on pages without it.
let loaded: Glyphs | null = null;
let loading: Promise<Glyphs> | null = null;
function loadGlyphs(): Promise<Glyphs> {
  loading ??= import("./caveatGlyphs").then((module) => {
    loaded = module.CAVEAT;
    return loaded;
  });
  return loading;
}

function useGlyphs(wanted: boolean): Glyphs | null {
  const [glyphs, setGlyphs] = useState(loaded);
  useEffect(() => {
    if (!wanted || glyphs) return;
    let live = true;
    loadGlyphs()
      .then((found) => live && setGlyphs(found))
      .catch(() => undefined);
    return () => {
      live = false;
    };
  }, [wanted, glyphs]);
  return glyphs;
}

// Wide enough that tracing the outline covers the letter's whole thickness as it goes.
const PEN_WIDTH = 140;

/** One letter, drawn along its outline: a mask of the outline's own stroke, revealed by its dash. */
function DrawnLetter({ char, glyphs, id }: { char: string; glyphs: Glyphs; id: string }) {
  const entry = glyphs.glyphs[char];
  if (!entry) return <>{char}</>;
  const [advance, d] = entry;
  const { unitsPerEm: em, ascender: top, descender: bottom } = glyphs;
  const height = top - bottom;
  return (
    <svg
      className="lib-drawn"
      viewBox={`0 ${-top} ${advance} ${height}`}
      style={{
        width: `${advance / em}em`,
        height: `${height / em}em`,
        verticalAlign: `${bottom / em}em`,
      }}
      aria-hidden="true"
    >
      <mask
        id={id}
        maskUnits="userSpaceOnUse"
        x={-PEN_WIDTH}
        y={-top}
        width={advance + 2 * PEN_WIDTH}
        height={height}
      >
        <path
          className="lib-pen-path"
          d={d}
          pathLength={1}
          fill="none"
          stroke="#fff"
          strokeWidth={PEN_WIDTH}
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </mask>
      <path d={d} fill="currentColor" mask={`url(#${id})`} />
    </svg>
  );
}

export function Hand({
  text,
  life,
  delay = 0,
  className,
  underline,
}: {
  text: string;
  life: Life;
  /** Seconds before the pen starts, as when a note follows its stroke. */
  delay?: number;
  className?: string;
  /** One word underlined by hand, as the notebook does with the word an entry hangs on. */
  underline?: { word: number; double: boolean; shape?: string };
}) {
  const writing = life === "writing" && !reducedMotion();
  const glyphs = useGlyphs(writing);
  const base = useId().replace(/:/g, "");
  const { glyphs: letters } = strokes(text);
  // Words stay whole so a line only ever breaks at a space.
  const words: (typeof letters)[] = [[]];
  for (const letter of letters) {
    if (letter.char === " ") words.push([]);
    else words[words.length - 1]?.push(letter);
  }
  // Until the outlines arrive (a moment, the first time), the letters appear at pen pace without drawing.
  const drawn = writing && glyphs !== null;
  let count = 0;
  return (
    <span
      className={`lib-hand${className ? ` ${className}` : ""}`}
      data-life={life}
      data-drawn={drawn || undefined}
      aria-hidden="true"
      style={{ "--rub": `${rubTime(text)}s` } as CSSProperties}
    >
      {words.map((word, index) => (
        // biome-ignore lint/suspicious/noArrayIndexKey: words of one fixed line, in order
        <span key={index}>
          {index > 0 && " "}
          <span
            className={`lib-word${underline?.word === index ? (underline.double ? " lib-u2" : " lib-u") : ""}`}
            style={
              underline?.word === index && underline.shape
                ? ({ "--shape": underline.shape } as CSSProperties)
                : undefined
            }
          >
            {word.map((letter, at) => {
              count += 1;
              return (
                <span
                  // biome-ignore lint/suspicious/noArrayIndexKey: letters of one fixed word, in order
                  key={at}
                  className="lib-g"
                  style={
                    {
                      "--s": `${(delay + letter.start).toFixed(3)}s`,
                      "--t": `${letter.duration.toFixed(3)}s`,
                      "--o": letter.opacity.toFixed(2),
                      "--y": `${letter.lift.toFixed(2)}px`,
                      "--r": `${letter.turn.toFixed(2)}deg`,
                    } as CSSProperties
                  }
                >
                  {drawn ? (
                    <DrawnLetter char={letter.char} glyphs={glyphs} id={`${base}g${count}`} />
                  ) : (
                    letter.char
                  )}
                </span>
              );
            })}
          </span>
        </span>
      ))}
    </span>
  );
}
