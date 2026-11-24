import {
  type ClipboardEvent,
  type KeyboardEvent,
  type Ref,
  useCallback,
  useImperativeHandle,
  useLayoutEffect,
  useRef,
} from "react";

// The answer field. It's an editable block of plain text rather than a textarea, because the Librarian
// needs one line to open for a note above a marked phrase (LibParts, "Where notes sit"), and a textarea's
// lines are all one height. The text itself is all the member's: marks are drawn on a layer above it,
// and the only thing inside the field is a span around each marked phrase, so its line can open.

export interface Span {
  id: string;
  start: number;
  end: number;
  /** What's drawn on it, so the field can grey a struck word and open the right height. */
  move?: string;
}

export interface Rect {
  left: number;
  top: number;
  width: number;
  height: number;
}

export interface AnswerTextHandle {
  focus(): void;
  element(): HTMLDivElement | null;
}

interface Props {
  id: string;
  value: string;
  placeholder: string;
  /** The marked phrases, in reading order, never overlapping. */
  spans: Span[];
  /** Phrases whose line is open for a note. */
  open: ReadonlySet<string>;
  onChange: (text: string) => void;
  onPaste?: (pasted: string) => void;
  onKeyDown?: (event: KeyboardEvent<HTMLDivElement>) => void;
  /** Where each phrase is now, line by line, relative to the field's box. */
  onLayout?: (rects: Map<string, Rect[]>) => void;
  handle?: Ref<AnswerTextHandle>;
  invalid?: boolean;
  labelledBy?: string;
}

function supportsPlainText(): boolean {
  const probe = document.createElement("div");
  try {
    probe.contentEditable = "plaintext-only";
  } catch {
    return false;
  }
  return probe.contentEditable === "plaintext-only";
}

const BLOCKS = new Set(["DIV", "P"]);

/** Every character in the field, line breaks as "\n", however the browser wrote them. */
function rawText(root: Node): string {
  let out = "";
  const walk = (node: Node) => {
    for (const child of node.childNodes) {
      if (child.nodeType === Node.TEXT_NODE) out += child.nodeValue ?? "";
      else if (child instanceof HTMLBRElement) out += "\n";
      else if (child instanceof HTMLElement) {
        if (BLOCKS.has(child.tagName) && out && !out.endsWith("\n")) out += "\n";
        walk(child);
      }
    }
  };
  walk(root);
  return out;
}

/** The text as the member sees it. A line break at the very end only shows as a line once something
 * follows it, so browsers keep one extra there; that one isn't the member's. */
export function textOf(root: Node): string {
  const raw = rawText(root);
  return raw.endsWith("\n") ? raw.slice(0, -1) : raw;
}

/** The DOM is exactly what `render` would make for this text and these spans. */
function canonical(root: HTMLElement, value: string, spans: Span[]): boolean {
  let at = 0;
  let index = 0;
  for (const child of root.childNodes) {
    if (child.nodeType === Node.TEXT_NODE) {
      const text = child.nodeValue ?? "";
      const next = spans[index];
      if (next && at + text.length > next.start) return false;
      at += text.length;
    } else if (child instanceof HTMLSpanElement && child.dataset.mk) {
      const span = spans[index];
      const text = child.textContent ?? "";
      if (!span || child.dataset.mk !== span.id || at !== span.start) return false;
      if (child.childNodes.length !== 1 || at + text.length !== span.end) return false;
      at += text.length;
      index++;
    } else if (child instanceof HTMLBRElement) {
      at += 1;
    } else return false;
  }
  return index === spans.length && textOf(root) === value;
}

function render(root: HTMLElement, value: string, spans: Span[]) {
  const parts = document.createDocumentFragment();
  let at = 0;
  for (const span of spans) {
    if (span.start > at) parts.append(value.slice(at, span.start));
    const element = document.createElement("span");
    element.dataset.mk = span.id;
    element.className = "lib-at";
    element.append(value.slice(span.start, span.end));
    parts.append(element);
    at = span.end;
  }
  // The extra line break that lets a last empty line show (see textOf).
  const rest = value.slice(at) + (value.endsWith("\n") || value === "" ? "\n" : "");
  if (value !== "" && rest) parts.append(rest);
  root.replaceChildren(parts);
}

function offsetOf(root: Node, node: Node, offset: number): number {
  let total = 0;
  let found = -1;
  const walk = (current: Node): boolean => {
    if (current === node && current.nodeType === Node.TEXT_NODE) {
      found = total + offset;
      return true;
    }
    if (current === node) {
      // A position between children: everything before child `offset`.
      for (let index = 0; index < offset; index++) {
        const child = current.childNodes[index];
        if (child) total += rawText(wrap(child)).length;
      }
      found = total;
      return true;
    }
    if (current.nodeType === Node.TEXT_NODE) {
      total += current.nodeValue?.length ?? 0;
      return false;
    }
    if (current instanceof HTMLBRElement) {
      total += 1;
      return false;
    }
    for (const child of current.childNodes) if (walk(child)) return true;
    return false;
  };
  walk(root);
  return found < 0 ? rawText(root).length : found;
}

function wrap(node: Node): Node {
  const holder = document.createElement("div");
  holder.append(node.cloneNode(true));
  return holder;
}

/** The DOM position for a place in the text. At the end of a marked phrase it's just after the span,
 * so the next letter typed lands outside it. */
function pointAt(root: HTMLElement, target: number): [Node, number] {
  let at = 0;
  const children = [...root.childNodes];
  for (let index = 0; index < children.length; index++) {
    const child = children[index] as Node;
    if (child instanceof HTMLBRElement) {
      if (at === target) return [root, index];
      at += 1;
      continue;
    }
    const text = child.textContent ?? "";
    if (target <= at + text.length) {
      if (child instanceof HTMLSpanElement && target === at + text.length) return [root, index + 1];
      const inner = child.nodeType === Node.TEXT_NODE ? child : (child.firstChild ?? child);
      return [inner, target - at];
    }
    at += text.length;
  }
  return [root, root.childNodes.length];
}

function caretOf(root: HTMLElement): [number, number] | null {
  const selection = window.getSelection();
  if (!selection || selection.rangeCount === 0) return null;
  const range = selection.getRangeAt(0);
  if (!root.contains(range.startContainer)) return null;
  return [
    offsetOf(root, range.startContainer, range.startOffset),
    offsetOf(root, range.endContainer, range.endOffset),
  ];
}

function setCaret(root: HTMLElement, [start, end]: [number, number]) {
  const selection = window.getSelection();
  if (!selection) return;
  const range = document.createRange();
  const [startNode, startOffset] = pointAt(root, start);
  const [endNode, endOffset] = pointAt(root, end);
  try {
    range.setStart(startNode, startOffset);
    range.setEnd(endNode, endOffset);
    selection.removeAllRanges();
    selection.addRange(range);
  } catch {
    // A position that no longer exists: leave the caret where the browser put it.
  }
}

export function AnswerText({
  id,
  value,
  placeholder,
  spans,
  open,
  onChange,
  onPaste,
  onKeyDown,
  onLayout,
  handle,
  invalid,
  labelledBy,
}: Props) {
  const root = useRef<HTMLDivElement>(null);
  const composing = useRef(false);
  const plain = useRef<boolean | null>(null);

  useImperativeHandle(handle, () => ({
    focus: () => root.current?.focus(),
    element: () => root.current,
  }));

  const measure = useCallback(() => {
    const element = root.current;
    if (!element || !onLayout) return;
    const box = element.getBoundingClientRect();
    const rects = new Map<string, Rect[]>();
    for (const span of element.querySelectorAll<HTMLSpanElement>("span[data-mk]")) {
      const range = document.createRange();
      range.selectNodeContents(span);
      const lines: Rect[] = [];
      for (const line of range.getClientRects?.() ?? []) {
        if (line.width === 0) continue;
        lines.push({
          left: line.left - box.left,
          top: line.top - box.top,
          width: line.width,
          height: line.height,
        });
      }
      rects.set(span.dataset.mk as string, lines);
    }
    onLayout(rects);
  }, [onLayout]);

  // Bring the DOM in line with the text and its marks, keeping the caret where it was. Typing that
  // doesn't touch a marked phrase leaves the DOM alone, so the browser's own undo keeps working.
  useLayoutEffect(() => {
    const element = root.current;
    if (!element || composing.current) return;
    if (!canonical(element, value, spans)) {
      const focused = document.activeElement === element;
      const caret = focused ? caretOf(element) : null;
      render(element, value, spans);
      if (caret) setCaret(element, caret);
    }
    element.dataset.empty = String(value === "");
  });

  // Lines open and close by an attribute only: the text isn't touched.
  useLayoutEffect(() => {
    const element = root.current;
    if (!element) return;
    for (const span of element.querySelectorAll<HTMLSpanElement>("span[data-mk]")) {
      const move = spans.find((item) => item.id === span.dataset.mk)?.move;
      if (move && span.dataset.move !== move) span.dataset.move = move;
      const wanted = open.has(span.dataset.mk as string);
      if (wanted && span.dataset.open !== "true") {
        // Starts closed, then opens, so it eases rather than jumps.
        span.dataset.open = "false";
        requestAnimationFrame(() => {
          span.dataset.open = "true";
        });
      } else if (!wanted && span.dataset.open === "true") span.dataset.open = "false";
    }
  });

  // Follow the text as it reflows, and while lines ease open.
  useLayoutEffect(() => {
    measure();
    let frame = 0;
    const until = performance.now() + 450;
    const follow = () => {
      measure();
      if (performance.now() < until) frame = requestAnimationFrame(follow);
    };
    frame = requestAnimationFrame(follow);
    return () => cancelAnimationFrame(frame);
  });

  useLayoutEffect(() => {
    const element = root.current;
    if (!element || typeof ResizeObserver === "undefined") return;
    const observer = new ResizeObserver(() => measure());
    observer.observe(element);
    document.fonts?.ready.then(() => measure()).catch(() => undefined);
    return () => observer.disconnect();
  }, [measure]);

  useLayoutEffect(() => {
    const element = root.current;
    if (!element) return;
    plain.current ??= supportsPlainText();
    element.contentEditable = plain.current ? "plaintext-only" : "true";
  }, []);

  const emit = () => {
    const element = root.current;
    if (element) onChange(textOf(element));
  };

  const paste = (event: ClipboardEvent<HTMLDivElement>) => {
    // Only words come in: no formatting, links or pictures.
    event.preventDefault();
    const text = event.clipboardData.getData("text/plain").replace(/\r\n?/g, "\n");
    if (!text) return;
    onPaste?.(text);
    insert(text);
  };

  const insert = (text: string) => {
    // insertText keeps the browser's undo. Where it isn't there, put the words in by hand.
    if (document.execCommand?.("insertText", false, text)) return;
    const element = root.current;
    if (!element) return;
    const caret = caretOf(element) ?? [value.length, value.length];
    onChange(value.slice(0, caret[0]) + text + value.slice(caret[1]));
  };

  return (
    // biome-ignore lint/a11y/useSemanticElements: a textarea can't open one line for a note
    <div
      id={id}
      ref={root}
      role="textbox"
      tabIndex={0}
      aria-multiline="true"
      aria-labelledby={labelledBy}
      aria-invalid={invalid || undefined}
      aria-placeholder={placeholder}
      data-placeholder={placeholder}
      className="lib-field"
      spellCheck
      suppressContentEditableWarning
      onInput={() => {
        if (!composing.current) emit();
      }}
      onCompositionStart={() => {
        composing.current = true;
      }}
      onCompositionEnd={() => {
        composing.current = false;
        emit();
      }}
      onPaste={paste}
      // A line that has finished opening has moved the words after it: draw the ink where they are now.
      onTransitionEnd={measure}
      onKeyDown={(event) => {
        onKeyDown?.(event);
        if (event.defaultPrevented) return;
        // Without plain-text editing a browser may write a new line as a block; write a plain one.
        if (event.key === "Enter" && !plain.current && !event.metaKey && !event.ctrlKey) {
          event.preventDefault();
          insert("\n");
        }
      }}
    />
  );
}
