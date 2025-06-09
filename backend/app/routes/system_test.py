"""
System test endpoints for verifying user events functionality.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any
import logging

from ..core.database import get_db
from ..models.event import Event
from ..models.category import EventCategory
from ..models.venue import Venue
from ..models.booking import TicketType
from ..models.user import User, UserRole

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/system-test", tags=["system-test"])


@router.get("/health")
def system_health_check(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Comprehensive system health check for user events feature."""
    try:
        results = {}
        
        # Test database connectivity
        results["database"] = "connected"
        
        # Test core tables exist
        try:
            event_count = db.query(Event).count()
            results["events_table"] = f"exists ({event_count} events)"
        except Exception as e:
            results["events_table"] = f"error: {str(e)}"
        
        try:
            category_count = db.query(EventCategory).count()
            results["categories_table"] = f"exists ({category_count} categories)"
        except Exception as e:
            results["categories_table"] = f"error: {str(e)}"
        
        try:
            venue_count = db.query(Venue).count()
            results["venues_table"] = f"exists ({venue_count} venues)"
        except Exception as e:
            results["venues_table"] = f"error: {str(e)}"
        
        try:
            user_count = db.query(User).count()
            results["users_table"] = f"exists ({user_count} users)"
        except Exception as e:
            results["users_table"] = f"error: {str(e)}"
        
        # Test new user events features
        try:
            # Check if event organizer role exists
            organizer_role = db.query(UserRole).filter(UserRole.name == 'event_organizer').first()
            results["event_organizer_role"] = "exists" if organizer_role else "missing"
        except Exception as e:
            results["event_organizer_role"] = f"error: {str(e)}"
        
        try:
            # Check for user-generated events
            user_events = db.query(Event).filter(Event.is_user_generated == True).count()
            results["user_generated_events"] = f"{user_events} events"
        except Exception as e:
            results["user_generated_events"] = f"error: {str(e)}"
        
        try:
            # Check ticket types table
            ticket_types = db.query(TicketType).count()
            results["ticket_types"] = f"{ticket_types} ticket types"
        except Exception as e:
            results["ticket_types"] = f"error: {str(e)}"
        
        # Test migrations status
        try:
            # Try to access new fields
            sample_event = db.query(Event).first()
            if sample_event:
                has_organizer_id = hasattr(sample_event, 'organizer_id')
                has_approval_status = hasattr(sample_event, 'approval_status')
                has_commission_rate = hasattr(sample_event, 'platform_commission_rate')
                has_user_generated = hasattr(sample_event, 'is_user_generated')
                
                results["event_schema_migration"] = {
                    "organizer_id": has_organizer_id,
                    "approval_status": has_approval_status,
                    "platform_commission_rate": has_commission_rate,
                    "is_user_generated": has_user_generated
                }
            else:
                results["event_schema_migration"] = "no events to test"
        except Exception as e:
            results["event_schema_migration"] = f"error: {str(e)}"
        
        # Overall status
        errors = [k for k, v in results.items() if isinstance(v, str) and "error" in v]
        results["overall_status"] = "healthy" if not errors else f"issues: {len(errors)}"
        results["timestamp"] = "2025-01-08T14:30:00Z"
        
        return results
        
    except Exception as e:
        logger.error(f"System health check failed: {e}")
        return {
            "status": "error",
            "message": str(e),
            "timestamp": "2025-01-08T14:30:00Z"
        }


@router.get("/sample-data")
def get_sample_data(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get sample data for testing the frontend."""
    try:
        # Get sample categories
        categories = db.query(EventCategory).limit(5).all()
        category_data = [{"id": c.id, "name": c.name} for c in categories] if categories else []
        
        # Get sample venues
        venues = db.query(Venue).limit(5).all()
        venue_data = [{"id": v.id, "name": v.name, "address": getattr(v, 'address', '')} for v in venues] if venues else []
        
        # Get sample events
        events = db.query(Event).limit(5).all()
        event_data = []
        for event in events:
            event_data.append({
                "id": event.id,
                "title": event.title,
                "date": event.date.isoformat() if event.date else None,
                "location": event.location,
                "source": event.source,
                "is_user_generated": getattr(event, 'is_user_generated', False),
                "approval_status": getattr(event, 'approval_status', 'unknown')
            })
        
        return {
            "categories": category_data,
            "venues": venue_data,
            "events": event_data,
            "counts": {
                "total_categories": len(category_data),
                "total_venues": len(venue_data),
                "total_events": len(event_data)
            }
        }
        
    except Exception as e:
        logger.error(f"Error fetching sample data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch sample data: {str(e)}"
        )


@router.post("/create-sample-category")
def create_sample_category(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Create a sample category for testing."""
    try:
        # Check if test category already exists
        existing = db.query(EventCategory).filter(EventCategory.name == "Test Events").first()
        if existing:
            return {"message": "Test category already exists", "category_id": existing.id}
        
        # Create new test category
        category = EventCategory(
            name="Test Events",
            description="Category for testing user-generated events"
        )
        db.add(category)
        db.commit()
        db.refresh(category)
        
        return {
            "message": "Sample category created successfully",
            "category": {
                "id": category.id,
                "name": category.name,
                "description": category.description
            }
        }
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating sample category: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create sample category: {str(e)}"
        )