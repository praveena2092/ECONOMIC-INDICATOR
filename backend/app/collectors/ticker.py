"""Live market ticker collector.

* NIFTY BANK / NIFTY IT  -> NSE India public endpoint `/api/allIndices` (requires a cookie-priming request).
* SENSEX                 -> BSE index, not published by NSE; fetched from Yahoo Finance's public chart endpoint
                            and labelled as a non-NSE source in the UI.
"""
from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Awaitable, Callable
from zoneinfo import ZoneInfo

import httpx

from app.collectors.base import BaseCollector, get_json, is_valid_number
from app.core.errors import CollectorError
from app.repositories import ticker as repo

log = logging.getLogger(__name__)
IST = ZoneInfo("Asia/Kolkata")

NSE_SYMBOLS = {"NIFTY BANK": ("NIFTY BANK", 1), "NIFTY IT": ("NIFTY IT", 2)}
NSE_PAGE = "https://www.nseindia.com/market-data/live-market-indices"


def in_market_hours(now: datetime | None = None) -> bool:
    now = (now or datetime.now(timezone.utc)).astimezone(IST)
    return now.weekday() < 5 and (9, 0) <= (now.hour, now.minute) < (16, 0)


def _nse_timestamp(raw) -> datetime:
    if isinstance(raw, str):
        for fmt in ("%d-%b-%Y %H:%M:%S", "%d-%b-%Y %H:%M", "%d-%b-%Y"):
            try:
                return datetime.strptime(raw.strip(), fmt).replace(tzinfo=IST).astimezone(timezone.utc)
            except ValueError:
                continue
    return datetime.now(timezone.utc)  # documented fallback: fetch time


def parse_nse_all_indices(payload) -> list[dict]:
    if not (isinstance(payload, dict) and isinstance(payload.get("data"), list)):
        raise CollectorError("NSE: unexpected allIndices response shape")
    as_of = _nse_timestamp(payload.get("timestamp"))
    out = []
    for item in payload["data"]:
        name = item.get("index") or item.get("indexSymbol")
        if name not in NSE_SYMBOLS:
            continue
        last, change, pct = item.get("last"), item.get("variation"), item.get("percentChange")
        if not all(is_valid_number(v) for v in (last, change, pct)) or last <= 0:
            log.warning("NSE: invalid numbers for %s, skipped", name)
            continue
        label, order = NSE_SYMBOLS[name]
        out.append({
            "symbol": name, "label": label, "last_price": float(last), "change": float(change),
            "pct_change": float(pct), "source_name": "NSE India", "source_url": NSE_PAGE,
            "is_nse": True, "as_of": as_of, "sort_order": order,
        })
    return out


def parse_yahoo_sensex(payload) -> dict:
    try:
        meta = payload["chart"]["result"][0]["meta"]
        price = meta["regularMarketPrice"]
        prev = meta.get("chartPreviousClose", meta.get("previousClose"))
        ts = meta.get("regularMarketTime")
    except (KeyError, IndexError, TypeError) as exc:
        raise CollectorError("Yahoo: unexpected chart response shape") from exc
    if not (is_valid_number(price) and is_valid_number(prev)) or price <= 0 or prev <= 0:
        raise CollectorError("Yahoo: invalid SENSEX numbers")
    change = price - prev
    as_of = datetime.fromtimestamp(ts, tz=timezone.utc) if is_valid_number(ts) else datetime.now(timezone.utc)
    return {
        "symbol": "SENSEX", "label": "SENSEX", "last_price": float(price), "change": round(change, 4),
        "pct_change": round(change / prev * 100, 4), "source_name": "BSE via Yahoo Finance",
        "source_url": "https://finance.yahoo.com/quote/%5EBSESN", "is_nse": False, "as_of": as_of, "sort_order": 0,
    }


class TickerCollector(BaseCollector):
    name = "ticker"

    def __init__(self, settings, on_update: Callable[[], Awaitable[None]] | None = None):
        super().__init__(settings)
        self._on_update = on_update
        self._last_run = 0.0
        self._nse_primed = False

    # -- scheduling ------------------------------------------------------------------------------
    def due(self) -> bool:
        interval = (self.settings.nse_refresh_seconds if in_market_hours()
                    else self.settings.nse_off_hours_refresh_seconds)
        return time.monotonic() - self._last_run >= interval

    async def run_if_due(self) -> None:
        if self.due():
            self._last_run = time.monotonic()
            await self.run()

    # -- collection ------------------------------------------------------------------------------
    async def _prime_nse(self) -> None:
        await self.client.get(self.settings.nse_base_url, headers={"Accept": "text/html"})
        self._nse_primed = True

    async def _fetch_nse(self) -> list[dict]:
        url = f"{self.settings.nse_base_url}/api/allIndices"
        headers = {"Referer": NSE_PAGE, "Accept-Language": "en-US,en;q=0.9"}
        for attempt in (1, 2):
            try:
                if not self._nse_primed:
                    await self._prime_nse()
                resp = await self.client.get(url, headers=headers)
                if resp.status_code in (401, 403):
                    raise CollectorError(f"NSE rejected request (HTTP {resp.status_code})")
                resp.raise_for_status()
                return parse_nse_all_indices(resp.json())
            except (httpx.HTTPError, ValueError, CollectorError) as exc:
                self._nse_primed = False  # force a fresh cookie next time
                if attempt == 2:
                    raise CollectorError(f"NSE fetch failed: {exc}") from exc
        return []

    async def _fetch_sensex(self) -> dict:
        url = f"{self.settings.yahoo_chart_url}/%5EBSESN"
        payload = await get_json(self.client, url, self.settings, params={"interval": "1d", "range": "1d"})
        return parse_yahoo_sensex(payload)

    async def collect(self) -> tuple[int, str | None]:
        quotes, errors = [], []
        try:
            quotes += await self._fetch_nse()
        except CollectorError as exc:
            errors.append(str(exc))
        try:
            quotes.append(await self._fetch_sensex())
        except CollectorError as exc:
            errors.append(str(exc))
        if not quotes:
            raise CollectorError("; ".join(errors) or "no ticker data")
        written = await repo.upsert_quotes(quotes)
        if self._on_update:
            await self._on_update()
        return written, ("; ".join(errors) if errors else None)
