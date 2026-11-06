"""The unsubscribe page linked from every email.

GET only shows a button and POST makes the change, so email scanners that open links in
advance can't unsubscribe anyone by accident.
"""

from html import escape
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse
from pymongo.asynchronous.database import AsyncDatabase

from trove.auth.service import set_email_notifications
from trove.core.database import get_database
from trove.notifications.links import user_id_from_unsubscribe_token

router = APIRouter(prefix="/notifications", tags=["Notifications"])


def page(body: str) -> HTMLResponse:
    return HTMLResponse(
        "<!doctype html><meta charset='utf-8'><meta name='viewport' content='width=device-width'>"
        "<title>Trove</title>"
        f"<body style='font-family:system-ui,sans-serif;max-width:28rem;margin:4rem auto;padding:0 1rem'>{body}</body>"
    )


def checked_user_id(token: str) -> str:
    user_id = user_id_from_unsubscribe_token(token)
    if user_id is None:
        raise HTTPException(status_code=400, detail="This unsubscribe link is not valid.")
    return user_id


@router.get("/unsubscribe", response_class=HTMLResponse)
async def unsubscribe_page(token: str = Query(max_length=200)) -> HTMLResponse:
    checked_user_id(token)
    return page(
        "<h2>Stop Trove emails?</h2>"
        f"<form method='post' action='/notifications/unsubscribe?token={escape(quote(token))}'>"
        "<button type='submit'>Unsubscribe</button></form>"
    )


@router.post("/unsubscribe", response_class=HTMLResponse)
async def unsubscribe(
    token: str = Query(max_length=200),
    database: AsyncDatabase = Depends(get_database),
) -> HTMLResponse:
    user_id = checked_user_id(token)
    await set_email_notifications(database, user_id, enabled=False)
    return page("<h2>You're unsubscribed.</h2><p>You won't get these emails from Trove anymore.</p>")
