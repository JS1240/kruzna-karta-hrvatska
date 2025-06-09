from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_
from typing import List, Optional

from ..core.database import get_db
from ..core.auth import get_current_user, get_current_active_user, get_current_superuser
from ..models.user import User, UserProfile, user_favorites
from ..models.event import Event
from ..models.user_schemas import (
    User as UserSchema, UserUpdate, UserResponse, UsersListResponse,
    UserProfile as UserProfileSchema, UserProfileUpdate,
    UserSearchParams, UserFavoritesList
)

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", response_model=UsersListResponse)
def get_users(
    q: Optional[str] = Query(None, description="Search users by name, email, or username"),
    city: Optional[str] = Query(None, description="Filter by city"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    is_verified: Optional[bool] = Query(None, description="Filter by verification status"),
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Page size"),
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """Get users list (admin only)."""
    query = db.query(User)
    
    # Apply filters
    if q:
        search_filter = or_(
            User.first_name.ilike(f"%{q}%"),
            User.last_name.ilike(f"%{q}%"),
            User.email.ilike(f"%{q}%"),
            User.username.ilike(f"%{q}%")
        )
        query = query.filter(search_filter)
    
    if city:
        query = query.filter(User.city.ilike(f"%{city}%"))
    
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    
    if is_verified is not None:
        query = query.filter(User.is_verified == is_verified)
    
    # Get total count
    total = query.count()
    
    # Calculate pagination
    skip = (page - 1) * size
    pages = (total + size - 1) // size if total > 0 else 0
    
    # Apply pagination and ordering
    users = query.order_by(User.created_at.desc()).offset(skip).limit(size).all()
    
    return UsersListResponse(
        users=users,
        total=total,
        page=page,
        size=len(users),
        pages=pages
    )


@router.get("/me", response_model=UserResponse)
def get_my_profile(current_user: User = Depends(get_current_user)):
    """Get current user's profile."""
    return UserResponse(user=current_user)


@router.put("/me", response_model=UserResponse)
def update_my_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update current user's profile."""
    # Check email uniqueness if email is being updated
    update_data = user_update.model_dump(exclude_unset=True)
    
    if 'email' in update_data and update_data['email'] != current_user.email:
        existing_user = db.query(User).filter(
            User.email == update_data['email'],
            User.id != current_user.id
        ).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already in use")
        
        # If email is changed, mark as unverified
        current_user.is_verified = False
    
    # Check username uniqueness if username is being updated
    if 'username' in update_data and update_data['username'] != current_user.username:
        existing_user = db.query(User).filter(
            User.username == update_data['username'],
            User.id != current_user.id
        ).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already taken")
    
    # Update user fields
    for field, value in update_data.items():
        setattr(current_user, field, value)
    
    db.commit()
    db.refresh(current_user)
    
    return UserResponse(user=current_user, message="Profile updated successfully")


@router.delete("/me")
def delete_my_account(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Delete current user's account."""
    # Soft delete - just deactivate the account
    current_user.is_active = False
    db.commit()
    
    return {"message": "Account deactivated successfully"}


@router.get("/me/profile", response_model=UserProfileSchema)
def get_my_detailed_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's detailed profile."""
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        # Create profile if it doesn't exist
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    
    return profile


@router.put("/me/profile", response_model=UserProfileSchema)
def update_my_detailed_profile(
    profile_update: UserProfileUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update current user's detailed profile."""
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if not profile:
        # Create profile if it doesn't exist
        profile = UserProfile(user_id=current_user.id)
        db.add(profile)
        db.flush()
    
    # Update profile fields
    update_data = profile_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(profile, field, value)
    
    db.commit()
    db.refresh(profile)
    
    return profile


@router.get("/me/favorites", response_model=UserFavoritesList)
def get_my_favorites(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's favorite events."""
    # Query favorite events with pagination
    query = db.query(Event).join(
        user_favorites, Event.id == user_favorites.c.event_id
    ).filter(
        user_favorites.c.user_id == current_user.id
    ).options(
        joinedload(Event.category),
        joinedload(Event.venue)
    )
    
    total = query.count()
    skip = (page - 1) * size
    
    favorites = query.order_by(user_favorites.c.created_at.desc()).offset(skip).limit(size).all()
    
    return UserFavoritesList(
        favorites=favorites,
        total=total
    )


@router.post("/me/favorites/{event_id}")
def add_to_favorites(
    event_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Add event to user's favorites."""
    # Check if event exists
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Check if already in favorites
    existing_favorite = db.query(user_favorites).filter(
        and_(
            user_favorites.c.user_id == current_user.id,
            user_favorites.c.event_id == event_id
        )
    ).first()
    
    if existing_favorite:
        raise HTTPException(status_code=400, detail="Event already in favorites")
    
    # Add to favorites
    stmt = user_favorites.insert().values(user_id=current_user.id, event_id=event_id)
    db.execute(stmt)
    
    # Update profile statistics
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if profile:
        profile.events_favorited += 1
    
    db.commit()
    
    return {"message": "Event added to favorites"}


@router.delete("/me/favorites/{event_id}")
def remove_from_favorites(
    event_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Remove event from user's favorites."""
    # Check if in favorites
    existing_favorite = db.query(user_favorites).filter(
        and_(
            user_favorites.c.user_id == current_user.id,
            user_favorites.c.event_id == event_id
        )
    ).first()
    
    if not existing_favorite:
        raise HTTPException(status_code=404, detail="Event not in favorites")
    
    # Remove from favorites
    stmt = user_favorites.delete().where(
        and_(
            user_favorites.c.user_id == current_user.id,
            user_favorites.c.event_id == event_id
        )
    )
    db.execute(stmt)
    
    # Update profile statistics
    profile = db.query(UserProfile).filter(UserProfile.user_id == current_user.id).first()
    if profile and profile.events_favorited > 0:
        profile.events_favorited -= 1
    
    db.commit()
    
    return {"message": "Event removed from favorites"}


@router.get("/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user by ID."""
    # Only superusers can view other users' full profiles
    # Regular users can only view basic public information
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # If not superuser and not own profile, return limited info
    if not current_user.is_superuser and current_user.id != user_id:
        # Check user's privacy settings
        profile = db.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        if profile and profile.profile_visibility == 'private':
            raise HTTPException(status_code=403, detail="User profile is private")
        
        # Return limited public information
        public_user = UserSchema(
            id=user.id,
            email="" if not (profile and profile.show_email) else user.email,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
            city=user.city if (profile and profile.show_location) else None,
            country=user.country if (profile and profile.show_location) else None,
            is_active=user.is_active,
            is_verified=user.is_verified,
            is_superuser=False,  # Don't reveal admin status
            created_at=user.created_at,
            updated_at=user.updated_at
        )
        return UserResponse(user=public_user)
    
    return UserResponse(user=user)