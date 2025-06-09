from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional


class EventBase(BaseModel):
    name: str
    time: str
    date: date
    location: str
    description: Optional[str] = None
    price: Optional[str] = None
    image: Optional[str] = None
    link: Optional[str] = None


class EventCreate(EventBase):
    pass


class EventUpdate(BaseModel):
    name: Optional[str] = None
    time: Optional[str] = None
    date: Optional[date] = None
    location: Optional[str] = None
    description: Optional[str] = None
    price: Optional[str] = None
    image: Optional[str] = None
    link: Optional[str] = None


class Event(EventBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class EventResponse(BaseModel):
    events: list[Event]
    total: int
    page: int
    size: int
    pages: int


class UserBase(BaseModel):
    email: str
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str
