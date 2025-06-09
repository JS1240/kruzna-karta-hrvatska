from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session

from ..core.auth import get_current_superuser, get_current_user
from ..core.database import get_db
from ..core.translation import (
    DEFAULT_LANGUAGE,
    TranslationService,
    get_translation_service,
)
from ..models.translation import Language
from ..models.translation_schemas import (
    BulkTranslationRequest,
    BulkTranslationResponse,
    CategoryTranslation,
    CategoryTranslationCreate,
    CategoryTranslationUpdate,
    EventTranslation,
    EventTranslationCreate,
    EventTranslationUpdate,
)
from ..models.translation_schemas import Language as LanguageSchema
from ..models.translation_schemas import (
    LanguageCreate,
    LanguageResponse,
    LanguageUpdate,
    StaticContentTranslation,
    StaticContentTranslationCreate,
    StaticContentTranslationUpdate,
    TranslationStatsResponse,
    TranslationStatusResponse,
    VenueTranslation,
    VenueTranslationCreate,
    VenueTranslationUpdate,
)
from ..models.user import User

router = APIRouter(prefix="/translations", tags=["translations"])


def get_language_from_header(accept_language: Optional[str] = Header(None)) -> str:
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


# Language Management Endpoints
@router.get("/languages", response_model=LanguageResponse)
def get_languages(db: Session = Depends(get_db)):
    """Get all supported languages."""
    languages = (
        db.query(Language)
        .filter(Language.is_active == True)
        .order_by(Language.is_default.desc(), Language.name.asc())
        .all()
    )
    return LanguageResponse(languages=languages, total=len(languages))


@router.post("/languages", response_model=LanguageSchema)
def create_language(
    language: LanguageCreate,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db),
):
    """Create a new language (admin only)."""
    # Check if language code already exists
    existing = db.query(Language).filter(Language.code == language.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Language code already exists")

    # If this is set as default, unset other defaults
    if language.is_default:
        db.query(Language).filter(Language.is_default == True).update(
            {"is_default": False}
        )

    db_language = Language(**language.model_dump())
    db.add(db_language)
    db.commit()
    db.refresh(db_language)

    return db_language


@router.put("/languages/{language_code}", response_model=LanguageSchema)
def update_language(
    language_code: str,
    language_update: LanguageUpdate,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db),
):
    """Update language settings (admin only)."""
    language = db.query(Language).filter(Language.code == language_code).first()
    if not language:
        raise HTTPException(status_code=404, detail="Language not found")

    update_data = language_update.model_dump(exclude_unset=True)

    # If setting as default, unset other defaults
    if update_data.get("is_default"):
        db.query(Language).filter(Language.is_default == True).update(
            {"is_default": False}
        )

    for field, value in update_data.items():
        setattr(language, field, value)

    db.commit()
    db.refresh(language)

    return language


# Event Translation Endpoints
@router.get("/events/{event_id}/translations", response_model=None)
def get_event_translations(
    event_id: int,
    db: Session = Depends(get_db),
    translation_service: TranslationService = Depends(get_translation_service),
):
    """Get all translations for an event."""
    from ..models.event import Event

    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    translations = {}
    languages = translation_service.get_supported_languages()

    for language in languages:
        translation = translation_service.get_event_translation(event_id, language.code)
        if translation:
            translations[language.code] = {
                "name": translation.name,
                "description": translation.description,
                "location": translation.location,
                "organizer": translation.organizer,
                "translation_quality": translation.translation_quality,
                "is_machine_translated": translation.is_machine_translated,
                "updated_at": translation.updated_at,
            }
        else:
            translations[language.code] = None

    return {"event_id": event_id, "translations": translations}


@router.post("/events/{event_id}/translations", response_model=EventTranslation)
def create_event_translation(
    event_id: int,
    translation: EventTranslationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    translation_service: TranslationService = Depends(get_translation_service),
):
    """Create or update event translation."""
    from ..models.event import Event

    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")

    # Verify language exists
    language = translation_service.get_language(translation.language_code)
    if not language:
        raise HTTPException(status_code=400, detail="Unsupported language")

    result = translation_service.create_event_translation(
        event_id=event_id,
        language_code=translation.language_code,
        name=translation.name,
        description=translation.description,
        location=translation.location,
        organizer=translation.organizer,
        translated_by=current_user.id,
        is_machine_translated=translation.is_machine_translated,
    )

    return result


@router.put(
    "/events/{event_id}/translations/{language_code}", response_model=EventTranslation
)
def update_event_translation(
    event_id: int,
    language_code: str,
    translation_update: EventTranslationUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    translation_service: TranslationService = Depends(get_translation_service),
):
    """Update event translation."""
    translation = translation_service.get_event_translation(event_id, language_code)
    if not translation:
        raise HTTPException(status_code=404, detail="Translation not found")

    update_data = translation_update.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        setattr(translation, field, value)

    # Track who reviewed the translation
    if (
        "translation_quality" in update_data
        and update_data["translation_quality"] == "reviewed"
    ):
        translation.reviewed_by = current_user.id

    db.commit()
    db.refresh(translation)

    return translation


# Category Translation Endpoints
@router.get("/categories/{category_id}/translations")
def get_category_translations(
    category_id: int,
    db: Session = Depends(get_db),
    translation_service: TranslationService = Depends(get_translation_service),
):
    """Get all translations for a category."""
    from ..models.category import EventCategory

    category = db.query(EventCategory).filter(EventCategory.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    translations = {}
    languages = translation_service.get_supported_languages()

    for language in languages:
        translation = translation_service.get_category_translation(
            category_id, language.code
        )
        if translation:
            translations[language.code] = {
                "name": translation.name,
                "description": translation.description,
                "slug": translation.slug,
                "translation_quality": translation.translation_quality,
                "is_machine_translated": translation.is_machine_translated,
                "updated_at": translation.updated_at,
            }
        else:
            translations[language.code] = None

    return {"category_id": category_id, "translations": translations}


@router.post(
    "/categories/{category_id}/translations", response_model=CategoryTranslation
)
def create_category_translation(
    category_id: int,
    translation: CategoryTranslationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    translation_service: TranslationService = Depends(get_translation_service),
):
    """Create or update category translation."""
    from ..models.category import EventCategory

    category = db.query(EventCategory).filter(EventCategory.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    language = translation_service.get_language(translation.language_code)
    if not language:
        raise HTTPException(status_code=400, detail="Unsupported language")

    result = translation_service.create_category_translation(
        category_id=category_id,
        language_code=translation.language_code,
        name=translation.name,
        description=translation.description,
        slug=translation.slug,
        translated_by=current_user.id,
        is_machine_translated=translation.is_machine_translated,
    )

    return result


# Static Content Translation Endpoints
@router.get("/static/{key}")
def get_static_content_translations(
    key: str,
    language: Optional[str] = Query(None, description="Language code"),
    accept_language: Optional[str] = Header(None),
    db: Session = Depends(get_db),
    translation_service: TranslationService = Depends(get_translation_service),
):
    """Get static content translation."""
    if not language:
        language = get_language_from_header(accept_language)

    content = translation_service.get_static_content(key, language)
    if content is None:
        raise HTTPException(status_code=404, detail="Translation not found")

    return {"key": key, "language": language, "content": content}


@router.post("/static", response_model=StaticContentTranslation)
def create_static_content_translation(
    translation: StaticContentTranslationCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    translation_service: TranslationService = Depends(get_translation_service),
):
    """Create or update static content translation."""
    language = translation_service.get_language(translation.language_code)
    if not language:
        raise HTTPException(status_code=400, detail="Unsupported language")

    result = translation_service.set_static_content(
        key=translation.key,
        language_code=translation.language_code,
        value=translation.value,
        context=translation.context,
        translated_by=current_user.id,
        is_machine_translated=translation.is_machine_translated,
    )

    return result


# Bulk Translation Endpoints
@router.post("/bulk", response_model=BulkTranslationResponse)
def bulk_translate(
    request: BulkTranslationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    translation_service: TranslationService = Depends(get_translation_service),
):
    """Bulk translate entities (placeholder for machine translation integration)."""
    # This would integrate with translation services like Google Translate, DeepL, etc.
    # For now, return a placeholder response

    processed = len(request.entity_ids)
    successful = 0
    failed = 0
    errors = []

    # TODO: Implement actual bulk translation logic
    errors.append("Bulk translation not yet implemented. Please translate manually.")
    failed = processed

    return BulkTranslationResponse(
        processed=processed, successful=successful, failed=failed, errors=errors
    )


# Translation Statistics
@router.get("/stats/{language_code}", response_model=TranslationStatsResponse)
def get_translation_stats(
    language_code: str,
    db: Session = Depends(get_db),
    translation_service: TranslationService = Depends(get_translation_service),
):
    """Get translation statistics for a language."""
    from ..models.category import EventCategory
    from ..models.event import Event
    from ..models.translation import (
        CategoryTranslation,
        EventTranslation,
        StaticContentTranslation,
        VenueTranslation,
    )
    from ..models.venue import Venue

    # Count translations
    events_translated = (
        db.query(EventTranslation)
        .filter(EventTranslation.language_code == language_code)
        .count()
    )
    categories_translated = (
        db.query(CategoryTranslation)
        .filter(CategoryTranslation.language_code == language_code)
        .count()
    )
    venues_translated = (
        db.query(VenueTranslation)
        .filter(VenueTranslation.language_code == language_code)
        .count()
    )
    static_content_translated = (
        db.query(StaticContentTranslation)
        .filter(StaticContentTranslation.language_code == language_code)
        .count()
    )

    # Count total entities
    total_events = db.query(Event).count()
    total_categories = db.query(EventCategory).count()
    total_venues = db.query(Venue).count()

    total_translated = (
        events_translated
        + categories_translated
        + venues_translated
        + static_content_translated
    )
    total_entities = total_events + total_categories + total_venues

    completion_percentage = (
        (total_translated / total_entities * 100) if total_entities > 0 else 0
    )

    return TranslationStatsResponse(
        language_code=language_code,
        events_translated=events_translated,
        categories_translated=categories_translated,
        venues_translated=venues_translated,
        static_content_translated=static_content_translated,
        total_translated=total_translated,
        translation_completion_percentage=completion_percentage,
    )
