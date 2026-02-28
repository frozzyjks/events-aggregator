from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from src.infrastructure.clients.paginator import EventsPaginator


def make_client(pages: list[dict]) -> AsyncMock:
    client = AsyncMock()

    all_pages = iter(pages)

    async def fake_events_since(changed_at):
        return next(all_pages)

    async def fake_events(cursor_url=None):
        return next(all_pages)

    client.events_since = AsyncMock(side_effect=fake_events_since)
    client.events = AsyncMock(side_effect=fake_events)
    return client


@pytest.mark.asyncio
async def test_paginator_single_page():
    pages = [
        {
            "next": None,
            "results": [{"id": "1"}, {"id": "2"}],
        }
    ]
    client = make_client(pages)
    collected = [e async for e in EventsPaginator(client, changed_at="2000-01-01")]
    assert len(collected) == 2
    assert collected[0]["id"] == "1"


@pytest.mark.asyncio
async def test_paginator_multiple_pages():
    pages = [
        {"next": "http://fake/page2", "results": [{"id": "1"}, {"id": "2"}]},
        {"next": "http://fake/page3", "results": [{"id": "3"}]},
        {"next": None, "results": [{"id": "4"}, {"id": "5"}]},
    ]
    client = make_client(pages)
    collected = [e async for e in EventsPaginator(client, changed_at="2000-01-01")]
    assert [e["id"] for e in collected] == ["1", "2", "3", "4", "5"]


@pytest.mark.asyncio
async def test_paginator_empty():
    pages = [{"next": None, "results": []}]
    client = make_client(pages)
    collected = [e async for e in EventsPaginator(client)]
    assert collected == []