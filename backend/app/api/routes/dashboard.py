import asyncio
import json

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from app.api.deps import current_user
from app.core.config import Settings, get_settings
from app.schemas.dashboard import DashboardResponse, ErrorResponse, Ticker
from app.services.dashboard import DashboardService
from app.services.events import bus

AUTH_ERRORS = {401: {"model": ErrorResponse, "description": "Missing, invalid or expired token"}}
router = APIRouter(tags=["dashboard"], dependencies=[Depends(current_user)], responses=AUTH_ERRORS)


@router.get("/dashboard", response_model=DashboardResponse, summary="Full dashboard payload")
async def dashboard(settings: Settings = Depends(get_settings)):
    """Complete dashboard payload: ticker + six indicator panels (see docs/API.md)."""
    return await DashboardService(settings).build()


@router.get("/ticker", response_model=Ticker, summary="Market ticker only")
async def ticker(settings: Settings = Depends(get_settings)):
    return await DashboardService(settings).ticker()


@router.get("/stream/ticker", summary="Live ticker (Server-Sent Events)",
            response_class=StreamingResponse)
async def stream_ticker(request: Request, settings: Settings = Depends(get_settings)):
    """Server-Sent Events stream (`text/event-stream`).

    Sends `event: ticker` with the full ticker JSON on connect and whenever new quotes are stored,
    plus a `: keep-alive` comment every 20 s. Swagger UI cannot display streams - use curl:
    `curl -N -H "Authorization: Bearer <token>" <base>/api/v1/stream/ticker`."""
    service = DashboardService(settings)

    async def events():
        with bus.subscribe() as queue:
            yield f"event: ticker\ndata: {json.dumps(await service.ticker())}\n\n"
            while not await request.is_disconnected():
                try:
                    await asyncio.wait_for(queue.get(), timeout=20)
                    yield f"event: ticker\ndata: {json.dumps(await service.ticker())}\n\n"
                except asyncio.TimeoutError:
                    yield ": keep-alive\n\n"

    return StreamingResponse(
        events(), media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )