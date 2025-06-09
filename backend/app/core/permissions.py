"""Utility helpers for permission checks."""

from fastapi import HTTPException, status

from ..models.user import User


def can_user_create_events(user: User) -> bool:
    """Return True if the user is allowed to create events."""
    return user.venue_owner or user.venue_manager or user.is_superuser


def require_event_creator(user: User, detail: str = "Access denied") -> None:
    """Raise 403 if the user cannot create or manage events."""
    if not can_user_create_events(user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


def require_admin(user: User, detail: str = "Admin access required") -> None:
    """Raise 403 if the user is not an administrator."""
    if not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


def require_owner_or_admin(owner_id: int, user: User, detail: str = "Access denied") -> None:
    """Raise 403 if the user is neither the owner nor an admin."""
    if owner_id != user.id and not user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=detail)
