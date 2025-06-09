from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from ..core.database import get_db
from ..core.social_service import SocialService
from ..models.user import User
from ..models.social_schemas import (
    UserSocialProfile, UserSocialProfileCreate, UserSocialProfileUpdate,
    SocialPost, SocialPostCreate, SocialPostUpdate, SocialFeedParams,
    PostComment, PostCommentCreate, PostCommentUpdate,
    PostReaction, PostReactionCreate, CommentReaction,
    EventReview, EventReviewCreate, EventReviewUpdate,
    UserConnection, UserConnectionCreate, UserConnectionUpdate,
    UserFollow, UserFollowCreate,
    EventAttendance, EventAttendanceCreate, EventAttendanceUpdate,
    SocialNotification, ContentReportCreate, ContentReport,
    UserSearchParams, PostSearchParams,
    SocialFeedResponse, UserConnectionsResponse, EventReviewsResponse,
    NotificationsResponse, TrendingHashtagsResponse, SocialStatsResponse,
    ConnectionStatus, PostType, ReactionType, NotificationType
)
from ..routes.auth import get_current_user

router = APIRouter(prefix="/social", tags=["Social Features"])


# User Profile Endpoints
@router.get("/profile", response_model=UserSocialProfile)
def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's social profile"""
    service = SocialService(db)
    profile = service.get_or_create_user_profile(current_user.id)
    return profile


@router.get("/profile/{user_id}", response_model=UserSocialProfile)
def get_user_profile(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Get user's social profile"""
    service = SocialService(db)
    profile = service.get_user_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.put("/profile", response_model=UserSocialProfile)
def update_my_profile(
    profile_data: UserSocialProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update current user's social profile"""
    service = SocialService(db)
    profile = service.update_user_profile(current_user.id, profile_data)
    return profile


# Social Posts Endpoints
@router.post("/posts", response_model=SocialPost, status_code=status.HTTP_201_CREATED)
def create_post(
    post_data: SocialPostCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new social post"""
    service = SocialService(db)
    post = service.create_post(current_user.id, post_data)
    return post


@router.get("/posts/{post_id}", response_model=SocialPost)
def get_post(
    post_id: int,
    db: Session = Depends(get_db)
):
    """Get post by ID"""
    service = SocialService(db)
    post = service.get_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return post


@router.put("/posts/{post_id}", response_model=SocialPost)
def update_post(
    post_id: int,
    post_data: SocialPostUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update post (only by owner)"""
    service = SocialService(db)
    post = service.update_post(post_id, current_user.id, post_data)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found or not authorized")
    return post


@router.delete("/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(
    post_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete post (only by owner)"""
    service = SocialService(db)
    success = service.delete_post(post_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Post not found or not authorized")


@router.get("/feed", response_model=SocialFeedResponse)
def get_social_feed(
    feed_type: str = Query("timeline"),
    post_type: Optional[PostType] = None,
    include_connections_only: bool = False,
    include_groups: bool = True,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get personalized social feed"""
    feed_params = SocialFeedParams(
        feed_type=feed_type,
        post_type=post_type,
        include_connections_only=include_connections_only,
        include_groups=include_groups,
        page=page,
        size=size
    )
    
    service = SocialService(db)
    posts, total = service.get_social_feed(current_user.id, feed_params)
    
    pages = (total + size - 1) // size
    has_more = page < pages
    
    return SocialFeedResponse(
        posts=posts,
        total=total,
        page=page,
        size=size,
        pages=pages,
        has_more=has_more
    )


@router.get("/posts/search", response_model=SocialFeedResponse)
def search_posts(
    q: Optional[str] = None,
    post_type: Optional[PostType] = None,
    hashtags: Optional[str] = Query(None),
    user_id: Optional[int] = None,
    event_id: Optional[int] = None,
    venue_id: Optional[int] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Search posts"""
    hashtag_list = hashtags.split(',') if hashtags else None
    
    search_params = PostSearchParams(
        q=q,
        post_type=post_type,
        hashtags=hashtag_list,
        user_id=user_id,
        event_id=event_id,
        venue_id=venue_id,
        date_from=date_from,
        date_to=date_to,
        page=page,
        size=size
    )
    
    service = SocialService(db)
    posts, total = service.search_posts(search_params)
    
    pages = (total + size - 1) // size
    has_more = page < pages
    
    return SocialFeedResponse(
        posts=posts,
        total=total,
        page=page,
        size=size,
        pages=pages,
        has_more=has_more
    )


# Comments Endpoints
@router.post("/posts/{post_id}/comments", response_model=PostComment, status_code=status.HTTP_201_CREATED)
def create_comment(
    post_id: int,
    comment_data: PostCommentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create post comment"""
    service = SocialService(db)
    try:
        comment = service.create_comment(post_id, current_user.id, comment_data)
        return comment
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/posts/{post_id}/comments", response_model=List[PostComment])
def get_post_comments(
    post_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get comments for a post"""
    service = SocialService(db)
    offset = (page - 1) * size
    comments = service.get_post_comments(post_id, size, offset)
    return comments


@router.get("/comments/{comment_id}/replies", response_model=List[PostComment])
def get_comment_replies(
    comment_id: int,
    db: Session = Depends(get_db)
):
    """Get replies to a comment"""
    service = SocialService(db)
    replies = service.get_comment_replies(comment_id)
    return replies


@router.put("/comments/{comment_id}", response_model=PostComment)
def update_comment(
    comment_id: int,
    comment_data: PostCommentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update comment (only by owner)"""
    service = SocialService(db)
    comment = service.update_comment(comment_id, current_user.id, comment_data)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found or not authorized")
    return comment


@router.delete("/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_comment(
    comment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete comment (only by owner or post owner)"""
    service = SocialService(db)
    success = service.delete_comment(comment_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Comment not found or not authorized")


# Reactions Endpoints
@router.post("/posts/{post_id}/react")
def react_to_post(
    post_id: int,
    reaction_data: PostReactionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """React to post (like, love, etc.)"""
    service = SocialService(db)
    reaction = service.toggle_post_reaction(post_id, current_user.id, reaction_data)
    
    if reaction:
        return {"message": "Reaction added", "reaction": reaction}
    else:
        return {"message": "Reaction removed"}


@router.post("/comments/{comment_id}/react")
def react_to_comment(
    comment_id: int,
    reaction_data: PostReactionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """React to comment"""
    service = SocialService(db)
    reaction = service.toggle_comment_reaction(comment_id, current_user.id, reaction_data)
    
    if reaction:
        return {"message": "Reaction added", "reaction": reaction}
    else:
        return {"message": "Reaction removed"}


# Event Reviews Endpoints
@router.post("/events/{event_id}/reviews", response_model=EventReview, status_code=status.HTTP_201_CREATED)
def create_event_review(
    event_id: int,
    review_data: EventReviewCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create event review"""
    # Ensure event_id matches route parameter
    review_data.event_id = event_id
    
    service = SocialService(db)
    try:
        review = service.create_event_review(current_user.id, review_data)
        return review
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/events/{event_id}/reviews", response_model=EventReviewsResponse)
def get_event_reviews(
    event_id: int,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Get reviews for an event"""
    service = SocialService(db)
    offset = (page - 1) * size
    reviews, total = service.get_event_reviews(event_id, size, offset)
    
    # Calculate average rating and distribution
    if reviews:
        total_rating = sum(review.rating for review in reviews)
        average_rating = total_rating / len(reviews)
        
        # Get rating distribution from all reviews for this event
        all_reviews, _ = service.get_event_reviews(event_id, limit=1000, offset=0)
        rating_distribution = {}
        for i in range(1, 6):
            rating_distribution[i] = sum(1 for r in all_reviews if r.rating == i)
    else:
        average_rating = None
        rating_distribution = {i: 0 for i in range(1, 6)}
    
    return EventReviewsResponse(
        reviews=reviews,
        total=total,
        average_rating=average_rating,
        rating_distribution=rating_distribution
    )


@router.put("/reviews/{review_id}", response_model=EventReview)
def update_event_review(
    review_id: int,
    review_data: EventReviewUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update event review or add organizer response"""
    service = SocialService(db)
    review = service.update_event_review(review_id, current_user.id, review_data)
    if not review:
        raise HTTPException(status_code=404, detail="Review not found or not authorized")
    return review


# User Connections Endpoints
@router.post("/connections/request", response_model=UserConnection, status_code=status.HTTP_201_CREATED)
def send_connection_request(
    connection_data: UserConnectionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send connection request"""
    service = SocialService(db)
    try:
        connection = service.send_connection_request(current_user.id, connection_data)
        return connection
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/connections/{connection_id}/respond", response_model=UserConnection)
def respond_to_connection_request(
    connection_id: int,
    response_data: UserConnectionUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Respond to connection request"""
    service = SocialService(db)
    connection = service.respond_to_connection_request(connection_id, current_user.id, response_data)
    if not connection:
        raise HTTPException(status_code=404, detail="Connection request not found")
    return connection


@router.get("/connections", response_model=UserConnectionsResponse)
def get_my_connections(
    connection_status: Optional[ConnectionStatus] = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's connections"""
    service = SocialService(db)
    connections = service.get_user_connections(current_user.id, connection_status)
    
    # Paginate results
    total = len(connections)
    start = (page - 1) * size
    end = start + size
    paginated_connections = connections[start:end]
    
    pages = (total + size - 1) // size
    
    return UserConnectionsResponse(
        connections=paginated_connections,
        total=total,
        page=page,
        size=size,
        pages=pages
    )


@router.delete("/connections/{connection_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_connection(
    connection_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Remove connection"""
    service = SocialService(db)
    success = service.remove_connection(connection_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Connection not found")


# Follow System Endpoints
@router.post("/follow", response_model=UserFollow, status_code=status.HTTP_201_CREATED)
def follow_user(
    follow_data: UserFollowCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Follow a user"""
    service = SocialService(db)
    try:
        follow = service.follow_user(current_user.id, follow_data)
        return follow
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/follow/{following_id}", status_code=status.HTTP_204_NO_CONTENT)
def unfollow_user(
    following_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Unfollow a user"""
    service = SocialService(db)
    success = service.unfollow_user(current_user.id, following_id)
    if not success:
        raise HTTPException(status_code=404, detail="Follow relationship not found")


# Event Attendance Endpoints
@router.post("/events/{event_id}/attendance", response_model=EventAttendance)
def update_event_attendance(
    event_id: int,
    attendance_data: EventAttendanceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update event attendance status"""
    # Ensure event_id matches route parameter
    attendance_data.event_id = event_id
    
    service = SocialService(db)
    attendance = service.update_event_attendance(current_user.id, attendance_data)
    return attendance


@router.post("/events/{event_id}/checkin")
def check_in_to_event(
    event_id: int,
    location: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Check in to event"""
    service = SocialService(db)
    success = service.check_in_to_event(current_user.id, event_id, location)
    if not success:
        raise HTTPException(status_code=400, detail="Cannot check in to this event")
    
    return {"message": "Successfully checked in to event"}


# Notifications Endpoints
@router.get("/notifications", response_model=NotificationsResponse)
def get_my_notifications(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user notifications"""
    service = SocialService(db)
    offset = (page - 1) * size
    notifications, total, unread_count = service.get_user_notifications(current_user.id, size, offset)
    
    return NotificationsResponse(
        notifications=notifications,
        total=total,
        unread_count=unread_count
    )


@router.put("/notifications/{notification_id}/read")
def mark_notification_as_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark notification as read"""
    service = SocialService(db)
    success = service.mark_notification_as_read(notification_id, current_user.id)
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    return {"message": "Notification marked as read"}


@router.put("/notifications/read-all")
def mark_all_notifications_as_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark all notifications as read"""
    service = SocialService(db)
    count = service.mark_all_notifications_as_read(current_user.id)
    
    return {"message": f"Marked {count} notifications as read"}


# Content Reporting Endpoints
@router.post("/report", response_model=ContentReport, status_code=status.HTTP_201_CREATED)
def report_content(
    report_data: ContentReportCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Report inappropriate content"""
    service = SocialService(db)
    report = service.report_content(current_user.id, report_data)
    return report


# Discovery and Trending Endpoints
@router.get("/trending/hashtags", response_model=TrendingHashtagsResponse)
def get_trending_hashtags(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Get trending hashtags"""
    service = SocialService(db)
    trends = service.get_trending_hashtags(limit)
    
    hashtags = [
        {
            "hashtag": trend.hashtag,
            "usage_count": trend.usage_count,
            "trend_score": trend.trend_score,
            "category": trend.category
        }
        for trend in trends
    ]
    
    return TrendingHashtagsResponse(
        hashtags=hashtags,
        total=len(hashtags)
    )


@router.get("/users/search")
def search_users(
    q: Optional[str] = None,
    location: Optional[str] = None,
    interests: Optional[str] = Query(None),
    is_verified: Optional[bool] = None,
    is_event_organizer: Optional[bool] = None,
    is_venue_owner: Optional[bool] = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Search users"""
    interests_list = interests.split(',') if interests else None
    
    search_params = UserSearchParams(
        q=q,
        location=location,
        interests=interests_list,
        is_verified=is_verified,
        is_event_organizer=is_event_organizer,
        is_venue_owner=is_venue_owner,
        page=page,
        size=size
    )
    
    service = SocialService(db)
    users, total = service.search_users(search_params)
    
    pages = (total + size - 1) // size
    
    return {
        "users": users,
        "total": total,
        "page": page,
        "size": size,
        "pages": pages
    }


# Statistics Endpoints
@router.get("/stats", response_model=SocialStatsResponse)
def get_my_social_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's social statistics"""
    service = SocialService(db)
    stats = service.get_user_stats(current_user.id)
    return SocialStatsResponse(**stats)


@router.get("/stats/{user_id}", response_model=SocialStatsResponse)
def get_user_social_stats(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Get user's social statistics"""
    service = SocialService(db)
    stats = service.get_user_stats(user_id)
    return SocialStatsResponse(**stats)