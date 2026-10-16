import asyncio
import sys


def ensure_selector_loop() -> None:
    """psycopg async mode cannot run on Windows' default ProactorEventLoop."""
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())