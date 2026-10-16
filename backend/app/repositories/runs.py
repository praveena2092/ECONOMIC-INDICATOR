from __future__ import annotations

from app.db.pool import connection


async def record_run(collector: str, status: str, rows: int, error: str | None, started_at) -> None:
    async with connection() as conn:
        await conn.execute(
            """insert into collector_runs (collector, status, started_at, finished_at, rows_written, error)
               values (%s, %s, %s, now(), %s, %s)""",
            (collector, status, started_at, rows, (error or None) and error[:1000]),
        )


async def latest_runs() -> list[dict]:
    async with connection() as conn:
        cur = await conn.execute(
            """select distinct on (collector) collector, status, finished_at, rows_written, error
               from collector_runs order by collector, started_at desc"""
        )
        return await cur.fetchall()
