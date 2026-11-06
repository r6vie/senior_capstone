"""The FastAPI app. Adding a feature = include its router here and list its ensure_indexes."""

from fastapi import FastAPI, Request

from trove.auth import service as auth_service
from trove.auth.router import router as auth_router
from trove.books import service as books_service
from trove.books.router import router as books_router
from trove.core.database import make_lifespan
from trove.core.errors import register_error_handlers
from trove.notifications import service as notification_service
from trove.notifications.router import router as notifications_router

INDEX_SETUPS = [
    auth_service.ensure_indexes,
    notification_service.ensure_indexes,
    books_service.ensure_indexes,
]
ROUTERS = [auth_router, notifications_router, books_router]

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
