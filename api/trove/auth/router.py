from datetime import UTC, datetime
from uuid import uuid4

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response
from pymongo.asynchronous.database import AsyncDatabase
from pymongo.errors import DuplicateKeyError
from starlette.concurrency import run_in_threadpool

from trove.auth.invites import claim_invite, release_invite
from trove.auth.models import (
    ContactDetailsResponse,
    ContactDetailsUpdate,
    DeleteAccountRequest,
    LoginRequest,
    LoginResponse,
    NameUpdate,
    NotificationSettingsUpdate,
    SignupRequest,
    UserResponse,
)
from trove.auth.service import (
    DUMMY_HASH,
    SESSION_SECONDS,
    contact_details_of,
    create_session,
    delete_account,
    get_current_user,
    get_session_token,
    limit_attempts,
    password_hasher,
    public_user,
    set_contact_details,
    set_email_notifications,
    token_digest,
)
from trove.auth.verification import code_digest, is_case_email, is_verified, new_verification
from trove.core.config import get_settings
from trove.core.database import get_database
from trove.notifications.service import notify_verification_code, notify_welcome

router = APIRouter(prefix="/auth", tags=["Accounts"])


@router.post("/signup", response_model=UserResponse, status_code=201)
async def signup(
    data: SignupRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    database: AsyncDatabase = Depends(get_database),
) -> UserResponse:
    """Create an account. Students use their case.edu email and get a code to enter at POST /auth/verify;
    alumni sign up with an invite from a member. Then sign in with POST /auth/login."""
    await limit_attempts(request, database, "signup", limit=5, seconds=3600)
    now = datetime.now(UTC)
    password_hash = await run_in_threadpool(password_hasher.hash, data.password.get_secret_value())
    user = {
        "_id": str(uuid4()),
        "first_name": data.first_name,
        "last_name": data.last_name,
        "email": data.email,
        "password_hash": password_hash,
        "is_active": True,
        "created_at": now,
    }
    code = None
    invite = data.invite if get_settings().verification_required else None
    if invite:
        inviter_id = await claim_invite(database, invite, user["_id"], now)
        if inviter_id is None:
            raise HTTPException(
                status_code=422, detail="This invite link has already been used or has expired."
            )
        user |= {"verified": True, "invited_by": inviter_id}
    elif get_settings().verification_required:
        if not is_case_email(data.email):
            raise HTTPException(
                status_code=422,
                detail="Sign up with your case.edu email, or use an invite link from a Trove member.",
            )
        code, record = new_verification(user["_id"], now)
        user |= {"verified": False, "verification": record}
    try:
        await database.users.insert_one(user)
    except DuplicateKeyError:
        # Someone who never entered their code can try again (or the address's real owner can sign up).
        if code is None:
            if invite:
                await release_invite(database, invite, user["_id"])
            raise HTTPException(
                status_code=409, detail="An account with this email already exists."
            ) from None
        existing = await database.users.find_one({"email": data.email, "verified": False}, {"_id": 1})
        if existing is None:
            raise HTTPException(
                status_code=409, detail="An account with this email already exists."
            ) from None
        user["_id"] = existing["_id"]
        user["verification"]["code_hash"] = code_digest(existing["_id"], code)
        pending = {
            key: user[key]
            for key in ("first_name", "last_name", "password_hash", "verification", "created_at")
        }
        await database.users.update_one({"_id": existing["_id"], "verified": False}, {"$set": pending})
    if code is not None:
        background_tasks.add_task(notify_verification_code, database, user["_id"], code, user["email"])
    else:
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
    if not is_verified(user):
        raise HTTPException(status_code=403, detail="Please confirm your case.edu email first.")
    token = await create_session(database, user["_id"])
    return LoginResponse(access_token=token, expires_in=SESSION_SECONDS)


@router.get("/me", response_model=UserResponse)
async def me(user: dict = Depends(get_current_user)) -> UserResponse:
    return public_user(user)


@router.patch("/me", response_model=UserResponse)
async def update_me(
    data: NameUpdate,
    user: dict = Depends(get_current_user),
    database: AsyncDatabase = Depends(get_database),
) -> UserResponse:
    """Set or change the member's first or last name. Their book shows the new name straight away."""
    changes = data.model_dump(exclude_none=True)
    await database.users.update_one({"_id": user["_id"]}, {"$set": changes})
    return public_user({**user, **changes})


@router.get("/me/contact", response_model=ContactDetailsResponse)
async def my_contact_details(
    user: dict = Depends(get_current_user),
    database: AsyncDatabase = Depends(get_database),
) -> ContactDetailsResponse:
    """The contact details this member will share when an author says yes, for them to edit."""
    details = await contact_details_of(database, user["_id"])
    if details is None:
        raise HTTPException(status_code=404, detail="Account not found.")
    return details


@router.put("/me/contact", response_model=ContactDetailsResponse)
async def update_my_contact_details(
    data: ContactDetailsUpdate,
    user: dict = Depends(get_current_user),
    database: AsyncDatabase = Depends(get_database),
) -> ContactDetailsResponse:
    """Choose what to share on a yes. The sign-in email is always shared; LinkedIn and phone are optional."""
    await set_contact_details(database, user["_id"], data)
    return await my_contact_details(user, database)


@router.put("/me/notifications", response_model=UserResponse)
async def update_my_notifications(
    data: NotificationSettingsUpdate,
    user: dict = Depends(get_current_user),
    database: AsyncDatabase = Depends(get_database),
) -> UserResponse:
    """Turn email notifications on or off. Account emails are sent either way."""
    await set_email_notifications(database, user["_id"], data.email_notifications)
    return public_user({**user, "email_notifications": data.email_notifications})


@router.delete("/me", status_code=204, response_class=Response)
async def delete_me(
    data: DeleteAccountRequest,
    user: dict = Depends(get_current_user),
    database: AsyncDatabase = Depends(get_database),
) -> Response:
    """Delete the account for good. The body must repeat the account's email address."""
    if data.email != user["email"]:
        raise HTTPException(status_code=422, detail="That is not the email address on this account.")
    await delete_account(database, user["_id"])
    return Response(status_code=204)


@router.post("/logout", status_code=204, response_class=Response)
async def logout(
    user: dict = Depends(get_current_user),
    token: str = Depends(get_session_token),
    database: AsyncDatabase = Depends(get_database),
) -> Response:
    """Revoke this session. Other signed-in sessions stay active."""
    await database.sessions.delete_one({"token_hash": token_digest(token), "user_id": user["_id"]})
    return Response(status_code=204)
