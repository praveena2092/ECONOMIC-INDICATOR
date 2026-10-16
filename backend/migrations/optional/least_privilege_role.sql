-- OPTIONAL but recommended for production. Run manually in the Supabase SQL editor
-- AFTER the main migrations. Replace the password placeholder; never commit the real one.
--
-- Creates a login role that can only touch this app's tables, then point DATABASE_URL at it
-- (user: dashboard_backend.<project-ref> when going through the Supabase pooler).

do $$
begin
    if not exists (select 1 from pg_roles where rolname = 'dashboard_backend') then
        create role dashboard_backend login password 'REPLACE_WITH_A_LONG_RANDOM_PASSWORD' nobypassrls;
    end if;
end $$;

grant usage on schema public to dashboard_backend;
grant select, insert, update, delete on app_users, indicators, observations, ticker_quotes, collector_runs to dashboard_backend;
grant usage, select on all sequences in schema public to dashboard_backend;
grant select, insert, update, delete on schema_migrations to dashboard_backend;

-- RLS is enabled on every table, so this role needs explicit policies.
do $$
declare t text;
begin
    foreach t in array array['app_users','indicators','observations','ticker_quotes','collector_runs'] loop
        execute format('drop policy if exists backend_all on %I', t);
        execute format('create policy backend_all on %I for all to dashboard_backend using (true) with check (true)', t);
    end loop;
end $$;
