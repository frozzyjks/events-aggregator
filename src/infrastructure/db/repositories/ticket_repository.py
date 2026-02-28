from __future__ import annotations

from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.models import Ticket


class SqlAlchemyTicketRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        event_id: str,
        ticket_id: str,
        first_name: str,
        last_name: str,
        email: str,
        seat: str,
    ) -> Ticket:
        db_ticket = Ticket(
            id=str(uuid4()),
            event_id=event_id,
            ticket_id=ticket_id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            seat=seat,
        )
        self._session.add(db_ticket)
        return db_ticket

    async def get_by_local_id(self, local_id: str) -> Ticket | None:
        result = await self._session.execute(
            select(Ticket).where(
            (Ticket.ticket_id == local_id) | (Ticket.id == local_id)
        )
        )
        return result.scalars().first()

    async def get_by_ticket_id(self, ticket_id: str) -> Ticket | None:
        result = await self._session.execute(
            select(Ticket).where(Ticket.ticket_id == ticket_id)
        )
        return result.scalars().first()

    async def delete(self, ticket: Ticket) -> None:
        await self._session.delete(ticket)