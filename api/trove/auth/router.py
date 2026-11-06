from datetime import UTC, datetime
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response
from pymongo.asynchronous.database import AsyncDatabase
from pymongo.errors import DuplicateKeyError
from starlette.concurrency import run_in_threadpool

from trove.auth.models import LoginRequest, LoginResponse, SignupRequest, UserResponse
from trove.auth.service import (
    DUMMY_HASH,
    SESSION_SECONDS,
    create_session,
    get_current_user,
    get_session_token,
    limit_attempts,
    password_hasher,
    public_user,
    token_digest,
)
from trove.core.database import get_database
from trove.notifications.service import notify_welcome

router = APIRouter(prefix="/auth", tags=["Accounts"])


@router.post("/signup", response_model=UserResponse, status_code=201)
async def signup(
    data: SignupRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    database: AsyncDatabase = Depends(get_database),
) -> UserResponse:
    """Create an account. Sign in afterwards with POST /auth/login."""
    await limit_attempts(request, database, "signup", limit=5, seconds=3600)
    password_hash = await run_in_threadpool(password_hasher.hash, data.password.get_secret_value())
    user = {
        "_id": str(uuid4()),
        "first_name": data.first_name,
        "email": data.email,
        "password_hash": password_hash,
        "is_active": True,
        "created_at": datetime.now(UTC),
    }
    try:
        await database.users.insert_one(user)
    except DuplicateKeyError:
        raise HTTPException(status_code=409, detail="An account with this email already exists.") from None
    background_tasks.add_task(notify_welcome, database, user["_id"], user["first_name"])
    return public_user(user)


@router.post("/login", response_model=LoginResponse)
async def login(
    data: LoginRequest,
    request: Request,
    database: AsyncDatabase = Depends(get_database),
) -> LoginResponse:
    await limit_attempts(request, database, "login", limit=10, seconds=900)
    user = await database.users.find_one({"email": data.email})
    password_hash = (user or {}).get("password_hash") or DUMMY_HASH
    valid = await run_in_threadpool(password_hasher.verify, data.password.get_secret_value(), password_hash)
    if not valid or user is None or not user.get("is_active", False):
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = await create_session(database, user["_id"])
    return LoginResponse(access_token=token, expires_in=SESSION_SECONDS)


@router.get("/me", response_model=UserResponse)
async def me(user: dict = Depends(get_current_user)) -> UserResponse:
    return public_user(user)


@router.post("/logout", status_code=204, response_class=Response)
async def logout(
    user: dict = Depends(get_current_user),
    token: str = Depends(get_session_token),
    database: AsyncDatabase = Depends(get_database),
) -> Response:
    """Revoke this session. Other signed-in sessions stay active."""
    await database.sessions.delete_one({"token_hash": token_digest(token), "user_id": user["_id"]})
    return Response(status_code=204)
