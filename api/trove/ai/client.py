"""A thin wrapper around the Anthropic SDK so every Claude call shares the same defaults."""

from anthropic import AsyncAnthropic
from anthropic.types.beta import BetaMessage
from fastapi import HTTPException

from trove.core.config import get_settings

# On a safety decline, the API re-runs the request on Anthropic's recommended fallback model.
FALLBACK_BETA = "server-side-fallback-2026-07-01"
# Models that accept fallbacks="default". Haiku 5.5 has no server-side fallback and must not get it.
FALLBACK_MODELS = {"claude-fable-5-1", "claude-opus-5-5", "claude-opus-5", "claude-sonnet-5-5"}


class ClaudeRefused(Exception):
    """Claude (and its fallback) declined the request. Features decide what the member sees."""


class Claude:
    def __init__(self, api_key: str, model: str):
        self.model = model
        self.client = AsyncAnthropic(api_key=api_key)

    def request(self, params: dict) -> dict:
        """The full request body: Trove's defaults plus the caller's parameters."""
        extra = {"betas": [FALLBACK_BETA], "fallbacks": "default"} if self.model in FALLBACK_MODELS else {}
        return {"model": self.model, **params, **extra}

    async def create(self, **params) -> BetaMessage:
        """Send one Messages API request. Raises ClaudeRefused instead of returning a refusal."""
        response = await self.client.beta.messages.create(**self.request(params))
        if response.stop_reason == "refusal":
            raise ClaudeRefused()
        return response


def text_of(response: BetaMessage) -> str:
    """All text blocks of a response, joined. Thinking and tool blocks are skipped."""
    return "".join(block.text for block in response.content if block.type == "text").strip()


_claude: Claude | None = None


def get_claude() -> Claude:
    """FastAPI dependency: the shared Claude client, or 503 until ANTHROPIC_API_KEY is set."""
    global _claude
    settings = get_settings()
    if not settings.anthropic_api_key:
        raise HTTPException(
            status_code=503, detail="AI isn't set up. Add ANTHROPIC_API_KEY to .env and restart."
        )
    if _claude is None or _claude.model != settings.anthropic_model:
        _claude = Claude(settings.anthropic_api_key, settings.anthropic_model)
    return _claude
