"""The FastAPI app. Adding a feature = include its router here and list its ensure_indexes."""

from fastapi import FastAPI, Request

from trove.ai.scripted import ensure_scripted_allowed
from trove.auth import service as auth_service
from trove.auth.router import router as auth_router
from trove.books import service as books_service
from trove.books.router import router as books_router
from trove.checkouts import service as checkouts_service
from trove.checkouts.router import router as checkouts_router
from trove.core.config import get_settings
from trove.core.database import make_lifespan
from trove.core.errors import register_error_handlers
from trove.interview import service as interview_service
from trove.interview.router import router as interview_router
from trove.notifications import service as notification_service
from trove.notifications.router import router as notifications_router

INDEX_SETUPS = [
    auth_service.ensure_indexes,
    notification_service.ensure_indexes,
    books_service.ensure_indexes,
    interview_service.ensure_indexes,
    checkouts_service.ensure_indexes,
]
ROUTERS = [auth_router, notifications_router, books_router, interview_router, checkouts_router]

# The app won't start at all with canned AI replies anywhere but on a developer's machine.
ensure_scripted_allowed(get_settings())

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
