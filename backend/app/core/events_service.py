"""Events service for handling complex event queries and business logic."""

import logging
from decimal import Decimal
from typing import Any, List, Optional, Tuple

from sqlalchemy import func, or_
from sqlalchemy.orm import Query, Session, joinedload

from app.models.event import Event
from app.models.schemas import EventSearchParams, EventResponse
from app.core.translation import TranslationService, DEFAULT_LANGUAGE

logger = logging.getLogger(__name__)


def convert_decimal_coordinates(event) -> Any:
    """Convert Decimal coordinates to float for proper JSON serialization.
    
    Utility function that ensures event and venue coordinates are properly
    converted from Decimal types to float for JSON API responses. This prevents
    serialization errors and ensures coordinates are in the correct format
    for frontend mapping libraries.
    
    Args:
        event: Event object with potential Decimal coordinate attributes
            (latitude, longitude) and optional venue with coordinates
            
    Returns:
        Any: The same event object with float coordinates for JSON serialization
        
    Note:
        This function modifies the event object in-place, converting both
        event-level coordinates and venue coordinates if present. Essential
        for proper API response formatting and frontend compatibility.
    """
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
        """Extract language preference from Accept-Language header.
        
        Parses the HTTP Accept-Language header to determine the user's preferred
        language for localized content. Supports quality values (q-factors) and
        returns the first supported language or defaults to Croatian (hr).
        
        Args:
            accept_language: HTTP Accept-Language header value (e.g., "hr,en;q=0.9,de;q=0.8")
                Can be None if header is not provided
                
        Returns:
            str: Two-letter language code from supported languages:
                - "hr": Croatian (default)
                - "en": English
                - "de": German
                - "it": Italian
                - "sl": Slovenian
                
        Note:
            The function parses comma-separated language preferences and ignores
            quality factors, returning the first match against supported languages.
            Falls back to DEFAULT_LANGUAGE if no supported language is found.
        """
        if accept_language:
            # Convert Header object to string if needed
            header_value = str(accept_language) if accept_language else None
            
            # Parse Accept-Language header (e.g., "hr,en;q=0.9,de;q=0.8")
            if header_value and header_value != "None":
                languages = []
                for lang_part in header_value.split(","):
                    lang = lang_part.split(";")[0].strip()
                    if len(lang) == 2:  # Only accept 2-letter codes
                        languages.append(lang)

                # Return first supported language
                supported = ["hr", "en", "de", "it", "sl"]
                for lang in languages:
                    if lang in supported:
                        return lang

        return DEFAULT_LANGUAGE
    
    def build_events_query(self, search_params: EventSearchParams) -> Query:
        """Build the SQLAlchemy query based on search parameters with transaction safety.
        
        Constructs a comprehensive SQLAlchemy query for event retrieval with multiple
        filter options including text search, geographic proximity, category/venue
        filtering, date ranges, and status filtering. Includes error handling for
        each filter type to ensure query resilience.
        
        Args:
            search_params: EventSearchParams object containing filter criteria:
                - q: Text search query for title, description, location
                - category_id: Filter by specific event category
                - venue_id: Filter by specific venue
                - city: Filter by city name (partial match)
                - date_from/date_to: Date range filtering
                - is_featured: Filter for featured events
                - event_status: Filter by status (e.g., "active")
                - latitude/longitude/radius_km: Geographic proximity search
                - tags: Filter by event tags
                
        Returns:
            Query: SQLAlchemy Query object with applied filters and eager loading
                for category and venue relationships
                
        Note:
            The method includes comprehensive error handling for each filter type,
            logging warnings for filter errors and continuing with remaining filters.
            Returns a basic query if query building fails completely.
        """
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
        """Get paginated events based on search parameters with transaction safety.
        
        Executes the event search query with pagination support, coordinate conversion,
        and comprehensive error handling. Orders results by date/time and converts
        Decimal coordinates to float for proper JSON serialization.
        
        Args:
            search_params: EventSearchParams object with search criteria and pagination:
                - page: Page number (1-based)
                - size: Number of items per page
                - All other search/filter parameters
            language: Optional language code for localized content (currently unused
                but reserved for future translation features)
                
        Returns:
            Tuple containing:
                - List[Event]: List of Event objects matching the search criteria
                - int: Total number of events matching the search (for pagination)
                - int: Total number of pages available
                
        Note:
            Events are ordered by date (ascending) then time (ascending) for chronological
            presentation. Includes fallback error handling that returns empty results
            if the query fails completely.
        """
        
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
        """Main method to search events with all parameters and transaction safety.
        
        Primary service method for event search operations, combining language detection,
        paginated querying, and response formatting. Provides the main business logic
        for the events API endpoints with comprehensive error handling.
        
        Args:
            search_params: Complete EventSearchParams object with all search criteria:
                - Search filters (q, category_id, venue_id, city, date ranges)
                - Geographic search (latitude, longitude, radius_km)
                - Status and feature filters (event_status, is_featured)
                - Pagination (page, size)
                - Optional language preference
            accept_language: HTTP Accept-Language header for automatic language detection
                Used when search_params.language is not specified
                
        Returns:
            EventResponse: Comprehensive response object containing:
                - events: List of Event objects matching search criteria
                - total: Total number of matching events across all pages
                - page: Current page number
                - size: Number of events returned in this response
                - pages: Total number of pages available for pagination
                
        Note:
            This method orchestrates the complete event search workflow including
            language detection, query building, pagination, and response formatting.
            Returns empty response with proper structure if search fails.
        """
        
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