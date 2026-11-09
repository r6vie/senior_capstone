import { type ReactNode, useEffect, useId, useRef, useState } from "react";
import { Button } from "../../ui/Button";
import { speechSupported, useSpeech } from "./useSpeech";

// The member's answer to one question: typed, or spoken and then corrected before sending.
// Drafts are kept in localStorage per question, so leaving mid-answer loses nothing.

type Mode = "typing" | "recording" | "transcript";

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

const BAR_COUNT = 19;

function levels(seed: number): number[] {
  // Deterministic, so the bars only change when a new piece of speech arrives.
  return Array.from({ length: BAR_COUNT }, (_, i) => 8 + ((seed * 7 + i * 13 + ((i * i) % 5) * 9) % 48));
}

interface Props {
  draftKey: string;
  busy: boolean;
  /** Shown beside Send once something is stored: an earlier answer or this draft. */
  hasSavedAnswers: boolean;
  onSend: (text: string) => void;
  onSkip: () => void;
  children?: ReactNode;
}

export function AnswerPanel({ draftKey, busy, hasSavedAnswers, onSend, onSkip, children }: Props) {
  const [mode, setMode] = useState<Mode>("typing");
  const [text, setText] = useState(() => readDraft(draftKey));
  const [draftSaved, setDraftSaved] = useState(false);
  const [stopping, setStopping] = useState(false);
  const speech = useSpeech();
  const canSpeak = speechSupported();
  const fieldId = useId();
  const field = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    setText(readDraft(draftKey));
    setMode("typing");
  }, [draftKey]);

  // Save the draft quietly a moment after the member stops typing.
  useEffect(() => {
    setDraftSaved(false);
    const timer = setTimeout(() => {
      writeDraft(draftKey, text);
      setDraftSaved(text.trim().length > 0);
    }, 600);
    return () => clearTimeout(timer);
  }, [draftKey, text]);

  // Final results can arrive just after Stop, so switch to the transcript once listening has ended.
  useEffect(() => {
    if (mode !== "recording" || speech.listening) return;
    if (speech.error) {
      setMode("typing");
      return;
    }
    if (stopping) {
      setText(speech.transcript);
      setStopping(false);
      setMode("transcript");
    }
  }, [mode, speech.listening, speech.error, speech.transcript, stopping]);

  function record() {
    setStopping(false);
    speech.start();
    setMode("recording");
  }

  function stop() {
    setStopping(true);
    speech.stop();
  }

  function cancel() {
    speech.cancel();
    setStopping(false);
    setMode("typing");
  }

  function send() {
    const answer = text.trim();
    if (!answer) {
      field.current?.focus();
      return;
    }
    onSend(answer);
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
          <div className="iv-wave" aria-hidden="true">
            {levels(speech.heard).map((height, i) => (
              // biome-ignore lint/suspicious/noArrayIndexKey: fixed set of bars
              <i key={i} style={{ height: speech.heard ? height : 6 }} />
            ))}
          </div>
          <p className="iv-note" role="status">
            Listening. Speak as you would to a friend. You can fix the words before anything is sent.
          </p>
        </div>
        <div className="iv-row">
          <Button onClick={stop} aria-busy={stopping}>
            Stop
          </Button>
          <span className="iv-grow" />
          <button type="button" className="button button-quiet" onClick={cancel}>
            Cancel
          </button>
        </div>
      </>
    );
  }

  const saved = hasSavedAnswers || draftSaved;

  return (
    <>
      <div className={`field iv-answer${mode === "transcript" ? " iv-answer-edit" : ""}`}>
        <label htmlFor={fieldId} className="iv-visually-hidden">
          Your answer
        </label>
        <textarea
          id={fieldId}
          ref={field}
          value={text}
          placeholder="Say it in your own words"
          onChange={(event) => setText(event.target.value)}
        />
      </div>
      {mode === "transcript" && <p className="iv-note">This is what I heard. Fix anything, then send it.</p>}
      {speech.error && (
        <p className="message" role="status">
          {speech.error}
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
        <button type="button" className="button button-quiet" onClick={onSkip}>
          Skip
        </button>
        <span className="iv-grow" />
        {saved && <span className="iv-saved">Saved</span>}
        <Button onClick={send} aria-busy={busy}>
          Send answer
        </Button>
      </div>
      {children}
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
