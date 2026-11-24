import {
  type KeyboardEvent,
  type Ref,
  useCallback,
  useImperativeHandle,
  useMemo,
  useRef,
  useState,
} from "react";
import type { InterviewClient, LibrarianView } from "../interviewClient";
import { AnswerText, type AnswerTextHandle, type Rect } from "./AnswerText";
import { Hand } from "./Hand";
import { Ink } from "./Ink";
import { useLibrarian } from "./useLibrarian";
import type { Notebook } from "./useNotebook";
import "./Librarian.css";

// The answer field with the Librarian reading over the member's shoulder: the member's words, the
// marks on them, and a line in the margin below when there's something to say there.

export interface LibrarianContext {
  client: InterviewClient;
  interviewId: string;
  questionId: string;
  view: LibrarianView | null | undefined;
  notebook: Notebook;
  say: (line: string) => void;
}

export interface LibrarianFieldHandle {
  focus(): void;
  /** True when Send should hold, because the Librarian has just said something it must see first. */
  holdSend(text: string): boolean;
}

interface Props {
  id: string;
  labelId: string;
  value: string;
  placeholder: string;
  invalid?: boolean;
  onChange: (text: string) => void;
  onKeyDown?: (event: KeyboardEvent<HTMLDivElement>) => void;
  librarian: LibrarianContext;
  handle?: Ref<LibrarianFieldHandle>;
}

// Notes need room above their words; a circle's note sits a little higher still.
const OPENS = new Set(["underline", "back_cover", "strike", "circle", "note", "highlight"]);

export function LibrarianField({
  id,
  labelId,
  value,
  placeholder,
  invalid,
  onChange,
  onKeyDown,
  librarian,
  handle,
}: Props) {
  const text = useRef<AnswerTextHandle>(null);
  const [rects, setRects] = useState(new Map<string, Rect[]>());
  const lastLayout = useRef("");
  const { marks, placed, margin, pasted, holdForContact } = useLibrarian({ ...librarian, text: value });

  useImperativeHandle(handle, () => ({
    focus: () => text.current?.focus(),
    holdSend: holdForContact,
  }));

  const spans = useMemo(
    () =>
      placed.map((p) => ({
        id: p.item.id,
        start: p.start,
        end: p.end,
        // A credited edit carries two notes, the struck one and the credit above it: its line opens further.
        move: p.item.struckNote ? "credit" : p.item.move,
      })),
    [placed],
  );
  const open = useMemo(() => {
    const lines = new Set<string>();
    for (const shown of marks) if (shown.mark.note && OPENS.has(shown.mark.move)) lines.add(shown.mark.id);
    return lines;
  }, [marks]);

  const onLayout = useCallback((next: Map<string, Rect[]>) => {
    const key = JSON.stringify(
      [...next].map(([key, lines]) => [key, lines.map((r) => [r.left, r.top, r.width].map(Math.round))]),
    );
    if (key === lastLayout.current) return;
    lastLayout.current = key;
    setRects(next);
  }, []);

  return (
    <div className="lib-box">
      <AnswerText
        id={id}
        labelledBy={labelId}
        value={value}
        placeholder={placeholder}
        spans={spans}
        open={open}
        invalid={invalid}
        onChange={onChange}
        onPaste={pasted}
        onKeyDown={onKeyDown}
        onLayout={onLayout}
        handle={text}
      />
      <Ink marks={marks} rects={rects} />
      {margin && (
        <p className="lib-margin" aria-hidden="true">
          <Hand text={margin.text} life={margin.life} />
        </p>
      )}
    </div>
  );
}
