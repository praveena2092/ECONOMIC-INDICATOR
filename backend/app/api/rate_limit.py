"""Small sliding-window limiter for the login endpoint (per process)."""
from __future__ import annotations

import time
from collections import defaultdict, deque

from app.core.errors import RateLimited


class SlidingWindowLimiter:
    def __init__(self, max_hits: int, window_seconds: int):
        self.max_hits, self.window = max_hits, window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def check(self, key: str) -> None:
        now = time.monotonic()
        q = self._hits[key]
        while q and now - q[0] > self.window:
            q.popleft()
        if len(q) >= self.max_hits:
            raise RateLimited("Too many attempts. Try again in a minute.", headers={"Retry-After": str(self.window)})
        q.append(now)

    def reset(self, key: str) -> None:
        self._hits.pop(key, None)


login_limiter = SlidingWindowLimiter(max_hits=5, window_seconds=60)
