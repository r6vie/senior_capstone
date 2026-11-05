"""Speech-to-text with word timestamps for member video takes (free, runs locally)."""

import subprocess
from dataclasses import dataclass


@dataclass(frozen=True)
class Word:
    text: str
    start: float
    end: float


def decode_audio(path: str):
    """16 kHz mono float samples via ffmpeg (avoids faster-whisper's PyAV decoder)."""
    import numpy as np

    raw = subprocess.run(
        ["ffmpeg", "-loglevel", "error", "-i", path, "-vn", "-ac", "1", "-ar", "16000", "-f", "f32le", "-"],
        check=True, capture_output=True,
    ).stdout
    return np.frombuffer(raw, dtype=np.float32)


def transcribe(path: str, model_size: str = "base") -> list[Word]:
    """Transcribe a video or audio file with faster-whisper on the CPU."""
    from faster_whisper import WhisperModel

    model = WhisperModel(model_size, device="cpu", compute_type="int8")
    segments, _ = model.transcribe(decode_audio(path), word_timestamps=True, vad_filter=True)
    return [Word(w.word.strip(), w.start, w.end) for s in segments for w in s.words or []]


def as_transcript(words: list[Word]) -> str:
    """Timestamped text for the cut-selection prompt: one numbered word per token."""
    return " ".join(f"[{i}|{w.start:.2f}]{w.text}" for i, w in enumerate(words))
