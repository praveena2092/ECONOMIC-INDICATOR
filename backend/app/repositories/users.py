from __future__ import annotations

from app.db.pool import connection


async def get_by_email(email: str) -> dict | None:
    async with connection() as conn:
        cur = await conn.execute(
            "select id::text, email, password_hash, role, is_active from app_users where email = %s",
            (email.lower(),),
        )
        return await cur.fetchone()


async def get_by_id(user_id: str) -> dict | None:
    async with connection() as conn:
        cur = await conn.execute(
            "select id::text, email, role, is_active from app_users where id = %s::uuid", (user_id,)
        )
        return await cur.fetchone()


async def touch_login(user_id: str) -> None:
    async with connection() as conn:
        await conn.execute("update app_users set last_login_at = now() where id = %s::uuid", (user_id,))


async def upsert_user(email: str, password_hash: str, role: str) -> None:
    async with connection() as conn:
        await conn.execute(
            """insert into app_users (email, password_hash, role) values (%s, %s, %s)
               on conflict (email) do update
               set password_hash = excluded.password_hash, role = excluded.role, is_active = true""",
            (email.lower(), password_hash, role),
        )
