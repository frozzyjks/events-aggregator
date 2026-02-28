from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class EventCreate(BaseModel):
    name: str
    event_time: datetime
    registration_deadline: datetime
    status: str
    number_of_visitors: int
    place_id: str


class EventResponse(EventCreate):
    id: str
    changed_at: datetime
    created_at: datetime
    status_changed_at: datetime


class EventRead(EventCreate):
    id: str
    name: str
    event_time: datetime
    registration_deadline: datetime
    status: str
    number_of_visitors: int
    place_id: str
    created_at: datetime
    changed_at: datetime
    status_changed_at: datetime

    class Config:
        orm_mode = True