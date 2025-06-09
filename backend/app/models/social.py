from enum import Enum as PyEnum

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
)
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import (
    ForeignKey,
    Index,
    Integer,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..core.database import Base


class ConnectionStatus(PyEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    BLOCKED = "blocked"
    DECLINED = "declined"


class PostType(PyEnum):
    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"
    EVENT_SHARE = "event_share"
    VENUE_SHARE = "venue_share"
    POLL = "poll"
    ANNOUNCEMENT = "announcement"


class ReactionType(PyEnum):
    LIKE = "like"
    LOVE = "love"
    LAUGH = "laugh"
    WOW = "wow"
    SAD = "sad"
    ANGRY = "angry"


class NotificationType(PyEnum):
    CONNECTION_REQUEST = "connection_request"
    CONNECTION_ACCEPTED = "connection_accepted"
    POST_LIKE = "post_like"
    POST_COMMENT = "post_comment"
    COMMENT_REPLY = "comment_reply"
    EVENT_INVITATION = "event_invitation"
    EVENT_REMINDER = "event_reminder"
    REVIEW_RESPONSE = "review_response"
    MENTION = "mention"


class ReportReason(PyEnum):
    SPAM = "spam"
    HARASSMENT = "harassment"
    INAPPROPRIATE_CONTENT = "inappropriate_content"
    FALSE_INFORMATION = "false_information"
    COPYRIGHT_VIOLATION = "copyright_violation"
    OTHER = "other"


# Association table for user connections (friendships)
user_connections = Table(
    "user_connections",
    Base.metadata,
    Column(
        "requester_id",
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "addressee_id",
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column("status", SQLEnum(ConnectionStatus), default=ConnectionStatus.PENDING),
    Column("created_at", DateTime(timezone=True), server_default=func.now()),
    Column(
        "updated_at",
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    ),
    CheckConstraint("requester_id != addressee_id", name="no_self_connection"),
)


# Association table for post tags (users mentioned in posts)
post_mentions = Table(
    "post_mentions",
    Base.metadata,
    Column(
        "post_id",
        Integer,
        ForeignKey("social_posts.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    ),
    Column("created_at", DateTime(timezone=True), server_default=func.now()),
)


class UserSocialProfile(Base):
    """Extended user profile for social features"""

    __tablename__ = "user_social_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )

    # Social profile information
    display_name = Column(String(100))
    tagline = Column(String(200))
    about = Column(Text)
    interests = Column(ARRAY(String))
    favorite_event_types = Column(ARRAY(String))
    location = Column(String(100))

    # Privacy settings
    profile_visibility = Column(
        String(20), default="public"
    )  # public, friends, private
    show_email = Column(Boolean, default=False)
    show_phone = Column(Boolean, default=False)
    show_location = Column(Boolean, default=True)
    show_events_attended = Column(Boolean, default=True)
    allow_connection_requests = Column(Boolean, default=True)
    allow_event_invitations = Column(Boolean, default=True)

    # Social stats (cached for performance)
    connections_count = Column(Integer, default=0)
    posts_count = Column(Integer, default=0)
    events_attended_count = Column(Integer, default=0)
    reviews_count = Column(Integer, default=0)
    followers_count = Column(Integer, default=0)
    following_count = Column(Integer, default=0)

    # Verification and badges
    is_verified = Column(Boolean, default=False)
    is_event_organizer = Column(Boolean, default=False)
    is_venue_owner = Column(Boolean, default=False)
    badges = Column(ARRAY(String))  # Achievement badges

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user = relationship("User", back_populates="social_profile")


class SocialPost(Base):
    """User posts and social content"""

    __tablename__ = "social_posts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Post content
    post_type = Column(SQLEnum(PostType), default=PostType.TEXT, index=True)
    content = Column(Text)
    title = Column(String(200))

    # Media attachments
    images = Column(ARRAY(String))  # Image URLs
    videos = Column(ARRAY(String))  # Video URLs

    # Related content
    event_id = Column(Integer, ForeignKey("events.id"), index=True)
    venue_id = Column(Integer, ForeignKey("venues.id"), index=True)

    # Poll data (for poll posts)
    poll_options = Column(JSONB)  # Poll options and votes
    poll_expires_at = Column(DateTime(timezone=True))
    poll_multiple_choice = Column(Boolean, default=False)

    # Post metadata
    is_pinned = Column(Boolean, default=False)
    is_featured = Column(Boolean, default=False)
    visibility = Column(String(20), default="public")  # public, friends, private
    allow_comments = Column(Boolean, default=True)
    allow_reactions = Column(Boolean, default=True)

    # Engagement stats
    likes_count = Column(Integer, default=0)
    comments_count = Column(Integer, default=0)
    shares_count = Column(Integer, default=0)
    views_count = Column(Integer, default=0)

    # Content moderation
    is_flagged = Column(Boolean, default=False)
    is_hidden = Column(Boolean, default=False)
    moderation_notes = Column(Text)

    # SEO and search
    hashtags = Column(ARRAY(String))
    search_vector = Column(Text)  # For full-text search

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user = relationship("User", back_populates="social_posts")
    event = relationship("Event", back_populates="social_posts")
    venue = relationship("Venue", back_populates="social_posts")
    comments = relationship(
        "PostComment", back_populates="post", cascade="all, delete-orphan"
    )
    reactions = relationship(
        "PostReaction", back_populates="post", cascade="all, delete-orphan"
    )
    mentions = relationship(
        "User", secondary=post_mentions, back_populates="mentioned_in_posts"
    )
    reports = relationship(
        "ContentReport", back_populates="post", cascade="all, delete-orphan"
    )


class PostComment(Base):
    """Comments on social posts"""

    __tablename__ = "post_comments"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(
        Integer,
        ForeignKey("social_posts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    parent_comment_id = Column(
        Integer, ForeignKey("post_comments.id"), index=True
    )  # For threaded replies

    # Comment content
    content = Column(Text, nullable=False)
    images = Column(ARRAY(String))  # Image attachments

    # Engagement
    likes_count = Column(Integer, default=0)
    replies_count = Column(Integer, default=0)

    # Moderation
    is_flagged = Column(Boolean, default=False)
    is_hidden = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    post = relationship("SocialPost", back_populates="comments")
    user = relationship("User", back_populates="post_comments")
    parent_comment = relationship(
        "PostComment", remote_side=[id], back_populates="replies"
    )
    replies = relationship("PostComment", back_populates="parent_comment")
    reactions = relationship(
        "CommentReaction", back_populates="comment", cascade="all, delete-orphan"
    )


class PostReaction(Base):
    """Reactions to social posts (likes, loves, etc.)"""

    __tablename__ = "post_reactions"

    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(
        Integer,
        ForeignKey("social_posts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    reaction_type = Column(SQLEnum(ReactionType), default=ReactionType.LIKE)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    post = relationship("SocialPost", back_populates="reactions")
    user = relationship("User", back_populates="post_reactions")

    # Constraints
    __table_args__ = (
        UniqueConstraint("post_id", "user_id", name="unique_post_user_reaction"),
    )


class CommentReaction(Base):
    """Reactions to comments"""

    __tablename__ = "comment_reactions"

    id = Column(Integer, primary_key=True, index=True)
    comment_id = Column(
        Integer,
        ForeignKey("post_comments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    reaction_type = Column(SQLEnum(ReactionType), default=ReactionType.LIKE)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    comment = relationship("PostComment", back_populates="reactions")
    user = relationship("User", back_populates="comment_reactions")

    # Constraints
    __table_args__ = (
        UniqueConstraint("comment_id", "user_id", name="unique_comment_user_reaction"),
    )


class EventReview(Base):
    """User reviews and ratings for events"""

    __tablename__ = "event_reviews"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(
        Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    booking_id = Column(
        Integer, ForeignKey("bookings.id"), index=True
    )  # If review is based on attendance

    # Review content
    rating = Column(Integer, nullable=False)  # 1-5 stars
    title = Column(String(200))
    review_text = Column(Text)

    # Detailed ratings
    organization_rating = Column(Integer)  # How well organized
    value_rating = Column(Integer)  # Value for money
    venue_rating = Column(Integer)  # Venue quality
    content_rating = Column(Integer)  # Content/program quality
    atmosphere_rating = Column(Integer)  # Event atmosphere

    # Review metadata
    is_verified = Column(Boolean, default=False)  # Based on actual attendance
    is_public = Column(Boolean, default=True)
    helpful_votes = Column(Integer, default=0)

    # Media attachments
    images = Column(ARRAY(String))
    videos = Column(ARRAY(String))

    # Response from organizer
    organizer_response = Column(Text)
    organizer_responded_at = Column(DateTime(timezone=True))

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    event = relationship("Event", back_populates="reviews")
    user = relationship("User", back_populates="event_reviews")
    booking = relationship("Booking", back_populates="review")

    # Constraints
    __table_args__ = (
        CheckConstraint(
            "rating >= 1 AND rating <= 5", name="event_review_rating_check"
        ),
        CheckConstraint(
            "organization_rating IS NULL OR (organization_rating >= 1 AND organization_rating <= 5)",
            name="organization_rating_check",
        ),
        CheckConstraint(
            "value_rating IS NULL OR (value_rating >= 1 AND value_rating <= 5)",
            name="value_rating_check",
        ),
        CheckConstraint(
            "venue_rating IS NULL OR (venue_rating >= 1 AND venue_rating <= 5)",
            name="venue_rating_check",
        ),
        CheckConstraint(
            "content_rating IS NULL OR (content_rating >= 1 AND content_rating <= 5)",
            name="content_rating_check",
        ),
        CheckConstraint(
            "atmosphere_rating IS NULL OR (atmosphere_rating >= 1 AND atmosphere_rating <= 5)",
            name="atmosphere_rating_check",
        ),
        UniqueConstraint("event_id", "user_id", name="unique_event_user_review"),
    )


class UserConnection(Base):
    """User connections and friendships"""

    __tablename__ = "user_social_connections"

    id = Column(Integer, primary_key=True, index=True)
    requester_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    addressee_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    status = Column(
        SQLEnum(ConnectionStatus), default=ConnectionStatus.PENDING, index=True
    )
    connection_message = Column(Text)  # Optional message with request

    # Connection metadata
    connection_strength = Column(
        Integer, default=1
    )  # Algorithm-based connection strength
    mutual_connections_count = Column(Integer, default=0)
    interaction_score = Column(Integer, default=0)  # Based on likes, comments, etc.

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    accepted_at = Column(DateTime(timezone=True))

    # Relationships
    requester = relationship(
        "User", foreign_keys=[requester_id], back_populates="sent_connections"
    )
    addressee = relationship(
        "User", foreign_keys=[addressee_id], back_populates="received_connections"
    )

    # Constraints
    __table_args__ = (
        CheckConstraint("requester_id != addressee_id", name="no_self_connection"),
        UniqueConstraint("requester_id", "addressee_id", name="unique_user_connection"),
    )


class UserFollow(Base):
    """User following relationships (asymmetric)"""

    __tablename__ = "user_follows"

    id = Column(Integer, primary_key=True, index=True)
    follower_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    following_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Follow settings
    receive_notifications = Column(Boolean, default=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    follower = relationship(
        "User", foreign_keys=[follower_id], back_populates="following"
    )
    following = relationship(
        "User", foreign_keys=[following_id], back_populates="followers"
    )

    # Constraints
    __table_args__ = (
        CheckConstraint("follower_id != following_id", name="no_self_follow"),
        UniqueConstraint("follower_id", "following_id", name="unique_user_follow"),
    )


class EventAttendance(Base):
    """Track event attendance for social features"""

    __tablename__ = "event_attendance"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(
        Integer, ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Attendance status
    attendance_status = Column(
        String(20), default="going"
    )  # going, interested, not_going
    visibility = Column(String(20), default="public")  # public, friends, private

    # Check-in information
    checked_in = Column(Boolean, default=False)
    check_in_time = Column(DateTime(timezone=True))
    check_in_location = Column(String(255))

    # Social sharing
    shared_on_timeline = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    event = relationship("Event", back_populates="attendances")
    user = relationship("User", back_populates="event_attendances")

    # Constraints
    __table_args__ = (
        UniqueConstraint("event_id", "user_id", name="unique_event_attendance"),
    )


class SocialNotification(Base):
    """Social notifications system"""

    __tablename__ = "social_notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Notification details
    notification_type = Column(SQLEnum(NotificationType), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    message = Column(Text)

    # Related entities
    from_user_id = Column(Integer, ForeignKey("users.id"), index=True)
    post_id = Column(Integer, ForeignKey("social_posts.id"), index=True)
    comment_id = Column(Integer, ForeignKey("post_comments.id"), index=True)
    event_id = Column(Integer, ForeignKey("events.id"), index=True)
    connection_id = Column(
        Integer, ForeignKey("user_social_connections.id"), index=True
    )

    # Notification state
    is_read = Column(Boolean, default=False, index=True)
    is_seen = Column(Boolean, default=False)

    # Action data
    action_url = Column(String(500))
    action_data = Column(JSONB)  # Additional action data

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    read_at = Column(DateTime(timezone=True))

    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="notifications")
    from_user = relationship("User", foreign_keys=[from_user_id])
    post = relationship("SocialPost", back_populates="notifications")
    comment = relationship("PostComment")
    event = relationship("Event")
    connection = relationship("UserConnection")


class ContentReport(Base):
    """User reports for inappropriate content"""

    __tablename__ = "content_reports"

    id = Column(Integer, primary_key=True, index=True)
    reporter_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Reported content
    post_id = Column(Integer, ForeignKey("social_posts.id"), index=True)
    comment_id = Column(Integer, ForeignKey("post_comments.id"), index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)  # Reported user

    # Report details
    reason = Column(SQLEnum(ReportReason), nullable=False)
    description = Column(Text)

    # Moderation
    status = Column(
        String(20), default="pending", index=True
    )  # pending, reviewed, resolved, dismissed
    moderator_id = Column(Integer, ForeignKey("users.id"), index=True)
    moderator_notes = Column(Text)
    action_taken = Column(
        String(100)
    )  # content_removed, user_warned, user_suspended, etc.

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    resolved_at = Column(DateTime(timezone=True))

    # Relationships
    reporter = relationship("User", foreign_keys=[reporter_id])
    post = relationship("SocialPost", back_populates="reports")
    comment = relationship("PostComment")
    reported_user = relationship("User", foreign_keys=[user_id])
    moderator = relationship("User", foreign_keys=[moderator_id])


class HashtagTrend(Base):
    """Trending hashtags and topics"""

    __tablename__ = "hashtag_trends"

    id = Column(Integer, primary_key=True, index=True)
    hashtag = Column(String(100), nullable=False, unique=True, index=True)

    # Trend metrics
    usage_count = Column(Integer, default=0)
    weekly_usage = Column(Integer, default=0)
    daily_usage = Column(Integer, default=0)
    peak_usage_date = Column(DateTime(timezone=True))

    # Trend analysis
    trend_score = Column(Integer, default=0)  # Algorithm-calculated trend score
    is_trending = Column(Boolean, default=False, index=True)
    category = Column(String(50))  # events, venues, general, etc.

    # Timestamps
    first_used = Column(DateTime(timezone=True), server_default=func.now())
    last_used = Column(DateTime(timezone=True), server_default=func.now())

    # Constraints
    __table_args__ = (Index("idx_hashtag_trending", "is_trending", "trend_score"),)


class SocialGroup(Base):
    """User groups and communities"""

    __tablename__ = "social_groups"

    id = Column(Integer, primary_key=True, index=True)
    creator_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Group details
    name = Column(String(100), nullable=False)
    description = Column(Text)
    category = Column(String(50))  # events, venues, interests, location

    # Group settings
    group_type = Column(String(20), default="public")  # public, private, secret
    join_approval_required = Column(Boolean, default=False)
    allow_member_posts = Column(Boolean, default=True)

    # Group image and branding
    cover_image = Column(String(500))
    avatar_image = Column(String(500))

    # Stats
    members_count = Column(Integer, default=1)  # Creator is first member
    posts_count = Column(Integer, default=0)

    # Moderation
    is_active = Column(Boolean, default=True)
    is_featured = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    creator = relationship("User", back_populates="created_groups")
    members = relationship(
        "GroupMembership", back_populates="group", cascade="all, delete-orphan"
    )
    posts = relationship(
        "GroupPost", back_populates="group", cascade="all, delete-orphan"
    )


class GroupMembership(Base):
    """Group membership management"""

    __tablename__ = "group_memberships"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(
        Integer,
        ForeignKey("social_groups.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Membership details
    role = Column(String(20), default="member")  # member, moderator, admin
    status = Column(String(20), default="active")  # active, pending, banned

    # Permissions
    can_post = Column(Boolean, default=True)
    can_moderate = Column(Boolean, default=False)
    can_invite = Column(Boolean, default=True)

    joined_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    group = relationship("SocialGroup", back_populates="members")
    user = relationship("User", back_populates="group_memberships")

    # Constraints
    __table_args__ = (
        UniqueConstraint("group_id", "user_id", name="unique_group_membership"),
    )


class GroupPost(Base):
    """Posts within social groups"""

    __tablename__ = "group_posts"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(
        Integer,
        ForeignKey("social_groups.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    # Post content (similar to SocialPost but group-specific)
    title = Column(String(200))
    content = Column(Text, nullable=False)
    post_type = Column(SQLEnum(PostType), default=PostType.TEXT)

    # Media and attachments
    images = Column(ARRAY(String))
    videos = Column(ARRAY(String))

    # Engagement
    likes_count = Column(Integer, default=0)
    comments_count = Column(Integer, default=0)

    # Moderation
    is_pinned = Column(Boolean, default=False)
    is_approved = Column(Boolean, default=True)
    is_flagged = Column(Boolean, default=False)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    group = relationship("SocialGroup", back_populates="posts")
    user = relationship("User", back_populates="group_posts")


# Update relationships in existing models by adding to User model
# This will be handled in the user.py model file separately
