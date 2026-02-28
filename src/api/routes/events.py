from datetime import datetime, timezone
from uuid import uuid4
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from src.domain.schemas.event import EventCreate, EventRead
from src.infrastructure.db.repositories.event_repository import SqlAlchemyEventRepository

from src.infrastructure.db.session import get_session
from src.infrastructure.db.repositories.event_repository import (
    SqlAlchemyEventRepository,
)
from src.domain.models import Event
from src.domain.schemas.event import EventCreate, EventResponse


router = APIRouter(prefix="/events", tags=["events"])


@router.post("/", response_model=EventResponse)
async def create_event(
    payload: EventCreate,
    session: AsyncSession = Depends(get_session),
):
    now = datetime.now(timezone.utc)

    event = Event(
        id=str(uuid4()),
        name=payload.name,
        event_time=payload.event_time,
        registration_deadline=payload.registration_deadline,
        status=payload.status,
        number_of_visitors=payload.number_of_visitors,
        place_id=payload.place_id,
        changed_at=now,
        created_at=now,
        status_changed_at=now,
    )

    repository = SqlAlchemyEventRepository(session)

    try:
        await repository.add(event)
        await session.commit()
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=400, detail=str(e))

    return event

@router.get("/", response_model=List[EventRead])
async def list_events(
    name: Optional[str] = Query(None, description="Filter by event name"),
    status: Optional[str] = Query(None, description="Filter by status"),
    start_date: Optional[datetime] = Query(None, description="Start of event time range"),
    end_date: Optional[datetime] = Query(None, description="End of event time range"),
    skip: int = 0,
    limit: int = 10,
    session: AsyncSession = Depends(get_session)
):
    repo = SqlAlchemyEventRepository(session)
    events = await repo.list(
        name=name,
        status=status,
        start_date=start_date,
        end_date=end_date,
        skip=skip,
        limit=limit
    )
    return events