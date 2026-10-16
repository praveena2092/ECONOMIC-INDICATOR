# API reference

Base URL: `https://<api-host>`. Interactive docs: `/docs` (disable with `ENABLE_API_DOCS=false`).
All `/api/v1/*` routes except `auth/login` need `Authorization: Bearer <token>`.

Errors always look like `{"error": {"code": "...", "message": "...", "request_id": "..."}}`
(`unauthenticated` 401, `forbidden` 403, `validation_error` 422, `rate_limited` 429, `internal_error` 500, `service_unavailable` 503).

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/health` | no | liveness `{"status":"ok","version":"1.0.0"}` |
| GET | `/health/ready` | no | DB check + latest collector run per collector; 503 if DB is down |
| POST | `/api/v1/auth/login` | no | body `{"email","password"}` → `{"access_token","token_type":"bearer","expires_in"}` |
| GET | `/api/v1/auth/me` | yes | `{"id","email","role"}` |
| GET | `/api/v1/dashboard` | yes | ticker + six panels |
| GET | `/api/v1/ticker` | yes | ticker only |
| GET | `/api/v1/stream/ticker` | yes | SSE; `event: ticker` with the ticker object, `: keep-alive` every 20 s |

## Token handling
HS256 JWT, claims `sub, role, iat, exp, jti`, default lifetime 60 min (`ACCESS_TOKEN_MINUTES`), no refresh token –
on `401` the SPA clears the token and shows the sign-in page. The SPA keeps the token in `sessionStorage`
(cleared when the tab closes). Because tokens are sent in a header (not cookies), CORS runs without credentials.

## `GET /api/v1/dashboard`
```jsonc
{
  "generated_at": "2026-10-16T09:30:00+00:00",
  "ticker": { "status": "ok|stale|unavailable", "as_of": "…", "items": [
      {"symbol": "NIFTY BANK", "label": "NIFTY BANK", "last": 55000.5, "change": -50.1, "pct_change": -0.09, "is_nse": true}], "sources": [] },
  "panels": [{
    "key": "gdp_growth|debt_gdp|trade|gst|inflation|gov_expenditure",
    "title": "…", "subtitle": "(YOY%)|null",
    "status": "ok|stale|unavailable", "as_of": "2025-12-31", "fetched_at": "…",
    "sources": [{"name": "World Bank (…)", "url": "…", "is_nse": false}],
    "cards": [{"id": "india", "label": "India", "value": 6.5, "unit": "%", "delta": -0.2, "delta_unit": "pp",
               "period": "2024", "basis": "actual"}],
    "chart": {"type": "bar|bar_line|area|line|stacked", "y_unit": "%", "x": ["2021", "…"],
              "series": [{"key": "india", "label": "India", "values": [8.7, null, 6.5]}], "totals": []},
    "notes": ["…"]
  }]
}
```
`null` = value not available (rendered `---`). `status: "stale"` = last refresh older than the indicator's window.
