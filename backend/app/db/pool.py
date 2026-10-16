"""Async Postgres pool (psycopg3). All SQL elsewhere uses bound parameters only."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from psycopg import AsyncConnection
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from app.core.config import Settings

log = logging.getLogger(__name__)
_pool: AsyncConnectionPool | None = None


async def open_pool(settings: Settings) -> AsyncConnectionPool:
    global _pool
    _pool = AsyncConnectionPool(
        conninfo=settings.database_url,
        min_size=settings.db_pool_min,
        max_size=settings.db_pool_max,
        # prepare_threshold=None keeps us compatible with Supabase's transaction pooler (pgbouncer).
        kwargs={"row_factory": dict_row, "prepare_threshold": None},
        timeout=10,
        open=False,
    )
    await _pool.open(wait=False)
    log.info("Database pool opened (min=%s max=%s)", settings.db_pool_min, settings.db_pool_max)
    return _pool


async def close_pool() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


def get_pool() -> AsyncConnectionPool:
    if _pool is None:
        raise RuntimeError("Database pool is not initialised")
    return _pool


@asynccontextmanager
async def connection() -> AsyncIterator[AsyncConnection]:
    async with get_pool().connection() as conn:
        yield conn
