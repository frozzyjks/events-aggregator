import aiohttp
from typing import List
import os

class EventsProviderClient:
    def __init__(self, api_key: str, base_url: str):
        self.api_key = api_key
        self.base_url = base_url

    async def register(self, event_id: str, first_name: str, last_name: str, email: str, seat: str) -> str:
        url = f"{self.base_url}/api/events/{event_id}/register/"
        payload = {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "seat": seat
        }
        headers = {"x-api-key": self.api_key}
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload, headers=headers) as resp:
                if resp.status != 201:
                    text = await resp.text()
                    raise Exception(f"Failed to register: {resp.status} {text}")
                data = await resp.json()
                return data["ticket_id"]

    async def unregister(self, event_id: str, ticket_id: str) -> bool:
        url = f"{self.base_url}/api/events/{event_id}/unregister/"
        payload = {"ticket_id": ticket_id}
        headers = {"x-api-key": self.api_key}
        async with aiohttp.ClientSession() as session:
            async with session.delete(url, json=payload, headers=headers) as resp:
                if resp.status != 200:
                    text = await resp.text()
                    raise Exception(f"Failed to unregister: {resp.status} {text}")
                data = await resp.json()
                return data.get("success", False)

def get_events_client() -> EventsProviderClient:
    return EventsProviderClient(
        api_key=os.getenv("EVENTS_API_KEY"),
        base_url=os.getenv("EVENTS_BASE_URL"),
    )