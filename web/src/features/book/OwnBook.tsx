import { type CSSProperties, type ReactNode, useEffect, useRef, useState } from "react";
import { ArtImage } from "../../ui/art/ArtImage";
import { type BookArt, pageInk } from "../../ui/art/bookArt";
import type { BookEdit, ChapterEdit, DraftBook } from "../interview/interviewClient";
import { AutoField, OpenBook } from "../interview/RevealParts";

// My book D2 (approved by Josef 2026-11-23): the shelf's own open book, opened to its author and written in where it
// is. The title page carries the book's design and the pen that changes it; the contents end with the back cover;
// a chapter or the back cover opens on the right with the contents beside it. Everything saves as it's typed.

type Page = { kind: "contents" } | { kind: "chapter"; id: string } | { kind: "back" };

function PenIcon() {
  return (
    <svg viewBox="0 0 20 20" width="18" height="18" aria-hidden="true" fill="none" stroke="currentColor">
      <path d="M3 17l1-4L14 3l3 3L7 16l-4 1z" strokeWidth="2" strokeLinejoin="round" />
      <path d="M12 5l3 3" strokeWidth="2" />
    </svg>
  );
}

export function OwnBook({
  book,
  art,
  canRemove,
  onEditBook,
  onEditChapter,
  onRemove,
  onDesign,
}: {
  book: DraftBook;
  art: BookArt | null;
  canRemove: boolean;
  onEditBook: (edit: BookEdit) => Promise<void>;
  onEditChapter: (chapterId: string, edit: ChapterEdit) => Promise<void>;
  /** Saves under way have landed by the time this is called. */
  onRemove: (chapterId: string) => Promise<void>;
  /** The pen on the art: the book closes and the designs open. */
  onDesign: () => void;
}) {
  const [page, setPage] = useState<Page>({ kind: "contents" });
  const [confirming, setConfirming] = useState(false);
  const pending = useRef(new Set<Promise<void>>());
  const [lost, setLost] = useState<string | null>(null);
  const track = (save: Promise<void>) => {
    pending.current.add(save);
    save
      .catch((reason) => setLost(reason instanceof Error ? reason.message : "That didn't save. Try again."))
      .finally(() => pending.current.delete(save));
  };
  const settled = () => Promise.allSettled([...pending.current]);
  // Moving to another page puts the keyboard on its heading, rather than on a button that's gone.
  const heading = useRef<HTMLHeadingElement>(null);
  const moved = useRef(false);
  // biome-ignore lint/correctness/useExhaustiveDependencies: runs when the page changes, by design
  useEffect(() => {
    if (!moved.current) return;
    heading.current?.focus({ preventScroll: true });
  }, [page]);
  const chapter = page.kind === "chapter" ? book.chapters.find((item) => item.id === page.id) : undefined;
  const at = chapter ? book.chapters.indexOf(chapter) : -1;
  useEffect(() => {
    if (page.kind === "chapter" && !chapter) setPage({ kind: "contents" });
  }, [page, chapter]);
  const go = (next: Page) => {
    moved.current = true;
    setConfirming(false);
    setPage(next);
  };
  const hasBack = book.blurb !== null;
  const current = (next: Page) =>
    next.kind === page.kind && (next.kind !== "chapter" || (page.kind === "chapter" && page.id === next.id))
      ? true
      : undefined;

  const tabs = (
    <nav className="rv-tabs" aria-label="Pages of this book">
      <button
        type="button"
        aria-current={current({ kind: "contents" }) && "page"}
        onClick={() => go({ kind: "contents" })}
      >
        Contents
      </button>
      {book.chapters.map((item, index) => (
        <button
          key={item.id}
          type="button"
          aria-label={`Chapter ${index + 1}`}
          aria-current={current({ kind: "chapter", id: item.id }) && "page"}
          onClick={() => go({ kind: "chapter", id: item.id })}
        >
          {index + 1}
        </button>
      ))}
      {hasBack && (
        <button
          type="button"
          aria-current={current({ kind: "back" }) && "page"}
          onClick={() => go({ kind: "back" })}
        >
          Back cover
        </button>
      )}
    </nav>
  );

  /** The contents: in full on their own page, compact beside an open chapter. */
  const contents = (compact: boolean) => (
    <ol className={compact ? "rv-toc mb-toc-compact" : "rv-toc"}>
      {book.chapters.map((item, index) => (
        <li key={item.id} style={{ "--i": index } as CSSProperties}>
          <button
            type="button"
            aria-current={current({ kind: "chapter", id: item.id }) && "page"}
            onClick={() => go({ kind: "chapter", id: item.id })}
          >
            <b>{index + 1}</b>
            <span className="rv-toc-t">{item.title}</span>
            <i aria-hidden="true">›</i>
            {!compact && <span className="rv-toc-s">{item.summary}</span>}
          </button>
        </li>
      ))}
      {hasBack && (
        <li className="rv-toc-back">
          <button
            type="button"
            aria-current={current({ kind: "back" }) && "page"}
            onClick={() => go({ kind: "back" })}
          >
            <b />
            <span className="rv-toc-t">Back cover</span>
            <i aria-hidden="true">›</i>
            {!compact && <span className="rv-toc-s">{book.blurb}</span>}
          </button>
        </li>
      )}
    </ol>
  );

  let left: ReactNode;
  let right: ReactNode;
  if (page.kind === "contents") {
    left = (
      <div className="rv-titlepage mb-titlepage" style={art ? pageInk(art) : undefined}>
        <AutoField
          label="Title"
          track={track}
          className="rv-booktitle"
          value={book.title}
          onSave={(title) => onEditBook({ title })}
        />
        <p className="rv-by mb-by">by {book.authorName}</p>
      </div>
    );
    right = (
      <>
        <h2 className="ib-pname" ref={heading} tabIndex={-1}>
          Contents
        </h2>
        {contents(false)}
      </>
    );
  } else {
    left = (
      <>
        <h2 className="ib-pname">Contents</h2>
        {contents(true)}
      </>
    );
    right = chapter ? (
      <div className="rv-chapter">
        <span className="rv-num" aria-hidden="true">
          {at + 1}
        </span>
        <h2 className="iv-visually-hidden" ref={heading} tabIndex={-1}>
          Chapter {at + 1}
        </h2>
        <AutoField
          key={`t-${chapter.id}`}
          label={`Chapter ${at + 1} title`}
          track={track}
          className="rv-ct"
          value={chapter.title}
          onSave={(title) => onEditChapter(chapter.id, { title })}
        />
        <AutoField
          key={`s-${chapter.id}`}
          label={`Chapter ${at + 1} text`}
          track={track}
          className="rv-text"
          long
          value={chapter.summary}
          onSave={(summary) => onEditChapter(chapter.id, { summary })}
        />
        {canRemove && (
          <div className="rv-confirm">
            {confirming ? (
              <>
                <b>Remove this chapter?</b>
                <button
                  type="button"
                  className="button button-quiet"
                  aria-label={`Remove ${chapter.title}`}
                  onClick={async () => {
                    setConfirming(false);
                    await settled();
                    moved.current = true;
                    await onRemove(chapter.id);
                  }}
                >
                  Remove
                </button>
                <button type="button" className="button button-quiet" onClick={() => setConfirming(false)}>
                  Keep it
                </button>
              </>
            ) : (
              <button type="button" className="button button-quiet" onClick={() => setConfirming(true)}>
                Remove this chapter
              </button>
            )}
          </div>
        )}
      </div>
    ) : (
      <div className="rv-back">
        <h2 className="ib-pname" ref={heading} tabIndex={-1}>
          Back cover
        </h2>
        <AutoField
          label="Back cover"
          track={track}
          className="rv-text"
          long
          value={book.blurb ?? ""}
          onSave={(blurb) => onEditBook({ blurb })}
        />
      </div>
    );
  }

  return (
    <div className="mb-own" data-page={page.kind}>
      <OpenBook
        label="Your book"
        left={
          <>
            {page.kind === "contents" && art && <ArtImage className="mb-page-art" src={art.page} />}
            {left}
            {page.kind === "contents" && (
              <button type="button" className="mb-pen" aria-label="Change the design" onClick={onDesign}>
                <PenIcon />
              </button>
            )}
          </>
        }
        right={
          <>
            <div className="ib-head ib-head-right">{tabs}</div>
            {right}
          </>
        }
      />
      {lost && (
        <p className="message message-error rv-problem" role="alert">
          <span>!</span>
          <span>{lost}</span>
        </p>
      )}
    </div>
  );
}
