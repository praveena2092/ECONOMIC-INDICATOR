import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app import __version__
from app.db.pool import connection
from app.repositories import runs

log = logging.getLogger(__name__)
router = APIRouter(tags=["health"])


@router.get("/health")
async def health():
    """Liveness: the process is up. No dependencies are touched."""
    return {"status": "ok", "version": __version__}


@router.get("/health/ready")
async def ready():
    """Readiness: database reachable; also reports the latest result of every collector."""
    try:
        async with connection() as conn:
            await conn.execute("select 1")
        collectors = [
            {"collector": r["collector"], "status": r["status"],
             "finished_at": r["finished_at"].isoformat() if r["finished_at"] else None}
            for r in await runs.latest_runs()
        ]
    except Exception:  # noqa: BLE001
        log.exception("readiness check failed")
        return JSONResponse(status_code=503, content={"status": "unavailable", "database": "down"})
    return {"status": "ok", "database": "up", "collectors": collectors}
