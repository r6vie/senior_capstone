"""Prompts live as Markdown files under trove/ai/prompts/, one file per prompt, reviewed like code."""

from functools import cache
from pathlib import Path

PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"


@cache
def load_prompt(name: str) -> str:
    """Load trove/ai/prompts/<name>.md, e.g. load_prompt("interview/system")."""
    path = (PROMPTS_DIR / f"{name}.md").resolve()
    if PROMPTS_DIR not in path.parents:
        raise ValueError(f"Prompt names stay inside {PROMPTS_DIR}: {name!r}")
    return path.read_text(encoding="utf-8").strip()
