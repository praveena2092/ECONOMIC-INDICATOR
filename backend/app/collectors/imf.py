"""IMF DataMapper collector: general government gross debt (% of GDP) for India and the US."""
from __future__ import annotations

from datetime import date

from app.collectors.base import BaseCollector, get_json, is_valid_number
from app.core.errors import CollectorError
from app.repositories import indicators as repo

INDICATOR = "GG_DEBT_GDP"
COUNTRIES = ["IND", "USA"]


def parse_imf(payload, max_year: int) -> list[dict]:
    try:
        values = payload["values"][INDICATOR]
    except (KeyError, TypeError) as exc:
        raise CollectorError("IMF: unexpected response shape") from exc
    rows = []
    for country in COUNTRIES:
        series = values.get(country) or {}
        for year, value in series.items():
            if not (isinstance(year, str) and year.isdigit() and len(year) == 4):
                continue
            y = int(year)
            if y > max_year or not is_valid_number(value):
                continue  # projections / gaps are not displayed
            rows.append({
                "indicator_code": "debt_gdp", "series_key": country, "period": year,
                "period_start": date(y, 1, 1), "value": float(value), "basis": "actual",
                "as_of": date(y, 12, 31),
            })
    return rows


class ImfCollector(BaseCollector):
    name = "imf"

    async def collect(self) -> tuple[int, str | None]:
        url = f"{self.settings.imf_base_url}/{INDICATOR}/{'/'.join(COUNTRIES)}"
        payload = await get_json(self.client, url, self.settings)
        rows = parse_imf(payload, max_year=date.today().year - 1)
        if not rows:
            raise CollectorError("IMF: no valid observations returned")
        return await repo.upsert_observations(rows), None
