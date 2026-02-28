from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.schemas.event import EventListItem, EventResponse, TicketCreateRequest
from src.infrastructure.clients.events_provider import EventsProviderClient, get_events_client
from src.infrastructure.db.repositories.event_repository import SqlAlchemyEventRepository
from src.infrastructure.db.repositories.ticket_repository import SqlAlchemyTicketRepository
from src.infrastructure.db.session import get_session
from src.usecases.tickets import (
    CancelTicketUsecase,
    CreateTicketUsecase,
    EventNotFound,
    EventNotPublished,
    RegistrationDeadlinePassed,
    TicketNotFound,
)

logger = logging.getLogger(__name__)

SEATS_CACHE_TTL = 30  # seconds
_seats_cache: dict[str, dict] = {}

router = APIRouter(prefix="/api", tags=["events"])



@router.get("/events")
async def list_events(
    request: Request,
    date_from: Optional[str] = Query(None, description="YYYY-MM-DD"),
    date_to: Optional[str] = Query(None, description="YYYY-MM-DD"),
    name: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    from datetime import date

    date_from_parsed = date.fromisoformat(date_from) if date_from else None
    date_to_parsed = date.fromisoformat(date_to) if date_to else None

    repo = SqlAlchemyEventRepository(session)
    total, events = await repo.list(
        name=name,
        status=status,
        date_from=date_from_parsed,
        date_to=date_to_parsed,
        page=page,
        page_size=page_size,
    )

    base_url = str(request.url).split("?")[0]

    def build_url(p: int) -> str:
        url = f"{base_url}?page={p}&page_size={page_size}"
        if date_from:
            url += f"&date_from={date_from}"
        if date_to:
            url += f"&date_to={date_to}"
        if name:
            url += f"&name={name}"
        if status:
            url += f"&status={status}"
        return url

    return {
        "count": total,
        "next": build_url(page + 1) if page * page_size < total else None,
        "previous": build_url(page - 1) if page > 1 else None,
        "results": [EventListItem.model_validate(e) for e in events],
    }



@router.get("/events/{event_id}", response_model=EventResponse)
async def get_event(
    event_id: str = Path(...),
    session: AsyncSession = Depends(get_session),
):
    repo = SqlAlchemyEventRepository(session)
    event = await repo.get_by_id(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return event



@router.get("/events/{event_id}/seats")
async def get_event_seats(
    event_id: str = Path(...),
    session: AsyncSession = Depends(get_session),
    events_client: EventsProviderClient = Depends(get_events_client),
):
    now = datetime.utcnow()

    cached = _seats_cache.get(event_id)
    if cached and cached["expires_at"] > now:
        return {"event_id": event_id, "available_seats": cached["seats"]}

    repo = SqlAlchemyEventRepository(session)
    event = await repo.get_by_id(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    if event.status != "published":
        raise HTTPException(status_code=400, detail="Event is not published")

    try:
        seats = await events_client.seats(event_id)
    except Exception as exc:
        logger.exception("Failed to fetch seats for event %s", event_id)
        raise HTTPException(status_code=502, detail=f"Failed to fetch seats: {exc}")

    _seats_cache[event_id] = {
        "seats": seats,
        "expires_at": now + timedelta(seconds=SEATS_CACHE_TTL),
    }

    return {"event_id": event_id, "available_seats": seats}



@router.post("/tickets", status_code=201)
async def create_ticket(
    payload: TicketCreateRequest,
    session: AsyncSession = Depends(get_session),
    events_client: EventsProviderClient = Depends(get_events_client),
):
    usecase = CreateTicketUsecase(
        client=events_client,
        events=SqlAlchemyEventRepository(session),
        tickets=SqlAlchemyTicketRepository(session),
    )

    try:
        ticket_id = await usecase.execute(
            event_id=payload.event_id,
            first_name=payload.first_name,
            last_name=payload.last_name,
            email=str(payload.email),
            seat=payload.seat,
        )
        await session.commit()
    except EventNotFound:
        raise HTTPException(status_code=404, detail="Event not found")
    except EventNotPublished:
        raise HTTPException(status_code=400, detail="Event is not published")
    except RegistrationDeadlinePassed:
        raise HTTPException(status_code=400, detail="Registration deadline has passed")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        await session.rollback()
        logger.exception("Ticket creation failed")
        raise HTTPException(status_code=502, detail=str(exc))

    return {"ticket_id": ticket_id}



@router.delete("/tickets/{ticket_id}")
async def delete_ticket(
    ticket_id: str = Path(...),
    session: AsyncSession = Depends(get_session),
    events_client: EventsProviderClient = Depends(get_events_client),
):
    usecase = CancelTicketUsecase(
        client=events_client,
        tickets=SqlAlchemyTicketRepository(session),
    )

    try:
        await usecase.execute(ticket_id)
        await session.commit()
    except TicketNotFound:
        raise HTTPException(status_code=404, detail="Ticket not found")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        await session.rollback()
        logger.exception("Ticket cancellation failed")
        raise HTTPException(status_code=502, detail=str(exc))

    return {"success": True}