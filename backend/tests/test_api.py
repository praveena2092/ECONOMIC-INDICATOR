"""Integration tests against a real Postgres (TEST DATABASE_URL, migrations applied)."""
import pytest
from httpx import ASGITransport, AsyncClient

from app.collectors.curated import CuratedCollector
from app.core.config import get_settings
from app.core.security import hash_password
from app.main import app
from app.repositories import users


@pytest.fixture
async def client():
    async with app.router.lifespan_context(app):
        await users.upsert_user("tester@example.com", hash_password("a-long-password"), "viewer")
        await CuratedCollector(get_settings()).run()
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://t") as c:
            yield c


async def _token(client) -> str:
    r = await client.post("/api/v1/auth/login", json={"email": "tester@example.com", "password": "a-long-password"})
    assert r.status_code == 200
    return r.json()["access_token"]


async def test_health_and_ready(client):
    assert (await client.get("/health")).json()["status"] == "ok"
    assert (await client.get("/health/ready")).json()["database"] == "up"


async def test_dashboard_requires_auth(client):
    r = await client.get("/api/v1/dashboard")
    assert r.status_code == 401 and r.json()["error"]["code"] == "unauthenticated"


async def test_login_failure_is_generic(client):
    r = await client.post("/api/v1/auth/login", json={"email": "tester@example.com", "password": "wrong"})
    assert r.status_code == 401 and "Incorrect" in r.json()["error"]["message"]


async def test_dashboard_payload_has_six_panels_and_gaps_are_null(client):
    token = await _token(client)
    r = await client.get("/api/v1/dashboard", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    body = r.json()
    panels = {p["key"]: p for p in body["panels"]}
    assert set(panels) == {"gdp_growth", "debt_gdp", "trade", "gst", "inflation", "gov_expenditure"}
    gst = panels["gst"]
    assert gst["cards"][0]["value"] == 22.08 and gst["cards"][1]["value"] == 1.84
    assert gst["chart"]["x"][-1] == "FY25"
    gov = panels["gov_expenditure"]
    assert gov["chart"]["x"] == ["FY24", "FY25"] and gov["cards"][1]["basis"] == "revised_estimate"
    # no World Bank / NSE data was collected in this test -> unavailable, never invented
    assert panels["gdp_growth"]["status"] == "unavailable" and panels["gdp_growth"]["cards"][0]["value"] is None
    assert body["ticker"]["status"] == "unavailable"


async def test_validation_error_envelope(client):
    r = await client.post("/api/v1/auth/login", json={"email": "bad"})
    assert r.status_code == 422 and r.json()["error"]["code"] == "validation_error"
