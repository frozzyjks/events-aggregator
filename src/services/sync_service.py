from __future__ import annotations

import logging
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.models import Event, Place, SyncMetadata
from src.infrastructure.clients.events_provider import EventsProviderClient
from src.infrastructure.clients.paginator import EventsPaginator
from src.infrastructure.db.repositories.event_repository import SqlAlchemyEventRepository
from src.infrastructure.db.repositories.sync_repository import SyncMetadataRepository

logger = logging.getLogger(__name__)


class SyncService:

    def __init__(
        self,
        client: EventsProviderClient,
        session: AsyncSession,
    ) -> None:
        self._client = client
        self._session = session
        self._event_repo = SqlAlchemyEventRepository(session)
        self._sync_repo = SyncMetadataRepository(session)

    async def run(self) -> None:
        logger.info("Starting sync...")
        meta = await self._sync_repo.get_or_create()

        if meta.last_changed_at:
            changed_at_str = meta.last_changed_at.strftime("%Y-%m-%d")
        else:
            changed_at_str = "2000-01-01"

        meta.sync_status = "running"
        meta.last_sync_time = datetime.now(timezone.utc)
        await self._session.commit()

        max_changed_at: datetime | None = None

        try:
            async for raw_event in EventsPaginator(self._client, changed_at=changed_at_str):
                event, place = self._parse_event(raw_event)

                existing_place = await self._session.get(Place, place.id)
                if existing_place is None:
                    self._session.add(place)
                else:
                    existing_place.name = place.name
                    existing_place.city = place.city
                    existing_place.address = place.address
                    existing_place.seats_pattern = place.seats_pattern
                    existing_place.changed_at = place.changed_at
                await self._session.flush()

                existing_event = await self._session.get(Event, event.id)
                if existing_event is None:
                    self._session.add(event)
                else:
                    existing_event.name = event.name
                    existing_event.event_time = event.event_time
                    existing_event.registration_deadline = event.registration_deadline
                    existing_event.status = event.status
                    existing_event.number_of_visitors = event.number_of_visitors
                    existing_event.changed_at = event.changed_at
                    existing_event.status_changed_at = event.status_changed_at
                    existing_event.place_id = event.place_id
                await self._session.flush()

                if max_changed_at is None or event.changed_at > max_changed_at:
                    max_changed_at = event.changed_at

            meta.sync_status = "success"
            if max_changed_at:
                meta.last_changed_at = max_changed_at
            await self._session.commit()
            logger.info("Sync completed successfully.")

        except Exception as exc:
            await self._session.rollback()
            meta.sync_status = "error"
            await self._session.commit()
            logger.exception("Sync failed: %s", exc)
            raise

    @staticmethod
    def _parse_event(raw: dict) -> tuple[Event, Place]:
        raw_place = raw["place"]
        place = Place(
            id=raw_place["id"],
            name=raw_place["name"],
            city=raw_place["city"],
            address=raw_place["address"],
            seats_pattern=raw_place["seats_pattern"],
            changed_at=datetime.fromisoformat(raw_place["changed_at"]),
            created_at=datetime.fromisoformat(raw_place["created_at"]),
        )
        event = Event(
            id=raw["id"],
            name=raw["name"],
            event_time=datetime.fromisoformat(raw["event_time"]),
            registration_deadline=datetime.fromisoformat(raw["registration_deadline"]),
            status=raw["status"],
            number_of_visitors=raw["number_of_visitors"],
            changed_at=datetime.fromisoformat(raw["changed_at"]),
            created_at=datetime.fromisoformat(raw["created_at"]),
            status_changed_at=datetime.fromisoformat(raw["status_changed_at"]),
            place_id=raw_place["id"],
        )
        return event, place