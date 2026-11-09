"""The ledger of real Claude calls: one JSON line per call, so a shared budget can't be overrun.

Print the total and a breakdown with `python3 scripts/ai_spend.py`.
"""

import json
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import NamedTuple

from anthropic.types.beta import BetaMessage

from trove.core.config import get_settings


class Price(NamedTuple):
    """Dollars per million tokens. Cache writes are the 5-minute kind, the only kind Trove uses."""

    input: float
    output: float
    cache_read: float
    cache_write: float


PRICES = {
    "claude-opus-5-5": Price(4.00, 20.00, 0.20, 5.00),
    "claude-sonnet-5-5": Price(2.00, 10.00, 0.20, 2.50),
    "claude-haiku-5-5": Price(0.10, 0.50, 0.01, 0.125),
}
# Haiku 5.5 costs five times as much once a prompt passes 100K tokens.
HAIKU_LONG_PROMPT = 100_000
HAIKU_LONG = Price(0.50, 2.50, 0.05, 0.625)
# A model missing from the table is priced high, so a mistake here can't hide spending.
UNKNOWN_MODEL = Price(10.00, 50.00, 1.00, 12.50)


class BudgetExceeded(Exception):
    """The ledger has reached AI_BUDGET_USD, so no more real calls are made."""


def cost_of(model: str, usage) -> float:
    """What one response cost, in dollars."""
    read = usage.cache_read_input_tokens or 0
    written = usage.cache_creation_input_tokens or 0
    price = PRICES.get(model, UNKNOWN_MODEL)
    if model == "claude-haiku-5-5" and usage.input_tokens + read + written > HAIKU_LONG_PROMPT:
        price = HAIKU_LONG
    return (
        usage.input_tokens * price.input
        + usage.output_tokens * price.output
        + read * price.cache_read
        + written * price.cache_write
    ) / 1_000_000


def read_ledger(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def total_spent(path: Path) -> float:
    return sum(entry["cost_usd"] for entry in read_ledger(path))


def check_budget() -> None:
    """Raise BudgetExceeded once the ledger's total reaches the budget. No ledger means no limit."""
    settings = get_settings()
    if settings.ai_usage_log and settings.ai_budget_usd is not None:
        spent = total_spent(Path(settings.ai_usage_log))
        if spent >= settings.ai_budget_usd:
            raise BudgetExceeded(f"Spent ${spent:.2f} of the ${settings.ai_budget_usd:.2f} AI budget.")


def record(response: BetaMessage, prompt: str | None) -> None:
    """Append one call to the ledger, if there is one."""
    log = get_settings().ai_usage_log
    if not log:
        return
    usage = response.usage
    entry = {
        "time": datetime.now(UTC).isoformat(),
        "model": response.model,
        "prompt": prompt,
        "input_tokens": usage.input_tokens,
        "output_tokens": usage.output_tokens,
        "cache_read_tokens": usage.cache_read_input_tokens or 0,
        "cache_write_tokens": usage.cache_creation_input_tokens or 0,
        "cost_usd": round(cost_of(response.model, usage), 6),
    }
    path = Path(log)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as ledger:
        ledger.write(json.dumps(entry) + "\n")


def report(entries: list[dict], budget: float | None) -> str:
    """The total, then calls and dollars by model and by prompt."""
    total = sum(entry["cost_usd"] for entry in entries)
    lines = [f"Total: ${total:.4f}" + (f" of ${budget:.2f}" if budget is not None else "")]
    lines.append(f"Calls: {len(entries)}")
    for field in ("model", "prompt"):
        groups: dict[str, list[dict]] = defaultdict(list)
        for entry in entries:
            groups[entry[field] or "(unknown)"].append(entry)
        lines += ["", f"By {field}:"]
        for name, group in sorted(groups.items(), key=lambda item: -sum(e["cost_usd"] for e in item[1])):
            spent = sum(entry["cost_usd"] for entry in group)
            lines.append(f"  {name:<28} {len(group):>5} calls  ${spent:.4f}")
    return "\n".join(lines)


def main() -> int:
    settings = get_settings()
    if not settings.ai_usage_log:
        print("AI_USAGE_LOG isn't set, so nothing is being recorded.")
        return 0
    print(report(read_ledger(Path(settings.ai_usage_log)), settings.ai_budget_usd))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
