from __future__ import annotations

import typing
from datetime import datetime, timezone


class EventsProviderClientProtocol(typing.Protocol):
    async def register(
        self, event_id: str, first_name: str, last_name: str, email: str, seat: str
    ) -> str: ...

    async def unregister(self, event_id: str, ticket_id: str) -> bool: ...


class EventRepositoryProtocol(typing.Protocol):
    async def get_by_id(self, event_id: str) -> typing.Any | None: ...


class TicketRepositoryProtocol(typing.Protocol):
    async def create(
        self,
        event_id: str,
        ticket_id: str,
        first_name: str,
        last_name: str,
        email: str,
        seat: str,
    ) -> typing.Any: ...

    async def get_by_local_id(self, local_id: str) -> typing.Any | None: ...

    async def delete(self, ticket: typing.Any) -> None: ...


class EventNotFound(Exception):
    pass


class EventNotPublished(Exception):
    pass


class RegistrationDeadlinePassed(Exception):
    pass


class TicketNotFound(Exception):
    pass


class CreateTicketUsecase:
    def __init__(
        self,
        client: EventsProviderClientProtocol,
        events: EventRepositoryProtocol,
        tickets: TicketRepositoryProtocol,
    ) -> None:
        self._client = client
        self._events = events
        self._tickets = tickets

    async def execute(
        self,
        event_id: str,
        first_name: str,
        last_name: str,
        email: str,
        seat: str,
    ) -> str:
        event = await self._events.get_by_id(event_id)
        if not event:
            raise EventNotFound(event_id)

        if event.status != "published":
            raise EventNotPublished(event_id)

        now = datetime.now(timezone.utc)
        deadline = event.registration_deadline
        if deadline.tzinfo is None:
            from datetime import timezone as tz
            deadline = deadline.replace(tzinfo=tz.utc)
        if now > deadline:
            raise RegistrationDeadlinePassed(event_id)

        ticket_id = await self._client.register(
            event_id=event_id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            seat=seat,
        )

        await self._tickets.create(
            event_id=event_id,
            ticket_id=ticket_id,
            first_name=first_name,
            last_name=last_name,
            email=email,
            seat=seat,
        )

        return ticket_id


class CancelTicketUsecase:
    def __init__(
        self,
        client: EventsProviderClientProtocol,
        tickets: TicketRepositoryProtocol,
    ) -> None:
        self._client = client
        self._tickets = tickets

    async def execute(self, local_ticket_id: str) -> None:
        ticket = await self._tickets.get_by_local_id(local_ticket_id)
        if not ticket:
            raise TicketNotFound(local_ticket_id)

        await self._client.unregister(ticket.event_id, ticket.ticket_id)
        await self._tickets.delete(ticket)