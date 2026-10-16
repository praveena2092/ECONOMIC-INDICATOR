# Deployment (frontend and API on different hosts, both HTTPS)

## API (e.g. Render / Railway / Fly.io – any container host with a static outbound IP if you use Supabase Network Restrictions)
1. Deploy `backend/` (uses `Dockerfile`; start command `uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1`).
   Keep **one worker/instance**: the scheduler and SSE bus are in-process.
2. Environment variables: `DATABASE_URL`, `JWT_SECRET`, `CORS_ORIGINS=https://<frontend-domain>`, `APP_ENV=production`
   (see README table). Health check path: `/health`.
3. Run migrations once from your machine or a release command: `python -m app.db.migrate`.
4. Create the panel account: `python -m scripts.create_user --email … --role viewer --password-env PANEL_PW`.
5. Smoke test: `curl https://<api>/health/ready`.

## Frontend (e.g. Vercel / Netlify / Cloudflare Pages)
1. Root `frontend/`, build `npm run build`, output `dist`.
2. Env var `VITE_API_BASE_URL=https://<api-domain>` (set at build time).
3. Add the resulting origin to the API's `CORS_ORIGINS` and redeploy the API.

## Scaling note
For multiple API instances move the ticker fan-out to Postgres `LISTEN/NOTIFY` or Redis and run the scheduler on a single worker.
