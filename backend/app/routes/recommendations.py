"""API routes for event recommendations."""

from fastapi import APIRouter, Depends, Query

from ..core.auth import get_current_active_user
from ..core.recommendation import RecommendationService, get_recommendation_service
from ..models.user import User

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("/events")
def get_recommended_events(
    limit: int = Query(10, ge=1, le=50),
    language: str = Query("hr"),
    current_user: User = Depends(get_current_active_user),
    service: RecommendationService = Depends(get_recommendation_service),
):
    """Return recommended events for the current user."""
    return service.get_recommendations(current_user.id, limit=limit, language=language)
