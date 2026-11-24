"""The FastAPI app. Adding a feature = include its router here and list its ensure_indexes."""

import logging

from fastapi import FastAPI, Request

from trove.ai.client import describe_ai
from trove.ai.scripted import ensure_scripted_allowed
from trove.auth import service as auth_service
from trove.auth.router import router as auth_router
from trove.auth.verify_router import router as verify_router
from trove.books import service as books_service
from trove.books.router import router as books_router
from trove.checkouts import service as checkouts_service
from trove.checkouts.router import router as checkouts_router
from trove.core.config import get_settings
from trove.core.database import make_lifespan
from trove.core.errors import register_error_handlers
from trove.discovery import service as discovery_service
from trove.discovery.router import router as discovery_router
from trove.interview import service as interview_service
from trove.interview.router import router as interview_router
from trove.meetings.router import router as meetings_router
from trove.messaging import service as messaging_service
from trove.messaging.router import router as messaging_router
from trove.notifications import service as notification_service
from trove.notifications.router import router as notifications_router

INDEX_SETUPS = [
    auth_service.ensure_indexes,
    notification_service.ensure_indexes,
    books_service.ensure_indexes,
    interview_service.ensure_indexes,
    checkouts_service.ensure_indexes,
    messaging_service.ensure_indexes,
    discovery_service.ensure_indexes,
]
ROUTERS = [
    auth_router,
    verify_router,
    notifications_router,
    books_router,
    interview_router,
    checkouts_router,
    meetings_router,
    messaging_router,
    discovery_router,
]

# The app won't start at all with canned AI replies anywhere but on a developer's machine.
ensure_scripted_allowed(get_settings())
# Uvicorn's own logger, so the line shows in the terminal beside its startup messages.
logging.getLogger("uvicorn.error").info(describe_ai(get_settings()))

app = FastAPI(title="Trove API", lifespan=make_lifespan(INDEX_SETUPS))
register_error_handlers(app)
for router in ROUTERS:
    app.include_router(router)


@app.middleware("http")
async def private_responses(request: Request, call_next):
    response = await call_next(request)
    # Almost every response is about a signed-in member, so nothing is cached by default.
    if request.url.path not in {"/docs", "/openapi.json", "/redoc"}:
        response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/health", tags=["Health"])
def health(request: Request) -> dict[str, bool]:
    """Is the API up, and is the database connected?"""
    return {"ok": True, "database": bool(request.app.state.database_ready)}
