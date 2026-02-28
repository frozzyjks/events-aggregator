from __future__ import annotations

from datetime import date, datetime, time
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.domain.models import Event, Place


class SqlAlchemyEventRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, event: Event) -> None:
        self._session.add(event)

    async def update(self, event: Event) -> None:
        await self._session.merge(event)

    async def get_by_id(self, event_id: str) -> Event | None:
        result = await self._session.execute(
            select(Event)
            .options(selectinload(Event.place))
            .where(Event.id == event_id)
        )
        return result.scalars().first()

    async def get_by_id_with_place(self, event_id: str) -> Event | None:
        return await self.get_by_id(event_id)

    async def list(
        self,
        name: Optional[str] = None,
        status: Optional[str] = None,
        date_from: Optional[date] = None,
        date_to: Optional[date] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[int, list[Event]]:
        query = select(Event).options(selectinload(Event.place))
        filters = []

        if name:
            filters.append(Event.name.ilike(f"%{name}%"))
        if status:
            filters.append(Event.status == status)
        if date_from:
            filters.append(Event.event_time >= datetime.combine(date_from, time.min))
        if date_to:
            filters.append(Event.event_time <= datetime.combine(date_to, time.max))

        if filters:
            query = query.where(*filters)

        total: int = await self._session.scalar(
            select(func.count()).select_from(query.subquery())
        )

        offset = (page - 1) * page_size
        result = await self._session.execute(query.offset(offset).limit(page_size))
        items = list(result.scalars().all())

        return total, items