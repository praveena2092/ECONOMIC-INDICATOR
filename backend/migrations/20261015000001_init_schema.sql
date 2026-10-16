-- 20261015000001_init_schema.sql
-- Core schema for the Economic Indicators Dashboard.
-- Idempotent: safe to re-run. Works on Supabase Postgres and plain Postgres 13+.

create table if not exists app_users (
    id            uuid primary key default gen_random_uuid(),
    email         text not null unique check (email = lower(email)),
    password_hash text not null,
    role          text not null default 'viewer' check (role in ('viewer', 'admin')),
    is_active     boolean not null default true,
    created_at    timestamptz not null default now(),
    last_login_at timestamptz
);

create table if not exists indicators (
    code                text primary key,
    name                text not null,
    unit                text not null,
    frequency           text not null check (frequency in ('intraday', 'annual', 'monthly')),
    source_name         text not null,
    source_url          text not null,
    is_nse              boolean not null default false,
    stale_after_seconds integer not null check (stale_after_seconds > 0),
    notes               text
);

create table if not exists observations (
    id             bigint generated always as identity primary key,
    indicator_code text not null references indicators (code) on delete cascade,
    series_key     text not null,
    period         text not null,                 -- '2024' | '2024-25' | '2026-03'
    period_start   date not null,                 -- used for ordering
    value          numeric(20, 6) not null,       -- only validated numbers are stored; gaps stay absent
    basis          text not null default 'actual' check (basis in ('actual', 'estimate', 'revised_estimate')),
    as_of          date not null,
    fetched_at     timestamptz not null default now(),
    constraint observations_unique unique (indicator_code, series_key, period)
);
create index if not exists observations_lookup_idx
    on observations (indicator_code, series_key, period_start desc);

create table if not exists ticker_quotes (
    symbol      text primary key,
    label       text not null,
    last_price  numeric(16, 4) not null,
    change      numeric(16, 4) not null,
    pct_change  numeric(10, 4) not null,
    source_name text not null,
    source_url  text not null,
    is_nse      boolean not null default false,
    as_of       timestamptz not null,
    fetched_at  timestamptz not null default now(),
    sort_order  smallint not null default 0
);

create table if not exists collector_runs (
    id            bigint generated always as identity primary key,
    collector     text not null,
    status        text not null check (status in ('success', 'partial', 'failed')),
    started_at    timestamptz not null default now(),
    finished_at   timestamptz,
    rows_written  integer not null default 0,
    error         text
);
create index if not exists collector_runs_lookup_idx on collector_runs (collector, started_at desc);

-- ---------------------------------------------------------------------------
-- Defence in depth: the browser must never reach these tables through Supabase's
-- auto-generated REST/GraphQL API. RLS is enabled with NO policies for anon /
-- authenticated, and their table privileges are revoked. Only the backend
-- connection (direct Postgres) can read/write.
-- ---------------------------------------------------------------------------
alter table app_users      enable row level security;
alter table indicators     enable row level security;
alter table observations   enable row level security;
alter table ticker_quotes  enable row level security;
alter table collector_runs enable row level security;

do $$
begin
    if exists (select 1 from pg_roles where rolname = 'anon') then
        revoke all on app_users, indicators, observations, ticker_quotes, collector_runs from anon;
    end if;
    if exists (select 1 from pg_roles where rolname = 'authenticated') then
        revoke all on app_users, indicators, observations, ticker_quotes, collector_runs from authenticated;
    end if;
end $$;
