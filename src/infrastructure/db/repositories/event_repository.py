from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete
from src.domain.models import Event
from datetime import datetime


class SqlAlchemyEventRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, event: Event):
        self.session.add(event)

    async def list(
        self,
        name: Optional[str] = None,
        status: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 10
    ) -> List[Event]:
        query = select(Event)
        filters = []

        if name:
            filters.append(Event.name.ilike(f"%{name}%"))
        if status:
            filters.append(Event.status == status)
        if start_date:
            filters.append(Event.event_time >= start_date)
        if end_date:
            filters.append(Event.event_time <= end_date)

        if filters:
            query = query.where(*filters)

        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()

    # Получение одного события по id
    async def get_by_id(self, event_id: str) -> Optional[Event]:
        query = select(Event).where(Event.id == event_id)
        result = await self.session.execute(query)
        return result.scalars().first()

    # Обновление события
    async def update(self, event: Event):
        await self.session.merge(event)

    # Удаление события
    async def delete(self, event: Event):
        await self.session.delete(event)