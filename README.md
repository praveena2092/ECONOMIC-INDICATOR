# Economic Indicators Dashboard

React + FastAPI + Supabase (Postgres) implementation of the *Interview Round II* assignment.
Live ticker + six indicator panels, JWT-protected API, server-side collectors, SSE ticker updates.

```
backend/    FastAPI app, collectors, SQL migrations, tests
frontend/   Vite + React + TypeScript + Recharts
docs/       SUPABASE_SETUP.md · API.md · DEPLOYMENT.md · ASSUMPTIONS.md
```

## Architecture

```
Browser (React) ──HTTPS + JWT──▶ FastAPI ──SQL (psycopg, parameterised)──▶ Supabase Postgres
      ▲  └─ SSE /stream/ticker        ▲
      │                               └─ APScheduler collectors ──▶ NSE · World Bank · IMF · Yahoo (SENSEX) · curated CSV
```

* The browser only ever talks to the FastAPI backend – never to NSE or any upstream.
* Collectors validate every upstream payload, write only valid numbers (gaps stay gaps) and record each run in
  `collector_runs`. A failed refresh leaves the last valid rows untouched; the API then flags them **stale**.
* Backend layers: `api/routes` (HTTP) → `services` (payload building) → `repositories` (SQL) → `db/pool`.
  `collectors/*` are independent plug-ins sharing `BaseCollector`.

## Quick start (local)

Prerequisites: Python 3.11+, Node 20+, a Supabase project ([docs/SUPABASE_SETUP.md](docs/SUPABASE_SETUP.md)).

```bash
# 1. Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env            # fill DATABASE_URL and JWT_SECRET
python -m app.db.migrate        # create tables (idempotent)
python -m scripts.create_user --email you@example.com --role admin
uvicorn app.main:app --reload --port 8000

# 2. Frontend (new terminal)
cd frontend
cp .env.example .env            # VITE_API_BASE_URL=http://localhost:8000
npm install
npm run dev                     # http://localhost:5173
```

Tests: `cd backend && pytest` (integration tests need `DATABASE_URL` pointing at a migrated **test** database –
never your production one) · `cd frontend && npm test`.

## Environment variables

| Variable | Where | Purpose |
|---|---|---|
| `DATABASE_URL` | backend | Supabase Postgres URI (`?sslmode=require`) |
| `JWT_SECRET` (≥32 chars), `JWT_ALGORITHM`, `ACCESS_TOKEN_MINUTES` | backend | token signing / expiry (default 60 min) |
| `CORS_ORIGINS` | backend | exact frontend origin(s); `*` is rejected at startup |
| `COLLECTORS_ENABLED`, `NSE_REFRESH_SECONDS`, `NSE_OFF_HOURS_REFRESH_SECONDS`, `MACRO_REFRESH_HOURS` | backend | refresh cadence |
| `HTTP_TIMEOUT_SECONDS`, `HTTP_MAX_RETRIES` | backend | upstream timeout / retries |
| `RBI_INFLATION_TARGET` | backend | RBI target shown on the Inflation panel |
| `VITE_API_BASE_URL` | frontend | API base URL (public, no secrets) |

## Refresh model

| Data | Refresh | Reaches the browser via |
|---|---|---|
| Ticker | every 60 s in market hours (Mon–Fri 09:00–16:00 IST), every 15 min otherwise | SSE `/api/v1/stream/ticker` (+ 60 s polling fallback) |
| World Bank / IMF / curated CSV | every 6 h and at startup | `/api/v1/dashboard`, re-fetched every 5 min |

## Error handling

* One JSON envelope for every error: `{"error": {"code", "message", "request_id"}}`; 500s never leak internals.
* Collectors: timeout + bounded retries + schema/number validation; never raise into the scheduler.
* UI states: loading skeleton, per-panel *unavailable*, *stale* badge, banner when a refresh fails (last data kept),
  full-page retry when nothing has ever loaded, `---` for every missing value.
* Login: generic failure message, constant-time check, 5 attempts/min/IP+e-mail.

## Granting the panel access

Create an account with `python -m scripts.create_user --email panel@… --role viewer --password-env PANEL_PW`
and send the credentials **separately** from the repo. Disable it later with
`update app_users set is_active = false where email = '…';`.

See [docs/ASSUMPTIONS.md](docs/ASSUMPTIONS.md) for data sources, deviations from the design and known limitations.
