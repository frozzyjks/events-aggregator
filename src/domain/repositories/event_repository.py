from typing import List, Optional
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.domain.models import Event

class EventRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, event: Event) -> Event:
        self.session.add(event)
        await self.session.commit()
        await self.session.refresh(event)
        return event

    async def list(
        self,
        name: Optional[str] = None,
        skip: int = 0,
        limit: int = 10
    ) -> List[Event]:
        query = select(Event)
        if name:
            query = query.where(Event.name.ilike(f"%{name}%"))
        query = query.offset(skip).limit(limit)
        result = await self.session.execute(query)
        return result.scalars().all()