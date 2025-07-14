"""Events service for handling complex event queries and business logic."""

import logging
from typing import List, Optional, Tuple

from sqlalchemy import and_, func, or_, text
from sqlalchemy.orm import Session, joinedload

from ..models.event import Event
from ..models.category import EventCategory
from ..models.venue import Venue
from ..models.schemas import EventSearchParams, EventResponse
from .translation import TranslationService, DEFAULT_LANGUAGE

logger = logging.getLogger(__name__)


class EventsService:
    """Service class for handling event-related operations."""
    
    def __init__(self, db: Session, translation_service: Optional[TranslationService] = None):
        self.db = db
        self.translation_service = translation_service
    
    def get_language_from_header(self, accept_language: Optional[str]) -> str:
        """Extract language preference from Accept-Language header."""
        if accept_language:
            # Parse Accept-Language header (e.g., "hr,en;q=0.9,de;q=0.8")
            languages = []
            for lang_part in accept_language.split(","):
                lang = lang_part.split(";")[0].strip()
                if len(lang) == 2:  # Only accept 2-letter codes
                    languages.append(lang)

            # Return first supported language
            supported = ["hr", "en", "de", "it", "sl"]
            for lang in languages:
                if lang in supported:
                    return lang

        return DEFAULT_LANGUAGE
    
    def build_events_query(self, search_params: EventSearchParams):
        """Build the SQLAlchemy query based on search parameters."""
        query = self.db.query(Event).options(
            joinedload(Event.category),
            joinedload(Event.venue)
        )
        
        # Apply filters
        if search_params.category_id:
            query = query.filter(Event.category_id == search_params.category_id)
        
        if search_params.venue_id:
            query = query.filter(Event.venue_id == search_params.venue_id)
        
        if search_params.city:
            query = query.filter(Event.location.ilike(f"%{search_params.city}%"))
        
        if search_params.date_from:
            query = query.filter(Event.date >= search_params.date_from)
        
        if search_params.date_to:
            query = query.filter(Event.date <= search_params.date_to)
        
        if search_params.is_featured is not None:
            query = query.filter(Event.is_featured == search_params.is_featured)
        
        if search_params.event_status:
            query = query.filter(Event.event_status == search_params.event_status)
        
        # Text search
        if search_params.q:
            search_term = f"%{search_params.q}%"
            query = query.filter(
                or_(
                    Event.title.ilike(search_term),
                    Event.description.ilike(search_term),
                    Event.location.ilike(search_term)
                )
            )
        
        # Geographic search
        if (search_params.latitude is not None and 
            search_params.longitude is not None and 
            search_params.radius_km is not None):
            
            # Use Haversine formula for distance calculation
            query = query.filter(
                func.earth_distance(
                    func.ll_to_earth(Event.latitude, Event.longitude),
                    func.ll_to_earth(search_params.latitude, search_params.longitude)
                ) <= search_params.radius_km * 1000  # Convert km to meters
            )
        
        # Tags filter (assuming tags are stored as array)
        if search_params.tags:
            for tag in search_params.tags:
                query = query.filter(Event.tags.any(tag))
        
        return query
    
    def get_events_paginated(
        self, 
        search_params: EventSearchParams, 
        language: Optional[str] = None
    ) -> Tuple[List[Event], int, int]:
        """Get paginated events based on search parameters."""
        
        # Build base query
        query = self.build_events_query(search_params)
        
        # Get total count
        total = query.count()
        
        # Apply ordering
        query = query.order_by(Event.date.asc(), Event.time.asc())
        
        # Apply pagination
        offset = (search_params.page - 1) * search_params.size
        events = query.offset(offset).limit(search_params.size).all()
        
        # Calculate total pages
        pages = (total + search_params.size - 1) // search_params.size
        
        return events, total, pages
    
    def search_events(
        self, 
        search_params: EventSearchParams, 
        accept_language: Optional[str] = None
    ) -> EventResponse:
        """Main method to search events with all parameters."""
        
        # Determine language
        language = search_params.language
        if not language:
            language = self.get_language_from_header(accept_language)
        
        # Get paginated results
        events, total, pages = self.get_events_paginated(search_params, language)
        
        return EventResponse(
            events=events,
            total=total,
            page=search_params.page,
            size=search_params.size,
            pages=pages
        )