"""Builds the dashboard payload from stored, validated observations.

No figure is ever invented: a missing value is `null` in the payload and rendered as '---' by the UI.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone

from app.core.config import Settings
from app.repositories import indicators as ind_repo
from app.repositories import ticker as ticker_repo

CHART_POINTS = 5
_FY = re.compile(r"^\d{4}-(\d{2})$")


# ---------------------------------------------------------------------------- pure helpers
def period_label(period: str) -> str:
    m = _FY.match(period)
    return f"FY{m.group(1)}" if m else period


def group(rows: list[dict]) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for r in rows:
        out.setdefault(r["series_key"], []).append(r)
    for series in out.values():
        series.sort(key=lambda r: r["period_start"])
    return out


def delta(series: list[dict], mode: str) -> float | None:
    """Change of the latest point vs the previous one. mode 'pp' = difference, 'pct' = % change."""
    if len(series) < 2:
        return None
    last, prev = series[-1]["value"], series[-2]["value"]
    if mode == "pp":
        return round(last - prev, 2)
    return None if prev == 0 else round((last - prev) / abs(prev) * 100, 2)


def axis(*series_lists: list[dict], n: int = CHART_POINTS) -> list[dict]:
    seen: dict[str, object] = {}
    for s in series_lists:
        for r in s:
            seen[r["period"]] = r["period_start"]
    ordered = sorted(seen.items(), key=lambda kv: kv[1])[-n:]
    return [{"period": p, "label": period_label(p)} for p, _ in ordered]


def values_on(series: list[dict], ax: list[dict], scale: float = 1.0, nd: int = 2) -> list[float | None]:
    by_period = {r["period"]: r["value"] for r in series}
    return [round(by_period[a["period"]] * scale, nd) if a["period"] in by_period else None for a in ax]


def _latest_val(series: list[dict], scale: float = 1.0, nd: int = 2) -> float | None:
    return round(series[-1]["value"] * scale, nd) if series else None


def _status(rows: list[dict], stale_after: int) -> str:
    if not rows:
        return "unavailable"
    newest = max(r["fetched_at"] for r in rows)
    age = (datetime.now(timezone.utc) - newest).total_seconds()
    return "stale" if age > stale_after else "ok"


def _card(cid: str, label: str, series: list[dict], unit: str, mode: str, scale: float = 1.0,
          nd: int = 2, **extra) -> dict:
    latest = series[-1] if series else None
    return {
        "id": cid, "label": label, "value": _latest_val(series, scale, nd), "unit": unit,
        "delta": delta(series, mode) if series else None,
        "delta_unit": "pp" if mode == "pp" else "%",
        "period": period_label(latest["period"]) if latest else None,
        "basis": latest["basis"] if latest else None, **extra,
    }


# ---------------------------------------------------------------------------- service
class DashboardService:
    def __init__(self, settings: Settings):
        self.settings = settings

    async def _load(self, code: str, keys: list[str]) -> list[dict]:
        return await ind_repo.fetch_observations(code, keys)

    def _panel(self, key: str, title: str, subtitle: str | None, codes: list[str], meta: dict,
               all_rows: list[dict], cards: list[dict], chart: dict, notes: list[str] | None = None) -> dict:
        stale_after = min((meta[c]["stale_after_seconds"] for c in codes if c in meta), default=259200)
        as_of = max((r["as_of"] for r in all_rows), default=None)
        fetched = max((r["fetched_at"] for r in all_rows), default=None)
        seen, sources = set(), []
        for c in codes:
            m = meta.get(c)
            if m and m["source_name"] not in seen:
                seen.add(m["source_name"])
                sources.append({"name": m["source_name"], "url": m["source_url"], "is_nse": m["is_nse"]})
        return {
            "key": key, "title": title, "subtitle": subtitle,
            "status": _status(all_rows, stale_after),
            "as_of": as_of.isoformat() if as_of else None,
            "fetched_at": fetched.isoformat() if fetched else None,
            "sources": sources, "cards": cards, "chart": chart, "notes": notes or [],
        }

    async def ticker(self) -> dict:
        quotes = await ticker_repo.list_quotes()
        meta = await ind_repo.list_indicators()
        stale_after = meta.get("ticker", {}).get("stale_after_seconds", 900)
        if not quotes:
            return {"status": "unavailable", "as_of": None, "fetched_at": None, "items": [], "sources": []}
        newest = max(q["fetched_at"] for q in quotes)
        age = (datetime.now(timezone.utc) - newest).total_seconds()
        sources = {q["source_name"]: {"name": q["source_name"], "url": q["source_url"], "is_nse": q["is_nse"]}
                   for q in quotes}
        return {
            "status": "stale" if age > stale_after else "ok",
            "as_of": max(q["as_of"] for q in quotes).isoformat(),
            "fetched_at": newest.isoformat(),
            "items": [{"symbol": q["symbol"], "label": q["label"], "last": q["last_price"],
                       "change": q["change"], "pct_change": q["pct_change"], "is_nse": q["is_nse"]} for q in quotes],
            "sources": list(sources.values()),
        }

    async def build(self) -> dict:
        meta = await ind_repo.list_indicators()
        gdp = group(await self._load("gdp_growth", ["IND", "WLD"]))
        debt = group(await self._load("debt_gdp", ["IND", "USA"]))
        exp = group(await self._load("exports", ["IND"])).get("IND", [])
        imp = group(await self._load("imports", ["IND"])).get("IND", [])
        gst = group(await self._load("gst_collections", ["IND"])).get("IND", [])
        infl = group(await self._load("inflation", ["IND"])).get("IND", [])
        gov = group(await self._load("gov_expenditure", ["TOTAL", "CAPITAL"]))

        panels = []

        # 1. GDP growth ------------------------------------------------------------------------
        g_in, g_wd = gdp.get("IND", []), gdp.get("WLD", [])
        ax = axis(g_in, g_wd)
        panels.append(self._panel(
            "gdp_growth", "GDP Growth - India vs World", "(YOY%)", ["gdp_growth"], meta, g_in + g_wd,
            [_card("india", "India", g_in, "%", "pp"), _card("world", "World", g_wd, "%", "pp")],
            {"type": "bar", "y_unit": "%", "x": [a["label"] for a in ax],
             "series": [{"key": "india", "label": "India", "values": values_on(g_in, ax)},
                        {"key": "world", "label": "World", "values": values_on(g_wd, ax)}]}))

        # 2. Debt to GDP -----------------------------------------------------------------------
        d_in, d_us = debt.get("IND", []), debt.get("USA", [])
        ax = axis(d_in, d_us, n=CHART_POINTS + 3)
        us_card = _card("us", "Ind vs US", d_us, "%", "pp", flag="US")
        panels.append(self._panel(
            "debt_gdp", "Debt to GDP Ratio", "(IND)", ["debt_gdp"], meta, d_in + d_us,
            [_card("india", f"India ({period_label(d_in[-1]['period'])})" if d_in else "India", d_in, "%", "pp", flag="IN"),
             us_card],
            {"type": "area", "y_unit": "%", "x": [a["label"] for a in ax],
             "series": [{"key": "india", "label": "India", "values": values_on(d_in, ax)}]},
            ["The 'Ind vs US' card shows the US ratio; the India-US gap is in the chart tooltip."]))

        # 3. Trade -----------------------------------------------------------------------------
        ax = axis(exp, imp)
        e_vals, i_vals = values_on(exp, ax, 1e-9, 1), values_on(imp, ax, 1e-9, 1)
        bal = [round(e - i, 1) if e is not None and i is not None else None for e, i in zip(e_vals, i_vals)]
        panels.append(self._panel(
            "trade", "Imports, Exports & Trade Balance", None, ["exports", "imports"], meta, exp + imp,
            [_card("exports", "Exports", exp, "$B", "pct", 1e-9, nd=1),
             _card("imports", "Imports", imp, "$B", "pct", 1e-9, nd=1)],
            {"type": "bar_line", "y_unit": "$B", "x": [a["label"] for a in ax],
             "series": [{"key": "imports", "label": "Imports", "values": i_vals},
                        {"key": "exports", "label": "Exports", "values": e_vals},
                        {"key": "balance", "label": "Trade Balance", "values": bal, "kind": "line"}]},
            ["Goods and services, current US$ (World Bank). Trade balance = exports - imports."]))

        # 4. GST -------------------------------------------------------------------------------
        ax = axis(gst)
        totals = values_on(gst, ax)
        avg_series = [{**r, "value": r["value"] / 12} for r in gst]
        panels.append(self._panel(
            "gst", "GST Tax Collection", "(YOY%)", ["gst_collections"], meta, gst,
            [_card("collections", "GST Collections", gst, "L Cr", "pct"),
             _card("average", "Monthly Average", avg_series, "L Cr", "pct")],
            {"type": "bar_line", "y_unit": "L Cr", "x": [a["label"] for a in ax],
             "series": [{"key": "collections", "label": "GST Collections", "values": totals},
                        {"key": "average", "label": "Monthly Average", "kind": "line",
                         "values": values_on(avg_series, ax)}]},
            ["Gross GST, INR lakh crore per fiscal year; monthly average = annual total / 12."]))

        # 5. Inflation -------------------------------------------------------------------------
        ax = axis(infl, n=CHART_POINTS + 1)
        target = self.settings.rbi_inflation_target
        panels.append(self._panel(
            "inflation", "Inflation", "(IND)", ["inflation"], meta, infl,
            [_card("rate", "Inflation Rate", infl, "%", "pp"),
             {"id": "target", "label": "RBI Target", "value": target, "unit": "%", "delta": 0.0,
              "delta_unit": "pp", "period": None, "basis": "actual"}],
            {"type": "line", "y_unit": "%", "x": [a["label"] for a in ax],
             "series": [{"key": "rate", "label": "CPI inflation", "values": values_on(infl, ax)}]},
            ["RBI target is the 4% (+/-2) flexible inflation-targeting mandate, set via RBI_INFLATION_TARGET."]))

        # 6. Government expenditure ------------------------------------------------------------
        g_tot, g_cap = gov.get("TOTAL", []), gov.get("CAPITAL", [])
        ax = axis(g_tot, g_cap)
        tot_v, cap_v = values_on(g_tot, ax), values_on(g_cap, ax)
        rev_v = [round(t - c, 2) if t is not None and c is not None else None for t, c in zip(tot_v, cap_v)]
        panels.append(self._panel(
            "gov_expenditure", "Government Expenditure", None, ["gov_expenditure"], meta, g_tot + g_cap,
            [_card("total", "Total Expenditure", g_tot, "L Cr", "pct"),
             _card("capital", "Capital Expenditure", g_cap, "L Cr", "pct")],
            {"type": "stacked", "y_unit": "L Cr", "x": [a["label"] for a in ax],
             "series": [{"key": "revenue", "label": "Revenue Expenditure", "values": rev_v},
                        {"key": "capital", "label": "Capital Expenditure", "values": cap_v}],
             "totals": tot_v},
            ["Union Budget actuals / revised estimates, INR lakh crore. Revenue expenditure = total - capital."]))

        return {"generated_at": datetime.now(timezone.utc).isoformat(),
                "ticker": await self.ticker(), "panels": panels}
