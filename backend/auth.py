"""Email/password accounts and revocable, one-hour bearer sessions."""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request, Response, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError
from pwdlib import PasswordHash
from starlette.concurrency import run_in_threadpool

from auth_models import LoginRequest, LoginResponse, SignupRequest, UserResponse
from database import get_database

router = APIRouter(prefix="/auth", tags=["Accounts"])
bearer = HTTPBearer(auto_error=False, description="Paste the access_token returned by POST /auth/login.")
password_hasher = PasswordHash.recommended()
# Unknown emails still perform password verification, avoiding an obvious timing shortcut.
DUMMY_HASH = password_hasher.hash("Not a real account password.")
SESSION_SECONDS = 3600


def token_digest(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def unauthorized() -> HTTPException:
    return HTTPException(
        status_code=401, detail="Please log in with a valid, unexpired session.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_session_token(
    credentials: HTTPAuthorizationCredentials | None = Security(bearer),
) -> str:
    if credentials is None or len(credentials.credentials) > 256:
        raise unauthorized()
    return credentials.credentials


async def get_current_user(
    token: str = Depends(get_session_token), database=Depends(get_database),
) -> dict:
    session = await database.sessions.find_one({
        "token_hash": token_digest(token),
        "expires_at": {"$gt": datetime.now(timezone.utc)},
    })
    if session is None:
        raise unauthorized()
    # Check membership on every request, even if a session has not expired yet.
    user = await database.users.find_one(
        {"_id": session["user_id"], "is_active": True},
        {"_id": 1, "name": 1, "email": 1, "created_at": 1},
    )
    if user is None:
        raise unauthorized()
    return user


def public_user(user: dict) -> UserResponse:
    return UserResponse(
        id=user["_id"], name=user["name"], email=user["email"], created_at=user["created_at"],
    )


async def limit_attempts(request: Request, database, action: str, limit: int, seconds: int):
    """Database-backed fixed-window limit shared by server workers/restarts."""
    now = datetime.now(timezone.utc)
    window = int(now.timestamp()) // seconds
    # Do not trust arbitrary X-Forwarded-For headers from clients.
    address = request.client.host if request.client else "unknown"
    key = token_digest(f"{action}:{address}:{window}")
    expires_at = datetime.fromtimestamp((window + 1) * seconds, timezone.utc)
    update = {"$inc": {"count": 1}, "$setOnInsert": {"expires_at": expires_at}}
    try:
        attempt = await database.auth_attempts.find_one_and_update(
            {"_id": key}, update, upsert=True, return_document=ReturnDocument.AFTER,
        )
    except DuplicateKeyError:
        # Another worker may have created this exact counter concurrently.
        attempt = await database.auth_attempts.find_one_and_update(
            {"_id": key}, {"$inc": {"count": 1}}, return_document=ReturnDocument.AFTER,
        )
    if attempt["count"] > limit:
        raise HTTPException(
            status_code=429, detail="Too many attempts. Please try again later.",
            headers={"Retry-After": str(max(1, int((expires_at - now).total_seconds())))},
        )


@router.post("/signup", response_model=UserResponse, status_code=201)
async def signup(data: SignupRequest, request: Request, database=Depends(get_database)) -> UserResponse:
    """Create an account with a 12–128 character password, then use /auth/login."""
    await limit_attempts(request, database, "signup", limit=5, seconds=3600)
    password_hash = await run_in_threadpool(password_hasher.hash, data.password.get_secret_value())
    user = {
        "_id": str(uuid4()), "name": data.name, "email": data.email,
        "password_hash": password_hash, "is_active": True,
        "created_at": datetime.now(timezone.utc),
    }
    try:
        await database.users.insert_one(user)
    except DuplicateKeyError:
        raise HTTPException(status_code=409, detail="An account with this email already exists.") from None
    return public_user(user)


@router.post("/login", response_model=LoginResponse)
async def login(
    data: LoginRequest, request: Request, response: Response, database=Depends(get_database),
) -> LoginResponse:
    """Log in and copy access_token into the docs' Authorize button."""
    await limit_attempts(request, database, "login", limit=10, seconds=900)
    user = await database.users.find_one({"email": data.email})
    password_hash = user["password_hash"] if user else DUMMY_HASH
    valid = await run_in_threadpool(password_hasher.verify, data.password.get_secret_value(), password_hash)
    if not valid or user is None or not user.get("is_active", False):
        raise HTTPException(
            status_code=401, detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = secrets.token_urlsafe(32)
    await database.sessions.insert_one({
        "token_hash": token_digest(token), "user_id": user["_id"],
        "expires_at": datetime.now(timezone.utc) + timedelta(seconds=SESSION_SECONDS),
    })
    response.headers["Cache-Control"] = "no-store"
    return LoginResponse(access_token=token, expires_in=SESSION_SECONDS)


@router.get("/me", response_model=UserResponse)
async def me(user: dict = Depends(get_current_user)) -> UserResponse:
    """Show the account belonging to the current login session."""
    return public_user(user)


@router.post("/logout", status_code=204, response_class=Response)
async def logout(
    user: dict = Depends(get_current_user), token: str = Depends(get_session_token),
    database=Depends(get_database),
) -> Response:
    """Immediately revoke this session. Other logged-in sessions remain active."""
    await database.sessions.delete_one({"token_hash": token_digest(token), "user_id": user["_id"]})
    return Response(status_code=204)
