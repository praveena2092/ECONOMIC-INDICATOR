from __future__ import annotations

import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api.routes import auth, dashboard, health
from app.collectors.scheduler import CollectorScheduler
from app.core.config import get_settings
from app.core.errors import register_exception_handlers
from app.core.logging import configure_logging
from app.db.pool import close_pool, open_pool
from app.services.events import bus
from app.core.loop import ensure_selector_loop

ensure_selector_loop()
log = logging.getLogger(__name__)
DESCRIPTION = """
Backend for the Economic Indicators Dashboard.

**How to try it:** call `POST /api/v1/auth/login`, copy the `access_token`, click **Authorize** (top right)
and paste the token. All `/api/v1/*` endpoints except login need it.

Missing values are returned as `null` (the UI shows `---`); they are never estimated. Every error uses
`{"error": {"code", "message", "request_id"}}`.
"""

TAGS = [
    {"name": "auth", "description": "Sign in and identify the current user."},
    {"name": "dashboard", "description": "Ticker and the six indicator panels."},
    {"name": "health", "description": "Liveness and readiness probes (no authentication)."},
]

@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level)
    await open_pool(settings)
    scheduler = None
    if settings.collectors_enabled:
        scheduler = CollectorScheduler(settings, on_ticker_update=bus.publish)
        scheduler.start()
    try:
        yield
    finally:
        if scheduler:
            await scheduler.stop()
        await close_pool()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Economic Indicators Dashboard API", version=__version__,description=DESCRIPTION, openapi_tags=TAGS,lifespan=lifespan,
        docs_url="/docs" if settings.enable_api_docs else None,
        redoc_url=None, openapi_url="/openapi.json" if settings.enable_api_docs else None,
    )
    app.add_middleware(
        CORSMiddleware, allow_origins=settings.cors_origin_list, allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"], allow_headers=["Authorization", "Content-Type"],
        max_age=600,
    )

    @app.middleware("http")
    async def request_context(request: Request, call_next):
        request.state.request_id = request.headers.get("x-request-id") or uuid.uuid4().hex[:12]
        response = await call_next(request)
        response.headers["X-Request-ID"] = request.state.request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Cache-Control"] = response.headers.get("Cache-Control", "no-store")
        return response

    register_exception_handlers(app)
    app.include_router(health.router)
    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(dashboard.router, prefix="/api/v1")
    return app


app = create_app()
