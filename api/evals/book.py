"""Write a book from a saved interview: draft, finish, blurb after a removal, one rewrite.

    uv run python -m evals.book                     # lists the fixtures; spends nothing
    uv run python -m evals.book dana theo ruth      # writes evals/out/book/<timestamp>/<slug>.{json,md}
    uv run python -m evals.book dana --title 2      # finish with the second title

No interview happens, so this costs a fraction of evals.interview: about 5 Opus calls a persona.
Lint the results with evals.lint, and judge them with evals/rubric.md.
"""

import argparse
import asyncio
import json
from datetime import datetime

from evals.lints import lint_run
from evals.run import OUT_DIR
from evals.saved import fixtures, packet, persona_of, turns_of
from evals.usage import CountingClaude, product_client
from trove.ai.client import Claude, get_claude
from trove.interview import engine


async def replay(claude: Claude, fixture: dict, *, title_index: int = 0) -> dict:
    """The fixture's interview with a freshly written book, in the same shape as a saved run."""
    turns = turns_of(fixture)
    draft = await engine.draft_book(claude, turns=turns)
    title = draft.titles[title_index].title
    finished = await engine.finish_book(claude, turns=turns, draft=draft, title=title)
    rewritten, after_removal = await asyncio.gather(
        engine.rewrite_chapter(
            claude, turns=turns, chapters=finished.chapters, chapter_id=finished.chapters[-1].id
        ),
        engine.write_blurb(claude, turns=turns, chapters=finished.chapters[1:]),
    )
    return {
        **{key: fixture[key] for key in ("persona", "slug", "turns")},
        "source": f"replay of {fixture['source']}",
        "book": {
            "titles": [t.model_dump() for t in draft.titles],
            "pool": [_chapter(c) for c in draft.pool],
            "title": title,
            "chapters": [_chapter(c) for c in finished.chapters],
            "blurbs": {"draft": draft.blurb, "finished": finished.blurb, "after_removal": after_removal},
            "rewrite": _chapter(rewritten),
        },
    }


def _chapter(chapter: engine.DraftChapter) -> dict:
    return {"title": chapter.title, "summary": chapter.summary, "quotes": chapter.quotes}


async def run_one(claude: Claude, fixture: dict, folder, title_index: int) -> float:
    counting = CountingClaude(product_client(claude))
    try:
        run = await replay(counting, fixture, title_index=title_index)
    except Exception as error:  # one persona failing shouldn't lose the others
        print(f"failed: {fixture['slug']}: {type(error).__name__}: {error}", flush=True)
        return counting.dollars()
    (folder / f"{fixture['slug']}.json").write_text(
        json.dumps(run, indent=1, ensure_ascii=False), encoding="utf-8"
    )
    (folder / f"{fixture['slug']}.md").write_text(packet(run), encoding="utf-8")
    findings = lint_run(run, resume=persona_of(run).get("resume"))
    errors = [f for f in findings if f.level == "error"]
    print(
        f"{fixture['slug']}: {counting.line()}; lint {len(errors)} errors, {len(findings) - len(errors)} warnings"
    )
    return counting.dollars()


async def main(names: list[str], title_index: int) -> None:
    saved = fixtures()
    if not names:
        print("Name the fixtures to replay (this costs money):", ", ".join(saved))
        return
    folder = OUT_DIR / "book" / f"{datetime.now():%Y-%m-%d_%H%M%S}"
    folder.mkdir(parents=True, exist_ok=True)
    claude = get_claude()
    spent = await asyncio.gather(*(run_one(claude, saved[name], folder, title_index) for name in names))
    print(f"Saved {folder}. This batch: about ${sum(spent):.2f}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("names", nargs="*")
    parser.add_argument("--title", type=int, default=1, help="which of the three titles to finish with")
    args = parser.parse_args()
    asyncio.run(main(args.names, args.title - 1))
