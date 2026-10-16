from __future__ import annotations

from app.db.pool import connection


async def upsert_quotes(quotes: list[dict]) -> int:
    if not quotes:
        return 0
    params = [
        (q["symbol"], q["label"], q["last_price"], q["change"], q["pct_change"], q["source_name"],
         q["source_url"], q["is_nse"], q["as_of"], q["sort_order"])
        for q in quotes
    ]
    async with connection() as conn:
        async with conn.transaction():
            async with conn.cursor() as cur:
                await cur.executemany(
                    """insert into ticker_quotes
                         (symbol, label, last_price, change, pct_change, source_name, source_url, is_nse, as_of, sort_order, fetched_at)
                       values (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s, now())
                       on conflict (symbol) do update set
                         label = excluded.label, last_price = excluded.last_price, change = excluded.change,
                         pct_change = excluded.pct_change, source_name = excluded.source_name,
                         source_url = excluded.source_url, is_nse = excluded.is_nse, as_of = excluded.as_of,
                         sort_order = excluded.sort_order, fetched_at = now()""",
                    params,
                )
    return len(params)


async def list_quotes() -> list[dict]:
    async with connection() as conn:
        cur = await conn.execute(
            """select symbol, label, last_price::float8 as last_price, change::float8 as change,
                      pct_change::float8 as pct_change, source_name, source_url, is_nse, as_of, fetched_at
               from ticker_quotes order by sort_order, symbol"""
        )
        return await cur.fetchall()
