from datetime import UTC, datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response
from pymongo.asynchronous.database import AsyncDatabase

from trove.auth import invites
from trove.auth.models import (
    InviteCheckRequest,
    InviteCheckResponse,
    InviteCreated,
    InviteView,
    LoginResponse,
    ResendRequest,
    VerifyRequest,
)
from trove.auth.service import (
    SESSION_SECONDS,
    create_session,
    full_names_of,
    get_current_user,
    limit_attempts,
)
from trove.auth.verification import check_code, resend_code
from trove.core.config import get_settings
from trove.core.database import get_database
from trove.notifications.service import notify_verification_code, notify_welcome

router = APIRouter(prefix="/auth", tags=["Verification and invites"])


@router.post("/verify", response_model=LoginResponse)
async def verify(
    data: VerifyRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    database: AsyncDatabase = Depends(get_database),
) -> LoginResponse:
    """Confirm a case.edu email with the 6-digit code we sent. Signs the member in."""
    await limit_attempts(request, database, "verify", limit=10, seconds=900)
    user_id = await check_code(database, data.email, data.code, datetime.now(UTC))
    if user_id is None:
        raise HTTPException(
            status_code=400, detail="That code isn't right, or it has expired. You can ask for a new one."
        )
    user = await database.users.find_one({"_id": user_id}, {"first_name": 1})
    background_tasks.add_task(notify_welcome, database, user_id, user["first_name"])
    token = await create_session(database, user_id)
    return LoginResponse(access_token=token, expires_in=SESSION_SECONDS)


@router.post("/verify/resend", status_code=204, response_class=Response)
async def resend(
    data: ResendRequest,
    request: Request,
    background_tasks: BackgroundTasks,
    database: AsyncDatabase = Depends(get_database),
) -> Response:
    """Send a new code. Answers the same whether or not the email has an account, and at most one a minute."""
    await limit_attempts(request, database, "resend", limit=5, seconds=3600)
    sent = await resend_code(database, data.email, datetime.now(UTC))
    if sent is not None:
        user_id, code = sent
        background_tasks.add_task(notify_verification_code, database, user_id, code, data.email)
    return Response(status_code=204)


@router.post("/invites", response_model=InviteCreated, status_code=201)
async def create_invite(
    user: dict = Depends(get_current_user),
    database: AsyncDatabase = Depends(get_database),
) -> InviteCreated:
    """Make a single-use link for an alum. It lasts 14 days; you can have 5 open at a time."""
    try:
        invite, token = await invites.create_invite(database, user["_id"], datetime.now(UTC))
    except invites.InviteLimit:
        raise HTTPException(
            status_code=409, detail="You have 5 open invites. Cancel one or wait for one to be used."
        ) from None
    link = f"{get_settings().frontend_url.rstrip('/')}/sign-up?invite={token}"
    return InviteCreated(
        id=invite["_id"], created_at=invite["created_at"], expires_at=invite["expires_at"], link=link
    )


@router.get("/invites", response_model=list[InviteView])
async def my_invites(
    user: dict = Depends(get_current_user),
    database: AsyncDatabase = Depends(get_database),
) -> list[InviteView]:
    """Your open invites. The link itself is only shown when you make it."""
    open_ones = await invites.open_invites(database, user["_id"], datetime.now(UTC))
    return [
        InviteView(id=invite["_id"], created_at=invite["created_at"], expires_at=invite["expires_at"])
        for invite in open_ones
    ]


@router.delete("/invites/{invite_id}", status_code=204, response_class=Response)
async def cancel_invite(
    invite_id: str,
    user: dict = Depends(get_current_user),
    database: AsyncDatabase = Depends(get_database),
) -> Response:
    if not await invites.revoke_invite(database, user["_id"], invite_id):
        raise HTTPException(status_code=404, detail="That invite isn't open.")
    return Response(status_code=204)


@router.post("/invites/check", response_model=InviteCheckResponse)
async def check_invite(
    data: InviteCheckRequest,
    request: Request,
    database: AsyncDatabase = Depends(get_database),
) -> InviteCheckResponse:
    """For the sign-up page: who invited you, if the link still works. Doesn't use it up."""
    await limit_attempts(request, database, "invite-check", limit=20, seconds=900)
    inviter_id = await invites.inviter_of(database, data.invite, datetime.now(UTC))
    name = (await full_names_of(database, [inviter_id] if inviter_id else [])).get(inviter_id or "")
    if name is None:
        raise HTTPException(status_code=404, detail="This invite link has already been used or has expired.")
    return InviteCheckResponse(inviter_name=name)
