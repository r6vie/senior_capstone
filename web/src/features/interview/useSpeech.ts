import { useCallback, useEffect, useRef, useState } from "react";

// The browser's built-in speech recognition (trove.md §4: no new service). Chrome and Safari expose it
// as webkitSpeechRecognition; where neither exists, the interview hides Speak and the member types.

interface RecognitionResult {
  isFinal: boolean;
  0: { transcript: string };
}

interface RecognitionEvent {
  resultIndex: number;
  results: ArrayLike<RecognitionResult>;
}

interface Recognition {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  onresult: ((event: RecognitionEvent) => void) | null;
  onerror: ((event: { error: string }) => void) | null;
  onend: (() => void) | null;
  start(): void;
  stop(): void;
  abort(): void;
}

type RecognitionConstructor = new () => Recognition;

function recognitionConstructor(): RecognitionConstructor | null {
  if (typeof window === "undefined") return null;
  const scope = window as unknown as {
    SpeechRecognition?: RecognitionConstructor;
    webkitSpeechRecognition?: RecognitionConstructor;
  };
  return scope.SpeechRecognition ?? scope.webkitSpeechRecognition ?? null;
}

export function speechSupported(): boolean {
  return recognitionConstructor() !== null;
}

const ERRORS: Record<string, string> = {
  "not-allowed": "The browser didn't allow the microphone. You can type your answer instead.",
  "service-not-allowed": "The browser didn't allow the microphone. You can type your answer instead.",
  "audio-capture": "No microphone was found. You can type your answer instead.",
  network: "Speech recognition needs a connection. You can type your answer instead.",
};

// How many times in a row recognition may end by itself, with nothing new heard, before we say so.
const MAX_QUIET_RESTARTS = 3;

function joined(left: string, right: string): string {
  return [left.trim(), right.trim()].filter(Boolean).join(" ");
}

export function useSpeech() {
  const recognition = useRef<Recognition | null>(null);
  const finalText = useRef("");
  const interimText = useRef("");
  // True from Speak until Stop, Cancel or an error: any other end is the browser giving up by itself.
  const wanted = useRef(false);
  const quietRestarts = useRef(0);
  const [listening, setListening] = useState(false);
  const [transcript, setTranscript] = useState("");
  const [dropped, setDropped] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const listen = useCallback(() => {
    const Constructor = recognitionConstructor();
    if (!Constructor) return;
    const next = new Constructor();
    next.continuous = true;
    next.interimResults = true;
    next.lang = navigator.language || "en-US";
    next.onresult = (event) => {
      let interim = "";
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i];
        if (!result) continue;
        // Some browsers run final results together, so the space is ours to add.
        if (result.isFinal) finalText.current = joined(finalText.current, result[0].transcript);
        else interim += result[0].transcript;
      }
      interimText.current = interim;
      quietRestarts.current = 0;
      setTranscript(joined(finalText.current, interim));
    };
    next.onerror = (event) => {
      if (event.error === "aborted" || event.error === "no-speech") return;
      wanted.current = false;
      setError(ERRORS[event.error] ?? "Speech recognition stopped. You can type your answer instead.");
    };
    next.onend = () => {
      // Words still in flight when recognition ended are the last thing the member said. Keep them.
      finalText.current = joined(finalText.current, interimText.current);
      interimText.current = "";
      setTranscript(finalText.current);
      if (recognition.current !== next) return;
      if (wanted.current) {
        quietRestarts.current += 1;
        if (quietRestarts.current <= MAX_QUIET_RESTARTS) {
          try {
            listen();
            return;
          } catch {
            // Falls through to telling the member the microphone stopped.
          }
        }
        wanted.current = false;
        setDropped(true);
      }
      setListening(false);
    };
    recognition.current = next;
    next.start();
  }, []);

  const start = useCallback(() => {
    recognition.current?.abort();
    finalText.current = "";
    interimText.current = "";
    quietRestarts.current = 0;
    wanted.current = true;
    setTranscript("");
    setDropped(false);
    setError(null);
    listen();
    setListening(true);
  }, [listen]);

  const stop = useCallback(() => {
    wanted.current = false;
    recognition.current?.stop();
  }, []);

  const cancel = useCallback(() => {
    wanted.current = false;
    recognition.current?.abort();
    setListening(false);
  }, []);

  useEffect(
    () => () => {
      wanted.current = false;
      recognition.current?.abort();
    },
    [],
  );

  return { listening, transcript, dropped, error, start, stop, cancel };
}
