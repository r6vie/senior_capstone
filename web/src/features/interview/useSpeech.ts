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

export function useSpeech() {
  const recognition = useRef<Recognition | null>(null);
  const finalText = useRef("");
  const [listening, setListening] = useState(false);
  const [transcript, setTranscript] = useState("");
  // Bumps on every result, so the level bars move only while the member is speaking.
  const [heard, setHeard] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const start = useCallback(() => {
    const Constructor = recognitionConstructor();
    if (!Constructor) return;
    recognition.current?.abort();
    const next = new Constructor();
    next.continuous = true;
    next.interimResults = true;
    next.lang = navigator.language || "en-US";
    finalText.current = "";
    setTranscript("");
    setError(null);
    next.onresult = (event) => {
      let interim = "";
      for (let i = event.resultIndex; i < event.results.length; i++) {
        const result = event.results[i];
        if (!result) continue;
        if (result.isFinal) finalText.current += result[0].transcript;
        else interim += result[0].transcript;
      }
      setTranscript((finalText.current + interim).trim());
      setHeard((count) => count + 1);
    };
    next.onerror = (event) => {
      if (event.error === "aborted" || event.error === "no-speech") return;
      setError(ERRORS[event.error] ?? "Speech recognition stopped. You can type your answer instead.");
    };
    next.onend = () => setListening(false);
    recognition.current = next;
    next.start();
    setListening(true);
  }, []);

  const stop = useCallback(() => recognition.current?.stop(), []);

  const cancel = useCallback(() => {
    recognition.current?.abort();
    setListening(false);
  }, []);

  useEffect(() => () => recognition.current?.abort(), []);

  return { listening, transcript, heard, error, start, stop, cancel };
}
