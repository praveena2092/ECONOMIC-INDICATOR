"""Domain errors and the single JSON error envelope returned by the API.

Envelope: {"error": {"code": str, "message": str, "request_id": str | null}}
"""
from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

log = logging.getLogger(__name__)


class AppError(Exception):
    status_code = 500
    code = "internal_error"

    def __init__(self, message: str = "Unexpected error", *, headers: dict[str, str] | None = None):
        super().__init__(message)
        self.message = message
        self.headers = headers


class AuthenticationError(AppError):
    status_code = 401
    code = "unauthenticated"


class PermissionDenied(AppError):
    status_code = 403
    code = "forbidden"


class RateLimited(AppError):
    status_code = 429
    code = "rate_limited"


class ServiceUnavailable(AppError):
    status_code = 503
    code = "service_unavailable"


class CollectorError(Exception):
    """Raised by collectors when upstream data is unreachable or fails validation."""


def _envelope(request: Request, code: str, message: str, status: int, headers=None) -> JSONResponse:
    rid = getattr(request.state, "request_id", None)
    return JSONResponse(
        status_code=status,
        content={"error": {"code": code, "message": message, "request_id": rid}},
        headers=headers,
    )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(request: Request, exc: AppError):
        return _envelope(request, exc.code, exc.message, exc.status_code, exc.headers)

    @app.exception_handler(StarletteHTTPException)
    async def _http_error(request: Request, exc: StarletteHTTPException):
        return _envelope(request, f"http_{exc.status_code}", str(exc.detail), exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def _validation_error(request: Request, exc: RequestValidationError):
        first = exc.errors()[0] if exc.errors() else {}
        loc = ".".join(str(p) for p in first.get("loc", []) if p != "body")
        return _envelope(request, "validation_error", f"Invalid request: {loc or 'body'} - {first.get('msg', 'invalid')}", 422)

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception):
        log.exception("Unhandled error on %s %s", request.method, request.url.path)
        return _envelope(request, "internal_error", "Something went wrong. Please try again.", 500)
