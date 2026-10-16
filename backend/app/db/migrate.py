"""Minimal, dependency-free migration runner.

    python -m app.db.migrate            # apply pending migrations
    python -m app.db.migrate --status   # list applied / pending

Files in backend/migrations/*.sql are applied in filename order, each inside a transaction,
guarded by an advisory lock and recorded with a checksum in `schema_migrations`.
The same files also work with `supabase db push` / the Supabase SQL editor.
"""
from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

import psycopg

from app.core.config import get_settings

MIGRATIONS_DIR = Path(__file__).resolve().parents[2] / "migrations"
LOCK_KEY = 726_105_001

BOOTSTRAP = """
create table if not exists schema_migrations (
    filename   text primary key,
    checksum   text not null,
    applied_at timestamptz not null default now()
);
alter table schema_migrations enable row level security;
"""


def _checksum(sql: str) -> str:
    return hashlib.sha256(sql.encode()).hexdigest()


def run(status_only: bool = False) -> int:
    files = sorted(MIGRATIONS_DIR.glob("*.sql"))
    if not files:
        print("No migration files found.")
        return 0

    with psycopg.connect(get_settings().database_url, autocommit=True, prepare_threshold=None) as conn:
        conn.execute(BOOTSTRAP)
        conn.execute("select pg_advisory_lock(%s)", (LOCK_KEY,))
        try:
            applied = {r[0]: r[1] for r in conn.execute("select filename, checksum from schema_migrations")}
            pending = []
            for f in files:
                sql = f.read_text(encoding="utf-8")
                if f.name in applied:
                    if applied[f.name] != _checksum(sql):
                        print(f"ERROR: {f.name} was modified after being applied. Add a new migration instead.")
                        return 1
                    print(f"  applied  {f.name}")
                else:
                    pending.append((f, sql))
                    print(f"  pending  {f.name}")
            if status_only:
                return 0
            for f, sql in pending:
                print(f"Applying {f.name} ...", end=" ", flush=True)
                with conn.transaction():
                    conn.execute(sql)
                    conn.execute(
                        "insert into schema_migrations (filename, checksum) values (%s, %s)",
                        (f.name, _checksum(sql)),
                    )
                print("done")
            print("Database is up to date." if pending else "Nothing to apply.")
            return 0
        finally:
            conn.execute("select pg_advisory_unlock(%s)", (LOCK_KEY,))


def main() -> None:
    parser = argparse.ArgumentParser(description="Apply SQL migrations")
    parser.add_argument("--status", action="store_true", help="only show migration status")
    args = parser.parse_args()
    try:
        sys.exit(run(status_only=args.status))
    except psycopg.Error as exc:
        print(f"Database error: {exc}")
        sys.exit(2)


if __name__ == "__main__":
    main()
