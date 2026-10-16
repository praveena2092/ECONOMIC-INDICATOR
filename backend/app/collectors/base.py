"""Collector base class, shared HTTP helper with timeout/retry, and run bookkeeping."""
from __future__ import annotations

import asyncio
import logging
import math
from abc import ABC, abstractmethod
from datetime import datetime, timezone

import httpx

from app.core.config import Settings
from app.core.errors import CollectorError
from app.repositories import runs

log = logging.getLogger(__name__)

BROWSER_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0 Safari/537.36"
)


def is_valid_number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


async def get_json(client: httpx.AsyncClient, url: str, settings: Settings, **kwargs):
    """GET with timeout (client-level), bounded retries and JSON validation."""
    last: Exception | None = None
    for attempt in range(settings.http_max_retries + 1):
        try:
            resp = await client.get(url, **kwargs)
            if resp.status_code in (429, 500, 502, 503, 504):
                raise CollectorError(f"upstream returned HTTP {resp.status_code}")
            resp.raise_for_status()
            return resp.json()
        except (httpx.HTTPError, ValueError, CollectorError) as exc:
            last = exc
            if attempt < settings.http_max_retries:
                await asyncio.sleep(min(2 ** attempt, 8))
    raise CollectorError(f"GET {url.split('?')[0]} failed: {last}") from last


class BaseCollector(ABC):
    name: str

    def __init__(self, settings: Settings):
        self.settings = settings
        self._client: httpx.AsyncClient | None = None

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.settings.http_timeout_seconds),
                headers={"User-Agent": BROWSER_UA, "Accept": "application/json, text/plain, */*"},
                follow_redirects=True,
            )
        return self._client

    async def aclose(self) -> None:
        if self._client is not None:
            await self._client.aclose()

    @abstractmethod
    async def collect(self) -> tuple[int, str | None]:
        """Fetch, validate and persist. Returns (rows_written, partial_error_message)."""

    async def run(self) -> None:
        """Run once. Never raises: failures are logged and recorded, last valid data stays untouched."""
        started = datetime.now(timezone.utc)
        try:
            rows, partial = await self.collect()
            status = "partial" if partial else "success"
            await self._record(status, rows, partial, started)
            log.info("collector=%s status=%s rows=%s", self.name, status, rows)
        except Exception as exc:  # noqa: BLE001 - boundary: scheduler must survive any failure
            log.warning("collector=%s failed: %s", self.name, exc)
            await self._record("failed", 0, str(exc), started)

    async def _record(self, status: str, rows: int, error: str | None, started: datetime) -> None:
        try:
            await runs.record_run(self.name, status, rows, error, started)
        except Exception:  # noqa: BLE001
            log.exception("could not record collector run for %s", self.name)
