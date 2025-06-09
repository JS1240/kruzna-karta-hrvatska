from typing import Dict, List, Optional, Union, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_
from fastapi import Depends
from ..core.database import get_db
from ..models.translation import (
    Language, EventTranslation, CategoryTranslation, 
    VenueTranslation, StaticContentTranslation
)
from ..models.event import Event
from ..models.category import EventCategory
from ..models.venue import Venue

# Supported languages for the Croatian platform
SUPPORTED_LANGUAGES = {
    'hr': {'name': 'Croatian', 'native_name': 'Hrvatski', 'flag': '🇭🇷', 'default': True},
    'en': {'name': 'English', 'native_name': 'English', 'flag': '🇬🇧', 'default': False},
    'de': {'name': 'German', 'native_name': 'Deutsch', 'flag': '🇩🇪', 'default': False},
    'it': {'name': 'Italian', 'native_name': 'Italiano', 'flag': '🇮🇹', 'default': False},
    'sl': {'name': 'Slovenian', 'native_name': 'Slovenščina', 'flag': '🇸🇮', 'default': False},
}

DEFAULT_LANGUAGE = 'hr'
FALLBACK_LANGUAGE = 'en'


class TranslationService:
    """Service for managing translations across the platform."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_supported_languages(self) -> List[Language]:
        """Get all supported languages."""
        return self.db.query(Language).filter(Language.is_active == True).all()
    
    def get_language(self, language_code: str) -> Optional[Language]:
        """Get language by code."""
        return self.db.query(Language).filter(Language.code == language_code).first()
    
    def get_default_language(self) -> Language:
        """Get the default language (Croatian)."""
        return self.db.query(Language).filter(Language.is_default == True).first()
    
    # Event Translation Methods
    def get_event_translation(self, event_id: int, language_code: str) -> Optional[EventTranslation]:
        """Get event translation for specific language."""
        return self.db.query(EventTranslation).filter(
            and_(
                EventTranslation.event_id == event_id,
                EventTranslation.language_code == language_code
            )
        ).first()
    
    def get_translated_event(self, event: Event, language_code: str) -> Dict[str, Any]:
        """Get event with translations applied."""
        translation = self.get_event_translation(event.id, language_code)
        
        # Start with original event data
        event_data = {
            'id': event.id,
            'name': event.name,
            'description': event.description,
            'location': event.location,
            'organizer': event.organizer,
            'slug': event.slug,
            # Include all other non-translatable fields
            'time': event.time,
            'date': event.date,
            'price': event.price,
            'link': event.link,
            'image': event.image,
            'category_id': event.category_id,
            'venue_id': event.venue_id,
            'latitude': event.latitude,
            'longitude': event.longitude,
            'source': event.source,
            'event_status': event.event_status,
            'is_featured': event.is_featured,
            'tags': event.tags,
            'created_at': event.created_at,
            'updated_at': event.updated_at,
        }
        
        # Apply translation if available
        if translation:
            event_data.update({
                'name': translation.name,
                'description': translation.description or event.description,
                'location': translation.location or event.location,
                'organizer': translation.organizer or event.organizer,
                'slug': translation.slug or event.slug,
                'translation_quality': translation.translation_quality,
                'is_machine_translated': translation.is_machine_translated,
            })
        
        return event_data
    
    def create_event_translation(
        self, 
        event_id: int, 
        language_code: str, 
        name: str,
        description: Optional[str] = None,
        location: Optional[str] = None,
        organizer: Optional[str] = None,
        translated_by: Optional[int] = None,
        is_machine_translated: bool = False
    ) -> EventTranslation:
        """Create or update event translation."""
        translation = self.get_event_translation(event_id, language_code)
        
        if translation:
            # Update existing translation
            translation.name = name
            translation.description = description
            translation.location = location
            translation.organizer = organizer
            if translated_by:
                translation.translated_by = translated_by
            translation.is_machine_translated = is_machine_translated
        else:
            # Create new translation
            translation = EventTranslation(
                event_id=event_id,
                language_code=language_code,
                name=name,
                description=description,
                location=location,
                organizer=organizer,
                translated_by=translated_by,
                is_machine_translated=is_machine_translated
            )
            self.db.add(translation)
        
        self.db.commit()
        self.db.refresh(translation)
        return translation
    
    # Category Translation Methods
    def get_category_translation(self, category_id: int, language_code: str) -> Optional[CategoryTranslation]:
        """Get category translation for specific language."""
        return self.db.query(CategoryTranslation).filter(
            and_(
                CategoryTranslation.category_id == category_id,
                CategoryTranslation.language_code == language_code
            )
        ).first()
    
    def get_translated_category(self, category: EventCategory, language_code: str) -> Dict[str, Any]:
        """Get category with translations applied."""
        translation = self.get_category_translation(category.id, language_code)
        
        category_data = {
            'id': category.id,
            'name': category.name,
            'description': category.description,
            'slug': category.slug,
            'color': category.color,
            'icon': category.icon,
            'created_at': category.created_at,
        }
        
        if translation:
            category_data.update({
                'name': translation.name,
                'description': translation.description or category.description,
                'slug': translation.slug or category.slug,
                'translation_quality': translation.translation_quality,
                'is_machine_translated': translation.is_machine_translated,
            })
        
        return category_data
    
    def create_category_translation(
        self,
        category_id: int,
        language_code: str,
        name: str,
        description: Optional[str] = None,
        slug: Optional[str] = None,
        translated_by: Optional[int] = None,
        is_machine_translated: bool = False
    ) -> CategoryTranslation:
        """Create or update category translation."""
        translation = self.get_category_translation(category_id, language_code)
        
        if translation:
            translation.name = name
            translation.description = description
            translation.slug = slug
            if translated_by:
                translation.translated_by = translated_by
            translation.is_machine_translated = is_machine_translated
        else:
            translation = CategoryTranslation(
                category_id=category_id,
                language_code=language_code,
                name=name,
                description=description,
                slug=slug,
                translated_by=translated_by,
                is_machine_translated=is_machine_translated
            )
            self.db.add(translation)
        
        self.db.commit()
        self.db.refresh(translation)
        return translation
    
    # Venue Translation Methods
    def get_venue_translation(self, venue_id: int, language_code: str) -> Optional[VenueTranslation]:
        """Get venue translation for specific language."""
        return self.db.query(VenueTranslation).filter(
            and_(
                VenueTranslation.venue_id == venue_id,
                VenueTranslation.language_code == language_code
            )
        ).first()
    
    def get_translated_venue(self, venue: Venue, language_code: str) -> Dict[str, Any]:
        """Get venue with translations applied."""
        translation = self.get_venue_translation(venue.id, language_code)
        
        venue_data = {
            'id': venue.id,
            'name': venue.name,
            'address': venue.address,
            'city': venue.city,
            'country': venue.country,
            'latitude': venue.latitude,
            'longitude': venue.longitude,
            'capacity': venue.capacity,
            'venue_type': venue.venue_type,
            'website': venue.website,
            'phone': venue.phone,
            'email': venue.email,
            'created_at': venue.created_at,
            'updated_at': venue.updated_at,
        }
        
        if translation:
            venue_data.update({
                'name': translation.name,
                'address': translation.address or venue.address,
                'description': translation.description,
                'translation_quality': translation.translation_quality,
                'is_machine_translated': translation.is_machine_translated,
            })
        
        return venue_data
    
    # Static Content Translation Methods
    def get_static_content(self, key: str, language_code: str, fallback: bool = True) -> Optional[str]:
        """Get translated static content."""
        translation = self.db.query(StaticContentTranslation).filter(
            and_(
                StaticContentTranslation.key == key,
                StaticContentTranslation.language_code == language_code
            )
        ).first()
        
        if translation:
            return translation.value
        
        # Fallback to English if Croatian translation not found
        if fallback and language_code != FALLBACK_LANGUAGE:
            return self.get_static_content(key, FALLBACK_LANGUAGE, fallback=False)
        
        return None
    
    def set_static_content(
        self,
        key: str,
        language_code: str,
        value: str,
        context: Optional[str] = None,
        translated_by: Optional[int] = None,
        is_machine_translated: bool = False
    ) -> StaticContentTranslation:
        """Set static content translation."""
        translation = self.db.query(StaticContentTranslation).filter(
            and_(
                StaticContentTranslation.key == key,
                StaticContentTranslation.language_code == language_code
            )
        ).first()
        
        if translation:
            translation.value = value
            translation.context = context
            if translated_by:
                translation.translated_by = translated_by
            translation.is_machine_translated = is_machine_translated
        else:
            translation = StaticContentTranslation(
                key=key,
                language_code=language_code,
                value=value,
                context=context,
                translated_by=translated_by,
                is_machine_translated=is_machine_translated
            )
            self.db.add(translation)
        
        self.db.commit()
        self.db.refresh(translation)
        return translation
    
    # Batch Translation Methods
    def get_events_with_translations(
        self, 
        events: List[Event], 
        language_code: str
    ) -> List[Dict[str, Any]]:
        """Get multiple events with translations applied."""
        return [self.get_translated_event(event, language_code) for event in events]
    
    def get_categories_with_translations(
        self, 
        categories: List[EventCategory], 
        language_code: str
    ) -> List[Dict[str, Any]]:
        """Get multiple categories with translations applied."""
        return [self.get_translated_category(category, language_code) for category in categories]
    
    def get_venues_with_translations(
        self, 
        venues: List[Venue], 
        language_code: str
    ) -> List[Dict[str, Any]]:
        """Get multiple venues with translations applied."""
        return [self.get_translated_venue(venue, language_code) for venue in venues]


def get_translation_service(db: Session = Depends(get_db)) -> TranslationService:
    """Dependency to get translation service."""
    return TranslationService(db)