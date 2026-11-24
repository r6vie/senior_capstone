"""Sending email. Features call the `notify_*` functions; nothing else sends mail."""

import json
import logging
import smtplib
import ssl
from collections.abc import Callable
from datetime import UTC, datetime
from email.message import EmailMessage
from email.utils import parseaddr
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen
from uuid import uuid4

from pymongo.asynchronous.database import AsyncDatabase
from pymongo.errors import DuplicateKeyError
from starlette.concurrency import run_in_threadpool

from trove.auth.service import email_recipient
from trove.core.config import Settings, get_settings
from trove.notifications import templates
from trove.notifications.links import unsubscribe_url

logger = logging.getLogger(__name__)

BREVO_SEND_URL = "https://api.brevo.com/v3/smtp/email"

# Builds (subject, text, html) from the recipient's unsubscribe link.
MakeMessage = Callable[[str], tuple[str, str, str]]


async def ensure_indexes(database: AsyncDatabase) -> None:
    await database.notifications.create_index("user_id", name="notifications_user")


def clean_header(value: str) -> str:
    # Member-supplied names can end up in subjects; collapse newlines so they cannot add headers.
    return " ".join(value.split())


def _send_sync(settings: Settings, to: str, subject: str, text: str, html: str) -> None:
    message = EmailMessage()
    message["From"] = clean_header(settings.email_from)
    message["To"] = to
    message["Subject"] = clean_header(subject)
    message.set_content(text)
    message.add_alternative(html, subtype="html")
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as server:
        server.starttls(context=ssl.create_default_context())
        if settings.smtp_user:
            server.login(settings.smtp_user, settings.smtp_password)
        server.send_message(message)


def _send_brevo_sync(settings: Settings, to: str, subject: str, text: str, html: str) -> None:
    """Send through Brevo's web API: plain HTTPS, so it works where SMTP ports are blocked."""
    name, address = parseaddr(clean_header(settings.email_from))
    body = {
        "sender": {"email": address, **({"name": name} if name else {})},
        "to": [{"email": to}],
        "subject": clean_header(subject),
        "textContent": text,
        "htmlContent": html,
    }
    request = Request(
        BREVO_SEND_URL,
        data=json.dumps(body).encode(),
        method="POST",
        headers={
            "api-key": settings.brevo_api_key,
            "content-type": "application/json",
            "accept": "application/json",
        },
    )
    with urlopen(request, timeout=10) as response:  # raises HTTPError for a refusal
        response.read()


def _why(error: Exception) -> str:
    """What to write in the log for a failed send: the kind of error, plus the provider's own reason when
    it gave one (it never includes our key). Never the recipient."""
    if isinstance(error, HTTPError):
        return f"HTTPError {error.code}: {error.read().decode(errors='replace')[:200]}"
    return type(error).__name__


async def notify_once(
    database: AsyncDatabase,
    dedupe_key: str,
    user_id: str,
    make_message: MakeMessage,
    transactional: bool = False,
) -> str:
    """Email one member at most once per dedupe_key.

    Returns "sent", "failed", "duplicate", "skipped" (inactive or unsubscribed) or "logged" (no
    SMTP configured: the email is printed instead). A failed send is retried by the next call
    with the same key. Transactional emails ignore the unsubscribe choice.
    """
    user = await email_recipient(database, user_id)
    if user is None or (not transactional and user.get("email_notifications", True) is False):
        return "skipped"

    settings = get_settings()
    if not settings.smtp_host and not settings.brevo_api_key:
        subject, text, _ = make_message(unsubscribe_url(user_id))
        print(f"[email not configured] To user {user_id}: {subject}\n{text}\n")
        return "logged"

    record = {"_id": dedupe_key, "user_id": user_id, "status": "pending", "created_at": datetime.now(UTC)}
    try:
        await database.notifications.insert_one(record)
    except DuplicateKeyError:
        retry = await database.notifications.find_one_and_update(
            {"_id": dedupe_key, "status": "failed"},
            {"$set": {"status": "pending"}},
        )
        if retry is None:
            return "duplicate"

    try:
        subject, text, html = make_message(unsubscribe_url(user_id))
        send = _send_brevo_sync if settings.brevo_api_key else _send_sync
        await run_in_threadpool(send, settings, user["email"], subject, text, html)
        status = "sent"
    except Exception as error:  # Email trouble must never break the request that triggered it.
        logger.warning("Email to user %s failed: %s", user_id, _why(error))
        status = "failed"
    await database.notifications.update_one({"_id": dedupe_key}, {"$set": {"status": status}})
    return status


async def notify_checkout_requested(
    database: AsyncDatabase,
    *,
    checkout_id: str,
    author_id: str,
    reader_name: str,
    book_title: str,
    message: str,
    answer_days: int,
) -> str:
    """Tell an author someone checked out their book. Sample books have no account, so nothing is sent."""
    checkouts_url = f"{get_settings().frontend_url.rstrip('/')}/checkouts"
    return await notify_once(
        database,
        f"checkout-requested:{checkout_id}",
        author_id,
        templates.checkout_requested(reader_name, book_title, message, checkouts_url, answer_days).render,
    )


async def notify_meeting_reminder(
    database: AsyncDatabase,
    *,
    checkout_id: str,
    user_id: str,
    other_name: str,
    book_title: str,
    start: datetime,
    video_link: str | None,
    place_note: str | None,
) -> str:
    """Remind one member of a confirmed meeting. A new time earns a new reminder."""
    meeting_url = f"{get_settings().frontend_url.rstrip('/')}/checkouts/{checkout_id}/meeting"
    when = f"{start:%A %B} {start.day} at {start:%H:%M} UTC"
    return await notify_once(
        database,
        f"meeting-reminder:{checkout_id}:{start.isoformat()}:{user_id}",
        user_id,
        templates.meeting_reminder(other_name, book_title, when, meeting_url, video_link, place_note).render,
    )


async def notify_checkout_accepted(
    database: AsyncDatabase,
    *,
    checkout_id: str,
    reader_id: str,
    author_id: str,
    reader_name: str,
    author_name: str,
    book_title: str,
) -> None:
    """Tell both people the author said yes. Each respects their own email setting."""
    checkouts_url = f"{get_settings().frontend_url.rstrip('/')}/checkouts"
    await notify_once(
        database,
        f"checkout-accepted-reader:{checkout_id}",
        reader_id,
        templates.checkout_accepted_for_reader(author_name, book_title, checkouts_url).render,
    )
    await notify_once(
        database,
        f"checkout-accepted-author:{checkout_id}",
        author_id,
        templates.checkout_accepted_for_author(reader_name, book_title, checkouts_url).render,
    )


async def notify_new_message(
    database: AsyncDatabase,
    *,
    message_id: str,
    checkout_id: str,
    recipient_id: str,
    sender_name: str,
    book_title: str,
) -> str:
    """Tell one member there's something new in a checkout's thread. Messaging decides when (10-minute gap)."""
    thread_url = f"{get_settings().frontend_url.rstrip('/')}/checkouts/{checkout_id}/messages"
    return await notify_once(
        database,
        f"new-message:{message_id}:{recipient_id}",
        recipient_id,
        templates.new_message(sender_name, book_title, thread_url).render,
    )


async def notify_welcome(database: AsyncDatabase, user_id: str, first_name: str) -> str:
    app_url = get_settings().frontend_url
    return await notify_once(
        database,
        f"welcome:{user_id}",
        user_id,
        templates.welcome(first_name, app_url).render,
    )


async def notify_verification_code(database: AsyncDatabase, user_id: str, code: str, email: str) -> str:
    """Send a case.edu verification code. Every code is a new email, and it goes out even if the member
    turned notifications off, since they cannot sign in without it."""
    verify_url = f"{get_settings().frontend_url.rstrip('/')}/verify?email={quote(email)}"
    return await notify_once(
        database,
        f"verification-code:{uuid4()}",
        user_id,
        templates.verification_code(code, verify_url).render,
        transactional=True,
    )


async def notify_password_reset_code(database: AsyncDatabase, user_id: str, code: str, email: str) -> str:
    """Send a password reset code. Like a verification code, every one is a new email and ignores the
    member's email setting."""
    reset_url = f"{get_settings().frontend_url.rstrip('/')}/reset-password?email={quote(email)}"
    return await notify_once(
        database,
        f"password-reset-code:{uuid4()}",
        user_id,
        templates.password_reset_code(code, reset_url).render,
        transactional=True,
    )
