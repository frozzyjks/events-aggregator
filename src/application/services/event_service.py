from src.domain.models import Event
from src.domain.repositories.event_repository import EventRepository


class EventService:

    def __init__(self, repository: EventRepository):
        self._repository = repository

    async def create_event(self, event: Event) -> Event:
        await self._repository.add(event)
        return event

    async def list_events(self):
        return await self._repository.list()