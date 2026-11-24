import { useEffect, useRef, useState } from "react";
import { ArtImage } from "../../ui/art/ArtImage";
import { type ArtCategory, BOOK_ARTS, type BookArt, coverInk } from "../../ui/art/bookArt";
import { Button } from "../../ui/Button";
import { reducedMotion } from "../interview/librarian/pen";

// Changing the design (My book D2, approved by Josef 2026-11-23): the book closes and steps aside, and the designs of
// one kind open beside it, each as the member's own cover with no names. Those not chosen sit back, smaller, fainter
// and less saturated. Choosing one fades the closed book back to paper (about 0.4 s), then the new cover paints itself
// in with its quick clip (about 4 s). With reduced motion it simply swaps.

const KINDS: { category: ArtCategory; label: string }[] = [
  { category: "strata", label: "Mosaic" },
  { category: "watercolor", label: "Watercolour" },
];
const TO_PAPER_MS = 400;
// A clip that can't start in this long (slow connection, autoplay refused) gives way to the still cover.
const CLIP_WAIT_MS = 1500;

type Phase = "still" | "paper" | "paint";

function Cover({ art, title, author }: { art: BookArt; title: string; author: string }) {
  return (
    <span className="book">
      <span className="book-cover" style={coverInk(art)}>
        <ArtImage className="book-art" src={art.cover} />
        <span className="book-title">{title}</span>
        <span className="book-author">{author}</span>
      </span>
    </span>
  );
}

export function DesignPicker({
  current,
  title,
  author,
  busy,
  error,
  onUse,
  onBack,
}: {
  current: BookArt;
  title: string;
  author: string;
  busy: boolean;
  error: string | null;
  onUse: (art: BookArt) => void;
  onBack: () => void;
}) {
  const [kind, setKind] = useState<ArtCategory>(current.category);
  const [chosen, setChosen] = useState(current);
  // What the closed book shows: it changes only once it has faded to paper.
  const [shown, setShown] = useState(current);
  const [phase, setPhase] = useState<Phase>("still");
  // A new choice cut into a clip: the half-painted cover goes straight to paper, never back to the last still.
  const [cut, setCut] = useState(false);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const video = useRef<HTMLVideoElement>(null);
  const heading = useRef<HTMLHeadingElement>(null);

  useEffect(() => {
    heading.current?.focus({ preventScroll: true });
    return () => {
      if (timer.current) clearTimeout(timer.current);
    };
  }, []);

  function choose(art: BookArt) {
    if (art.id === chosen.id) return;
    setChosen(art);
    if (timer.current) clearTimeout(timer.current);
    setCut(phase === "paint");
    if (reducedMotion()) {
      setShown(art);
      setPhase("still");
      return;
    }
    setPhase("paper");
    timer.current = setTimeout(() => {
      setShown(art);
      setPhase(art.anim ? "paint" : "still");
    }, TO_PAPER_MS);
  }

  // Painting: play the clip from its first (white) frame; if it won't start, show the still cover instead.
  // biome-ignore lint/correctness/useExhaustiveDependencies: restarts for each newly shown design
  useEffect(() => {
    if (phase !== "paint") return;
    const clip = video.current;
    if (!clip) {
      setPhase("still");
      return;
    }
    const giveUp = setTimeout(() => setPhase("still"), CLIP_WAIT_MS);
    const started = () => clearTimeout(giveUp);
    clip.addEventListener("playing", started);
    const playing = clip.play?.();
    if (playing && typeof playing.catch === "function") playing.catch(() => setPhase("still"));
    return () => {
      clearTimeout(giveUp);
      clip.removeEventListener("playing", started);
    };
  }, [phase, shown]);

  const designs = BOOK_ARTS.filter((art) => art.category === kind);

  return (
    <div className="mb-design">
      <div className="mb-closed" data-phase={phase} data-cut={cut || undefined} aria-hidden="true">
        <span className="book book-lg">
          <span className="book-cover" style={coverInk(shown)}>
            <ArtImage className="book-art" src={shown.cover} />
            {phase === "paint" && shown.anim && (
              <video
                key={shown.id}
                ref={video}
                className="book-art mb-clip"
                muted
                playsInline
                preload="auto"
                disablePictureInPicture
                tabIndex={-1}
                onEnded={() => setPhase("still")}
                onError={() => setPhase("still")}
              >
                <source src={shown.anim.webm} type="video/webm" />
                <source src={shown.anim.mp4} type="video/mp4" />
              </video>
            )}
            <span className="book-title">{title}</span>
            <span className="book-author">{author}</span>
          </span>
        </span>
      </div>
      <section className="mb-pick" aria-labelledby="mb-pick-title">
        <h2 id="mb-pick-title" ref={heading} tabIndex={-1}>
          Choose a design
        </h2>
        <div className="mb-kinds" role="tablist" aria-label="Kinds of design">
          {KINDS.map((item) => (
            <button
              key={item.category}
              type="button"
              role="tab"
              aria-selected={kind === item.category}
              onClick={() => setKind(item.category)}
            >
              {item.label}
            </button>
          ))}
        </div>
        <ul className="mb-designs">
          {designs.map((art) => (
            <li key={art.id}>
              <button
                type="button"
                className="mb-design-opt"
                aria-label={art.name}
                aria-pressed={art.id === chosen.id}
                onClick={() => choose(art)}
              >
                <Cover art={art} title={title} author={author} />
              </button>
            </li>
          ))}
        </ul>
        {error && (
          <p className="message message-error" role="alert">
            <span>!</span>
            <span>{error}</span>
          </p>
        )}
        <div className="mb-pick-go">
          <Button onClick={() => onUse(chosen)} aria-busy={busy || undefined} disabled={busy}>
            Use this design
          </Button>
          <button type="button" className="button button-quiet" onClick={onBack}>
            Back to my book
          </button>
        </div>
      </section>
    </div>
  );
}
