"""Signed tokens for links in emails, so nobody can forge an unsubscribe link for someone else."""

import hashlib
import hmac
import secrets
from urllib.parse import quote

from trove.core.config import get_settings

# Used only when EMAIL_LINK_SECRET is missing; links then stop working after a restart.
_FALLBACK_SECRET = secrets.token_hex(32)


def sign(message: str) -> str:
    secret = get_settings().email_link_secret or _FALLBACK_SECRET
    return hmac.new(secret.encode(), message.encode(), hashlib.sha256).hexdigest()[:32]


def unsubscribe_token(user_id: str) -> str:
    return f"{user_id}.{sign(f'unsubscribe:{user_id}')}"


def user_id_from_unsubscribe_token(token: str) -> str | None:
    user_id, _, signature = token.rpartition(".")
    if user_id and hmac.compare_digest(signature.encode(), sign(f"unsubscribe:{user_id}").encode()):
        return user_id
    return None


def unsubscribe_url(user_id: str) -> str:
    return f"{get_settings().api_url.rstrip('/')}/notifications/unsubscribe?token={quote(unsubscribe_token(user_id))}"
