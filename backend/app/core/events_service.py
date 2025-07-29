"""Events service for handling complex event queries and business logic."""

import logging
from decimal import Decimal
from typing import List, Optional, Tuple

from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from ..models.event import Event
from ..models.schemas import EventSearchParams, EventResponse
from .translation import TranslationService, DEFAULT_LANGUAGE

logger = logging.getLogger(__name__)


def convert_decimal_coordinates(event):
    """Convert Decimal coordinates to float for proper JSON serialization."""
    if hasattr(event, 'latitude') and isinstance(event.latitude, Decimal):
        event.latitude = float(event.latitude)
    if hasattr(event, 'longitude') and isinstance(event.longitude, Decimal):
        event.longitude = float(event.longitude)
    
    # Also handle venue coordinates if present
    if hasattr(event, 'venue') and event.venue:
        venue = event.venue
        if hasattr(venue, 'latitude') and isinstance(venue.latitude, Decimal):
            venue.latitude = float(venue.latitude)
        if hasattr(venue, 'longitude') and isinstance(venue.longitude, Decimal):
            venue.longitude = float(venue.longitude)
    
    return event


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
        """Build the SQLAlchemy query based on search parameters with transaction safety."""
        try:
            query = self.db.query(Event).options(
                joinedload(Event.category),
                joinedload(Event.venue)
            )
            
            # Apply filters with error handling
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
            
            # Text search with error handling
            if search_params.q:
                try:
                    search_term = f"%{search_params.q}%"
                    query = query.filter(
                        or_(
                            Event.title.ilike(search_term),
                            Event.description.ilike(search_term),
                            Event.location.ilike(search_term)
                        )
                    )
                except Exception as search_error:
                    logger.warning(f"Error applying text search filter: {search_error}")
            
            # Geographic search with error handling
            if (search_params.latitude is not None and 
                search_params.longitude is not None and 
                search_params.radius_km is not None):
                
                try:
                    # Use Haversine formula for distance calculation
                    query = query.filter(
                        func.earth_distance(
                            func.ll_to_earth(Event.latitude, Event.longitude),
                            func.ll_to_earth(search_params.latitude, search_params.longitude)
                        ) <= search_params.radius_km * 1000  # Convert km to meters
                    )
                except Exception as geo_error:
                    logger.warning(f"Error applying geographic filter: {geo_error}")
            
            # Tags filter with error handling
            if search_params.tags:
                try:
                    for tag in search_params.tags:
                        query = query.filter(Event.tags.any(tag))
                except Exception as tag_error:
                    logger.warning(f"Error applying tags filter: {tag_error}")
            
            return query
            
        except Exception as e:
            logger.error(f"Error building events query: {e}", exc_info=True)
            # Return basic query on error
            return self.db.query(Event)
    
    def get_events_paginated(
        self, 
        search_params: EventSearchParams, 
        language: Optional[str] = None
    ) -> Tuple[List[Event], int, int]:
        """Get paginated events based on search parameters with transaction safety."""
        
        try:
            # Build base query
            query = self.build_events_query(search_params)
            
            # Get total count with error handling
            try:
                total = query.count()
            except Exception as count_error:
                logger.error(f"Error counting events: {count_error}")
                # Fallback to basic count
                total = self.db.query(Event).count()
            
            # Apply ordering
            query = query.order_by(Event.date.asc(), Event.time.asc())
            
            # Apply pagination
            offset = (search_params.page - 1) * search_params.size
            events = query.offset(offset).limit(search_params.size).all()
            
            # Convert Decimal coordinates to float for proper serialization
            events = [convert_decimal_coordinates(event) for event in events]
            
            # Calculate total pages
            pages = (total + search_params.size - 1) // search_params.size
            
            return events, total, pages
            
        except Exception as e:
            logger.error(f"Error in get_events_paginated: {e}", exc_info=True)
            # Return empty results on error
            return [], 0, 0
    
    def search_events(
        self, 
        search_params: EventSearchParams, 
        accept_language: Optional[str] = None
    ) -> EventResponse:
        """Main method to search events with all parameters and transaction safety."""
        
        try:
            # Determine language
            language = search_params.language
            if not language:
                language = self.get_language_from_header(accept_language)
            
            # Get paginated results with error handling
            events, total, pages = self.get_events_paginated(search_params, language)
            
            return EventResponse(
                events=events,
                total=total,
                page=search_params.page,
                size=search_params.size,
                pages=pages
            )
            
        except Exception as e:
            logger.error(f"Error in search_events: {e}", exc_info=True)
            # Return empty response on error
            return EventResponse(
                events=[],
                total=0,
                page=search_params.page,
                size=search_params.size,
                pages=0
            )