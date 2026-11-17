"""Proving someone belongs to CWRU (docs/trove.md §9.2).

Students get a 6-digit code at their case.edu address. Alumni join with a single-use invite from a
verified member (see `invites.py`). Accounts made before verification existed count as verified.
"""

import hmac
import secrets
from datetime import datetime, timedelta

from pymongo import ReturnDocument
from pymongo.asynchronous.database import AsyncDatabase

from trove.auth.service import token_digest

CODE_MINUTES = 15
MAX_ATTEMPTS = 5
RESEND_SECONDS = 60


def is_case_email(email: str) -> bool:
    """Exactly `@case.edu`; `x@alumni.case.edu` or `x@case.edu.evil.com` do not count. Emails arrive lowercased."""
    return email.endswith("@case.edu")


def is_verified(user: dict) -> bool:
    return user.get("verified", True)


def code_digest(user_id: str, code: str) -> str:
    return token_digest(f"{user_id}:{code}")


def new_verification(user_id: str, now: datetime) -> tuple[str, dict]:
    """A fresh code and the record to store for it. Only a hash of the code is kept."""
    code = f"{secrets.randbelow(10**6):06d}"
    record = {
        "code_hash": code_digest(user_id, code),
        "expires_at": now + timedelta(minutes=CODE_MINUTES),
        "sent_at": now,
        "attempts": 0,
    }
    return code, record


async def resend_code(database: AsyncDatabase, email: str, now: datetime) -> tuple[str, str] | None:
    """A new code for an unverified account, unless one was sent in the last minute.

    Returns (user_id, code), or None when there is nothing to send. The caller answers the same
    either way, so nobody can use this to find out which emails have accounts.
    """
    user = await database.users.find_one({"email": email, "verified": False, "is_active": True}, {"_id": 1})
    if user is None:
        return None
    code, record = new_verification(user["_id"], now)
    sent = await database.users.update_one(
        {
            "_id": user["_id"],
            "verified": False,
            "$or": [
                {"verification.sent_at": {"$lte": now - timedelta(seconds=RESEND_SECONDS)}},
                {"verification": None},
            ],
        },
        {"$set": {"verification": record}},
    )
    return (user["_id"], code) if sent.modified_count else None


async def check_code(database: AsyncDatabase, email: str, code: str, now: datetime) -> str | None:
    """Verify the account if the code is right. Every try counts; after 5 wrong ones the code is dead
    until a new one is sent. Returns the user's id, or None."""
    user = await database.users.find_one_and_update(
        {
            "email": email,
            "verified": False,
            "is_active": True,
            "verification.expires_at": {"$gt": now},
            "verification.attempts": {"$lt": MAX_ATTEMPTS},
        },
        {"$inc": {"verification.attempts": 1}},
        return_document=ReturnDocument.AFTER,
    )
    if user is None or not hmac.compare_digest(
        user["verification"]["code_hash"], code_digest(user["_id"], code)
    ):
        return None
    await database.users.update_one(
        {"_id": user["_id"]}, {"$set": {"verified": True}, "$unset": {"verification": ""}}
    )
    return user["_id"]
