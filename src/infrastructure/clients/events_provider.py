from __future__ import annotations

import logging
from typing import AsyncIterator

import httpx

logger = logging.getLogger(__name__)


class EventsProviderClient:

    def __init__(self, base_url: str, api_key: str) -> None:
        self._base_url = base_url.rstrip("/")
        self._headers = {"x-api-key": api_key}


    async def events(self, cursor_url: str | None = None) -> dict:
        url = cursor_url or f"{self._base_url}/api/events/?changed_at=2000-01-01"
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=self._headers, follow_redirects=True)
            resp.raise_for_status()
            return resp.json()

    async def events_since(self, changed_at: str) -> dict:
        url = f"{self._base_url}/api/events/?changed_at={changed_at}"
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=self._headers, follow_redirects=True)
            resp.raise_for_status()
            return resp.json()

    async def seats(self, event_id: str) -> list[str]:
        url = f"{self._base_url}/api/events/{event_id}/seats/"
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, headers=self._headers, follow_redirects=True)
            resp.raise_for_status()
            data = resp.json()
            return data.get("seats", [])

    async def register(
        self,
        event_id: str,
        first_name: str,
        last_name: str,
        email: str,
        seat: str,
    ) -> str:
        url = f"{self._base_url}/api/events/{event_id}/register/"
        payload = {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "seat": seat,
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                url, json=payload, headers=self._headers, follow_redirects=False
            )
            if resp.status_code not in (200, 201):
                raise ValueError(f"Register failed: {resp.status_code} {resp.text}")
            return resp.json()["ticket_id"]

    async def unregister(self, event_id: str, ticket_id: str) -> bool:
        """Отменить регистрацию. Возвращает True при успехе."""
        url = f"{self._base_url}/api/events/{event_id}/unregister/"
        payload = {"ticket_id": ticket_id}
        async with httpx.AsyncClient() as client:
            resp = await client.request(
                "DELETE",
                url,
                json=payload,
                headers=self._headers,
                follow_redirects=False,
            )
            if resp.status_code != 200:
                raise ValueError(f"Unregister failed: {resp.status_code} {resp.text}")
            return resp.json().get("success", False)


def get_events_client() -> EventsProviderClient:
    from src.core.config import settings
    return EventsProviderClient(
        base_url=settings.events_api_url,
        api_key=settings.events_api_key,
    )