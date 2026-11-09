import { type ReactNode, useEffect, useId, useRef, useState } from "react";
import { Button } from "../../ui/Button";
import { speechSupported, useSpeech } from "./useSpeech";

// The member's answer to one question: typed, or spoken and then corrected before sending.
// Drafts are kept in localStorage per question, so leaving mid-answer loses nothing.

type Mode = "typing" | "recording" | "transcript";

// The API's limit on one answer. A long dictation can pass it, and it's likely the member's best one.
export const MAX_ANSWER_LENGTH = 5000;

function MicIcon() {
  return (
    <svg
      width="18"
      height="18"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2.2"
      strokeLinecap="round"
      aria-hidden="true"
    >
      <rect x="9" y="3" width="6" height="11" rx="3" />
      <path d="M5 11a7 7 0 0 0 14 0M12 18v3" />
    </svg>
  );
}

function withSpeech(prior: string, heard: string): string {
  return prior ? `${prior}\n\n${heard}` : heard;
}

/** The way out of the questions. It never drops words: anything in the field goes with it. */
export interface AnswerExit {
  label: string;
  labelWithWords: string;
  onFinish: (words: string | undefined) => void;
}

interface Props {
  /** Give the panel this as its `key` too: one panel per question, each with its own draft. */
  draftKey: string;
  busy: boolean;
  onSend: (text: string) => void;
  /** Move past the question. Offered only while the field is empty. */
  onSkip?: () => void;
  /** Sits under the field, for what the member should know before answering. */
  note?: ReactNode;
  /** A quiet action beside Speak that's always there, in place of Skip. */
  aside?: ReactNode;
  /** One line under the panel on how far along this is. Never a count. */
  progress?: string;
  exit?: AnswerExit;
}

export function AnswerPanel({ draftKey, busy, onSend, onSkip, note, aside, progress, exit }: Props) {
  const [mode, setMode] = useState<Mode>("typing");
  const [text, setText] = useState(() => readDraft(draftKey));
  const [draftSaved, setDraftSaved] = useState(false);
  const [micStopped, setMicStopped] = useState(false);
  const speech = useSpeech();
  const canSpeak = speechSupported();
  const fieldId = useId();
  const field = useRef<HTMLTextAreaElement>(null);
  const stopButton = useRef<HTMLButtonElement>(null);
  const previousMode = useRef<Mode>(mode);
  // What was in the field when Speak was pressed, and what the last recording added to it.
  const prior = useRef("");
  const lastHeard = useRef("");

  // Save the draft quietly a moment after the member stops typing.
  useEffect(() => {
    setDraftSaved(false);
    const timer = setTimeout(() => {
      writeDraft(draftKey, text);
      setDraftSaved(text.trim().length > 0);
    }, 600);
    return () => clearTimeout(timer);
  }, [draftKey, text]);

  // Final results can arrive just after Stop, so bring the words in once listening has really ended.
  // The field only ever gains words here: an empty recording leaves what the member typed alone.
  useEffect(() => {
    if (mode !== "recording" || speech.listening) return;
    const heard = speech.transcript.trim();
    lastHeard.current = heard;
    setText(heard ? withSpeech(prior.current, heard) : prior.current);
    setMicStopped(speech.dropped);
    setMode(heard ? "transcript" : "typing");
  }, [mode, speech.listening, speech.transcript, speech.dropped]);

  // Speak, Stop and Cancel unmount as the mode changes; keep keyboard focus where the member is working.
  useEffect(() => {
    if (previousMode.current === mode) return;
    previousMode.current = mode;
    if (mode === "recording") stopButton.current?.focus();
    else field.current?.focus();
  }, [mode]);

  function record() {
    // "Record again" replaces only the last recording, unless the member has since edited it.
    const again = mode === "transcript" && lastHeard.current && text.endsWith(lastHeard.current);
    prior.current = again ? text.slice(0, -lastHeard.current.length).trimEnd() : text.trimEnd();
    setMicStopped(false);
    speech.start();
    setMode("recording");
  }

  function cancel() {
    speech.cancel();
    setMode("typing");
  }

  const tooLong = text.length > MAX_ANSWER_LENGTH;
  const empty = !text.trim();

  function send() {
    if (tooLong) return;
    if (empty) {
      field.current?.focus();
      return;
    }
    onSend(text.trim());
  }

  if (mode === "recording") {
    return (
      <>
        <div className="panel iv-rec">
          <div className="iv-ring">
            <b>
              <MicIcon />
            </b>
          </div>
          {/* The words appearing are the honest sign that the microphone is working. */}
          {speech.transcript && <p className="iv-live">{speech.transcript}</p>}
          <p className="iv-note" role="status">
            Listening. Speak naturally. You can fix the words before anything is sent.
          </p>
        </div>
        <div className="iv-row">
          <button
            type="button"
            ref={stopButton}
            className="button button-primary"
            onClick={() => speech.stop()}
          >
            Stop
          </button>
          <span className="iv-grow" />
          <button type="button" className="button button-quiet" onClick={cancel}>
            Cancel
          </button>
        </div>
      </>
    );
  }

  return (
    <>
      <div
        className={`field iv-answer${mode === "transcript" ? " iv-answer-edit" : ""}`}
        data-invalid={tooLong || undefined}
      >
        <label htmlFor={fieldId} className="iv-visually-hidden">
          Your answer
        </label>
        <textarea
          id={fieldId}
          ref={field}
          value={text}
          placeholder="Say it in your own words"
          onChange={(event) => setText(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === "Enter" && (event.metaKey || event.ctrlKey)) {
              event.preventDefault();
              send();
            }
          }}
        />
        {tooLong && (
          <span className="hint" role="status">
            That's longer than I can take in one go. Trim it, or send the first part and I'll ask for the
            rest.
          </span>
        )}
      </div>
      {note && <p className="iv-note">{note}</p>}
      {mode === "transcript" && text.includes(lastHeard.current) && (
        <p className="iv-note">
          {micStopped
            ? "The microphone stopped. Here's what I heard."
            : "This is what I heard. Fix anything, then send it."}
        </p>
      )}
      {speech.error && (
        <p className="message" role="status">
          {speech.error}
        </p>
      )}
      {micStopped && mode === "typing" && (
        <p className="message" role="status">
          The microphone stopped before I heard anything. You can try again or type your answer.
        </p>
      )}
      <div className="iv-row">
        {canSpeak && (
          <Button variant="secondary" onClick={record}>
            <MicIcon /> {mode === "transcript" ? "Record again" : "Speak"}
          </Button>
        )}
        {mode === "transcript" && (
          <button type="button" className="button button-quiet" onClick={() => setMode("typing")}>
            Type instead
          </button>
        )}
        {/* Only while the field is empty: a mis-tap beside Send must never cost the member their words. */}
        {empty && onSkip && (
          <button type="button" className="button button-quiet" onClick={onSkip}>
            Skip
          </button>
        )}
        {aside}
        <span className="iv-grow" />
        {draftSaved && <span className="iv-saved">Saved</span>}
        <Button
          onClick={send}
          disabled={tooLong}
          aria-busy={busy}
          aria-keyshortcuts="Meta+Enter Control+Enter"
        >
          Send answer
        </Button>
      </div>
      {(exit || progress) && (
        <div className="iv-exit">
          {progress && <p className="iv-note">{progress}</p>}
          {exit && (
            <button
              type="button"
              className="iv-textlink"
              disabled={tooLong}
              onClick={() => exit.onFinish(empty ? undefined : text.trim())}
            >
              {empty ? exit.label : exit.labelWithWords}
            </button>
          )}
        </div>
      )}
    </>
  );
}

function readDraft(key: string): string {
  try {
    return localStorage.getItem(key) ?? "";
  } catch {
    return "";
  }
}

function writeDraft(key: string, text: string) {
  try {
    if (text.trim()) localStorage.setItem(key, text);
    else localStorage.removeItem(key);
  } catch {
    // Storage can be unavailable (private windows); the answer is still sent normally.
  }
}

export function clearDraft(key: string) {
  writeDraft(key, "");
}

const DRAFT_PREFIX = "trove_interview_draft:";

export function draftKeyFor(userId: string, question: string): string {
  return `${DRAFT_PREFIX}${userId}:${question}`;
}

/** Remove every saved draft on this browser. For sign-out, on a computer members may share. */
export function clearAllDrafts() {
  try {
    for (const key of Object.keys(localStorage)) {
      if (key.startsWith(DRAFT_PREFIX)) localStorage.removeItem(key);
    }
  } catch {
    // Nothing was stored, then.
  }
}
