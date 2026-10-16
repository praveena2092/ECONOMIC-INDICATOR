"""IMF WEO general government gross debt (% of GDP), via FRED's public CSV download."""
from __future__ import annotations

import asyncio
import csv
import io
from datetime import date
from pathlib import Path

import httpx

from app.collectors.base import BaseCollector, is_valid_number
from app.core.errors import CollectorError
from app.repositories import indicators as repo

URL = "https://fred.stlouisfed.org/graph/fredgraph.csv"
SERIES = {"IND": "GGGDTAINA188N", "USA": "GGGDTAUSA188N"}
DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "curated"

# FRED stalls requests that send a browser-style or custom User-Agent, so use curl's.
FRED_HEADERS = {"User-Agent": "curl/8.4.0", "Accept": "*/*"}


def parse_fred_csv(text: str, series_key: str, max_year: int) -> list[dict]:
    reader = csv.reader(io.StringIO(text))
    header = next(reader, None)
    if not header or len(header) < 2:
        raise CollectorError("FRED: unexpected CSV format")
    rows = []
    for rec in reader:
        if len(rec) < 2:
            continue
        try:
            d = date.fromisoformat(rec[0].strip())
            value = float(rec[1])
        except ValueError:
            continue  # "." marks a missing observation
        if d.year > max_year or not is_valid_number(value):
            continue
        rows.append({
            "indicator_code": "debt_gdp", "series_key": series_key, "period": str(d.year),
            "period_start": date(d.year, 1, 1), "value": value, "basis": "actual",
            "as_of": date(d.year, 12, 31),
        })
    return rows


class FredCollector(BaseCollector):
    name = "fred"

    async def collect(self) -> tuple[int, str | None]:
        total, errors = 0, []
        max_year = date.today().year - 1

        for key, series_id in SERIES.items():
            last_error = None
            for attempt in range(3):
                try:
                    resp = await self.client.get(
                        URL, params={"id": series_id},
                        headers=FRED_HEADERS,
                        timeout=httpx.Timeout(20.0, connect=10.0),
                    )
                    resp.raise_for_status()
                    total += await repo.upsert_observations(parse_fred_csv(resp.text, key, max_year))
                    last_error = None
                    break
                except (httpx.HTTPError, CollectorError) as exc:
                    # the type name matters: httpx timeouts have an empty message
                    last_error = f"{type(exc).__name__}: {exc}"
                    await asyncio.sleep(2 * (attempt + 1))

            if last_error:
                # Backup: a CSV saved earlier (backend/data/curated/fred_ind.csv, fred_usa.csv)
                local = DATA_DIR / f"fred_{key.lower()}.csv"
                if local.exists():
                    rows = parse_fred_csv(local.read_text(encoding="utf-8"), key, max_year)
                    total += await repo.upsert_observations(rows)
                    errors.append(f"{key}: live fetch failed ({last_error}); loaded {local.name}")
                else:
                    errors.append(f"{key}: {last_error}")

        if total == 0:
            raise CollectorError("; ".join(errors) or "FRED: no observations returned")
        return total, ("; ".join(errors) if errors else None)