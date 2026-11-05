"""Try the video pipeline on one file: python scripts/video_spike.py clip.mp4 [out_dir] [model]."""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from video_edit import plan_cuts, render
from video_transcribe import transcribe


def main() -> None:
    src = Path(sys.argv[1])
    out = Path(sys.argv[2] if len(sys.argv) > 2 else "video_out")
    model = sys.argv[3] if len(sys.argv) > 3 else "base"
    out.mkdir(parents=True, exist_ok=True)

    t = time.perf_counter()
    words = transcribe(str(src), model)
    print(f"transcribed {len(words)} words in {time.perf_counter() - t:.1f}s ({model})")
    print(" ".join(w.text for w in words))

    segments, _ = plan_cuts(words)
    kept = sum(s.end - s.start for s in segments)
    print(f"keeping {len(segments)} segments, {kept:.1f}s of speech")

    t = time.perf_counter()
    result = render(src, (out / f"{src.stem}_edit.mp4").resolve(), words)
    print(f"rendered {result} in {time.perf_counter() - t:.1f}s")


if __name__ == "__main__":
    main()
