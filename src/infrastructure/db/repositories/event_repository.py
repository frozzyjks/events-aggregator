from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy import update, delete
from src.domain.models import Event
from datetime import date, datetime, time
from sqlalchemy.orm import selectinload


class SqlAlchemyEventRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, event: Event):
        self.session.add(event)

    async def list(
            self,
            name: Optional[str] = None,
            status: Optional[str] = None,
            date_from: Optional[date] = None,
            date_to: Optional[date] = None,
            page: int = 1,
            page_size: int = 20,
    ) -> Tuple[int, List[Event]]:
        query = select(Event)
        filters = []

        if name:
            filters.append(Event.name.ilike(f"%{name}%"))

        if status:
            filters.append(Event.status == status)

        if date_from:
            start_dt = datetime.combine(date_from, time.min)
            filters.append(Event.event_time >= start_dt)

        if date_to:
            end_dt = datetime.combine(date_to, time.max)
            filters.append(Event.event_time <= end_dt)

        if filters:
            query = query.where(*filters)

        count_query = select(func.count()).select_from(query.subquery())
        total = await self.session.scalar(count_query)

        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await self.session.execute(query)
        items = result.scalars().all()

        return total, items

    async def get_by_id(self, event_id: str) -> Optional[Event]:
        query = select(Event).options(selectinload(Event.place)).where(Event.id == event_id)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def get_by_id_with_place(self, event_id: str) -> Optional[Event]:
        query = select(Event).options(selectinload(Event.place)).where(Event.id == event_id)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def update(self, event: Event):
        await self.session.merge(event)

    async def delete(self, event: Event):
        await self.session.delete(event)