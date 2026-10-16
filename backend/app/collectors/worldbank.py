"""World Bank API collector: GDP growth, exports, imports, CPI inflation (annual)."""
from __future__ import annotations

import re
from datetime import date

from app.collectors.base import BaseCollector, get_json, is_valid_number
from app.core.errors import CollectorError
from app.repositories import indicators as repo

# (indicator_code, World Bank series id, [(country code, series_key)])
SERIES = [
    ("gdp_growth", "NY.GDP.MKTP.KD.ZG", [("IND", "IND"), ("WLD", "WLD")]),
    ("exports", "NE.EXP.GNFS.CD", [("IND", "IND")]),
    ("imports", "NE.IMP.GNFS.CD", [("IND", "IND")]),
    ("inflation", "FP.CPI.TOTL.ZG", [("IND", "IND")]),
]
_YEAR = re.compile(r"^\d{4}$")


def parse_worldbank(payload, indicator_code: str, series_key: str) -> list[dict]:
    """Validate a World Bank v2 response and return observation rows. Null values are skipped."""
    if not (isinstance(payload, list) and len(payload) == 2):
        raise CollectorError("World Bank: unexpected response shape")
    meta, data = payload
    if data is None:
        if isinstance(meta, dict) and meta.get("message"):
            raise CollectorError(f"World Bank error: {meta['message']}")
        return []
    if not isinstance(data, list):
        raise CollectorError("World Bank: 'data' is not a list")
    rows = []
    for item in data:
        year, value = item.get("date"), item.get("value")
        if not (isinstance(year, str) and _YEAR.match(year)) or not is_valid_number(value):
            continue  # missing / malformed -> leave a gap rather than inventing a figure
        y = int(year)
        rows.append({
            "indicator_code": indicator_code, "series_key": series_key, "period": year,
            "period_start": date(y, 1, 1), "value": float(value), "basis": "actual",
            "as_of": date(y, 12, 31),
        })
    return rows


class WorldBankCollector(BaseCollector):
    name = "worldbank"

    async def collect(self) -> tuple[int, str | None]:
        base = self.settings.worldbank_base_url
        this_year = date.today().year
        total, errors = 0, []
        for code, wb_id, countries in SERIES:
            for country, key in countries:
                url = f"{base}/country/{country}/indicator/{wb_id}"
                try:
                    payload = await get_json(
                        self.client, url, self.settings,
                        params={"format": "json", "per_page": 100, "date": f"2012:{this_year}"},
                    )
                    total += await repo.upsert_observations(parse_worldbank(payload, code, key))
                except Exception as exc:  # noqa: BLE001 - keep other series flowing
                    errors.append(f"{code}/{key}: {exc}")
        if errors and total == 0:
            raise CollectorError("; ".join(errors))
        return total, ("; ".join(errors) if errors else None)
