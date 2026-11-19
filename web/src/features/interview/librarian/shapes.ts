import { seeded } from "./pen";

// Hand-drawn strokes, a little different every time but the same for the same mark on every render:
// each is seeded from the mark or entry it belongs to. Used as CSS masks, so they take the ink.

type Kind = "under" | "double" | "strike" | "circle";

const VIEW: Record<Kind, [number, number]> = {
  under: [100, 10],
  double: [100, 12],
  strike: [100, 8],
  circle: [100, 40],
};

function wave(random: () => number, y: number, swing: number): string {
  // A pen going left to right: starts a touch off the line, wanders, and lifts at a slight angle.
  const at = (base: number) => (base + (random() - 0.5) * swing).toFixed(1);
  const start = (random() * 3).toFixed(1);
  const end = (97 + random() * 3).toFixed(1);
  return `M${start} ${at(y)}C${(18 + random() * 10).toFixed(1)} ${at(y)} ${(38 + random() * 10).toFixed(1)} ${at(y)} ${(55 + random() * 8).toFixed(1)} ${at(y)}S${(85 + random() * 6).toFixed(1)} ${at(y)} ${end} ${at(y - 0.6)}`;
}

function loop(random: () => number): string {
  // A loose oval that overshoots where it started.
  const n = (base: number, swing: number) => (base + (random() - 0.5) * swing).toFixed(1);
  return `M${n(20, 6)} ${n(8, 4)}C${n(7, 4)} ${n(12, 4)} ${n(2, 2)} ${n(22, 4)} ${n(8, 3)} ${n(29, 3)}C${n(16, 4)} ${n(38, 2)} ${n(70, 6)} ${n(40, 2)} ${n(91, 4)} ${n(31, 3)}C${n(102, 2)} ${n(24, 3)} ${n(98, 3)} ${n(9, 3)} ${n(77, 5)} ${n(5, 2)}C${n(57, 5)} ${n(1, 2)} ${n(27, 5)} ${n(2, 2)} ${n(14, 4)} ${n(12, 3)}C${n(10, 2)} ${n(15, 2)} ${n(9, 2)} ${n(19, 2)} ${n(11, 2)} ${n(23, 3)}`;
}

const cache = new Map<string, string>();

/** A `url(...)` for a mask: this mark's own stroke. */
export function strokeOf(kind: Kind, seed: string): string {
  const key = `${kind}:${seed}`;
  const found = cache.get(key);
  if (found) return found;
  const random = seeded(key);
  const [width, height] = VIEW[kind];
  const weight = (2 + random() * 0.6).toFixed(2);
  const paths =
    kind === "circle"
      ? [loop(random)]
      : kind === "double"
        ? [wave(random, 3.2, 2), wave(random, 9, 2)]
        : [wave(random, kind === "strike" ? 4.2 : 5, kind === "strike" ? 3 : 3.6)];
  const svg = `<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 ${width} ${height}' preserveAspectRatio='none'>${paths
    .map(
      (d) =>
        `<path d='${d}' fill='none' stroke='black' stroke-width='${weight}' stroke-linecap='round' stroke-linejoin='round' vector-effect='non-scaling-stroke'/>`,
    )
    .join("")}</svg>`;
  const url = `url("data:image/svg+xml,${encodeURIComponent(svg)}")`;
  cache.set(key, url);
  return url;
}
