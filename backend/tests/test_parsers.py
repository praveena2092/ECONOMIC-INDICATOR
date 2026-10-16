from datetime import date

import pytest

from app.collectors.curated import parse_curated_csv, parse_period_start, DATA_DIR
from app.collectors.imf import parse_imf
from app.collectors.ticker import in_market_hours, parse_nse_all_indices, parse_yahoo_sensex
from app.collectors.worldbank import parse_worldbank
from app.core.errors import CollectorError
from datetime import datetime, timezone


def test_worldbank_skips_nulls_and_bad_values():
    payload = [{"page": 1}, [
        {"date": "2024", "value": 6.5}, {"date": "2023", "value": None},
        {"date": "bad", "value": 1.0}, {"date": "2022", "value": float("nan")}]]
    rows = parse_worldbank(payload, "gdp_growth", "IND")
    assert [r["period"] for r in rows] == ["2024"] and rows[0]["value"] == 6.5


def test_worldbank_rejects_wrong_shape():
    with pytest.raises(CollectorError):
        parse_worldbank({"message": "boom"}, "gdp_growth", "IND")


def test_imf_drops_projection_years():
    payload = {"values": {"GG_DEBT_GDP": {"IND": {"2023": 81.3, "2030": 75.0}, "USA": {"2023": 120.0}}}}
    rows = parse_imf(payload, max_year=2025)
    assert {(r["series_key"], r["period"]) for r in rows} == {("IND", "2023"), ("USA", "2023")}


def test_nse_parser_validates_numbers():
    payload = {"timestamp": "15-Oct-2026 15:30:00", "data": [
        {"index": "NIFTY BANK", "last": 55000.5, "variation": -50.1, "percentChange": -0.09},
        {"index": "NIFTY IT", "last": "oops", "variation": 1, "percentChange": 1},
        {"index": "NIFTY 50", "last": 1, "variation": 1, "percentChange": 1}]}
    out = parse_nse_all_indices(payload)
    assert [q["symbol"] for q in out] == ["NIFTY BANK"]
    assert out[0]["as_of"] == datetime(2026, 10, 15, 10, 0, tzinfo=timezone.utc)


def test_yahoo_parser():
    payload = {"chart": {"result": [{"meta": {"regularMarketPrice": 110.0, "chartPreviousClose": 100.0,
                                                 "regularMarketTime": 1760000000}}]}}
    q = parse_yahoo_sensex(payload)
    assert q["change"] == 10.0 and q["pct_change"] == 10.0 and q["is_nse"] is False
    with pytest.raises(CollectorError):
        parse_yahoo_sensex({"chart": {"result": None}})


def test_market_hours():
    assert in_market_hours(datetime(2026, 10, 15, 6, 0, tzinfo=timezone.utc))      # Thu 11:30 IST
    assert not in_market_hours(datetime(2026, 10, 17, 6, 0, tzinfo=timezone.utc))  # Sat


def test_fiscal_period_parsing():
    assert parse_period_start("2024-25") == date(2024, 4, 1)
    with pytest.raises(ValueError):
        parse_period_start("2024-27")


def test_shipped_curated_csvs_are_valid():
    for name, code in [("gst_collections.csv", "gst_collections"), ("union_budget_expenditure.csv", "gov_expenditure")]:
        rows, errors = parse_curated_csv(DATA_DIR / name, {code})
        assert rows and not errors
