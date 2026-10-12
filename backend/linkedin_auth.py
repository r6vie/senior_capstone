"""Sign up and log in with LinkedIn (OpenID Connect authorization-code flow).

LinkedIn is the only way to create an account. The browser never sees LinkedIn's
tokens: the backend trades the code for the member's details, saves them on the
user, and hands the browser a short-lived, single-use code to swap for a session.
"""

import os
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode
from uuid import uuid4

import httpx
from dotenv import dotenv_values
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from pymongo.errors import DuplicateKeyError

from auth import SESSION_SECONDS, create_session, limit_attempts, token_digest
from auth_models import LinkedInExchangeRequest, LinkedInLoginResponse
from database import get_database

router = APIRouter(prefix="/auth/linkedin", tags=["LinkedIn sign-in"])

AUTHORIZE_URL = "https://www.linkedin.com/oauth/v2/authorization"
TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
USERINFO_URL = "https://api.linkedin.com/v2/userinfo"
SCOPES = "openid profile email"
STATE_COOKIE = "linkedin_oauth_state"
STATE_SECONDS = 600
CODE_SECONDS = 60
# Details LinkedIn shares with us; kept on the user to build AI-written profiles later.
PROFILE_FIELDS = ("name", "given_name", "family_name", "picture", "locale")


def linkedin_settings() -> dict[str, str]:
    # Same lookup as the database settings: the project's .env, overridden by real environment variables.
    values = {**dotenv_values(Path(__file__).resolve().parent.parent / ".env"), **os.environ}
    frontend = (values.get("FRONTEND_URL") or "http://127.0.0.1:5173").strip().rstrip("/")
    return {
        "client_id": (values.get("LINKEDIN_CLIENT_ID") or "").strip(),
        "client_secret": (values.get("LINKEDIN_CLIENT_SECRET") or "").strip(),
        "redirect_uri": (values.get("LINKEDIN_REDIRECT_URI") or f"{frontend}/api/auth/linkedin/callback").strip(),
        "frontend_url": frontend,
    }


class LinkedInError(Exception):
    """A sign-in problem the member can be told about, identified by a short code."""

    def __init__(self, code: str):
        self.code = code


def back_to_site(settings: dict, error: str) -> RedirectResponse:
    response = RedirectResponse(f"{settings['frontend_url']}/signup?{urlencode({'error': error})}", status_code=303)
    response.delete_cookie(STATE_COOKIE, path="/")
    response.headers["Cache-Control"] = "no-store"
    return response


async def fetch_linkedin_member(code: str, settings: dict) -> dict:
    """Trade the authorization code for the member's LinkedIn details."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            token = await client.post(TOKEN_URL, data={
                "grant_type": "authorization_code", "code": code,
                "redirect_uri": settings["redirect_uri"],
                "client_id": settings["client_id"], "client_secret": settings["client_secret"],
            })
            token.raise_for_status()
            member = await client.get(
                USERINFO_URL, headers={"Authorization": f"Bearer {token.json()['access_token']}"},
            )
            member.raise_for_status()
            return member.json()
    except (httpx.HTTPError, KeyError, ValueError):
        # Never include LinkedIn's response: it may echo our client secret or the code.
        raise LinkedInError("linkedin_failed") from None


async def find_or_create_user(database, member: dict) -> tuple[dict, bool]:
    """Return (user, is_new) for this LinkedIn member, creating the account on first sign-in."""
    subject, email = member.get("sub"), member.get("email")
    if not isinstance(subject, str) or not subject or not isinstance(email, str) or not email.strip():
        raise LinkedInError("missing_email")
    email = email.strip().casefold()
    details = {
        "linkedin": {
            **{field: member[field] for field in PROFILE_FIELDS if field in member},
            "email_verified": member.get("email_verified") is True,
            "updated_at": datetime.now(timezone.utc),
        },
    }

    user = await database.users.find_one({"linkedin_sub": subject})
    if user is None and details["linkedin"]["email_verified"]:
        # Link a member who already has an account under the same verified email address.
        user = await database.users.find_one({"email": email})
        if user is not None:
            details["linkedin_sub"] = subject
    if user is not None:
        if not user.get("is_active", False):
            raise LinkedInError("account_disabled")
        await database.users.update_one({"_id": user["_id"]}, {"$set": details})
        return user, False

    if not details["linkedin"]["email_verified"]:
        raise LinkedInError("email_unverified")
    name = str(member.get("name") or "").strip() or email.split("@")[0]
    user = {
        "_id": str(uuid4()), "name": name, "email": email, "linkedin_sub": subject,
        "is_active": True, "created_at": datetime.now(timezone.utc), **details,
    }
    try:
        await database.users.insert_one(user)
    except DuplicateKeyError:
        # A concurrent first sign-in, or the same subject already registered.
        raise LinkedInError("linkedin_failed") from None
    return user, True


@router.get("/start", status_code=303, response_class=RedirectResponse)
async def start(request: Request, database=Depends(get_database)) -> RedirectResponse:
    """Send the browser to LinkedIn's consent screen."""
    settings = linkedin_settings()
    if not settings["client_id"] or not settings["client_secret"]:
        return back_to_site(settings, "not_configured")
    try:
        await limit_attempts(request, database, "linkedin_start", limit=20, seconds=900)
    except HTTPException:
        return back_to_site(settings, "too_many_attempts")

    state = secrets.token_urlsafe(32)
    await database.oauth_states.insert_one({
        "_id": token_digest(state),
        "expires_at": datetime.now(timezone.utc) + timedelta(seconds=STATE_SECONDS),
    })
    query = urlencode({
        "response_type": "code", "client_id": settings["client_id"],
        "redirect_uri": settings["redirect_uri"], "state": state, "scope": SCOPES,
    })
    response = RedirectResponse(f"{AUTHORIZE_URL}?{query}", status_code=303)
    # The cookie ties the callback to this browser, so a forged link cannot sign someone into our account.
    response.set_cookie(
        STATE_COOKIE, state, max_age=STATE_SECONDS, httponly=True, samesite="lax",
        secure=settings["redirect_uri"].startswith("https://"), path="/",
    )
    response.headers["Cache-Control"] = "no-store"
    return response


@router.get("/callback", status_code=303, response_class=RedirectResponse)
async def callback(
    request: Request, code: str | None = None, state: str | None = None, error: str | None = None,
    database=Depends(get_database),
) -> RedirectResponse:
    """LinkedIn sends the member back here after they approve (or decline)."""
    settings = linkedin_settings()
    try:
        await limit_attempts(request, database, "linkedin_callback", limit=20, seconds=900)
    except HTTPException:
        return back_to_site(settings, "too_many_attempts")

    cookie = request.cookies.get(STATE_COOKIE)
    if not state or not cookie or not secrets.compare_digest(state.encode(), cookie.encode()):
        return back_to_site(settings, "invalid_state")
    # States are single use, and must still be unexpired.
    saved = await database.oauth_states.find_one_and_delete({
        "_id": token_digest(state), "expires_at": {"$gt": datetime.now(timezone.utc)},
    })
    if saved is None:
        return back_to_site(settings, "invalid_state")
    if error:
        return back_to_site(settings, "cancelled" if error == "user_cancelled_login" else "linkedin_failed")
    if not code or not settings["client_id"] or not settings["client_secret"]:
        return back_to_site(settings, "linkedin_failed")

    try:
        member = await fetch_linkedin_member(code, settings)
        user, is_new = await find_or_create_user(database, member)
    except LinkedInError as problem:
        return back_to_site(settings, problem.code)

    login_code = secrets.token_urlsafe(32)
    await database.login_codes.insert_one({
        "_id": token_digest(login_code), "user_id": user["_id"], "is_new": is_new,
        "expires_at": datetime.now(timezone.utc) + timedelta(seconds=CODE_SECONDS),
    })
    response = RedirectResponse(
        f"{settings['frontend_url']}/auth/linkedin?{urlencode({'code': login_code})}", status_code=303,
    )
    response.delete_cookie(STATE_COOKIE, path="/")
    response.headers["Cache-Control"] = "no-store"
    return response


@router.post("/exchange", response_model=LinkedInLoginResponse)
async def exchange(
    data: LinkedInExchangeRequest, request: Request, response: Response, database=Depends(get_database),
) -> LinkedInLoginResponse:
    """Swap the one-time code from the sign-in redirect for a session token."""
    await limit_attempts(request, database, "linkedin_exchange", limit=20, seconds=900)
    login = await database.login_codes.find_one_and_delete({
        "_id": token_digest(data.code), "expires_at": {"$gt": datetime.now(timezone.utc)},
    })
    user = login and await database.users.find_one({"_id": login["user_id"], "is_active": True}, {"_id": 1})
    if login is None or user is None:
        raise HTTPException(status_code=400, detail="This sign-in link expired. Please try again.")
    token = await create_session(database, user["_id"])
    response.headers["Cache-Control"] = "no-store"
    return LinkedInLoginResponse(access_token=token, expires_in=SESSION_SECONDS, is_new=login["is_new"])
