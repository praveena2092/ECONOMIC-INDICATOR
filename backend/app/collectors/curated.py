"""Curated CSV loader for indicators that have no public API (GST collections, Union Budget).

Rows are validated strictly; invalid rows are rejected (and reported) instead of being coerced.
"""
from __future__ import annotations

import csv
import logging
from datetime import date
from pathlib import Path

from app.collectors.base import BaseCollector, is_valid_number
from app.core.errors import CollectorError
from app.repositories import indicators as repo

log = logging.getLogger(__name__)
DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "curated"
FILES = {"gst_collections.csv": {"gst_collections"}, "union_budget_expenditure.csv": {"gov_expenditure"}}
BASES = {"actual", "estimate", "revised_estimate"}


def parse_period_start(period: str) -> date:
    """'2024-25' -> 2024-04-01 (Indian FY); '2024' -> 2024-01-01."""
    if len(period) == 7 and period[4] == "-" and period[:4].isdigit() and period[5:].isdigit():
        start = int(period[:4])
        if (start + 1) % 100 != int(period[5:]):
            raise ValueError("fiscal-year period must look like 2024-25")
        return date(start, 4, 1)
    if len(period) == 4 and period.isdigit():
        return date(int(period), 1, 1)
    raise ValueError("period must be YYYY or YYYY-YY")


def parse_curated_csv(path: Path, allowed_codes: set[str]) -> tuple[list[dict], list[str]]:
    rows, errors = [], []
    with path.open(newline="", encoding="utf-8") as fh:
        for n, rec in enumerate(csv.DictReader(fh), start=2):
            try:
                code = rec["indicator_code"].strip()
                if code not in allowed_codes:
                    raise ValueError(f"unexpected indicator_code '{code}'")
                value = float(rec["value"])
                if not is_valid_number(value):
                    raise ValueError("value is not finite")
                basis = rec["basis"].strip()
                if basis not in BASES:
                    raise ValueError(f"basis must be one of {sorted(BASES)}")
                period = rec["period"].strip()
                rows.append({
                    "indicator_code": code, "series_key": rec["series_key"].strip().upper(),
                    "period": period, "period_start": parse_period_start(period), "value": value,
                    "basis": basis, "as_of": date.fromisoformat(rec["as_of"].strip()),
                })
            except (KeyError, ValueError, AttributeError) as exc:
                errors.append(f"{path.name}:{n}: {exc}")
    return rows, errors


class CuratedCollector(BaseCollector):
    name = "curated"

    async def collect(self) -> tuple[int, str | None]:
        all_rows, all_errors = [], []
        for filename, codes in FILES.items():
            path = DATA_DIR / filename
            if not path.exists():
                all_errors.append(f"{filename}: file missing")
                continue
            rows, errors = parse_curated_csv(path, codes)
            all_rows += rows
            all_errors += errors
        if not all_rows:
            raise CollectorError("; ".join(all_errors) or "no curated rows found")
        written = await repo.upsert_observations(all_rows)
        return written, ("; ".join(all_errors) if all_errors else None)
