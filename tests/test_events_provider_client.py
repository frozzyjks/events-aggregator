from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.infrastructure.clients.events_provider import EventsProviderClient

BASE_URL = "http://fake-provider.test"
API_KEY = "test-key"


@pytest.fixture
def client() -> EventsProviderClient:
    return EventsProviderClient(base_url=BASE_URL, api_key=API_KEY)


@pytest.mark.asyncio
async def test_events_since_returns_parsed_json(client):
    fake_response = {
        "next": None,
        "previous": None,
        "results": [{"id": "abc", "name": "Test Event"}],
    }

    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json = MagicMock(return_value=fake_response)

    mock_get = AsyncMock(return_value=mock_resp)
    mock_http_client = MagicMock()
    mock_http_client.get = mock_get
    mock_http_client.__aenter__ = AsyncMock(return_value=mock_http_client)
    mock_http_client.__aexit__ = AsyncMock(return_value=False)

    with patch("httpx.AsyncClient", return_value=mock_http_client):
        result = await client.events_since("2000-01-01")

    assert result["results"][0]["id"] == "abc"
    mock_get.assert_called_once()
    call_url = mock_get.call_args[0][0]
    assert "changed_at=2000-01-01" in call_url


@pytest.mark.asyncio
async def test_events_since_sends_api_key_header(client):
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json = MagicMock(return_value={"next": None, "results": []})

    mock_get = AsyncMock(return_value=mock_resp)
    mock_http_client = MagicMock()
    mock_http_client.get = mock_get
    mock_http_client.__aenter__ = AsyncMock(return_value=mock_http_client)
    mock_http_client.__aexit__ = AsyncMock(return_value=False)

    with patch("httpx.AsyncClient", return_value=mock_http_client):
        await client.events_since("2000-01-01")

    headers = mock_get.call_args.kwargs.get("headers", {})
    assert headers.get("x-api-key") == API_KEY


@pytest.mark.asyncio
async def test_register_returns_ticket_id(client):
    mock_resp = MagicMock()
    mock_resp.status_code = 201
    mock_resp.json = MagicMock(return_value={"ticket_id": "ticket-uuid-123"})

    mock_post = AsyncMock(return_value=mock_resp)
    mock_http_client = MagicMock()
    mock_http_client.post = mock_post
    mock_http_client.__aenter__ = AsyncMock(return_value=mock_http_client)
    mock_http_client.__aexit__ = AsyncMock(return_value=False)

    with patch("httpx.AsyncClient", return_value=mock_http_client):
        ticket_id = await client.register(
            event_id="event-1",
            first_name="Ivan",
            last_name="Ivanov",
            email="ivan@example.com",
            seat="A1",
        )

    assert ticket_id == "ticket-uuid-123"


@pytest.mark.asyncio
async def test_register_raises_on_non_201(client):
    mock_resp = MagicMock()
    mock_resp.status_code = 400
    mock_resp.text = "seat already taken"

    mock_post = AsyncMock(return_value=mock_resp)
    mock_http_client = MagicMock()
    mock_http_client.post = mock_post
    mock_http_client.__aenter__ = AsyncMock(return_value=mock_http_client)
    mock_http_client.__aexit__ = AsyncMock(return_value=False)

    with patch("httpx.AsyncClient", return_value=mock_http_client):
        with pytest.raises(ValueError, match="Register failed"):
            await client.register(
                event_id="event-1",
                first_name="Ivan",
                last_name="Ivanov",
                email="ivan@example.com",
                seat="A1",
            )


@pytest.mark.asyncio
async def test_unregister_returns_true_on_success(client):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json = MagicMock(return_value={"success": True})

    mock_request = AsyncMock(return_value=mock_resp)
    mock_http_client = MagicMock()
    mock_http_client.request = mock_request
    mock_http_client.__aenter__ = AsyncMock(return_value=mock_http_client)
    mock_http_client.__aexit__ = AsyncMock(return_value=False)

    with patch("httpx.AsyncClient", return_value=mock_http_client):
        result = await client.unregister("event-1", "ticket-uuid-123")

    assert result is True


@pytest.mark.asyncio
async def test_unregister_raises_on_failure(client):
    mock_resp = MagicMock()
    mock_resp.status_code = 404
    mock_resp.text = "not found"

    mock_request = AsyncMock(return_value=mock_resp)
    mock_http_client = MagicMock()
    mock_http_client.request = mock_request
    mock_http_client.__aenter__ = AsyncMock(return_value=mock_http_client)
    mock_http_client.__aexit__ = AsyncMock(return_value=False)

    with patch("httpx.AsyncClient", return_value=mock_http_client):
        with pytest.raises(ValueError, match="Unregister failed"):
            await client.unregister("event-1", "ticket-uuid-123")


@pytest.mark.asyncio
async def test_seats_returns_list(client):
    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json = MagicMock(return_value={"seats": ["A1", "A2", "B5"]})

    mock_get = AsyncMock(return_value=mock_resp)
    mock_http_client = MagicMock()
    mock_http_client.get = mock_get
    mock_http_client.__aenter__ = AsyncMock(return_value=mock_http_client)
    mock_http_client.__aexit__ = AsyncMock(return_value=False)

    with patch("httpx.AsyncClient", return_value=mock_http_client):
        seats = await client.seats("event-1")

    assert seats == ["A1", "A2", "B5"]