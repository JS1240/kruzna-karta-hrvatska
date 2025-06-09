from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..models.category import EventCategory
from ..models.schemas import (
    CategoryResponse,
)
from ..models.schemas import EventCategory as CategorySchema
from ..models.schemas import (
    EventCategoryCreate,
    EventCategoryUpdate,
)

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("/", response_model=CategoryResponse)
def get_categories(
    search: Optional[str] = Query(None, description="Search categories by name"),
    db: Session = Depends(get_db),
):
    """Get all event categories."""
    query = db.query(EventCategory)

    if search:
        query = query.filter(EventCategory.name.ilike(f"%{search}%"))

    categories = query.order_by(EventCategory.name.asc()).all()

    return CategoryResponse(categories=categories, total=len(categories))


@router.get("/{category_id}", response_model=CategorySchema)
def get_category(category_id: int, db: Session = Depends(get_db)):
    """Get a specific category by ID."""
    category = db.query(EventCategory).filter(EventCategory.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


@router.get("/slug/{slug}", response_model=CategorySchema)
def get_category_by_slug(slug: str, db: Session = Depends(get_db)):
    """Get a specific category by slug."""
    category = db.query(EventCategory).filter(EventCategory.slug == slug).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


@router.post("/", response_model=CategorySchema)
def create_category(category: EventCategoryCreate, db: Session = Depends(get_db)):
    """Create a new event category."""
    # Check if slug already exists
    existing = (
        db.query(EventCategory).filter(EventCategory.slug == category.slug).first()
    )
    if existing:
        raise HTTPException(
            status_code=400, detail="Category with this slug already exists"
        )

    db_category = EventCategory(**category.model_dump())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category


@router.put("/{category_id}", response_model=CategorySchema)
def update_category(
    category_id: int, category: EventCategoryUpdate, db: Session = Depends(get_db)
):
    """Update an existing category."""
    db_category = (
        db.query(EventCategory).filter(EventCategory.id == category_id).first()
    )
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")

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
            raise HTTPException(
                status_code=400, detail="Category with this slug already exists"
            )

    # Update only provided fields
    for field, value in update_data.items():
        setattr(db_category, field, value)

    db.commit()
    db.refresh(db_category)
    return db_category


@router.delete("/{category_id}")
def delete_category(category_id: int, db: Session = Depends(get_db)):
    """Delete a category."""
    db_category = (
        db.query(EventCategory).filter(EventCategory.id == category_id).first()
    )
    if not db_category:
        raise HTTPException(status_code=404, detail="Category not found")

    # Check if category has events
    from ..models.event import Event

    events_count = db.query(Event).filter(Event.category_id == category_id).count()
    if events_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete category. It has {events_count} associated events.",
        )

    db.delete(db_category)
    db.commit()
    return {"message": "Category deleted successfully"}


@router.get("/{category_id}/events")
def get_category_events(
    category_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Get all events for a specific category."""
    # Import here to avoid circular imports
    from .events import get_events

    # Verify category exists
    category = db.query(EventCategory).filter(EventCategory.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    return get_events(category_id=category_id, page=page, size=size, db=db)
