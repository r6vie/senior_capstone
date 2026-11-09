"""What eval runs spend, and the cheap client for the simulated member.

The real ledger is the client's AI_USAGE_LOG. This only breaks a run down so a report can say what
each step cost. Prices are dollars per million tokens (input, output, cache read); a cache write
costs 1.25 times input.
"""

import copy

from trove.ai.client import Claude

PRICES = {
    "claude-opus-5-5": (4.00, 20.00, 0.20),
    "claude-sonnet-5-5": (2.00, 10.00, 0.20),
    "claude-haiku-5-5": (0.10, 0.50, 0.01),
}
# The member is only played, so a cheaper model does it; the product's own prompts stay on Opus. Haiku was
# tried first: it opened nearly every answer with "Honestly" and never used Skip, which stopped testing either.
MEMBER_MODEL = "claude-sonnet-5-5"


# What the product ships on (docs/trove.md §4). A local .env may point the app at something cheaper, and an
# eval on that would measure the wrong model.
PRODUCT_MODEL = "claude-opus-5-5"


def on_model(claude: Claude, model: str) -> Claude:
    """The same client, including whatever guards it, on another model."""
    moved = copy.copy(claude)
    moved.model = model
    return moved


def member_client(claude: Claude) -> Claude:
    return on_model(claude, MEMBER_MODEL)


def product_client(claude: Claude) -> Claude:
    return on_model(claude, PRODUCT_MODEL)


class CountingClaude(Claude):
    """Passes calls through and adds up tokens, so each case reports what it cost."""

    def __init__(self, inner: Claude):
        self.model = inner.model
        self.inner = inner
        self.input_tokens = self.output_tokens = self.cached_tokens = self.written_tokens = self.calls = 0

    async def create(self, **params):
        response = await self.inner.create(**params)
        usage = response.usage
        self.calls += 1
        self.input_tokens += usage.input_tokens
        self.written_tokens += usage.cache_creation_input_tokens or 0
        self.cached_tokens += usage.cache_read_input_tokens or 0
        self.output_tokens += usage.output_tokens
        return response

    def dollars(self) -> float:
        price_in, price_out, price_cached = PRICES[self.model]
        return (
            self.input_tokens * price_in
            + self.written_tokens * price_in * 1.25
            + self.cached_tokens * price_cached
            + self.output_tokens * price_out
        ) / 1_000_000

    def line(self) -> str:
        return (
            f"{self.model}: {self.calls} calls, {self.input_tokens + self.written_tokens:,} input + "
            f"{self.cached_tokens:,} cached, {self.output_tokens:,} output, ${self.dollars():.3f}"
        )
