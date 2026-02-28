from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr


class PlaceListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    city: str
    address: str


class PlaceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    city: str
    address: str
    seats_pattern: Optional[str] = None


class EventListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    place: PlaceResponse
    event_time: datetime
    registration_deadline: datetime
    status: str
    number_of_visitors: int


class EventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    place: PlaceResponse
    event_time: datetime
    registration_deadline: datetime
    status: str
    number_of_visitors: int



class EventCreate(BaseModel):
    name: str
    event_time: datetime
    registration_deadline: datetime
    status: str
    number_of_visitors: int
    place_id: str


class TicketCreateRequest(BaseModel):
    event_id: str
    first_name: str
    last_name: str
    email: EmailStr
    seat: str