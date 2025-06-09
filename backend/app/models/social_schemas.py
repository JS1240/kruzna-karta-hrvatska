from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum


class ConnectionStatus(str, Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    BLOCKED = "blocked"
    DECLINED = "declined"


class PostType(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    EVENT_SHARE = "event_share"
    VENUE_SHARE = "venue_share"
    POLL = "poll"
    ANNOUNCEMENT = "announcement"


class ReactionType(str, Enum):
    LIKE = "like"
    LOVE = "love"
    LAUGH = "laugh"
    WOW = "wow"
    SAD = "sad"
    ANGRY = "angry"


class NotificationType(str, Enum):
    CONNECTION_REQUEST = "connection_request"
    CONNECTION_ACCEPTED = "connection_accepted"
    POST_LIKE = "post_like"
    POST_COMMENT = "post_comment"
    COMMENT_REPLY = "comment_reply"
    EVENT_INVITATION = "event_invitation"
    EVENT_REMINDER = "event_reminder"
    REVIEW_RESPONSE = "review_response"
    MENTION = "mention"


class ReportReason(str, Enum):
    SPAM = "spam"
    HARASSMENT = "harassment"
    INAPPROPRIATE_CONTENT = "inappropriate_content"
    FALSE_INFORMATION = "false_information"
    COPYRIGHT_VIOLATION = "copyright_violation"
    OTHER = "other"


# User Profile Schemas
class UserSocialProfileBase(BaseModel):
    display_name: Optional[str] = Field(None, max_length=100)
    tagline: Optional[str] = Field(None, max_length=200)
    about: Optional[str] = None
    interests: Optional[List[str]] = None
    favorite_event_types: Optional[List[str]] = None
    location: Optional[str] = Field(None, max_length=100)
    
    # Privacy settings
    profile_visibility: str = Field(default="public")
    show_email: bool = False
    show_phone: bool = False
    show_location: bool = True
    show_events_attended: bool = True
    allow_connection_requests: bool = True
    allow_event_invitations: bool = True
    
    @validator('profile_visibility')
    def validate_visibility(cls, v):
        if v not in ['public', 'friends', 'private']:
            raise ValueError('Invalid visibility setting')
        return v


class UserSocialProfileCreate(UserSocialProfileBase):
    pass


class UserSocialProfileUpdate(BaseModel):
    display_name: Optional[str] = Field(None, max_length=100)
    tagline: Optional[str] = Field(None, max_length=200)
    about: Optional[str] = None
    interests: Optional[List[str]] = None
    favorite_event_types: Optional[List[str]] = None
    location: Optional[str] = Field(None, max_length=100)
    
    profile_visibility: Optional[str] = None
    show_email: Optional[bool] = None
    show_phone: Optional[bool] = None
    show_location: Optional[bool] = None
    show_events_attended: Optional[bool] = None
    allow_connection_requests: Optional[bool] = None
    allow_event_invitations: Optional[bool] = None


class UserSocialProfile(UserSocialProfileBase):
    id: int
    user_id: int
    
    # Social stats
    connections_count: int = 0
    posts_count: int = 0
    events_attended_count: int = 0
    reviews_count: int = 0
    followers_count: int = 0
    following_count: int = 0
    
    # Verification and badges
    is_verified: bool = False
    is_event_organizer: bool = False
    is_venue_owner: bool = False
    badges: Optional[List[str]] = None
    
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Social Post Schemas
class SocialPostBase(BaseModel):
    post_type: PostType = PostType.TEXT
    content: Optional[str] = None
    title: Optional[str] = Field(None, max_length=200)
    
    # Media attachments
    images: Optional[List[str]] = None
    videos: Optional[List[str]] = None
    
    # Related content
    event_id: Optional[int] = None
    venue_id: Optional[int] = None
    
    # Poll data
    poll_options: Optional[Dict[str, Any]] = None
    poll_expires_at: Optional[datetime] = None
    poll_multiple_choice: bool = False
    
    # Post settings
    visibility: str = Field(default="public")
    allow_comments: bool = True
    allow_reactions: bool = True
    
    # Content
    hashtags: Optional[List[str]] = None

    @validator('visibility')
    def validate_visibility(cls, v):
        if v not in ['public', 'friends', 'private']:
            raise ValueError('Invalid visibility setting')
        return v


class SocialPostCreate(SocialPostBase):
    mention_users: Optional[List[int]] = None  # User IDs to mention


class SocialPostUpdate(BaseModel):
    content: Optional[str] = None
    title: Optional[str] = Field(None, max_length=200)
    visibility: Optional[str] = None
    allow_comments: Optional[bool] = None
    allow_reactions: Optional[bool] = None
    hashtags: Optional[List[str]] = None


class SocialPost(SocialPostBase):
    id: int
    user_id: int
    
    # Engagement stats
    likes_count: int = 0
    comments_count: int = 0
    shares_count: int = 0
    views_count: int = 0
    
    # Flags
    is_pinned: bool = False
    is_featured: bool = False
    is_flagged: bool = False
    is_hidden: bool = False
    
    created_at: datetime
    updated_at: datetime
    
    # Nested objects (when needed)
    user: Optional[Dict[str, Any]] = None
    event: Optional[Dict[str, Any]] = None
    venue: Optional[Dict[str, Any]] = None
    user_reaction: Optional[ReactionType] = None  # Current user's reaction

    class Config:
        from_attributes = True


# Comment Schemas
class PostCommentBase(BaseModel):
    content: str = Field(..., min_length=1, max_length=1000)
    images: Optional[List[str]] = None
    parent_comment_id: Optional[int] = None


class PostCommentCreate(PostCommentBase):
    pass


class PostCommentUpdate(BaseModel):
    content: Optional[str] = Field(None, min_length=1, max_length=1000)


class PostComment(PostCommentBase):
    id: int
    post_id: int
    user_id: int
    
    # Stats
    likes_count: int = 0
    replies_count: int = 0
    
    # Flags
    is_flagged: bool = False
    is_hidden: bool = False
    
    created_at: datetime
    updated_at: datetime
    
    # Nested objects
    user: Optional[Dict[str, Any]] = None
    user_reaction: Optional[ReactionType] = None
    replies: Optional[List['PostComment']] = None

    class Config:
        from_attributes = True


# Reaction Schemas
class PostReactionCreate(BaseModel):
    reaction_type: ReactionType = ReactionType.LIKE


class PostReaction(BaseModel):
    id: int
    post_id: int
    user_id: int
    reaction_type: ReactionType
    created_at: datetime
    
    # Nested objects
    user: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


class CommentReactionCreate(BaseModel):
    reaction_type: ReactionType = ReactionType.LIKE


class CommentReaction(BaseModel):
    id: int
    comment_id: int
    user_id: int
    reaction_type: ReactionType
    created_at: datetime

    class Config:
        from_attributes = True


# Event Review Schemas
class EventReviewBase(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    title: Optional[str] = Field(None, max_length=200)
    review_text: Optional[str] = None
    
    # Detailed ratings
    organization_rating: Optional[int] = Field(None, ge=1, le=5)
    value_rating: Optional[int] = Field(None, ge=1, le=5)
    venue_rating: Optional[int] = Field(None, ge=1, le=5)
    content_rating: Optional[int] = Field(None, ge=1, le=5)
    atmosphere_rating: Optional[int] = Field(None, ge=1, le=5)
    
    # Media
    images: Optional[List[str]] = None
    videos: Optional[List[str]] = None
    
    is_public: bool = True


class EventReviewCreate(EventReviewBase):
    event_id: int
    booking_id: Optional[int] = None


class EventReviewUpdate(BaseModel):
    rating: Optional[int] = Field(None, ge=1, le=5)
    title: Optional[str] = Field(None, max_length=200)
    review_text: Optional[str] = None
    
    organization_rating: Optional[int] = Field(None, ge=1, le=5)
    value_rating: Optional[int] = Field(None, ge=1, le=5)
    venue_rating: Optional[int] = Field(None, ge=1, le=5)
    content_rating: Optional[int] = Field(None, ge=1, le=5)
    atmosphere_rating: Optional[int] = Field(None, ge=1, le=5)
    
    images: Optional[List[str]] = None
    videos: Optional[List[str]] = None
    is_public: Optional[bool] = None
    
    organizer_response: Optional[str] = None


class EventReview(EventReviewBase):
    id: int
    event_id: int
    user_id: int
    booking_id: Optional[int] = None
    
    is_verified: bool = False
    helpful_votes: int = 0
    
    organizer_response: Optional[str] = None
    organizer_responded_at: Optional[datetime] = None
    
    created_at: datetime
    updated_at: datetime
    
    # Nested objects
    user: Optional[Dict[str, Any]] = None
    event: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


# Connection Schemas
class UserConnectionCreate(BaseModel):
    addressee_id: int
    connection_message: Optional[str] = Field(None, max_length=500)


class UserConnectionUpdate(BaseModel):
    status: ConnectionStatus
    connection_message: Optional[str] = Field(None, max_length=500)


class UserConnection(BaseModel):
    id: int
    requester_id: int
    addressee_id: int
    status: ConnectionStatus
    connection_message: Optional[str] = None
    
    # Metadata
    connection_strength: int = 1
    mutual_connections_count: int = 0
    interaction_score: int = 0
    
    created_at: datetime
    updated_at: datetime
    accepted_at: Optional[datetime] = None
    
    # Nested objects
    requester: Optional[Dict[str, Any]] = None
    addressee: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


# Follow Schemas
class UserFollowCreate(BaseModel):
    following_id: int
    receive_notifications: bool = True


class UserFollow(BaseModel):
    id: int
    follower_id: int
    following_id: int
    receive_notifications: bool = True
    created_at: datetime
    
    # Nested objects
    follower: Optional[Dict[str, Any]] = None
    following: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


# Event Attendance Schemas
class EventAttendanceCreate(BaseModel):
    event_id: int
    attendance_status: str = Field(default="going")
    visibility: str = Field(default="public")
    shared_on_timeline: bool = False

    @validator('attendance_status')
    def validate_attendance_status(cls, v):
        if v not in ['going', 'interested', 'not_going']:
            raise ValueError('Invalid attendance status')
        return v

    @validator('visibility')
    def validate_visibility(cls, v):
        if v not in ['public', 'friends', 'private']:
            raise ValueError('Invalid visibility setting')
        return v


class EventAttendanceUpdate(BaseModel):
    attendance_status: Optional[str] = None
    visibility: Optional[str] = None
    shared_on_timeline: Optional[bool] = None


class EventAttendance(BaseModel):
    id: int
    event_id: int
    user_id: int
    attendance_status: str
    visibility: str
    
    checked_in: bool = False
    check_in_time: Optional[datetime] = None
    check_in_location: Optional[str] = None
    shared_on_timeline: bool = False
    
    created_at: datetime
    updated_at: datetime
    
    # Nested objects
    user: Optional[Dict[str, Any]] = None
    event: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


# Notification Schemas
class SocialNotificationCreate(BaseModel):
    user_id: int
    notification_type: NotificationType
    title: str = Field(..., max_length=200)
    message: Optional[str] = None
    
    from_user_id: Optional[int] = None
    post_id: Optional[int] = None
    comment_id: Optional[int] = None
    event_id: Optional[int] = None
    connection_id: Optional[int] = None
    
    action_url: Optional[str] = Field(None, max_length=500)
    action_data: Optional[Dict[str, Any]] = None


class SocialNotification(BaseModel):
    id: int
    user_id: int
    notification_type: NotificationType
    title: str
    message: Optional[str] = None
    
    from_user_id: Optional[int] = None
    post_id: Optional[int] = None
    comment_id: Optional[int] = None
    event_id: Optional[int] = None
    connection_id: Optional[int] = None
    
    is_read: bool = False
    is_seen: bool = False
    
    action_url: Optional[str] = None
    action_data: Optional[Dict[str, Any]] = None
    
    created_at: datetime
    read_at: Optional[datetime] = None
    
    # Nested objects
    from_user: Optional[Dict[str, Any]] = None

    class Config:
        from_attributes = True


# Report Schemas
class ContentReportCreate(BaseModel):
    post_id: Optional[int] = None
    comment_id: Optional[int] = None
    user_id: Optional[int] = None
    
    reason: ReportReason
    description: Optional[str] = Field(None, max_length=1000)


class ContentReport(BaseModel):
    id: int
    reporter_id: int
    
    post_id: Optional[int] = None
    comment_id: Optional[int] = None
    user_id: Optional[int] = None
    
    reason: ReportReason
    description: Optional[str] = None
    status: str = "pending"
    
    moderator_id: Optional[int] = None
    moderator_notes: Optional[str] = None
    action_taken: Optional[str] = None
    
    created_at: datetime
    resolved_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# Group Schemas
class SocialGroupBase(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=50)
    
    group_type: str = Field(default="public")
    join_approval_required: bool = False
    allow_member_posts: bool = True
    
    cover_image: Optional[str] = Field(None, max_length=500)
    avatar_image: Optional[str] = Field(None, max_length=500)

    @validator('group_type')
    def validate_group_type(cls, v):
        if v not in ['public', 'private', 'secret']:
            raise ValueError('Invalid group type')
        return v


class SocialGroupCreate(SocialGroupBase):
    pass


class SocialGroupUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=50)
    
    group_type: Optional[str] = None
    join_approval_required: Optional[bool] = None
    allow_member_posts: Optional[bool] = None
    
    cover_image: Optional[str] = Field(None, max_length=500)
    avatar_image: Optional[str] = Field(None, max_length=500)


class SocialGroup(SocialGroupBase):
    id: int
    creator_id: int
    
    members_count: int = 1
    posts_count: int = 0
    
    is_active: bool = True
    is_featured: bool = False
    
    created_at: datetime
    updated_at: datetime
    
    # Nested objects
    creator: Optional[Dict[str, Any]] = None
    user_membership: Optional[Dict[str, Any]] = None  # Current user's membership

    class Config:
        from_attributes = True


# Search and Filter Schemas
class SocialFeedParams(BaseModel):
    feed_type: str = Field(default="timeline")  # timeline, discover, following
    post_type: Optional[PostType] = None
    include_connections_only: bool = False
    include_groups: bool = True
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)

    @validator('feed_type')
    def validate_feed_type(cls, v):
        if v not in ['timeline', 'discover', 'following', 'trending']:
            raise ValueError('Invalid feed type')
        return v


class UserSearchParams(BaseModel):
    q: Optional[str] = None  # Search query
    location: Optional[str] = None
    interests: Optional[List[str]] = None
    is_verified: Optional[bool] = None
    is_event_organizer: Optional[bool] = None
    is_venue_owner: Optional[bool] = None
    
    # Connection filters
    connection_status: Optional[ConnectionStatus] = None
    mutual_connections: Optional[bool] = None
    
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)


class PostSearchParams(BaseModel):
    q: Optional[str] = None
    post_type: Optional[PostType] = None
    hashtags: Optional[List[str]] = None
    user_id: Optional[int] = None
    event_id: Optional[int] = None
    venue_id: Optional[int] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    
    page: int = Field(default=1, ge=1)
    size: int = Field(default=20, ge=1, le=100)


# Response Schemas
class SocialFeedResponse(BaseModel):
    posts: List[SocialPost]
    total: int
    page: int
    size: int
    pages: int
    has_more: bool


class UserConnectionsResponse(BaseModel):
    connections: List[UserConnection]
    total: int
    page: int
    size: int
    pages: int


class EventReviewsResponse(BaseModel):
    reviews: List[EventReview]
    total: int
    average_rating: Optional[float] = None
    rating_distribution: Optional[Dict[int, int]] = None


class NotificationsResponse(BaseModel):
    notifications: List[SocialNotification]
    total: int
    unread_count: int


class TrendingHashtagsResponse(BaseModel):
    hashtags: List[Dict[str, Any]]
    total: int


class SocialStatsResponse(BaseModel):
    user_id: int
    connections_count: int
    followers_count: int
    following_count: int
    posts_count: int
    reviews_count: int
    events_attended_count: int
    total_likes_received: int
    total_comments_received: int