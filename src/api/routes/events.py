from datetime import datetime, timezone, date, timedelta
from uuid import uuid4
import asyncio
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Path
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from sqlalchemy.orm import selectinload
from sqlalchemy import select
from src.domain.schemas.event import EventCreate, EventRead
from src.infrastructure.db.repositories.event_repository import SqlAlchemyEventRepository

from src.infrastructure.db.session import get_session
from src.domain.models import Event
from src.domain.schemas.event import EventCreate, EventResponse
from pydantic import BaseModel, EmailStr
from src.infrastructure.clients.events_provider import EventsProviderClient
from src.infrastructure.db.repositories.ticket_repository import SqlAlchemyTicketRepository

from src.infrastructure.clients.events_provider import (
    EventsProviderClient,
    get_events_client,
)


class TicketCreateRequest(BaseModel):
    event_id: str
    first_name: str
    last_name: str
    email: EmailStr
    seat: str

CACHE_TTL_SECONDS = 30
_seats_cache = {}

router = APIRouter(prefix="/api/events", tags=["events"])


@router.post("/", response_model=EventResponse)
async def create_event(
    payload: EventCreate,
    session: AsyncSession = Depends(get_session),
):
    now = datetime.now(timezone.utc)
    place_id_clean = str(payload.place_id).strip()

    event = Event(
        id=str(uuid4()),
        name=payload.name,
        event_time=payload.event_time,
        registration_deadline=payload.registration_deadline,
        status=payload.status,
        number_of_visitors=payload.number_of_visitors,
        place_id=place_id_clean,
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

@router.post("/tickets", response_model=dict, status_code=201)
async def create_ticket(
    payload: TicketCreateRequest,
    session: AsyncSession = Depends(get_session),
    events_client: EventsProviderClient = Depends(get_events_client),
):
    repo = SqlAlchemyEventRepository(session)
    ticket_repo = SqlAlchemyTicketRepository(session)

    event = await repo.get_by_id(payload.event_id)
    now = datetime.utcnow()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    if event.status != "published":
        raise HTTPException(status_code=400, detail="Event is not published")
    if event.registration_deadline < now:
        raise HTTPException(status_code=400, detail="Registration deadline passed")

    try:
        ticket_id = await events_client.register(
            event_id=payload.event_id,
            first_name=payload.first_name,
            last_name=payload.last_name,
            email=payload.email,
            seat=payload.seat
        )
        if not ticket_id:
            raise HTTPException(status_code=502, detail="Events Provider returned empty ticket_id")
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to register ticket: {str(e)}")

    try:
        await ticket_repo.create(
            event_id=payload.event_id,
            ticket_id=ticket_id,
            first_name=payload.first_name,
            last_name=payload.last_name,
            email=payload.email,
            seat=payload.seat
        )
        await session.commit()
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to save ticket: {str(e)}")

    return {"ticket_id": str(ticket_id)}


@router.get("/")
async def list_events(
    request: Request,
    name: Optional[str] = Query(None, description="Filter by event name"),
    status: Optional[str] = Query(None, description="Filter by event status"),
    date_from: Optional[date] = Query(None, description="Start date filter (YYYY-MM-DD)"),
    date_to: Optional[date] = Query(None, description="End date filter (YYYY-MM-DD)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    session: AsyncSession = Depends(get_session),
):
    repo = SqlAlchemyEventRepository(session)

    total, events = await repo.list(
        name=name,
        status=status,
        date_from=date_from,
        date_to=date_to,
        page=page,
        page_size=page_size,
    )

    base_url = str(request.url).split("?")[0]

    next_page = None
    if page * page_size < total:
        next_page = f"{base_url}?page={page+1}&page_size={page_size}"
        if name:
            next_page += f"&name={name}"
        if status:
            next_page += f"&status={status}"
        if date_from:
            next_page += f"&date_from={date_from}"
        if date_to:
            next_page += f"&date_to={date_to}"

    previous_page = None
    if page > 1:
        previous_page = f"{base_url}?page={page-1}&page_size={page_size}"
        if name:
            previous_page += f"&name={name}"
        if status:
            previous_page += f"&status={status}"
        if date_from:
            previous_page += f"&date_from={date_from}"
        if date_to:
            previous_page += f"&date_to={date_to}"

    return {
        "count": total,
        "next": next_page,
        "previous": previous_page,
        "results": events,
    }

@router.get("/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: str = Path(..., description="UUID события"),
    session: AsyncSession = Depends(get_session),
):
    repo = SqlAlchemyEventRepository(session)
    event = await repo.get_by_id(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event

@router.get("/{event_id}/seats")
async def get_event_seats(
    event_id: str = Path(..., description="UUID события"),
    session: AsyncSession = Depends(get_session),
):
    now = datetime.utcnow()

    cached = _seats_cache.get(event_id)
    if cached and cached["expires_at"] > now:
        return {"event_id": event_id, "available_seats": cached["seats"]}

    repo = SqlAlchemyEventRepository(session)
    event = await repo.get_by_id_with_place(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    available_seats = []
    if event.place and event.place.seats_pattern:
        for section in event.place.seats_pattern.split(","):
            try:
                sec, rng = section[0], section[1:]
                start, end = map(int, rng.split("-"))
                available_seats.extend([f"{sec}{i}" for i in range(start, end + 1)])
            except Exception:
                # Если формат seats_pattern неверный, пропускаем секцию
                continue

    _seats_cache[event_id] = {
        "seats": available_seats,
        "expires_at": now + timedelta(seconds=CACHE_TTL_SECONDS),
    }

    return {"event_id": event_id, "available_seats": available_seats}

@router.delete("/tickets/{ticket_id}", response_model=dict)
async def delete_ticket(
    ticket_id: str,
    session: AsyncSession = Depends(get_session),
    events_client: EventsProviderClient = Depends(get_events_client)
):
    ticket_repo = SqlAlchemyTicketRepository(session)
    ticket = await ticket_repo.get(ticket_id)
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    try:
        success = await events_client.unregister(ticket.event_id, ticket.ticket_id)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to unregister ticket: {str(e)}")

    if not success:
        raise HTTPException(status_code=400, detail="Failed to unregister ticket")

    await ticket_repo.delete(ticket.id)
    await session.commit()
    return {"success": True}