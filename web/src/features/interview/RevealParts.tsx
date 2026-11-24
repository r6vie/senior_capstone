import { type CSSProperties, type ReactNode, useEffect, useId, useRef, useState } from "react";
import { Button } from "../../ui/Button";
import type { BookEdit, ChapterEdit, DraftBook, TitleOption } from "./interviewClient";
import { reducedMotion } from "./librarian/pen";
import "./IntroBook.css";
import "./RevealParts.css";

// The reveal (StartReveal, approved by Josef 2026-11-23/24): the three titles as white books on a shelf,
// the chosen book open while it's written, and review in that same open book.

// ---------- Three titles on a shelf ----------

const LETTER_MS = 24;
// Each book starts a moment after the last one's title is on.
const NEXT_BOOK_MS = 700;
const RISE_STAGGER_MS = 120;

function useTitleTyping(titles: TitleOption[]): number[] {
  const [typed, setTyped] = useState<number[]>(() =>
    reducedMotion() ? titles.map((option) => option.title.length) : titles.map(() => 0),
  );
  useEffect(() => {
    if (reducedMotion()) return;
    const timers: ReturnType<typeof setTimeout>[] = [];
    let at = RISE_STAGGER_MS * titles.length + 300;
    titles.forEach((option, index) => {
      for (let letter = 1; letter <= option.title.length; letter++) {
        const count = letter;
        timers.push(
          setTimeout(
            () => setTyped((now) => now.map((n, i) => (i === index ? count : n))),
            at + letter * LETTER_MS,
          ),
        );
      }
      at += option.title.length * LETTER_MS + NEXT_BOOK_MS;
    });
    return () => {
      for (const timer of timers) clearTimeout(timer);
    };
  }, [titles]);
  return typed;
}

/** A white book with its title lettered on and the member's name under it. */
function WhiteBook({ title, author, typed }: { title: string; author: string; typed?: number }) {
  return (
    <span className="rv-cover">
      <span className="rv-title">
        {/* The whole title holds its place; the typed letters are ink. */}
        <span className="rv-full">{title}</span>
        <span className="rv-typed" aria-hidden="true">
          {title.slice(0, typed ?? title.length)}
        </span>
      </span>
      <span className="rv-author">{author}</span>
    </span>
  );
}

export function TitleShelf({
  titles,
  author,
  busy,
  error,
  onChoose,
}: {
  titles: TitleOption[];
  author: string;
  busy: boolean;
  error: ReactNode;
  onChoose: (titleId: string) => void;
}) {
  const typed = useTitleTyping(titles);
  const [picked, setPicked] = useState<string | null>(null);
  const all = typed.every((count, index) => count >= (titles[index]?.title.length ?? 0));
  return (
    <div className="rv-shelf" data-picked={picked ? true : undefined}>
      {/* The whole book is what you choose (replaces the cards and their radio buttons). */}
      <fieldset className="rv-books">
        <legend className="iv-visually-hidden">Choose a title</legend>
        {titles.map((option, index) => {
          const shown = (typed[index] ?? 0) > 0 || reducedMotion();
          return (
            <button
              key={option.id}
              type="button"
              aria-pressed={picked === option.id}
              aria-describedby={`rv-why-${option.id}`}
              className="rv-book"
              data-on={picked === option.id || undefined}
              style={{ "--i": index } as CSSProperties}
              disabled={!shown}
              onClick={() => setPicked(option.id)}
            >
              <span className="rv-face">
                <span className="rv-ribbon" aria-hidden="true" />
                <WhiteBook title={option.title} author={author} typed={typed[index]} />
              </span>
              {/* On a phone the reason sits beside its book; on a wide screen it's under the shelf. */}
              <span className="rv-why-beside" aria-hidden="true">
                {picked === option.id && <span className="rv-pick">Your pick</span>}
                {option.why}
              </span>
            </button>
          );
        })}
      </fieldset>
      <div className="rv-ledge" aria-hidden="true" />
      <div className="rv-whys">
        {titles.map((option, index) => (
          <p
            key={option.id}
            id={`rv-why-${option.id}`}
            className="rv-why"
            data-shown={(typed[index] ?? 0) >= option.title.length || undefined}
            data-dim={(picked && picked !== option.id) || undefined}
          >
            {picked === option.id && <span className="rv-pick">Your pick</span>}
            {option.why}
          </p>
        ))}
      </div>
      {error}
      <div className="rv-go">
        <Button disabled={!picked || !all} aria-busy={busy} onClick={() => picked && onChoose(picked)}>
          Choose this title
        </Button>
      </div>
    </div>
  );
}

// ---------- The chosen book, open while it's written ----------

/** The open book as the shelf's reader draws it: board, spine, page edge and two pages. */
function OpenBook({ left, right, label }: { left: ReactNode; right: ReactNode; label: string }) {
  return (
    <div className="ib-book rv-open">
      <span className="ib-edge" aria-hidden="true" />
      <section className="ib-page ib-left" aria-label={`${label}: title page`}>
        {left}
      </section>
      <section className="ib-page ib-right" aria-label={`${label}: pages`}>
        {right}
      </section>
    </div>
  );
}

export function WritingBook({
  title,
  author,
  places = 4,
}: {
  title: string | null;
  author: string;
  places?: number;
}) {
  return (
    <OpenBook
      label="Your book, being written"
      left={
        <div className="rv-titlepage">
          {title ? <h2 className="rv-booktitle">{title}</h2> : <span className="ib-bar rv-titlebar" />}
          <p className="rv-by">by {author}</p>
        </div>
      }
      right={
        <div aria-hidden="true">
          <h2 className="ib-pname">Contents</h2>
          <ol className="ib-places">
            {Array.from({ length: places }, (_, index) => (
              <li
                // biome-ignore lint/suspicious/noArrayIndexKey: the contents' fixed, empty places
                key={index}
                data-drawn
                style={{ "--w": `${[78, 64, 86, 70][index % 4]}%` } as CSSProperties}
              >
                <b>{index + 1}</b>
                <span>
                  <span className="ib-bar" />
                  <span className="ib-bar ib-bar-s" />
                </span>
              </li>
            ))}
          </ol>
        </div>
      }
    />
  );
}

// ---------- Review: the book, open, every word a field ----------

const SAVE_AFTER_MS = 700;

/** A field that saves itself a moment after the member stops typing, and when they leave it. */
function AutoField({
  label,
  value,
  onSave,
  className,
  long,
}: {
  label: string;
  value: string;
  onSave: (text: string) => Promise<void>;
  className?: string;
  long?: boolean;
}) {
  const id = useId();
  const [text, setText] = useState(value);
  const [problem, setProblem] = useState<string | null>(null);
  const saved = useRef(value);
  const focused = useRef(false);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  // The book changing elsewhere (a removal, another field) shows here unless the member is typing in it.
  useEffect(() => {
    if (!focused.current) {
      setText(value);
      saved.current = value;
    }
  }, [value]);
  const save = async (now: string) => {
    if (timer.current) clearTimeout(timer.current);
    timer.current = null;
    const trimmed = now.trim();
    if (!trimmed || trimmed === saved.current.trim()) return;
    try {
      await onSave(trimmed);
      saved.current = trimmed;
      setProblem(null);
    } catch (reason) {
      setProblem(reason instanceof Error ? reason.message : "That didn't save. Try again.");
    }
  };
  useEffect(
    () => () => {
      if (timer.current) clearTimeout(timer.current);
    },
    [],
  );
  return (
    <div className={`rv-field${className ? ` ${className}` : ""}`} data-long={long || undefined}>
      <label htmlFor={id} className="iv-visually-hidden">
        {label}
      </label>
      <textarea
        id={id}
        className="rv-fld"
        value={text}
        rows={1}
        aria-invalid={problem ? true : undefined}
        onFocus={() => {
          focused.current = true;
        }}
        onBlur={() => {
          focused.current = false;
          save(text);
        }}
        onChange={(event) => {
          const now = event.target.value;
          setText(now);
          if (timer.current) clearTimeout(timer.current);
          timer.current = setTimeout(() => save(now), SAVE_AFTER_MS);
        }}
      />
      {problem && (
        <p className="message message-error rv-problem" role="alert">
          <span>!</span>
          <span>{problem}</span>
        </p>
      )}
    </div>
  );
}

type Page = { kind: "contents" } | { kind: "chapter"; id: string } | { kind: "back" };

export function ReviewBook({
  book,
  signOff,
  canRemove,
  onEditBook,
  onEditChapter,
  onRemove,
  under,
  notes,
}: {
  book: DraftBook;
  /** The Librarian's line under the name, in its hand. */
  signOff: ReactNode;
  canRemove: boolean;
  onEditBook: (edit: BookEdit) => Promise<void>;
  onEditChapter: (chapterId: string, edit: ChapterEdit) => Promise<void>;
  onRemove: (chapterId: string) => Promise<boolean>;
  /** Put it on the shelf, and See the other titles, under the book. */
  under: ReactNode;
  /** Said under the book after a change, such as the back cover rewritten to match. */
  notes?: ReactNode;
}) {
  const [page, setPage] = useState<Page>({ kind: "contents" });
  const [confirming, setConfirming] = useState(false);
  const chapter = page.kind === "chapter" ? book.chapters.find((item) => item.id === page.id) : undefined;
  const at = chapter ? book.chapters.indexOf(chapter) : -1;
  // A removed chapter's page closes back to the contents.
  useEffect(() => {
    if (page.kind === "chapter" && !chapter) setPage({ kind: "contents" });
  }, [page, chapter]);
  const go = (next: Page) => {
    setConfirming(false);
    setPage(next);
  };
  const tabs = (
    <nav className="rv-tabs" aria-label="Pages of this book">
      <button
        type="button"
        aria-current={page.kind === "contents" ? "page" : undefined}
        onClick={() => go({ kind: "contents" })}
      >
        Contents
      </button>
      {book.chapters.map((item, index) => (
        <button
          key={item.id}
          type="button"
          aria-label={`Chapter ${index + 1}`}
          aria-current={page.kind === "chapter" && page.id === item.id ? "page" : undefined}
          onClick={() => go({ kind: "chapter", id: item.id })}
        >
          {index + 1}
        </button>
      ))}
      {book.blurb !== null && (
        <button
          type="button"
          aria-current={page.kind === "back" ? "page" : undefined}
          onClick={() => go({ kind: "back" })}
        >
          Back cover
        </button>
      )}
    </nav>
  );

  let right: ReactNode;
  if (chapter) {
    right = (
      <div className="rv-chapter">
        <span className="rv-num" aria-hidden="true">
          {at + 1}
        </span>
        <h2 className="iv-visually-hidden">Chapter {at + 1}</h2>
        <AutoField
          key={`t-${chapter.id}`}
          label={`Chapter ${at + 1} title`}
          className="rv-ct"
          value={chapter.title}
          onSave={(title) => onEditChapter(chapter.id, { title })}
        />
        <AutoField
          key={`s-${chapter.id}`}
          label={`Chapter ${at + 1} text`}
          className="rv-text"
          long
          value={chapter.summary}
          onSave={(summary) => onEditChapter(chapter.id, { summary })}
        />
        {canRemove &&
          (confirming ? (
            <div className="rv-confirm">
              <b>Remove this chapter?</b>
              <button
                type="button"
                className="button button-quiet"
                aria-label={`Remove ${chapter.title}`}
                onClick={async () => {
                  setConfirming(false);
                  await onRemove(chapter.id);
                }}
              >
                Remove
              </button>
              <button type="button" className="button button-quiet" onClick={() => setConfirming(false)}>
                Keep it
              </button>
            </div>
          ) : (
            <div className="rv-confirm">
              <button
                type="button"
                className="button button-quiet"
                aria-label={`Remove ${chapter.title}`}
                onClick={() => setConfirming(true)}
              >
                Remove chapter
              </button>
            </div>
          ))}
      </div>
    );
  } else if (page.kind === "back" && book.blurb !== null) {
    right = (
      <div className="rv-back">
        <h2 className="ib-pname">Back cover</h2>
        <AutoField
          label="Back cover"
          className="rv-text"
          long
          value={book.blurb}
          onSave={(blurb) => onEditBook({ blurb })}
        />
      </div>
    );
  } else {
    right = (
      <>
        <h2 className="ib-pname">Contents</h2>
        <ol className="rv-toc" data-arriving={reducedMotion() ? undefined : true}>
          {book.chapters.map((item, index) => (
            <li key={item.id} style={{ "--i": index } as CSSProperties}>
              <button type="button" onClick={() => go({ kind: "chapter", id: item.id })}>
                <b>{index + 1}</b>
                <span className="rv-toc-t">{item.title}</span>
                <i aria-hidden="true">›</i>
                <span className="rv-toc-s">{item.summary}</span>
              </button>
            </li>
          ))}
          {book.blurb !== null && (
            <li className="rv-toc-back" style={{ "--i": book.chapters.length } as CSSProperties}>
              <button type="button" onClick={() => go({ kind: "back" })}>
                <b />
                <span className="rv-toc-t">Back cover</span>
                <i aria-hidden="true">›</i>
              </button>
            </li>
          )}
        </ol>
      </>
    );
  }

  return (
    <div className="rv-review">
      <OpenBook
        label="Your book"
        left={
          <div className="rv-titlepage">
            <AutoField
              label="Title"
              className="rv-booktitle"
              value={book.title}
              onSave={(title) => onEditBook({ title })}
            />
            <p className="rv-by">by {book.authorName}</p>
            {signOff}
          </div>
        }
        right={
          <>
            <div className="ib-head ib-head-right">{tabs}</div>
            {right}
          </>
        }
      />
      {notes}
      <div className="rv-under">{under}</div>
    </div>
  );
}
