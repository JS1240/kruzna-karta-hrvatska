from typing import Dict, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.error_handlers import (
    CategoryNotFoundError,
    ResourceAlreadyExistsError,
    CannotDeleteReferencedEntityError
)
from app.models.category import EventCategory
from app.models.schemas import (
    CategoryResponse,
    EventResponse,
)
from app.models.schemas import EventCategory as CategorySchema
from app.models.schemas import (
    EventCategoryCreate,
    EventCategoryUpdate,
)

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("/", response_model=CategoryResponse)
def get_categories(
    search: Optional[str] = Query(None, description="Search categories by name"),
    db: Session = Depends(get_db),
) -> CategoryResponse:
    """Get all event categories with optional search filtering.
    
    Retrieves a complete list of event categories available in the system.
    Categories are used to classify events (e.g., concerts, sports, theater)
    and enable users to filter event listings by type. Supports optional
    text-based search for finding specific categories.
    
    Args:
        search: Optional search query to filter categories by name (case-insensitive)
        db: Database session dependency (automatically injected)
        
    Returns:
        CategoryResponse: Response containing:
            - categories: List of EventCategory objects with full details
                (id, name, slug, description, color, icon, etc.)
            - total: Total number of categories returned
            
    Note:
        Categories are sorted alphabetically by name for consistent presentation.
        This endpoint does not use pagination as the number of categories is
        typically small (10-50 categories).
    """
    query = db.query(EventCategory)

    if search:
        query = query.filter(EventCategory.name.ilike(f"%{search}%"))

    categories = query.order_by(EventCategory.name.asc()).all()

    return CategoryResponse(categories=categories, total=len(categories))


@router.get("/{category_id}", response_model=CategorySchema)
def get_category(category_id: int, db: Session = Depends(get_db)) -> CategorySchema:
    """Get a specific event category by its unique ID.
    
    Retrieves detailed information for a single category using its numeric
    identifier. Useful for displaying category details, editing forms, or
    when you have a category ID from another API response.
    
    Args:
        category_id: Unique numeric identifier of the category to retrieve
        db: Database session dependency (automatically injected)
        
    Returns:
        CategorySchema: Complete category object containing:
            - id: Unique category identifier
            - name: Display name of the category
            - slug: URL-friendly identifier for the category
            - description: Detailed category description
            - color: Associated color for UI theming
            - icon: Icon identifier for visual representation
            
    Raises:
        CategoryNotFoundError: If category with given ID is not found
    """
    category = db.query(EventCategory).filter(EventCategory.id == category_id).first()
    if not category:
        raise CategoryNotFoundError(category_id)
    return category


@router.get("/slug/{slug}", response_model=CategorySchema)
def get_category_by_slug(slug: str, db: Session = Depends(get_db)) -> CategorySchema:
    """Get a specific event category by its URL-friendly slug.
    
    Retrieves category information using the slug identifier, which is the
    URL-friendly version of the category name. Slugs are used in clean URLs
    and are more user-friendly than numeric IDs for public-facing routes.
    
    Args:
        slug: URL-friendly string identifier of the category (e.g., "concerts", "sports")
        db: Database session dependency (automatically injected)
        
    Returns:
        CategorySchema: Complete category object with the same structure as get_category:
            - id: Unique category identifier
            - name: Display name of the category
            - slug: URL-friendly identifier (matches the input parameter)
            - description: Detailed category description
            - color: Associated color for UI theming
            - icon: Icon identifier for visual representation
            
    Raises:
        CategoryNotFoundError: If category with given slug is not found
    """
    category = db.query(EventCategory).filter(EventCategory.slug == slug).first()
    if not category:
        raise CategoryNotFoundError(slug, by_slug=True)
    return category


@router.post("/", response_model=CategorySchema)
def create_category(category: EventCategoryCreate, db: Session = Depends(get_db)) -> CategorySchema:
    """Create a new event category in the system.
    
    Administrative endpoint for adding new event categories. Categories are used
    to classify events and help users filter event listings. Each category must
    have a unique slug for URL-friendly identification.
    
    Args:
        category: EventCategoryCreate object containing category details:
            - name: Display name of the category (required)
            - slug: URL-friendly identifier (required, must be unique)
            - description: Detailed description of the category
            - color: Hex color code for UI theming
            - icon: Icon identifier for visual representation
        db: Database session dependency (automatically injected)
        
    Returns:
        CategorySchema: The newly created category with generated ID and timestamps
        
    Raises:
        ResourceAlreadyExistsError: If a category with the same slug already exists
    """
    # Check if slug already exists
    existing = (
        db.query(EventCategory).filter(EventCategory.slug == category.slug).first()
    )
    if existing:
        raise ResourceAlreadyExistsError("Category", "slug", category.slug)

    db_category = EventCategory(**category.model_dump())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category


@router.put("/{category_id}", response_model=CategorySchema)
def update_category(
    category_id: int, category: EventCategoryUpdate, db: Session = Depends(get_db)
) -> CategorySchema:
    """Update an existing category."""
    db_category = (
        db.query(EventCategory).filter(EventCategory.id == category_id).first()
    )
    if not db_category:
        raise CategoryNotFoundError(category_id)

    # Check if new slug conflicts with existing category
    update_data = category.model_dump(exclude_unset=True)
    if "slug" in update_data:
        existing = (
            db.query(EventCategory)
            .filter(
                EventCategory.slug == update_data["slug"],
                EventCategory.id != category_id,
            )
            .first()
        )
        if existing:
            raise ResourceAlreadyExistsError("Category", "slug", update_data["slug"])

    # Update only provided fields
    for field, value in update_data.items():
        setattr(db_category, field, value)

    db.commit()
    db.refresh(db_category)
    return db_category


@router.delete("/{category_id}")
def delete_category(category_id: int, db: Session = Depends(get_db)) -> Dict[str, str]:
    """Delete an event category from the system.
    
    Administrative endpoint for removing categories. Before deletion, the system
    checks if any events are associated with this category and prevents deletion
    if events exist to maintain data integrity.
    
    Args:
        category_id: Unique identifier of the category to delete
        db: Database session dependency (automatically injected)
        
    Returns:
        Dict containing confirmation message:
            - message: "Category deleted successfully"
            
    Raises:
        CategoryNotFoundError: If category with given ID is not found
        CannotDeleteReferencedEntityError: If category has associated events and cannot be deleted
    """
    db_category = (
        db.query(EventCategory).filter(EventCategory.id == category_id).first()
    )
    if not db_category:
        raise CategoryNotFoundError(category_id)

    # Check if category has events
    from app.models.event import Event

    events_count = db.query(Event).filter(Event.category_id == category_id).count()
    if events_count > 0:
        raise CannotDeleteReferencedEntityError("category", category_id, events_count, "events")

    db.delete(db_category)
    db.commit()
    return {"message": "Category deleted successfully"}


@router.get("/{category_id}/events")
def get_category_events(
    category_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> EventResponse:
    """Get all events for a specific category."""
    # Import here to avoid circular imports
    from app.routes.events import get_events

    # Verify category exists
    category = db.query(EventCategory).filter(EventCategory.id == category_id).first()
    if not category:
        raise CategoryNotFoundError(category_id)

    return get_events(category_id=category_id, page=page, size=size, db=db)
