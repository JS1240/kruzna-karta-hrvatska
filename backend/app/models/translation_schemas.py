from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any


# Language Schemas
class LanguageBase(BaseModel):
    code: str = Field(..., max_length=10, description="Language code (e.g., 'hr', 'en')")
    name: str = Field(..., max_length=100, description="Language name in English")
    native_name: str = Field(..., max_length=100, description="Language name in native language")
    flag_emoji: Optional[str] = Field(None, max_length=10, description="Flag emoji")
    rtl: Optional[bool] = Field(default=False, description="Right-to-left language")


class LanguageCreate(LanguageBase):
    is_active: Optional[bool] = Field(default=True)
    is_default: Optional[bool] = Field(default=False)


class LanguageUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    native_name: Optional[str] = Field(None, max_length=100)
    flag_emoji: Optional[str] = Field(None, max_length=10)
    rtl: Optional[bool] = None
    is_active: Optional[bool] = None
    is_default: Optional[bool] = None


class Language(LanguageBase):
    id: int
    is_active: bool
    is_default: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Translation Base Schemas
class TranslationQuality(BaseModel):
    translation_quality: str = Field(default='pending', description="Translation quality status")
    is_machine_translated: bool = Field(default=False, description="Whether translation was machine-generated")
    translated_by: Optional[int] = Field(None, description="ID of user who translated")
    reviewed_by: Optional[int] = Field(None, description="ID of user who reviewed")


# Event Translation Schemas
class EventTranslationBase(BaseModel):
    name: str = Field(..., max_length=500, description="Translated event name")
    description: Optional[str] = Field(None, description="Translated event description")
    location: Optional[str] = Field(None, max_length=500, description="Translated location name")
    organizer: Optional[str] = Field(None, max_length=255, description="Translated organizer name")
    slug: Optional[str] = Field(None, max_length=600, description="SEO-friendly URL slug")
    meta_title: Optional[str] = Field(None, max_length=200, description="SEO meta title")
    meta_description: Optional[str] = Field(None, max_length=300, description="SEO meta description")


class EventTranslationCreate(EventTranslationBase):
    language_code: str = Field(..., max_length=10, description="Target language code")
    is_machine_translated: Optional[bool] = Field(default=False)


class EventTranslationUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    location: Optional[str] = Field(None, max_length=500)
    organizer: Optional[str] = Field(None, max_length=255)
    slug: Optional[str] = Field(None, max_length=600)
    meta_title: Optional[str] = Field(None, max_length=200)
    meta_description: Optional[str] = Field(None, max_length=300)
    translation_quality: Optional[str] = Field(None, description="pending, reviewed, approved")


class EventTranslation(EventTranslationBase, TranslationQuality):
    id: int
    event_id: int
    language_code: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Category Translation Schemas
class CategoryTranslationBase(BaseModel):
    name: str = Field(..., max_length=100, description="Translated category name")
    description: Optional[str] = Field(None, description="Translated category description")
    slug: Optional[str] = Field(None, max_length=100, description="Translated URL slug")


class CategoryTranslationCreate(CategoryTranslationBase):
    language_code: str = Field(..., max_length=10, description="Target language code")
    is_machine_translated: Optional[bool] = Field(default=False)


class CategoryTranslationUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    slug: Optional[str] = Field(None, max_length=100)
    translation_quality: Optional[str] = Field(None, description="pending, reviewed, approved")


class CategoryTranslation(CategoryTranslationBase, TranslationQuality):
    id: int
    category_id: int
    language_code: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Venue Translation Schemas
class VenueTranslationBase(BaseModel):
    name: str = Field(..., max_length=255, description="Translated venue name")
    address: Optional[str] = Field(None, description="Translated venue address")
    description: Optional[str] = Field(None, description="Translated venue description")


class VenueTranslationCreate(VenueTranslationBase):
    language_code: str = Field(..., max_length=10, description="Target language code")
    is_machine_translated: Optional[bool] = Field(default=False)


class VenueTranslationUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    address: Optional[str] = None
    description: Optional[str] = None
    translation_quality: Optional[str] = Field(None, description="pending, reviewed, approved")


class VenueTranslation(VenueTranslationBase, TranslationQuality):
    id: int
    venue_id: int
    language_code: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Static Content Translation Schemas
class StaticContentTranslationBase(BaseModel):
    key: str = Field(..., max_length=200, description="Translation key")
    value: str = Field(..., description="Translated content")
    context: Optional[str] = Field(None, max_length=100, description="Context for translators")


class StaticContentTranslationCreate(StaticContentTranslationBase):
    language_code: str = Field(..., max_length=10, description="Target language code")
    is_machine_translated: Optional[bool] = Field(default=False)


class StaticContentTranslationUpdate(BaseModel):
    value: Optional[str] = None
    context: Optional[str] = Field(None, max_length=100)
    translation_quality: Optional[str] = Field(None, description="pending, reviewed, approved")


class StaticContentTranslation(StaticContentTranslationBase, TranslationQuality):
    id: int
    language_code: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Bulk Translation Schemas
class BulkTranslationRequest(BaseModel):
    source_language: str = Field(..., description="Source language code")
    target_language: str = Field(..., description="Target language code")
    entity_type: str = Field(..., description="Type: 'event', 'category', 'venue'")
    entity_ids: List[int] = Field(..., description="List of entity IDs to translate")
    use_machine_translation: Optional[bool] = Field(default=True)


class BulkTranslationResponse(BaseModel):
    processed: int
    successful: int
    failed: int
    errors: List[str]


# Response Schemas with Translations
class TranslatedEvent(BaseModel):
    """Event with applied translations"""
    id: int
    name: str
    description: Optional[str] = None
    location: str
    organizer: Optional[str] = None
    slug: Optional[str] = None
    
    # Original fields
    time: str
    date: str
    price: Optional[str] = None
    link: Optional[str] = None
    image: Optional[str] = None
    category_id: Optional[int] = None
    venue_id: Optional[int] = None
    
    # Translation metadata
    translation_quality: Optional[str] = None
    is_machine_translated: Optional[bool] = None
    
    class Config:
        from_attributes = True


class TranslatedCategory(BaseModel):
    """Category with applied translations"""
    id: int
    name: str
    description: Optional[str] = None
    slug: str
    color: str
    icon: Optional[str] = None
    
    # Translation metadata
    translation_quality: Optional[str] = None
    is_machine_translated: Optional[bool] = None
    
    class Config:
        from_attributes = True


class TranslatedVenue(BaseModel):
    """Venue with applied translations"""
    id: int
    name: str
    address: Optional[str] = None
    description: Optional[str] = None
    city: str
    country: str
    
    # Original fields
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    capacity: Optional[int] = None
    venue_type: Optional[str] = None
    
    # Translation metadata
    translation_quality: Optional[str] = None
    is_machine_translated: Optional[bool] = None
    
    class Config:
        from_attributes = True


# Language Response Schemas
class LanguageResponse(BaseModel):
    languages: List[Language]
    total: int


class TranslationStatsResponse(BaseModel):
    language_code: str
    events_translated: int
    categories_translated: int
    venues_translated: int
    static_content_translated: int
    total_translated: int
    translation_completion_percentage: float


class TranslationStatusResponse(BaseModel):
    entity_type: str
    entity_id: int
    translations: List[Dict[str, Any]]  # Language code -> translation status
    completion_percentage: float
    missing_languages: List[str]