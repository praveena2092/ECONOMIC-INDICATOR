"""In-process APScheduler wiring. Runs inside the API process (single worker)."""
from __future__ import annotations

import asyncio
import logging
from typing import Awaitable, Callable

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.collectors.curated import CuratedCollector
# from app.collectors.imf import ImfCollector
from app.collectors.fred import FredCollector
from app.collectors.ticker import TickerCollector
from app.collectors.worldbank import WorldBankCollector
from app.core.config import Settings

log = logging.getLogger(__name__)


class CollectorScheduler:
    def __init__(self, settings: Settings, on_ticker_update: Callable[[], Awaitable[None]]):
        self.settings = settings
        self.ticker = TickerCollector(settings, on_update=on_ticker_update)
        self.macro = [WorldBankCollector(settings), FredCollector(settings), CuratedCollector(settings)]
        self.scheduler = AsyncIOScheduler(timezone="UTC")
        self._bootstrap: asyncio.Task | None = None

    async def _run_macro(self) -> None:
        for collector in self.macro:
            await collector.run()

    def start(self) -> None:
        job = dict(max_instances=1, coalesce=True, misfire_grace_time=30)
        # Wake every 15s; TickerCollector decides if it is due (market hours vs off hours).
        self.scheduler.add_job(self.ticker.run_if_due, "interval", seconds=15, id="ticker", **job)
        self.scheduler.add_job(self._run_macro, "interval", hours=self.settings.macro_refresh_hours, id="macro", **job)
        self.scheduler.start()
        # Warm the database in the background so startup is never blocked by upstreams.
        self._bootstrap = asyncio.create_task(self._initial_load())
        log.info("Collector scheduler started")

    async def _initial_load(self) -> None:
        await self._run_macro()
        await self.ticker.run_if_due()

    async def stop(self) -> None:
        self.scheduler.shutdown(wait=False)
        if self._bootstrap:
            self._bootstrap.cancel()
        for c in [self.ticker, *self.macro]:
            await c.aclose()
