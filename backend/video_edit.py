"""Automatic short-form editing: trim dead air and fillers, caption, crop and clean audio."""

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from video_transcribe import Word

FILLERS = {"um", "uh", "er", "erm", "ah", "hmm", "mm", "uhh", "umm"}
MAX_GAP = 0.35
PAD = 0.08
CAPTION_GROUP = 3


@dataclass(frozen=True)
class Segment:
    start: float
    end: float


def is_filler(word: Word) -> bool:
    return re.sub(r"[^a-z]", "", word.text.lower()) in FILLERS


def plan_cuts(words: list[Word], max_gap: float = MAX_GAP, pad: float = PAD) -> tuple[list[Segment], list[Word]]:
    """Keep speech, drop fillers and long pauses.

    Returns the source segments to keep and the kept words retimed onto the edited timeline.
    """
    groups: list[list[Word]] = []
    split = True
    for word in words:
        if is_filler(word):
            split = True
            continue
        if split or word.start - groups[-1][-1].end > max_gap:
            groups.append([])
        groups[-1].append(word)
        split = False

    segments, captions, offset = [], [], 0.0
    for group in groups:
        start, end = max(0.0, group[0].start - pad), group[-1].end + pad
        if segments and start < segments[-1].end:
            start = segments[-1].end
        segments.append(Segment(start, end))
        captions += [Word(w.text, offset + w.start - start, offset + w.end - start) for w in group]
        offset += end - start
    return segments, captions


def _ass_time(seconds: float) -> str:
    cs = round(seconds * 100)
    return f"{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"


def build_ass(words: list[Word], width: int, height: int) -> str:
    """Word-by-word highlighted captions, three words at a time, lower third."""
    header = (
        f"[Script Info]\nScriptType: v4.00+\nPlayResX: {width}\nPlayResY: {height}\n\n"
        "[V4+ Styles]\nFormat: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,"
        "BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,"
        "Shadow,Alignment,MarginL,MarginR,MarginV,Encoding\n"
        f"Style: Default,Arial,{height // 22},&H0000E0FF,&H00FFFFFF,&H00000000,&H80000000,1,0,0,0,"
        f"100,100,0,0,1,4,1,2,60,60,{height // 5},1\n\n"
        "[Events]\nFormat: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text\n"
    )
    lines = []
    for i in range(0, len(words), CAPTION_GROUP):
        chunk = words[i:i + CAPTION_GROUP]
        text = " ".join(f"{{\\k{max(1, round((w.end - w.start) * 100))}}}{w.text}" for w in chunk)
        lines.append(f"Dialogue: 0,{_ass_time(chunk[0].start)},{_ass_time(chunk[-1].end)},Default,,0,0,0,,{text}")
    return header + "\n".join(lines) + "\n"


def render(src: Path, dst: Path, words: list[Word], vertical: bool = True) -> Path:
    """Cut `src` down to the speech in `words`, caption it and write `dst` (mp4)."""
    segments, captions = plan_cuts(words)
    if not segments:
        raise ValueError("No speech to keep")
    width, height = (1080, 1920) if vertical else (1280, 720)
    ass = dst.with_suffix(".ass")
    ass.write_text(build_ass(captions, width, height), encoding="utf-8")

    parts = []
    for i, seg in enumerate(segments):
        parts.append(f"[0:v]trim={seg.start:.3f}:{seg.end:.3f},setpts=PTS-STARTPTS[v{i}]")
        parts.append(f"[0:a]atrim={seg.start:.3f}:{seg.end:.3f},asetpts=PTS-STARTPTS[a{i}]")
    joined = "".join(f"[v{i}][a{i}]" for i in range(len(segments)))
    frame = f"crop=ih*{width}/{height}:ih,scale={width}:{height}" if vertical else f"scale={width}:{height}"
    parts.append(f"{joined}concat=n={len(segments)}:v=1:a=1[cv][ca]")
    parts.append(f"[cv]{frame},subtitles={ass.name}[v]")
    parts.append("[ca]highpass=f=80,afftdn=nf=-25,loudnorm=I=-16:TP=-1.5:LRA=11[a]")

    subprocess.run(
        ["ffmpeg", "-y", "-loglevel", "error", "-i", str(src.resolve()),
         "-filter_complex", ";".join(parts), "-map", "[v]", "-map", "[a]",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "128k", "-movflags", "+faststart", dst.name],
        cwd=dst.parent, check=True,
    )
    return dst
