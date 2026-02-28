from sqlalchemy.ext.asyncio import AsyncSession
from src.domain.models import Ticket
from uuid import uuid4

class SqlAlchemyTicketRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, event_id: str, ticket_id: str, first_name: str, last_name: str, email: str, seat: str):
        db_ticket = Ticket(
            id=str(uuid4()),
            event_id=event_id,
            ticket_id=ticket_id,  # ticket_id от внешнего сервиса
            first_name=first_name,
            last_name=last_name,
            email=email,
            seat=seat
        )
        self.session.add(db_ticket)

    async def delete(self, ticket_id: str):
        await self.session.execute(
            "DELETE FROM tickets WHERE id=:ticket_id",
            {"ticket_id": ticket_id}
        )

    async def get(self, ticket_id: str):
        result = await self.session.execute(
            "SELECT * FROM tickets WHERE id=:ticket_id",
            {"ticket_id": ticket_id}
        )
        return result.first()