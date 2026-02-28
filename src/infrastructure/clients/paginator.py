from __future__ import annotations

import logging
from typing import AsyncIterator

from src.infrastructure.clients.events_provider import EventsProviderClient

logger = logging.getLogger(__name__)


class EventsPaginator:

    def __init__(self, client: EventsProviderClient, changed_at: str = "2000-01-01") -> None:
        self._client = client
        self._changed_at = changed_at

    def __aiter__(self) -> "EventsPaginator":
        self._next_url: str | None = None
        self._buffer: list[dict] = []
        self._started = False
        return self

    async def __anext__(self) -> dict:
        if self._buffer:
            return self._buffer.pop(0)

        if self._started and self._next_url is None:
            raise StopAsyncIteration

        if not self._started:
            page = await self._client.events_since(self._changed_at)
            self._started = True
        else:
            page = await self._client.events(cursor_url=self._next_url)

        self._next_url = page.get("next")
        results = page.get("results", [])

        if not results and self._next_url is None:
            raise StopAsyncIteration

        self._buffer = list(results)

        if self._buffer:
            return self._buffer.pop(0)

        raise StopAsyncIteration