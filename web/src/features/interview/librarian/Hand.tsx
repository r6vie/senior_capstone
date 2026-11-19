import type { CSSProperties } from "react";
import { rubDuration, strokes } from "./pen";

// The Librarian's handwriting: written letter by letter at pen pace, resting, or rubbed out from the
// left. Never faded or cut, except as the reduced-motion fade. Screen readers get the words elsewhere,
// announced once; this is ink only.

export type Life = "writing" | "resting" | "erasing";

/** Seconds a line takes to write. */
export function writeTime(text: string): number {
  return strokes(text).total;
}

/** Seconds a line takes to rub out. */
export function rubTime(text: string): number {
  return rubDuration(text.length);
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
  underline?: { word: number; double: boolean };
}) {
  const { glyphs } = strokes(text);
  // Words stay whole so a line only ever breaks at a space.
  const words: (typeof glyphs)[] = [[]];
  for (const glyph of glyphs) {
    if (glyph.char === " ") words.push([]);
    else words[words.length - 1]?.push(glyph);
  }
  return (
    <span
      className={`lib-hand${className ? ` ${className}` : ""}`}
      data-life={life}
      aria-hidden="true"
      style={{ "--rub": `${rubTime(text)}s` } as CSSProperties}
    >
      {words.map((word, index) => (
        // biome-ignore lint/suspicious/noArrayIndexKey: words of one fixed line, in order
        <span key={index}>
          {index > 0 && " "}
          <span
            className={`lib-word${underline?.word === index ? (underline.double ? " lib-u2" : " lib-u") : ""}`}
          >
            {word.map((glyph, at) => (
              <span
                // biome-ignore lint/suspicious/noArrayIndexKey: letters of one fixed word, in order
                key={at}
                className="lib-g"
                style={
                  {
                    "--s": `${(delay + glyph.start).toFixed(3)}s`,
                    "--t": `${glyph.duration.toFixed(3)}s`,
                    "--o": glyph.opacity.toFixed(2),
                    "--y": `${glyph.lift.toFixed(2)}px`,
                    "--r": `${glyph.turn.toFixed(2)}deg`,
                  } as CSSProperties
                }
              >
                {glyph.char}
              </span>
            ))}
          </span>
        </span>
      ))}
    </span>
  );
}
