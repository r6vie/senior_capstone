"""Sessions, password hashing and rate limits. Other features import `get_current_user` from here."""

import hashlib
import secrets
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime, timedelta

from fastapi import Depends, HTTPException, Request, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pwdlib import PasswordHash
from pymongo import ReturnDocument
from pymongo.asynchronous.database import AsyncDatabase
from pymongo.errors import DuplicateKeyError

from trove.auth.models import ContactDetailsResponse, ContactDetailsUpdate, UserResponse
from trove.core.database import get_database

SESSION_SECONDS = 7 * 24 * 3600
bearer = HTTPBearer(auto_error=False, description="The access_token returned by POST /auth/login.")
password_hasher = PasswordHash.recommended()
# Unknown emails still run a password check, so response timing doesn't reveal which accounts exist.
DUMMY_HASH = password_hasher.hash("Not a real account password.")
USER_FIELDS = {
    "_id": 1,
    "first_name": 1,
    "last_name": 1,
    "email": 1,
    "email_notifications": 1,
    "created_at": 1,
}


async def ensure_indexes(database: AsyncDatabase) -> None:
    # Unique indexes prevent duplicates even when requests arrive at the same moment.
    await database.users.create_index("email", unique=True, name="users_email_unique")
    await database.sessions.create_index("token_hash", unique=True, name="sessions_token_unique")
    await database.sessions.create_index("expires_at", expireAfterSeconds=0, name="sessions_expiry")
    await database.auth_attempts.create_index("expires_at", expireAfterSeconds=0, name="attempts_expiry")


def token_digest(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def unauthorized() -> HTTPException:
    return HTTPException(
        status_code=401,
        detail="Please sign in again.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def public_user(user: dict) -> UserResponse:
    return UserResponse(
        id=user["_id"],
        first_name=user["first_name"],
        last_name=user.get("last_name"),
        full_name=full_name(user),
        email=user["email"],
        email_notifications=user.get("email_notifications", True),
        created_at=user["created_at"],
    )


def get_session_token(credentials: HTTPAuthorizationCredentials | None = Security(bearer)) -> str:
    if credentials is None or len(credentials.credentials) > 256:
        raise unauthorized()
    return credentials.credentials


async def get_current_user(
    token: str = Depends(get_session_token),
    database: AsyncDatabase = Depends(get_database),
) -> dict:
    """FastAPI dependency: the signed-in user's account document, or 401."""
    session = await database.sessions.find_one(
        {
            "token_hash": token_digest(token),
            "expires_at": {"$gt": datetime.now(UTC)},
        }
    )
    if session is None:
        raise unauthorized()
    # Check the account on every request, even if the session has not expired yet.
    user = await database.users.find_one({"_id": session["user_id"], "is_active": True}, USER_FIELDS)
    if user is None:
        raise unauthorized()
    return user


async def create_session(database: AsyncDatabase, user_id: str) -> str:
    """Store a new session and return its bearer token. Only the token's hash is saved."""
    token = secrets.token_urlsafe(32)
    await database.sessions.insert_one(
        {
            "token_hash": token_digest(token),
            "user_id": user_id,
            "expires_at": datetime.now(UTC) + timedelta(seconds=SESSION_SECONDS),
        }
    )
    return token


async def limit_attempts(request: Request, database: AsyncDatabase, action: str, limit: int, seconds: int):
    """A fixed-window limit kept in the database, so it holds across workers and restarts."""
    now = datetime.now(UTC)
    window = int(now.timestamp()) // seconds
    # Don't trust X-Forwarded-For headers sent by clients.
    address = request.client.host if request.client else "unknown"
    key = token_digest(f"{action}:{address}:{window}")
    expires_at = datetime.fromtimestamp((window + 1) * seconds, UTC)
    try:
        attempt = await database.auth_attempts.find_one_and_update(
            {"_id": key},
            {"$inc": {"count": 1}, "$setOnInsert": {"expires_at": expires_at}},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
    except DuplicateKeyError:
        # Another worker created this exact counter at the same moment.
        attempt = await database.auth_attempts.find_one_and_update(
            {"_id": key},
            {"$inc": {"count": 1}},
            return_document=ReturnDocument.AFTER,
        )
    if attempt["count"] > limit:
        raise HTTPException(
            status_code=429,
            detail="Too many attempts. Please try again later.",
            headers={"Retry-After": str(max(1, int((expires_at - now).total_seconds())))},
        )


def full_name(user: dict) -> str:
    """First and last name. Accounts made before last names were collected have only a first name."""
    return " ".join(part for part in (user.get("first_name"), user.get("last_name")) if part)


async def full_names_of(database: AsyncDatabase, user_ids: list[str]) -> dict[str, str]:
    """The full name of each active account among `user_ids`, by id. Books show these (trove.md §3)."""
    users = database.users.find(
        {"_id": {"$in": user_ids}, "is_active": True}, {"first_name": 1, "last_name": 1}
    )
    return {user["_id"]: full_name(user) async for user in users}


async def email_recipient(database: AsyncDatabase, user_id: str) -> dict | None:
    """The active account's email address and email preference, for the notifications feature."""
    return await database.users.find_one(
        {"_id": user_id, "is_active": True}, {"email": 1, "email_notifications": 1}
    )


async def set_email_notifications(database: AsyncDatabase, user_id: str, enabled: bool) -> None:
    await database.users.update_one({"_id": user_id}, {"$set": {"email_notifications": enabled}})


async def first_name_of(database: AsyncDatabase, user_id: str) -> str | None:
    """The active account's first name, for greetings. Books show full names (trove.md §9.1)."""
    user = await database.users.find_one({"_id": user_id, "is_active": True}, {"first_name": 1})
    return user["first_name"] if user else None


async def contact_details_of(database: AsyncDatabase, user_id: str) -> ContactDetailsResponse | None:
    """What this member chose to share once an author says yes: their email, plus a LinkedIn link
    and a phone number if they added them. `None` if there is no active account.

    Call this only after an accepted checkout (trove.md §9.1). Contact details never appear on a
    book, on the shelf, or before a yes.
    """
    user = await database.users.find_one({"_id": user_id, "is_active": True}, {"email": 1, "contact": 1})
    if user is None:
        return None
    contact = user.get("contact") or {}
    return ContactDetailsResponse(
        email=user["email"], linkedin_url=contact.get("linkedin_url"), phone=contact.get("phone")
    )


async def set_contact_details(database: AsyncDatabase, user_id: str, details: ContactDetailsUpdate) -> None:
    contact = {key: value for key, value in details.model_dump().items() if value is not None}
    await database.users.update_one({"_id": user_id}, {"$set": {"contact": contact}})


# Other features clean up their own data when an account is deleted (CONTRIBUTING.md: a feature only
# touches its own collections). Each owner registers a function from its own service module, for
# example books removes the member's book. A hook is called with the database and the member's id.
DeletionHook = Callable[[AsyncDatabase, str], Awaitable[None]]
deletion_hooks: list[DeletionHook] = []


def on_account_deleted(hook: DeletionHook) -> DeletionHook:
    """Register a cleanup that runs, before the account goes, when a member deletes their account."""
    deletion_hooks.append(hook)
    return hook


async def delete_account(database: AsyncDatabase, user_id: str) -> None:
    """Remove the account and everything auth keeps about it. Other features' hooks run first, so a
    failing hook leaves the account in place and the member can try again."""
    for hook in deletion_hooks:
        await hook(database, user_id)
    await database.sessions.delete_many({"user_id": user_id})
    await database.users.delete_one({"_id": user_id})
