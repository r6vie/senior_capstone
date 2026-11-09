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


@cache
def _names_by_text() -> dict[str, str]:
    return {
        path.read_text(encoding="utf-8").strip(): path.relative_to(PROMPTS_DIR).with_suffix("").as_posix()
        for path in PROMPTS_DIR.rglob("*.md")
    }


def prompt_name(system: object) -> str | None:
    """Which prompt file a request's `system` text came from, or None if it isn't one of them."""
    return _names_by_text().get(system) if isinstance(system, str) else None
