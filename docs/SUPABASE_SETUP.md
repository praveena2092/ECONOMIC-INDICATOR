# Supabase setup

## 1. Create the project
1. supabase.com → **New project**. Choose a region close to where the API will run; save the database password.
2. **Connect** (top bar) → copy the **Session pooler** URI (IPv4-friendly, works for a long-running API).
   Append `?sslmode=require`. Put it in `backend/.env` as `DATABASE_URL`.
   (Direct connection hosts may be IPv6-only on some plans; the transaction pooler also works – the code disables
   prepared statements for it.)

## 2. Run the migrations
```bash
cd backend && python -m app.db.migrate          # applies backend/migrations/*.sql in order
python -m app.db.migrate --status               # shows applied / pending
```
Alternatives: paste each file into the Supabase **SQL editor**, or `supabase db push`
(files use the `YYYYMMDDHHMMSS_name.sql` convention). Migrations are idempotent and checksummed.

| File | Purpose |
|---|---|
| `20261015000001_init_schema.sql` | tables, indexes, RLS on, `anon`/`authenticated` revoked |
| `20261015000002_seed_indicators.sql` | indicator catalogue (source names/URLs, staleness windows) |
| `optional/least_privilege_role.sql` | run manually: limited `dashboard_backend` role + policies |

## 3. Lock the database down (assignment requirement: DB not publicly reachable)
Supabase is hosted Postgres with a public hostname, so "not reachable from the internet" has to be enforced with
project settings. Do all of the following and describe them in your submission:

1. **Network Restrictions** (Project Settings → Database): allow only the backend host's egress IP(s).
   *Check that your plan offers this feature before relying on it.* Use a backend host with a static outbound IP.
2. **Turn off the Data API** (Project Settings → Data API / API settings) – the browser must never reach tables
   through PostgREST. RLS is also enabled on every table with no policies, and `anon`/`authenticated` are revoked.
3. **Enforce SSL** (Database settings → SSL configuration).
4. Run `optional/least_privilege_role.sql` and use that role in `DATABASE_URL`
   (user becomes `dashboard_backend.<project-ref>` on the pooler). Never ship the `postgres` or service-role keys to the browser.
5. If the panel requires strictly private networking (no public endpoint at all), host Postgres on the backend VM
   bound to `127.0.0.1`/private IP with a firewall rule – the same migrations run unchanged.

## 4. First user
`python -m scripts.create_user --email you@example.com --role admin`

## 5. Verify
`curl https://<api>/health/ready` → `{"status":"ok","database":"up", ...}`
