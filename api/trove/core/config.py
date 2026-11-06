"""Settings read from the repository's .env file. Real environment variables win."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=REPO_ROOT / ".env", env_ignore_empty=True, extra="ignore")

    mongodb_uri: str = ""
    # Each developer uses their own database (trove_dev_<name>) so test data never collides.
    mongodb_database: str = "trove_dev"

    anthropic_api_key: str = ""
    anthropic_model: str = "claude-opus-5-5"

    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    email_from: str = "Trove <noreply@example.com>"
    email_link_secret: str = ""

    frontend_url: str = "http://127.0.0.1:5173"
    api_url: str = "http://127.0.0.1:8000"


@lru_cache
def get_settings() -> Settings:
    return Settings()
