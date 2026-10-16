"""Create or update a user (also how the panel's evaluation account is granted).

    python -m scripts.create_user --email panel@example.com --role viewer
    (password is prompted; or pass --password-env VAR to read it from an environment variable)
"""
import argparse
import asyncio
import getpass
import os
import sys

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.pool import close_pool, open_pool
from app.repositories import users
from app.core.loop import ensure_selector_loop

ensure_selector_loop()

async def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--email", required=True)
    p.add_argument("--role", choices=["viewer", "admin"], default="viewer")
    p.add_argument("--password-env", help="read the password from this environment variable")
    args = p.parse_args()

    password = os.environ.get(args.password_env, "") if args.password_env else getpass.getpass("Password: ")
    if len(password) < 10:
        print("Password must be at least 10 characters.")
        return 1
    await open_pool(get_settings())
    try:
        await users.upsert_user(args.email.strip().lower(), hash_password(password), args.role)
    finally:
        await close_pool()
    print(f"User {args.email} saved with role '{args.role}'.")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
