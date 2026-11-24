import { artFor, coverInk } from "../../ui/art/bookArt";

export function BookObject({
  id,
  book,
  size,
  out,
  onOpen,
  onInterest,
}: {
  /** Chooses the book's art (ui/art/bookArt.ts). */
  id: string;
  book: { title: string; authorName: string };
  size?: "lg";
  /** Open in front of the shelf: its place stays empty until it's put back. */
  out?: boolean;
  onOpen?: (element: HTMLButtonElement) => void;
  /** Pointed at or focused: likely to be opened, so its contents can be fetched ahead. */
  onInterest?: () => void;
}) {
  const art = artFor(id);
  const cover = (
    <span className="book-cover" style={coverInk(art)}>
      <img className="book-art" src={art.cover} alt="" />
      <span className="book-title">{book.title}</span>
      <span className="book-author">{book.authorName}</span>
    </span>
  );
  if (!onOpen) {
    return (
      <div className={size === "lg" ? "book book-lg" : "book"} aria-hidden="true">
        {cover}
      </div>
    );
  }
  return (
    <button
      type="button"
      className={size === "lg" ? "book book-lg" : "book"}
      data-out={out || undefined}
      aria-label={`${book.title}, by ${book.authorName}`}
      onClick={(event) => onOpen(event.currentTarget)}
      onPointerEnter={onInterest}
      onFocus={onInterest}
    >
      {cover}
    </button>
  );
}
