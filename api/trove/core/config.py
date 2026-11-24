"""Settings read from the repository's .env file. Real environment variables win."""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=REPO_ROOT / ".env", env_ignore_empty=True, extra="ignore")

    mongodb_uri: str = ""
    # Each developer uses their own database (trove_dev_<name>) so test data never collides.
    mongodb_database: str = "trove_dev"
    # Where the tests make their throwaway databases. A local MongoDB makes the suite many times faster than
    # the shared Atlas cluster, and keeps test load off the cluster the live site also uses.
    trove_test_mongodb_uri: str = ""

    anthropic_api_key: str = ""
    anthropic_model: str = "claude-opus-5-5"
    # The ledger of real Claude calls, and the total at which the client stops making them.
    ai_usage_log: str = ""
    ai_budget_usd: float | None = None
    # "scripted" swaps Claude for canned replies that cost nothing. Local development only.
    ai_mode: Literal["real", "scripted"] = "real"
    ai_scripted_delay_seconds: float = 1.5

    # Brevo's web API, for hosts that block outbound SMTP (Render's free tier does). When set, mail goes
    # through it over HTTPS and the smtp_* settings are not used. An API key, not an SMTP key.
    brevo_api_key: str = ""

    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    email_from: str = "Trove <noreply@example.com>"
    email_link_secret: str = ""

    # Anything but a development value turns off the development-only features above.
    environment: str = "development"
    # Sign-up needs a case.edu code or an invite (docs/trove.md §9.2). Turn off only for local work.
    verification_required: bool = True

    # How many proxies sit in front of the API and add their view of the caller to X-Forwarded-For (a host's
    # load balancer is 1). 0 means none, and the header is ignored. Attempt limits are per address, so
    # behind a proxy this must be set or every visitor looks like the same one (docs/deploy.md).
    trusted_proxy_hops: int = 0

    frontend_url: str = "http://127.0.0.1:5173"
    api_url: str = "http://127.0.0.1:8000"


@lru_cache
def get_settings() -> Settings:
    return Settings()
