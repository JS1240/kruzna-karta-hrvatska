from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Table,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from ..core.database import Base

# Association table for user favorites
user_favorites = Table(
    "user_favorites",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("event_id", Integer, ForeignKey("events.id"), primary_key=True),
    Column("created_at", DateTime(timezone=True), server_default=func.now()),
)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=True)
    hashed_password = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    is_superuser = Column(Boolean, default=False)

    # Profile information
    phone = Column(String(50), nullable=True)
    date_of_birth = Column(DateTime(timezone=True), nullable=True)
    city = Column(String(100), nullable=True)
    country = Column(String(100), default="Croatia")
    bio = Column(Text, nullable=True)
    avatar_url = Column(String(500), nullable=True)

    # Preferences
    preferred_language = Column(String(10), default="hr")  # hr, en
    email_notifications = Column(Boolean, default=True)
    marketing_emails = Column(Boolean, default=False)

    # Venue management roles
    venue_owner = Column(Boolean, default=False)
    venue_manager = Column(Boolean, default=False)

    # Authentication
    email_verification_token = Column(String(255), nullable=True)
    password_reset_token = Column(String(255), nullable=True)
    password_reset_expires = Column(DateTime(timezone=True), nullable=True)
    last_login = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    favorite_events = relationship(
        "Event", secondary=user_favorites, back_populates="favorited_by"
    )
    user_profile = relationship(
        "UserProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    bookings = relationship("Booking", back_populates="user")
    tickets = relationship("Ticket", back_populates="user")
    venue_bookings = relationship("VenueBooking", back_populates="customer")
    venue_reviews = relationship("VenueReview", back_populates="user")
    owned_venues = relationship(
        "EnhancedVenue", foreign_keys="EnhancedVenue.owner_id", back_populates="owner"
    )
    managed_venues = relationship(
        "EnhancedVenue",
        foreign_keys="EnhancedVenue.manager_id",
        back_populates="manager",
    )

    # Social relationships
    social_posts = relationship(
        "SocialPost", back_populates="user", cascade="all, delete-orphan"
    )
    post_comments = relationship(
        "PostComment", back_populates="user", cascade="all, delete-orphan"
    )
    post_reactions = relationship(
        "PostReaction", back_populates="user", cascade="all, delete-orphan"
    )
    comment_reactions = relationship(
        "CommentReaction", back_populates="user", cascade="all, delete-orphan"
    )
    event_reviews = relationship(
        "EventReview", back_populates="user", cascade="all, delete-orphan"
    )
    sent_connections = relationship(
        "UserConnection",
        foreign_keys="UserConnection.requester_id",
        back_populates="requester",
    )
    received_connections = relationship(
        "UserConnection",
        foreign_keys="UserConnection.addressee_id",
        back_populates="addressee",
    )
    following = relationship(
        "UserFollow", foreign_keys="UserFollow.follower_id", back_populates="follower"
    )
    followers = relationship(
        "UserFollow", foreign_keys="UserFollow.following_id", back_populates="following"
    )
    event_attendances = relationship(
        "EventAttendance", back_populates="user", cascade="all, delete-orphan"
    )
    notifications = relationship(
        "SocialNotification",
        foreign_keys="SocialNotification.user_id",
        back_populates="user",
    )
    mentioned_in_posts = relationship(
        "SocialPost", secondary="post_mentions", back_populates="mentions"
    )
    created_groups = relationship("SocialGroup", back_populates="creator")
    group_memberships = relationship("GroupMembership", back_populates="user")
    group_posts = relationship("GroupPost", back_populates="user")

    # Event organizer relationship
    organized_events = relationship(
        "Event", foreign_keys="Event.organizer_id", back_populates="event_organizer"
    )

    @property
    def is_admin(self) -> bool:
        """Check if user has admin privileges."""
        return self.is_superuser


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)

    # Extended profile information
    website = Column(String(500), nullable=True)
    social_links = Column(Text, nullable=True)  # JSON string for social media links
    interests = Column(Text, nullable=True)  # JSON array of interests
    event_preferences = Column(Text, nullable=True)  # JSON object for event preferences

    # Privacy settings
    profile_visibility = Column(
        String(20), default="public"
    )  # public, friends, private
    show_email = Column(Boolean, default=False)
    show_phone = Column(Boolean, default=False)
    show_location = Column(Boolean, default=True)

    # Statistics (cached for performance)
    events_attended = Column(Integer, default=0)
    events_favorited = Column(Integer, default=0)
    reviews_written = Column(Integer, default=0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user = relationship("User", back_populates="user_profile")


class UserRole(Base):
    __tablename__ = "user_roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(
        String(50), unique=True, nullable=False
    )  # admin, moderator, organizer, user
    description = Column(Text, nullable=True)
    permissions = Column(Text, nullable=True)  # JSON array of permissions

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    users = relationship("UserRoleAssignment", back_populates="role")


class UserRoleAssignment(Base):
    __tablename__ = "user_role_assignments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role_id = Column(Integer, ForeignKey("user_roles.id"), nullable=False)
    assigned_by = Column(
        Integer, ForeignKey("users.id"), nullable=True
    )  # Who assigned this role
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)  # For temporary roles
    is_active = Column(Boolean, default=True)

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    role = relationship("UserRole", back_populates="users")
    assigner = relationship("User", foreign_keys=[assigned_by])
