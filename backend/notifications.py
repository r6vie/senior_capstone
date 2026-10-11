"""Email sending, once-only delivery, unsubscribe links, and the hooks the API calls."""

import hashlib
import hmac
import logging
import os
import secrets
import smtplib
import ssl
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
from email_templates import connection_accepted, connection_request, welcome
from match_reasons import match_reasons

router = APIRouter(prefix="/notifications", tags=["Notifications"])
log = logging.getLogger(__name__)
# Used only when UNSUBSCRIBE_SECRET is missing: links then stop working after a restart.
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


# ---- Unsubscribe links: signed so nobody can unsubscribe someone else ----------------------

def _signature(user_id: str) -> str:
    secret = settings().get("UNSUBSCRIBE_SECRET") or _FALLBACK_SECRET
    return hmac.new(secret.encode(), user_id.encode(), hashlib.sha256).hexdigest()[:32]


def unsubscribe_token(user_id: str) -> str:
    return f"{user_id}.{_signature(user_id)}"


def user_id_from_token(token: str) -> str | None:
    user_id, _, signature = token.rpartition(".")
    if user_id and hmac.compare_digest(signature.encode(), _signature(user_id).encode()):
        return user_id
    return None


def unsubscribe_url(user_id: str) -> str:
    return f"{api_url()}/notifications/unsubscribe?token={quote(unsubscribe_token(user_id))}"


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


async def notify_once(database, dedupe_key: str, user_id: str, make_message, extra: dict | None = None) -> str:
    """Email one member at most once per dedupe_key.

    make_message(unsubscribe_url) returns (subject, text, html). Returns "sent", "failed",
    "duplicate", "skipped" (inactive or opted out) or "logged" (no SMTP configured).
    A failed send can be retried: the next call with the same key tries again.
    """
    user = await database.users.find_one(
        {"_id": user_id, "is_active": True}, {"email": 1, "email_notifications": 1},
    )
    if user is None or user.get("email_notifications", True) is False:
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

    def make(unsubscribe):
        return connection_accepted(sender, accepter, reasons, frontend_url()).render(unsubscribe)

    return await notify_once(
        database, f"connection-accepted:{connection_id}", connection["sender_user_id"], make,
    )


# ---- Unsubscribe page (public). GET only shows a button; POST makes the change, so email
# ---- scanners that open links in advance cannot unsubscribe anyone by accident. -------------

def _message_page(body: str) -> HTMLResponse:
    return HTMLResponse(
        "<!doctype html><meta charset='utf-8'><meta name='viewport' content='width=device-width'>"
        "<title>FoundersCircle emails</title>"
        f"<body style='font-family:system-ui,sans-serif;max-width:28rem;margin:4rem auto;padding:0 1rem'>{body}</body>"
    )


@router.get("/unsubscribe", response_class=HTMLResponse)
async def unsubscribe_page(token: str = Query(max_length=200)) -> HTMLResponse:
    """Confirmation page linked from every notification email."""
    if user_id_from_token(token) is None:
        raise HTTPException(status_code=400, detail="This unsubscribe link is not valid.")
    return _message_page(
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
    return _message_page("<h2>You're unsubscribed.</h2><p>You will no longer get emails from FoundersCircle.</p>")
