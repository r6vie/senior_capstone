"""Invite links: how alumni join (docs/trove.md §9.2).

A verified member makes a link; whoever signs up with it is verified without a case.edu email.
Each link works once and expires after 14 days, a member can have 5 open at a time, and we keep
who invited whom. Only a hash of the link's token is stored, so it can be shown once.
"""

import secrets
from datetime import datetime, timedelta
from uuid import uuid4

from pymongo.asynchronous.database import AsyncDatabase

from trove.auth.service import token_digest

INVITE_DAYS = 14
MAX_OPEN = 5


class InviteLimit(Exception):
    pass


def open_filter(now: datetime) -> dict:
    return {"used_by": None, "expires_at": {"$gt": now}}


async def create_invite(database: AsyncDatabase, inviter_id: str, now: datetime) -> tuple[dict, str]:
    """Make a link. Returns the stored invite and the token for the link, which is never stored."""
    if await database.invites.count_documents({"inviter_id": inviter_id, **open_filter(now)}) >= MAX_OPEN:
        raise InviteLimit
    token = secrets.token_urlsafe(24)
    invite = {
        "_id": str(uuid4()),
        "token_hash": token_digest(token),
        "inviter_id": inviter_id,
        "created_at": now,
        "expires_at": now + timedelta(days=INVITE_DAYS),
        "used_by": None,
    }
    await database.invites.insert_one(invite)
    return invite, token


async def open_invites(database: AsyncDatabase, inviter_id: str, now: datetime) -> list[dict]:
    cursor = database.invites.find({"inviter_id": inviter_id, **open_filter(now)}).sort("created_at", -1)
    return [invite async for invite in cursor]


async def revoke_invite(database: AsyncDatabase, inviter_id: str, invite_id: str) -> bool:
    result = await database.invites.delete_one({"_id": invite_id, "inviter_id": inviter_id, "used_by": None})
    return result.deleted_count == 1


async def inviter_of(database: AsyncDatabase, token: str, now: datetime) -> str | None:
    """Who a still-usable link came from, without using it."""
    invite = await database.invites.find_one({"token_hash": token_digest(token), **open_filter(now)})
    return invite["inviter_id"] if invite else None


async def claim_invite(database: AsyncDatabase, token: str, user_id: str, now: datetime) -> str | None:
    """Use a link for this new account. Returns the inviter's id, or None if it is used or expired.
    Two people racing for one link cannot both get it."""
    invite = await database.invites.find_one_and_update(
        {"token_hash": token_digest(token), **open_filter(now)},
        {"$set": {"used_by": user_id, "used_at": now}},
    )
    return invite["inviter_id"] if invite else None


async def release_invite(database: AsyncDatabase, token: str, user_id: str) -> None:
    """Give the link back when the sign-up it was used for did not go through."""
    await database.invites.update_one(
        {"token_hash": token_digest(token), "used_by": user_id},
        {"$set": {"used_by": None}, "$unset": {"used_at": ""}},
    )
