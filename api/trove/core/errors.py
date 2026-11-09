"""Error responses that never leak private details."""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pymongo.errors import PyMongoError


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(PyMongoError)
    async def database_error(request: Request, error: PyMongoError) -> JSONResponse:
        return JSONResponse(
            status_code=503, content={"detail": "Something's wrong on our side. Nothing you said is lost."}
        )

    @app.exception_handler(RequestValidationError)
    async def validation_error(request: Request, error: RequestValidationError) -> JSONResponse:
        # Never echo submitted values (passwords, answers) back in validation errors.
        details = [{key: item[key] for key in ("type", "loc", "msg")} for item in error.errors()]
        return JSONResponse(status_code=422, content={"detail": details})
