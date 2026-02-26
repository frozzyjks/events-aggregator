from datetime import datetime

from sqlalchemy import (
    String,
    DateTime,
    Integer,
    ForeignKey,
    Index,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    relationship,
)


class Base(DeclarativeBase):
    pass


class Place(Base):
    __tablename__ = "places"

    id: Mapped[str] = mapped_column(String, primary_key=True)

    name: Mapped[str] = mapped_column(String, nullable=False)
    city: Mapped[str] = mapped_column(String, nullable=False)
    address: Mapped[str] = mapped_column(String, nullable=False)
    seats_pattern: Mapped[str] = mapped_column(String, nullable=False)

    changed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # обратная связь (необязательно, но удобно)
    events: Mapped[list["Event"]] = relationship(
        back_populates="place",
        cascade="all, delete-orphan",
    )


class Event(Base):
    __tablename__ = "events"

    __table_args__ = (
        Index("ix_events_event_time", "event_time"),
        Index("ix_events_changed_at", "changed_at"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True)

    name: Mapped[str] = mapped_column(String, nullable=False)

    event_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    registration_deadline: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    status: Mapped[str] = mapped_column(String, nullable=False)
    number_of_visitors: Mapped[int] = mapped_column(Integer, nullable=False)

    changed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    status_changed_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    place_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("places.id"),
        nullable=False,
    )

    place: Mapped["Place"] = relationship(back_populates="events")

    tickets: Mapped[list["Ticket"]] = relationship(
        back_populates="event",
        cascade="all, delete-orphan",
    )


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[str] = mapped_column(String, primary_key=True)

    event_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("events.id"),
        nullable=False,
    )

    ticket_id: Mapped[str] = mapped_column(String, nullable=False)

    first_name: Mapped[str] = mapped_column(String, nullable=False)
    last_name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False)
    seat: Mapped[str] = mapped_column(String, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    event: Mapped["Event"] = relationship(back_populates="tickets")


class SyncMetadata(Base):
    __tablename__ = "sync_metadata"

    # всегда будет одна строка с id=1
    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)

    last_sync_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_changed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    sync_status: Mapped[str | None] = mapped_column(String, nullable=True)