from fastapi import APIRouter, Query
from typing import Optional, List
from datetime import datetime, date
from pydantic import BaseModel

router = APIRouter()

class MockEvent(BaseModel):
    id: int
    name: str
    time: str
    date: date
    location: str
    description: str
    price: str
    image: Optional[str] = None
    link: Optional[str] = None

class MockEventsResponse(BaseModel):
    events: List[MockEvent]
    total: int

# Mock Croatian events data
MOCK_EVENTS = [
    MockEvent(
        id=1,
        name="Zagreb Music Festival",
        time="20:00",
        date=date(2025, 6, 15),
        location="Zagreb",
        description="Annual music festival featuring Croatian and international artists",
        price="150 HRK",
        image="https://images.unsplash.com/photo-1470229722913-7c0e2dbbafd3?w=400",
        link="https://example.com/zagreb-music"
    ),
    MockEvent(
        id=2,
        name="Split Summer Concert",
        time="19:30",
        date=date(2025, 6, 20),
        location="Split",
        description="Open-air concert by the Adriatic Sea",
        price="100 HRK",
        image="https://images.unsplash.com/photo-1493225457124-a3eb161ffa5f?w=400",
        link="https://example.com/split-concert"
    ),
    MockEvent(
        id=3,
        name="Dubrovnik Cultural Evening",
        time="18:00",
        date=date(2025, 6, 25),
        location="Dubrovnik",
        description="Traditional Croatian cultural performance in historic Old Town",
        price="80 HRK",
        image="https://images.unsplash.com/photo-1467269204594-9661b134dd2b?w=400",
        link="https://example.com/dubrovnik-culture"
    ),
    MockEvent(
        id=4,
        name="Rijeka Tech Conference",
        time="09:00",
        date=date(2025, 6, 18),
        location="Rijeka",
        description="Technology conference with leading Croatian and European speakers",
        price="200 HRK",
        image="https://images.unsplash.com/photo-1540575467063-178a50c2df87?w=400",
        link="https://example.com/rijeka-tech"
    ),
    MockEvent(
        id=5,
        name="Zadar Sunset Festival",
        time="17:00",
        date=date(2025, 6, 22),
        location="Zadar",
        description="Sunset music festival featuring electronic and ambient music",
        price="120 HRK",
        image="https://images.unsplash.com/photo-1520637836862-4d197d17c0a4?w=400",
        link="https://example.com/zadar-sunset"
    ),
    MockEvent(
        id=6,
        name="Pula Film Screening",
        time="21:00",
        date=date(2025, 6, 16),
        location="Pula",
        description="Outdoor cinema screening in the famous Roman amphitheater",
        price="60 HRK",
        image="https://images.unsplash.com/photo-1489599142025-4c2ac1e9de39?w=400",
        link="https://example.com/pula-cinema"
    ),
    MockEvent(
        id=7,
        name="Makarska Beach Party",
        time="22:00",
        date=date(2025, 6, 19),
        location="Makarska",
        description="Summer beach party with DJ sets and cocktails",
        price="Free",
        image="https://images.unsplash.com/photo-1559827260-dc66d52bef19?w=400",
        link="https://example.com/makarska-beach"
    ),
    MockEvent(
        id=8,
        name="Osijek Food Festival",
        time="12:00",
        date=date(2025, 6, 21),
        location="Osijek",
        description="Traditional Slavonian cuisine and local specialties",
        price="50 HRK",
        image="https://images.unsplash.com/photo-1414235077428-338989a2e8c0?w=400",
        link="https://example.com/osijek-food"
    ),
]

@router.get("/", response_model=MockEventsResponse)
async def get_mock_events(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None),
    location: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None)
):
    """Get mock events for demonstration"""
    filtered_events = MOCK_EVENTS.copy()
    
    # Apply search filter
    if search:
        search_lower = search.lower()
        filtered_events = [
            event for event in filtered_events
            if (search_lower in event.name.lower() or 
                search_lower in event.description.lower())
        ]
    
    # Apply location filter
    if location:
        location_lower = location.lower()
        filtered_events = [
            event for event in filtered_events
            if location_lower in event.location.lower()
        ]
    
    # Apply date filters
    if date_from:
        try:
            from_date = datetime.strptime(date_from, "%Y-%m-%d").date()
            filtered_events = [
                event for event in filtered_events
                if event.date >= from_date
            ]
        except ValueError:
            pass
    
    if date_to:
        try:
            to_date = datetime.strptime(date_to, "%Y-%m-%d").date()
            filtered_events = [
                event for event in filtered_events
                if event.date <= to_date
            ]
        except ValueError:
            pass
    
    # Apply pagination
    total = len(filtered_events)
    events = filtered_events[skip:skip + limit]
    
    return MockEventsResponse(events=events, total=total)