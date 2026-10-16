import logging
import sys


def configure_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=level.upper(),
        stream=sys.stdout,
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(logging.WARNING)
