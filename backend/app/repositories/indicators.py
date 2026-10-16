from __future__ import annotations

from datetime import date
from typing import Iterable

from app.db.pool import connection


async def list_indicators() -> dict[str, dict]:
    async with connection() as conn:
        cur = await conn.execute(
            "select code, name, unit, source_name, source_url, is_nse, stale_after_seconds, notes from indicators"
        )
        return {r["code"]: r for r in await cur.fetchall()}


async def fetch_observations(indicator_code: str, series_keys: Iterable[str]) -> list[dict]:
    async with connection() as conn:
        cur = await conn.execute(
            """select series_key, period, period_start, value::float8 as value, basis, as_of, fetched_at
               from observations
               where indicator_code = %s and series_key = any(%s)
               order by period_start asc""",
            (indicator_code, list(series_keys)),
        )
        return await cur.fetchall()


async def upsert_observations(rows: list[dict]) -> int:
    """rows: indicator_code, series_key, period, period_start(date), value(float), basis, as_of(date)."""
    if not rows:
        return 0
    params = [
        (r["indicator_code"], r["series_key"], r["period"], r["period_start"], r["value"], r["basis"], r["as_of"])
        for r in rows
    ]
    async with connection() as conn:
        async with conn.transaction():
            async with conn.cursor() as cur:
                await cur.executemany(
                    """insert into observations
                         (indicator_code, series_key, period, period_start, value, basis, as_of, fetched_at)
                       values (%s, %s, %s, %s, %s, %s, %s, now())
                       on conflict (indicator_code, series_key, period) do update
                       set value = excluded.value, basis = excluded.basis, as_of = excluded.as_of,
                           period_start = excluded.period_start, fetched_at = now()""",
                    params,
                )
    return len(params)


def year_start(year: int) -> date:
    return date(year, 1, 1)
