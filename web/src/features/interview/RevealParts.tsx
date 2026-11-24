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
const SLIDE_AWAY_MS = 320;

function useTitleTyping(titles: TitleOption[]): number[] {
  const [typed, setTyped] = useState<number[]>(() =>
    reducedMotion() ? titles.map((option) => option.title.length) : titles.map(() => 0),
  );
  // Restarts only for other titles, not for the same titles sent again.
  const key = titles.map((option) => option.id).join();
  // biome-ignore lint/correctness/useExhaustiveDependencies: keyed by the titles' ids on purpose
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
  }, [key]);
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
  failed,
  onChoose,
}: {
  titles: TitleOption[];
  author: string;
  busy: boolean;
  error: ReactNode;
  /** The last choice didn't go through: the shelf comes back as it was. */
  failed: boolean;
  onChoose: (titleId: string) => void;
}) {
  const typed = useTitleTyping(titles);
  const [picked, setPicked] = useState<string | null>(null);
  // Choosing: the other two slide away first, then the chosen book comes forward and opens.
  const [leaving, setLeaving] = useState(false);
  const choose = (id: string) => {
    if (leaving) return;
    setLeaving(true);
    setTimeout(() => onChoose(id), reducedMotion() ? 0 : SLIDE_AWAY_MS);
  };
  useEffect(() => {
    if (failed && !busy) setLeaving(false);
  }, [failed, busy]);
  const all = typed.every((count, index) => count >= (titles[index]?.title.length ?? 0));
  return (
    <div className="rv-shelf" data-picked={picked ? true : undefined} data-leaving={leaving || undefined}>
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
        <Button
          disabled={!picked || !all}
          aria-busy={busy || leaving}
          onClick={() => picked && choose(picked)}
        >
          Choose this title
        </Button>
      </div>
    </div>
  );
}

// ---------- The chosen book, open while it's written ----------

/** The open book as the shelf's reader draws it: board, spine, page edge and two pages. */
export function OpenBook({
  left,
  right,
  label,
  opening,
}: {
  left: ReactNode;
  right: ReactNode;
  label: string;
  /** The chosen book arrives closed and opens (StartReveal, Writing): its cover swings open about the spine. */
  opening?: { title: string; author: string } | null;
}) {
  return (
    <div className="ib-book rv-open" data-opening={opening ? true : undefined}>
      <span className="ib-edge" aria-hidden="true" />
      {/* The title page is the cover's inside: it swings over from the right as the cover opens. */}
      <div className="rv-leaf">
        <section className="ib-page ib-left" aria-label={`${label}: title page`}>
          {left}
        </section>
        {opening && (
          <span className="rv-leaf-cover" aria-hidden="true">
            <WhiteBook title={opening.title} author={opening.author} />
          </span>
        )}
      </div>
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
  opening,
}: {
  title: string | null;
  author: string;
  places?: number;
  /** Arriving straight from the pick: the book comes forward closed and opens. */
  opening?: boolean;
}) {
  return (
    <OpenBook
      label="Your book, being written"
      opening={opening && title ? { title, author } : null}
      left={
        <div className="rv-titlepage">
          {title ? <h2 className="rv-booktitle">{title}</h2> : <span className="ib-bar rv-titlebar" />}
          <p className="rv-by">by {author}</p>
        </div>
      }
      right={
        <div>
          <div className="ib-head ib-head-right">
            <span className="rv-tabs" aria-hidden="true">
              <span aria-current="page">Contents</span>
              {Array.from({ length: places }, (_, index) => (
                // biome-ignore lint/suspicious/noArrayIndexKey: the book's fixed, empty pages
                <span key={index}>{index + 1}</span>
              ))}
            </span>
          </div>
          <h2 className="ib-pname">Contents</h2>
          <ol className="ib-places" aria-hidden="true">
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
export function AutoField({
  label,
  value,
  onSave,
  track,
  className,
  long,
}: {
  label: string;
  value: string;
  onSave: (text: string) => Promise<void>;
  /** Hands each save to the book, so shelving or removing waits for it. */
  track: (save: Promise<void>) => void;
  className?: string;
  long?: boolean;
}) {
  const id = useId();
  const problemId = useId();
  const [text, setText] = useState(value);
  const [problem, setProblem] = useState<string | null>(null);
  const saved = useRef(value);
  const focused = useRef(false);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  // Saves go one after another, so an older reply can never land after a newer one.
  const chain = useRef<Promise<void>>(Promise.resolve());
  const inFlight = useRef(0);
  const live = useRef(true);
  // The book changing elsewhere (a removal, another field) shows here, unless the member is typing in it or
  // its own save is still on its way.
  useEffect(() => {
    if (!focused.current && inFlight.current === 0) {
      setText(value);
      saved.current = value;
    }
  }, [value]);
  const save = (now: string) => {
    if (timer.current) clearTimeout(timer.current);
    timer.current = null;
    const trimmed = now.trim();
    if (!trimmed || trimmed === saved.current.trim()) return;
    inFlight.current += 1;
    const done = chain.current.then(async () => {
      try {
        await onSave(trimmed);
        saved.current = trimmed;
        if (live.current) setProblem(null);
      } catch (reason) {
        // Said here, or, once the field has gone (another tab), by the book.
        const message = reason instanceof Error ? reason.message : "That didn't save. Try again.";
        if (live.current) setProblem(message);
        else throw reason;
      } finally {
        inFlight.current -= 1;
      }
    });
    chain.current = done.catch(() => undefined);
    track(done);
  };
  useEffect(() => {
    live.current = true;
    return () => {
      live.current = false;
      if (timer.current) clearTimeout(timer.current);
    };
  }, []);
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
        aria-describedby={problem ? problemId : undefined}
        onFocus={() => {
          focused.current = true;
        }}
        onBlur={() => {
          focused.current = false;
          // An emptied field isn't saved, so it shows what is.
          if (!text.trim()) {
            setText(saved.current);
            return;
          }
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
        <p id={problemId} className="message message-error rv-problem" role="alert">
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
  onShelve,
  busy,
  others,
  notes,
  opening,
}: {
  book: DraftBook;
  /** Arriving straight from the pick: the book comes forward closed and opens. */
  opening?: boolean;
  /** The Librarian's line under the name, in its hand. */
  signOff: ReactNode;
  canRemove: boolean;
  onEditBook: (edit: BookEdit) => Promise<void>;
  onEditChapter: (chapterId: string, edit: ChapterEdit) => Promise<void>;
  onRemove: (chapterId: string) => Promise<boolean>;
  /** Put it on the shelf: only once every save under way has landed. */
  onShelve: () => void;
  busy: boolean;
  /** See the other titles, beside Put it on the shelf. */
  others: ReactNode;
  /** Said under the book after a change, such as the back cover rewritten to match. */
  notes?: ReactNode;
}) {
  const [page, setPage] = useState<Page>({ kind: "contents" });
  const [confirming, setConfirming] = useState(false);
  // Saves under way, so shelving or removing never runs ahead of the member's last words.
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
  // A removed chapter's page closes back to the contents.
  useEffect(() => {
    if (page.kind === "chapter" && !chapter) setPage({ kind: "contents" });
  }, [page, chapter]);
  const go = (next: Page) => {
    moved.current = true;
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
        <h2 className="ib-pname" ref={heading} tabIndex={-1}>
          Back cover
        </h2>
        <AutoField
          label="Back cover"
          track={track}
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
        <h2 className="ib-pname" ref={heading} tabIndex={-1}>
          Contents
        </h2>
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
        opening={opening ? { title: book.title, author: book.authorName } : null}
        left={
          <div className="rv-titlepage">
            <AutoField
              label="Title"
              track={track}
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
      {lost && (
        <p className="message message-error rv-problem" role="alert">
          <span>!</span>
          <span>{lost}</span>
        </p>
      )}
      {notes}
      <div className="rv-under">
        <Button
          aria-busy={busy}
          onClick={async () => {
            await settled();
            onShelve();
          }}
        >
          Put it on the shelf
        </Button>
        {others}
      </div>
    </div>
  );
}
