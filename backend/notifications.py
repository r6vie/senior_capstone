"""Email sending, once-only delivery, unsubscribe links, and the hooks the API calls."""

import hashlib
import hmac
import logging
import os
import secrets
import smtplib
import ssl
import time
from datetime import datetime, timezone
from email.message import EmailMessage
from html import escape
from pathlib import Path
from urllib.parse import quote

from dotenv import dotenv_values
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse
from pymongo.errors import DuplicateKeyError
from starlette.concurrency import run_in_threadpool

from database import get_database
from email_templates import connection_accepted, connection_request, new_message, verify_email, welcome
from match_reasons import match_reasons

router = APIRouter(prefix="/notifications", tags=["Notifications"])
log = logging.getLogger(__name__)
# Used only when EMAIL_LINK_SECRET is missing: links then stop working after a restart.
_FALLBACK_SECRET = secrets.token_hex(32)
PUBLIC_FIELDS = {"_id": 1, "name": 1, "affiliation": 1, "location": 1, "expertise": 1, "interests": 1}


def settings() -> dict:
    # Same .env location database.py uses; real environment variables win.
    return {**dotenv_values(Path(__file__).resolve().parent.parent / ".env"), **os.environ}


def smtp_configured() -> bool:
    return bool(settings().get("SMTP_HOST"))


def frontend_url() -> str:
    return (settings().get("FRONTEND_URL") or "http://localhost:5173").rstrip("/")


def api_url() -> str:
    return (settings().get("API_URL") or "http://127.0.0.1:8000").rstrip("/")


# ---- Signed links: nobody can forge an unsubscribe or confirmation link -------------------

def _sign(message: str) -> str:
    config = settings()
    # UNSUBSCRIBE_SECRET is the older name for the same setting.
    secret = config.get("EMAIL_LINK_SECRET") or config.get("UNSUBSCRIBE_SECRET") or _FALLBACK_SECRET
    return hmac.new(secret.encode(), message.encode(), hashlib.sha256).hexdigest()[:32]


def unsubscribe_token(user_id: str) -> str:
    return f"{user_id}.{_sign(user_id)}"


def user_id_from_token(token: str) -> str | None:
    user_id, _, signature = token.rpartition(".")
    if user_id and hmac.compare_digest(signature.encode(), _sign(user_id).encode()):
        return user_id
    return None


def unsubscribe_url(user_id: str) -> str:
    return f"{api_url()}/notifications/unsubscribe?token={quote(unsubscribe_token(user_id))}"


VERIFY_SECONDS = 24 * 3600


def verification_token(user_id: str, now: float | None = None) -> str:
    """A link token that names the account and stops working after 24 hours."""
    expires = int(time.time() if now is None else now) + VERIFY_SECONDS
    return f"{user_id}.{expires}.{_sign(f'verify:{user_id}:{expires}')}"


def verification_user_id(token: str, now: float | None = None) -> str | None:
    """The account a confirmation token names, or None if it is forged, malformed or expired."""
    parts = token.rsplit(".", 2)  # account ids are UUIDs, so they contain no dots
    if len(parts) != 3:
        return None
    user_id, expires, signature = parts
    try:
        expires_at = int(expires)
    except ValueError:
        return None
    if not user_id or not hmac.compare_digest(signature.encode(), _sign(f"verify:{user_id}:{expires}").encode()):
        return None
    return user_id if expires_at > (time.time() if now is None else now) else None


def verification_url(user_id: str) -> str:
    return f"{api_url()}/auth/verify?token={quote(verification_token(user_id))}"


# ---- Sending -------------------------------------------------------------------------------

def clean_header(value: str) -> str:
    # Member-supplied names end up in subjects; collapse newlines so they cannot add headers.
    return " ".join(value.split())


def _send_sync(s: dict, to: str, subject: str, text: str, html: str | None) -> None:
    message = EmailMessage()
    message["From"], message["To"], message["Subject"] = clean_header(s["EMAIL_FROM"]), to, clean_header(subject)
    message.set_content(text)
    if html:
        message.add_alternative(html, subtype="html")
    with smtplib.SMTP(s["SMTP_HOST"], int(s.get("SMTP_PORT") or 587), timeout=10) as server:
        server.starttls(context=ssl.create_default_context())
        if s.get("SMTP_USER"):
            server.login(s["SMTP_USER"], s.get("SMTP_PASSWORD") or "")
        server.send_message(message)


async def send_email(to: str, subject: str, text: str, html: str | None = None) -> None:
    await run_in_threadpool(_send_sync, settings(), to, subject, text, html)


async def notify_once(
    database, dedupe_key: str, user_id: str, make_message, extra: dict | None = None,
    transactional: bool = False,
) -> str:
    """Email one member at most once per dedupe_key.

    make_message(unsubscribe_url) returns (subject, text, html). Returns "sent", "failed",
    "duplicate", "skipped" (inactive or opted out) or "logged" (no SMTP configured).
    A failed send can be retried: the next call with the same key tries again.
    Transactional emails (such as confirming an address) ignore the unsubscribe choice.
    """
    user = await database.users.find_one(
        {"_id": user_id, "is_active": True}, {"email": 1, "email_notifications": 1},
    )
    if user is None or (not transactional and user.get("email_notifications", True) is False):
        return "skipped"

    if not smtp_configured():
        # Development mode: show the email instead of sending it, and record nothing.
        subject, text, _ = make_message(unsubscribe_url(user_id))
        print(f"[email not configured] For user {user_id}: {subject}\n{text}\n")
        return "logged"

    record = {"_id": dedupe_key, "user_id": user_id, "status": "pending",
              "created_at": datetime.now(timezone.utc), **(extra or {})}
    try:
        await database.notifications.insert_one(record)
    except DuplicateKeyError:
        retry = await database.notifications.find_one_and_update(
            {"_id": dedupe_key, "status": "failed"}, {"$set": {"status": "pending"}},
        )
        if retry is None:
            return "duplicate"

    try:
        subject, text, html = make_message(unsubscribe_url(user_id))
        await send_email(user["email"], subject, text, html)
        status = "sent"
    except Exception as error:  # Email trouble must never break the request that triggered it.
        log.warning("Email for user %s failed: %s", user_id, type(error).__name__)
        status = "failed"
    await database.notifications.update_one({"_id": dedupe_key}, {"$set": {"status": status}})
    return status


# ---- Hooks called by the API ---------------------------------------------------------------

async def _profile_of(database, user_id: str):
    return await database.profiles.find_one({"owner_user_id": user_id}, PUBLIC_FIELDS)


def _reasons(viewer: dict, other: dict) -> list[str]:
    try:
        return list(match_reasons(viewer, other))
    except Exception as error:  # A matching bug must not stop a request email from going out.
        log.warning("match_reasons failed: %s", type(error).__name__)
        return []


async def notify_verification(database, user_id: str, name: str) -> str:
    """Ask a new member to confirm their address. A repeat within 5 minutes sends nothing new."""
    window = int(time.time()) // 300

    def make(unsubscribe):
        return verify_email(name, verification_url(user_id)).render(unsubscribe)

    return await notify_once(database, f"verify:{user_id}:{window}", user_id, make, transactional=True)


async def notify_welcome(database, user_id: str, name: str) -> str:
    return await notify_once(
        database, f"welcome:{user_id}", user_id, lambda unsubscribe: welcome(name, frontend_url()).render(unsubscribe),
    )


async def notify_connection_request(database, connection_id: str) -> str | None:
    connection = await database.connections.find_one({"_id": connection_id})
    if connection is None:
        return None
    sender = await _profile_of(database, connection["sender_user_id"])
    recipient = await _profile_of(database, connection["recipient_user_id"])
    if sender is None or recipient is None:
        return None
    reasons = _reasons(recipient, sender)

    def make(unsubscribe):
        return connection_request(
            recipient, sender, connection.get("message"), reasons, frontend_url(),
            request_type=connection.get("type", "other"),
        ).render(unsubscribe)

    return await notify_once(
        database, f"connection-request:{connection_id}", connection["recipient_user_id"], make,
    )


async def notify_connection_accepted(database, connection_id: str) -> str | None:
    connection = await database.connections.find_one({"_id": connection_id})
    if connection is None:
        return None
    sender = await _profile_of(database, connection["sender_user_id"])
    accepter = await _profile_of(database, connection["recipient_user_id"])
    if sender is None or accepter is None:
        return None
    reasons = _reasons(sender, accepter)
    # Accepting means agreeing to share an email address, so the sender gets it here.
    accepter_account = await database.users.find_one(
        {"_id": connection["recipient_user_id"], "is_active": True}, {"email": 1},
    )
    contact_email = accepter_account["email"] if accepter_account else None

    def make(unsubscribe):
        return connection_accepted(
            sender, accepter, reasons, frontend_url(), request_type=connection.get("type", "other"),
            contact_email=contact_email,
        ).render(unsubscribe)

    return await notify_once(
        database, f"connection-accepted:{connection_id}", connection["sender_user_id"], make,
    )


async def notify_new_message(database, connection_id: str, message_id: str) -> str | None:
    """Email the other person about a new message, at most once per 10 minutes per conversation."""
    connection = await database.connections.find_one({"_id": connection_id})
    message = await database.messages.find_one({"_id": message_id})
    if connection is None or message is None:
        return None
    author_id = message["sender_user_id"]
    recipient_id = (
        connection["recipient_user_id"] if author_id == connection["sender_user_id"] else connection["sender_user_id"]
    )
    author = await _profile_of(database, author_id)
    recipient = await _profile_of(database, recipient_id)
    if author is None or recipient is None:
        return None

    def make(unsubscribe):
        return new_message(recipient, author, message["body"], frontend_url()).render(unsubscribe)

    window = int(time.time()) // 600
    return await notify_once(database, f"message:{connection_id}:{recipient_id}:{window}", recipient_id, make)


# ---- Unsubscribe page (public). GET only shows a button; POST makes the change, so email
# ---- scanners that open links in advance cannot unsubscribe anyone by accident. -------------

def message_page(body: str, status_code: int = 200) -> HTMLResponse:
    return HTMLResponse(
        "<!doctype html><meta charset='utf-8'><meta name='viewport' content='width=device-width'>"
        "<title>FoundersCircle</title>"
        f"<body style='font-family:system-ui,sans-serif;max-width:28rem;margin:4rem auto;padding:0 1rem'>{body}</body>",
        status_code=status_code,
    )


@router.get("/unsubscribe", response_class=HTMLResponse)
async def unsubscribe_page(token: str = Query(max_length=200)) -> HTMLResponse:
    """Confirmation page linked from every notification email."""
    if user_id_from_token(token) is None:
        raise HTTPException(status_code=400, detail="This unsubscribe link is not valid.")
    return message_page(
        "<h2>Stop FoundersCircle emails?</h2>"
        f"<form method='post' action='/notifications/unsubscribe?token={escape(quote(token))}'>"
        "<button type='submit'>Unsubscribe</button></form>"
    )


@router.post("/unsubscribe", response_class=HTMLResponse)
async def unsubscribe(token: str = Query(max_length=200), database=Depends(get_database)) -> HTMLResponse:
    """Turn off notification emails for the account named in the signed token."""
    user_id = user_id_from_token(token)
    if user_id is None:
        raise HTTPException(status_code=400, detail="This unsubscribe link is not valid.")
    await database.users.update_one({"_id": user_id}, {"$set": {"email_notifications": False}})
    return message_page("<h2>You're unsubscribed.</h2><p>You will no longer get emails from FoundersCircle.</p>")
