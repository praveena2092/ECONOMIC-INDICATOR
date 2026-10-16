"""Tiny in-process pub/sub used to push ticker updates to SSE clients.

Single-process only. For several API instances, replace with Postgres LISTEN/NOTIFY or Redis pub/sub
(the SSE route and collectors only depend on `publish` / `subscribe`).
"""
from __future__ import annotations

import asyncio
from contextlib import contextmanager
from typing import Iterator


class EventBus:
    def __init__(self) -> None:
        self._subscribers: set[asyncio.Queue[str]] = set()

    @contextmanager
    def subscribe(self) -> Iterator[asyncio.Queue[str]]:
        queue: asyncio.Queue[str] = asyncio.Queue(maxsize=8)
        self._subscribers.add(queue)
        try:
            yield queue
        finally:
            self._subscribers.discard(queue)

    async def publish(self, topic: str = "ticker") -> None:
        for queue in list(self._subscribers):
            if queue.full():  # slow client: drop the oldest notification, keep the latest
                try:
                    queue.get_nowait()
                except asyncio.QueueEmpty:
                    pass
            queue.put_nowait(topic)


bus = EventBus()
