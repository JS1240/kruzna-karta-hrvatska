import logging
import re
from collections import Counter
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, asc, desc, func, or_, text
from sqlalchemy.orm import Session

from ..models.event import Event
from ..models.social import (
    CommentReaction,
    ConnectionStatus,
    ContentReport,
    EventAttendance,
    EventReview,
    GroupMembership,
    GroupPost,
    HashtagTrend,
    NotificationType,
    PostComment,
    PostReaction,
    PostType,
    ReactionType,
    ReportReason,
    SocialGroup,
    SocialNotification,
    SocialPost,
    UserConnection,
    UserFollow,
    UserSocialProfile,
    post_mentions,
)
from ..models.social_schemas import (
    ContentReportCreate,
    EventAttendanceCreate,
    EventAttendanceUpdate,
    EventReviewCreate,
    EventReviewUpdate,
    PostCommentCreate,
    PostCommentUpdate,
    PostReactionCreate,
    PostSearchParams,
    SocialFeedParams,
    SocialNotificationCreate,
    SocialPostCreate,
    SocialPostUpdate,
    UserConnectionCreate,
    UserConnectionUpdate,
    UserFollowCreate,
    UserSearchParams,
    UserSocialProfileCreate,
    UserSocialProfileUpdate,
)
from ..models.user import User, UserProfile
from ..models.venue import Venue

logger = logging.getLogger(__name__)


class SocialService:
    """Comprehensive social features service"""

    def __init__(self, db: Session):
        self.db = db

    # User Profile Management
    def get_or_create_user_profile(self, user_id: int) -> UserSocialProfile:
        """Get or create user social profile"""
        profile = (
            self.db.query(UserSocialProfile)
            .filter(UserSocialProfile.user_id == user_id)
            .first()
        )
        if not profile:
            profile = UserSocialProfile(user_id=user_id)
            self.db.add(profile)
            self.db.commit()
            self.db.refresh(profile)
        return profile

    def update_user_profile(
        self, user_id: int, profile_data: UserSocialProfileUpdate
    ) -> UserSocialProfile:
        """Update user social profile"""
        profile = self.get_or_create_user_profile(user_id)

        update_data = profile_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(profile, field, value)

        self.db.commit()
        self.db.refresh(profile)

        logger.info(f"Updated social profile for user {user_id}")
        return profile

    def get_user_profile(self, user_id: int) -> Optional[UserSocialProfile]:
        """Get user social profile"""
        return (
            self.db.query(UserSocialProfile)
            .filter(UserSocialProfile.user_id == user_id)
            .first()
        )

    # Social Posts Management
    def create_post(self, user_id: int, post_data: SocialPostCreate) -> SocialPost:
        """Create a new social post"""
        # Extract hashtags from content
        hashtags = self._extract_hashtags(post_data.content or "")

        post = SocialPost(
            user_id=user_id,
            **post_data.dict(exclude={"mention_users"}),
            hashtags=hashtags,
        )

        self.db.add(post)
        self.db.commit()
        self.db.refresh(post)

        # Handle user mentions
        if post_data.mention_users:
            self._add_post_mentions(post.id, post_data.mention_users)

        # Update hashtag trends
        self._update_hashtag_trends(hashtags)

        # Update user stats
        self._update_user_post_count(user_id, 1)

        logger.info(f"Created post {post.id} by user {user_id}")
        return post

    def get_post(self, post_id: int) -> Optional[SocialPost]:
        """Get post by ID"""
        return self.db.query(SocialPost).filter(SocialPost.id == post_id).first()

    def update_post(
        self, post_id: int, user_id: int, post_data: SocialPostUpdate
    ) -> Optional[SocialPost]:
        """Update post (only by owner)"""
        post = self.get_post(post_id)
        if not post or post.user_id != user_id:
            return None

        update_data = post_data.dict(exclude_unset=True)

        # Update hashtags if content changed
        if "content" in update_data:
            hashtags = self._extract_hashtags(update_data["content"] or "")
            update_data["hashtags"] = hashtags
            self._update_hashtag_trends(hashtags)

        for field, value in update_data.items():
            setattr(post, field, value)

        self.db.commit()
        self.db.refresh(post)

        logger.info(f"Updated post {post_id}")
        return post

    def delete_post(self, post_id: int, user_id: int) -> bool:
        """Delete post (only by owner or admin)"""
        post = self.get_post(post_id)
        if not post or post.user_id != user_id:
            return False

        self.db.delete(post)
        self.db.commit()

        # Update user stats
        self._update_user_post_count(user_id, -1)

        logger.info(f"Deleted post {post_id}")
        return True

    def get_social_feed(
        self, user_id: int, feed_params: SocialFeedParams
    ) -> Tuple[List[SocialPost], int]:
        """Get personalized social feed"""
        query = self.db.query(SocialPost).filter(SocialPost.is_hidden == False)

        if feed_params.feed_type == "timeline":
            # User's own posts + connections' posts
            connections = self._get_user_connections(user_id)
            connection_ids = [
                c.addressee_id if c.requester_id == user_id else c.requester_id
                for c in connections
            ]
            connection_ids.append(user_id)  # Include user's own posts

            query = query.filter(SocialPost.user_id.in_(connection_ids))

        elif feed_params.feed_type == "discover":
            # Public posts, trending content
            query = query.filter(SocialPost.visibility == "public")
            # Boost featured and trending posts
            query = query.order_by(
                desc(SocialPost.is_featured),
                desc(SocialPost.likes_count + SocialPost.comments_count),
                desc(SocialPost.created_at),
            )

        elif feed_params.feed_type == "following":
            # Posts from followed users
            following = self._get_user_following(user_id)
            following_ids = [f.following_id for f in following]

            if following_ids:
                query = query.filter(SocialPost.user_id.in_(following_ids))
            else:
                # No following, return empty
                return [], 0

        # Filter by post type
        if feed_params.post_type:
            query = query.filter(SocialPost.post_type == feed_params.post_type)

        # Apply visibility and connection filters
        if not feed_params.include_connections_only:
            # Include public posts and posts from connections
            connections = self._get_user_connections(user_id)
            connection_ids = [
                c.addressee_id if c.requester_id == user_id else c.requester_id
                for c in connections
            ]
            connection_ids.append(user_id)

            query = query.filter(
                or_(
                    SocialPost.visibility == "public",
                    and_(
                        SocialPost.visibility == "friends",
                        SocialPost.user_id.in_(connection_ids),
                    ),
                    SocialPost.user_id == user_id,
                )
            )

        # Default ordering for timeline and following
        if feed_params.feed_type in ["timeline", "following"]:
            query = query.order_by(desc(SocialPost.created_at))

        # Get total count
        total = query.count()

        # Pagination
        offset = (feed_params.page - 1) * feed_params.size
        posts = query.offset(offset).limit(feed_params.size).all()

        return posts, total

    def search_posts(
        self, search_params: PostSearchParams
    ) -> Tuple[List[SocialPost], int]:
        """Search posts with filters"""
        query = self.db.query(SocialPost).filter(
            and_(SocialPost.is_hidden == False, SocialPost.visibility == "public")
        )

        # Text search
        if search_params.q:
            search_term = f"%{search_params.q}%"
            query = query.filter(
                or_(
                    SocialPost.content.ilike(search_term),
                    SocialPost.title.ilike(search_term),
                )
            )

        # Filter by post type
        if search_params.post_type:
            query = query.filter(SocialPost.post_type == search_params.post_type)

        # Filter by user
        if search_params.user_id:
            query = query.filter(SocialPost.user_id == search_params.user_id)

        # Filter by event
        if search_params.event_id:
            query = query.filter(SocialPost.event_id == search_params.event_id)

        # Filter by venue
        if search_params.venue_id:
            query = query.filter(SocialPost.venue_id == search_params.venue_id)

        # Filter by hashtags
        if search_params.hashtags:
            for hashtag in search_params.hashtags:
                query = query.filter(SocialPost.hashtags.contains([hashtag]))

        # Date range filter
        if search_params.date_from:
            query = query.filter(SocialPost.created_at >= search_params.date_from)

        if search_params.date_to:
            query = query.filter(SocialPost.created_at <= search_params.date_to)

        # Order by relevance and recency
        query = query.order_by(
            desc(SocialPost.likes_count + SocialPost.comments_count),
            desc(SocialPost.created_at),
        )

        total = query.count()

        # Pagination
        offset = (search_params.page - 1) * search_params.size
        posts = query.offset(offset).limit(search_params.size).all()

        return posts, total

    # Comments Management
    def create_comment(
        self, post_id: int, user_id: int, comment_data: PostCommentCreate
    ) -> PostComment:
        """Create post comment"""
        post = self.get_post(post_id)
        if not post or not post.allow_comments:
            raise ValueError("Comments not allowed on this post")

        comment = PostComment(post_id=post_id, user_id=user_id, **comment_data.dict())

        self.db.add(comment)

        # Update post comment count
        post.comments_count += 1

        # Update reply count for parent comment if this is a reply
        if comment_data.parent_comment_id:
            parent_comment = (
                self.db.query(PostComment)
                .filter(PostComment.id == comment_data.parent_comment_id)
                .first()
            )
            if parent_comment:
                parent_comment.replies_count += 1

        self.db.commit()
        self.db.refresh(comment)

        # Create notification for post owner
        if post.user_id != user_id:
            self._create_notification(
                user_id=post.user_id,
                notification_type=NotificationType.POST_COMMENT,
                title=f"New comment on your post",
                from_user_id=user_id,
                post_id=post_id,
                comment_id=comment.id,
            )

        logger.info(f"Created comment {comment.id} on post {post_id}")
        return comment

    def update_comment(
        self, comment_id: int, user_id: int, comment_data: PostCommentUpdate
    ) -> Optional[PostComment]:
        """Update comment (only by owner)"""
        comment = (
            self.db.query(PostComment).filter(PostComment.id == comment_id).first()
        )
        if not comment or comment.user_id != user_id:
            return None

        update_data = comment_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(comment, field, value)

        self.db.commit()
        self.db.refresh(comment)

        return comment

    def delete_comment(self, comment_id: int, user_id: int) -> bool:
        """Delete comment (only by owner or post owner)"""
        comment = (
            self.db.query(PostComment).filter(PostComment.id == comment_id).first()
        )
        if not comment:
            return False

        post = self.get_post(comment.post_id)
        if comment.user_id != user_id and post.user_id != user_id:
            return False

        # Update counts
        post.comments_count -= 1

        if comment.parent_comment_id:
            parent_comment = (
                self.db.query(PostComment)
                .filter(PostComment.id == comment.parent_comment_id)
                .first()
            )
            if parent_comment:
                parent_comment.replies_count -= 1

        self.db.delete(comment)
        self.db.commit()

        return True

    def get_post_comments(
        self, post_id: int, limit: int = 20, offset: int = 0
    ) -> List[PostComment]:
        """Get comments for a post"""
        return (
            self.db.query(PostComment)
            .filter(
                and_(
                    PostComment.post_id == post_id,
                    PostComment.is_hidden == False,
                    PostComment.parent_comment_id.is_(None),  # Top-level comments only
                )
            )
            .order_by(desc(PostComment.created_at))
            .offset(offset)
            .limit(limit)
            .all()
        )

    def get_comment_replies(self, comment_id: int) -> List[PostComment]:
        """Get replies to a comment"""
        return (
            self.db.query(PostComment)
            .filter(
                and_(
                    PostComment.parent_comment_id == comment_id,
                    PostComment.is_hidden == False,
                )
            )
            .order_by(asc(PostComment.created_at))
            .all()
        )

    # Reactions Management
    def toggle_post_reaction(
        self, post_id: int, user_id: int, reaction_data: PostReactionCreate
    ) -> Optional[PostReaction]:
        """Toggle post reaction (add or remove)"""
        existing_reaction = (
            self.db.query(PostReaction)
            .filter(
                and_(PostReaction.post_id == post_id, PostReaction.user_id == user_id)
            )
            .first()
        )

        post = self.get_post(post_id)
        if not post or not post.allow_reactions:
            return None

        if existing_reaction:
            if existing_reaction.reaction_type == reaction_data.reaction_type:
                # Remove reaction
                self.db.delete(existing_reaction)
                post.likes_count -= 1
                self.db.commit()
                return None
            else:
                # Update reaction type
                existing_reaction.reaction_type = reaction_data.reaction_type
                self.db.commit()
                self.db.refresh(existing_reaction)
                return existing_reaction
        else:
            # Add new reaction
            reaction = PostReaction(
                post_id=post_id,
                user_id=user_id,
                reaction_type=reaction_data.reaction_type,
            )
            self.db.add(reaction)
            post.likes_count += 1

            # Create notification for post owner
            if post.user_id != user_id:
                self._create_notification(
                    user_id=post.user_id,
                    notification_type=NotificationType.POST_LIKE,
                    title=f"Someone liked your post",
                    from_user_id=user_id,
                    post_id=post_id,
                )

            self.db.commit()
            self.db.refresh(reaction)
            return reaction

    def toggle_comment_reaction(
        self, comment_id: int, user_id: int, reaction_data: PostReactionCreate
    ) -> Optional[CommentReaction]:
        """Toggle comment reaction"""
        existing_reaction = (
            self.db.query(CommentReaction)
            .filter(
                and_(
                    CommentReaction.comment_id == comment_id,
                    CommentReaction.user_id == user_id,
                )
            )
            .first()
        )

        comment = (
            self.db.query(PostComment).filter(PostComment.id == comment_id).first()
        )
        if not comment:
            return None

        if existing_reaction:
            if existing_reaction.reaction_type == reaction_data.reaction_type:
                # Remove reaction
                self.db.delete(existing_reaction)
                comment.likes_count -= 1
                self.db.commit()
                return None
            else:
                # Update reaction type
                existing_reaction.reaction_type = reaction_data.reaction_type
                self.db.commit()
                self.db.refresh(existing_reaction)
                return existing_reaction
        else:
            # Add new reaction
            reaction = CommentReaction(
                comment_id=comment_id,
                user_id=user_id,
                reaction_type=reaction_data.reaction_type,
            )
            self.db.add(reaction)
            comment.likes_count += 1
            self.db.commit()
            self.db.refresh(reaction)
            return reaction

    # Event Reviews Management
    def create_event_review(
        self, user_id: int, review_data: EventReviewCreate
    ) -> EventReview:
        """Create event review"""
        # Check if user already reviewed this event
        existing_review = (
            self.db.query(EventReview)
            .filter(
                and_(
                    EventReview.event_id == review_data.event_id,
                    EventReview.user_id == user_id,
                )
            )
            .first()
        )

        if existing_review:
            raise ValueError("User has already reviewed this event")

        # Verify event exists
        event = self.db.query(Event).filter(Event.id == review_data.event_id).first()
        if not event:
            raise ValueError("Event not found")

        review = EventReview(user_id=user_id, **review_data.dict())

        self.db.add(review)
        self.db.commit()
        self.db.refresh(review)

        # Update user review count
        profile = self.get_or_create_user_profile(user_id)
        profile.reviews_count += 1

        self.db.commit()

        logger.info(
            f"Created event review {review.id} for event {review_data.event_id}"
        )
        return review

    def update_event_review(
        self, review_id: int, user_id: int, review_data: EventReviewUpdate
    ) -> Optional[EventReview]:
        """Update event review"""
        review = self.db.query(EventReview).filter(EventReview.id == review_id).first()
        if not review:
            return None

        # Check permissions
        event = self.db.query(Event).filter(Event.id == review.event_id).first()
        is_review_author = review.user_id == user_id
        is_event_organizer = event and event.organizer == user_id  # Simplified check

        if not (is_review_author or is_event_organizer):
            return None

        update_data = review_data.dict(exclude_unset=True)

        # Only organizers can add responses
        if is_event_organizer and not is_review_author:
            if "organizer_response" in update_data:
                review.organizer_response = update_data["organizer_response"]
                review.organizer_responded_at = datetime.utcnow()
        elif is_review_author:
            # Authors can update their review content
            for field, value in update_data.items():
                if field not in ["organizer_response"]:
                    setattr(review, field, value)

        self.db.commit()
        self.db.refresh(review)
        return review

    def get_event_reviews(
        self, event_id: int, limit: int = 20, offset: int = 0
    ) -> Tuple[List[EventReview], int]:
        """Get reviews for an event"""
        query = self.db.query(EventReview).filter(
            and_(EventReview.event_id == event_id, EventReview.is_public == True)
        )

        total = query.count()
        reviews = (
            query.order_by(desc(EventReview.created_at))
            .offset(offset)
            .limit(limit)
            .all()
        )

        return reviews, total

    # User Connections Management
    def send_connection_request(
        self, requester_id: int, connection_data: UserConnectionCreate
    ) -> UserConnection:
        """Send connection request"""
        if requester_id == connection_data.addressee_id:
            raise ValueError("Cannot connect to yourself")

        # Check if connection already exists
        existing = (
            self.db.query(UserConnection)
            .filter(
                or_(
                    and_(
                        UserConnection.requester_id == requester_id,
                        UserConnection.addressee_id == connection_data.addressee_id,
                    ),
                    and_(
                        UserConnection.requester_id == connection_data.addressee_id,
                        UserConnection.addressee_id == requester_id,
                    ),
                )
            )
            .first()
        )

        if existing:
            raise ValueError("Connection already exists")

        # Check if addressee allows connection requests
        addressee_profile = self.get_user_profile(connection_data.addressee_id)
        if addressee_profile and not addressee_profile.allow_connection_requests:
            raise ValueError("User does not accept connection requests")

        connection = UserConnection(requester_id=requester_id, **connection_data.dict())

        self.db.add(connection)
        self.db.commit()
        self.db.refresh(connection)

        # Create notification
        self._create_notification(
            user_id=connection_data.addressee_id,
            notification_type=NotificationType.CONNECTION_REQUEST,
            title="New connection request",
            from_user_id=requester_id,
            connection_id=connection.id,
        )

        logger.info(
            f"Connection request sent from {requester_id} to {connection_data.addressee_id}"
        )
        return connection

    def respond_to_connection_request(
        self, connection_id: int, user_id: int, response_data: UserConnectionUpdate
    ) -> Optional[UserConnection]:
        """Respond to connection request"""
        connection = (
            self.db.query(UserConnection)
            .filter(UserConnection.id == connection_id)
            .first()
        )
        if not connection or connection.addressee_id != user_id:
            return None

        connection.status = response_data.status

        if response_data.status == ConnectionStatus.ACCEPTED:
            connection.accepted_at = datetime.utcnow()

            # Update connection counts
            self._update_user_connection_count(connection.requester_id, 1)
            self._update_user_connection_count(connection.addressee_id, 1)

            # Create notification for requester
            self._create_notification(
                user_id=connection.requester_id,
                notification_type=NotificationType.CONNECTION_ACCEPTED,
                title="Connection request accepted",
                from_user_id=user_id,
                connection_id=connection.id,
            )

        self.db.commit()
        self.db.refresh(connection)
        return connection

    def get_user_connections(
        self, user_id: int, status: Optional[ConnectionStatus] = None
    ) -> List[UserConnection]:
        """Get user connections"""
        query = self.db.query(UserConnection).filter(
            or_(
                UserConnection.requester_id == user_id,
                UserConnection.addressee_id == user_id,
            )
        )

        if status:
            query = query.filter(UserConnection.status == status)

        return query.order_by(desc(UserConnection.created_at)).all()

    def remove_connection(self, connection_id: int, user_id: int) -> bool:
        """Remove connection"""
        connection = (
            self.db.query(UserConnection)
            .filter(UserConnection.id == connection_id)
            .first()
        )
        if not connection:
            return False

        # Check if user is part of this connection
        if connection.requester_id != user_id and connection.addressee_id != user_id:
            return False

        # Update connection counts if connection was accepted
        if connection.status == ConnectionStatus.ACCEPTED:
            self._update_user_connection_count(connection.requester_id, -1)
            self._update_user_connection_count(connection.addressee_id, -1)

        self.db.delete(connection)
        self.db.commit()
        return True

    # Follow System
    def follow_user(
        self, follower_id: int, follow_data: UserFollowCreate
    ) -> UserFollow:
        """Follow a user"""
        if follower_id == follow_data.following_id:
            raise ValueError("Cannot follow yourself")

        # Check if already following
        existing = (
            self.db.query(UserFollow)
            .filter(
                and_(
                    UserFollow.follower_id == follower_id,
                    UserFollow.following_id == follow_data.following_id,
                )
            )
            .first()
        )

        if existing:
            raise ValueError("Already following this user")

        follow = UserFollow(follower_id=follower_id, **follow_data.dict())

        self.db.add(follow)

        # Update follow counts
        self._update_user_following_count(follower_id, 1)
        self._update_user_followers_count(follow_data.following_id, 1)

        self.db.commit()
        self.db.refresh(follow)

        logger.info(f"User {follower_id} started following {follow_data.following_id}")
        return follow

    def unfollow_user(self, follower_id: int, following_id: int) -> bool:
        """Unfollow a user"""
        follow = (
            self.db.query(UserFollow)
            .filter(
                and_(
                    UserFollow.follower_id == follower_id,
                    UserFollow.following_id == following_id,
                )
            )
            .first()
        )

        if not follow:
            return False

        # Update follow counts
        self._update_user_following_count(follower_id, -1)
        self._update_user_followers_count(following_id, -1)

        self.db.delete(follow)
        self.db.commit()

        return True

    # Event Attendance
    def update_event_attendance(
        self, user_id: int, attendance_data: EventAttendanceCreate
    ) -> EventAttendance:
        """Update event attendance status"""
        # Check if attendance record exists
        existing = (
            self.db.query(EventAttendance)
            .filter(
                and_(
                    EventAttendance.event_id == attendance_data.event_id,
                    EventAttendance.user_id == user_id,
                )
            )
            .first()
        )

        if existing:
            # Update existing record
            update_data = attendance_data.dict(exclude={"event_id"})
            for field, value in update_data.items():
                setattr(existing, field, value)

            self.db.commit()
            self.db.refresh(existing)
            return existing
        else:
            # Create new record
            attendance = EventAttendance(user_id=user_id, **attendance_data.dict())

            self.db.add(attendance)

            # Update user events attended count if status is 'going'
            if attendance_data.attendance_status == "going":
                profile = self.get_or_create_user_profile(user_id)
                profile.events_attended_count += 1

            self.db.commit()
            self.db.refresh(attendance)
            return attendance

    def check_in_to_event(
        self, user_id: int, event_id: int, location: Optional[str] = None
    ) -> bool:
        """Check in to event"""
        attendance = (
            self.db.query(EventAttendance)
            .filter(
                and_(
                    EventAttendance.event_id == event_id,
                    EventAttendance.user_id == user_id,
                    EventAttendance.attendance_status == "going",
                )
            )
            .first()
        )

        if not attendance:
            return False

        attendance.checked_in = True
        attendance.check_in_time = datetime.utcnow()
        attendance.check_in_location = location

        self.db.commit()
        return True

    # Notifications
    def get_user_notifications(
        self, user_id: int, limit: int = 20, offset: int = 0
    ) -> Tuple[List[SocialNotification], int, int]:
        """Get user notifications"""
        query = self.db.query(SocialNotification).filter(
            SocialNotification.user_id == user_id
        )

        total = query.count()
        unread_count = query.filter(SocialNotification.is_read == False).count()

        notifications = (
            query.order_by(desc(SocialNotification.created_at))
            .offset(offset)
            .limit(limit)
            .all()
        )

        return notifications, total, unread_count

    def mark_notification_as_read(self, notification_id: int, user_id: int) -> bool:
        """Mark notification as read"""
        notification = (
            self.db.query(SocialNotification)
            .filter(
                and_(
                    SocialNotification.id == notification_id,
                    SocialNotification.user_id == user_id,
                )
            )
            .first()
        )

        if not notification:
            return False

        notification.is_read = True
        notification.read_at = datetime.utcnow()
        self.db.commit()
        return True

    def mark_all_notifications_as_read(self, user_id: int) -> int:
        """Mark all notifications as read"""
        count = (
            self.db.query(SocialNotification)
            .filter(
                and_(
                    SocialNotification.user_id == user_id,
                    SocialNotification.is_read == False,
                )
            )
            .update({"is_read": True, "read_at": datetime.utcnow()})
        )

        self.db.commit()
        return count

    # Content Reporting
    def report_content(
        self, reporter_id: int, report_data: ContentReportCreate
    ) -> ContentReport:
        """Report inappropriate content"""
        report = ContentReport(reporter_id=reporter_id, **report_data.dict())

        self.db.add(report)
        self.db.commit()
        self.db.refresh(report)

        logger.info(f"Content reported by user {reporter_id}: {report_data.reason}")
        return report

    # Trending and Discovery
    def get_trending_hashtags(self, limit: int = 10) -> List[HashtagTrend]:
        """Get trending hashtags"""
        return (
            self.db.query(HashtagTrend)
            .filter(HashtagTrend.is_trending == True)
            .order_by(desc(HashtagTrend.trend_score))
            .limit(limit)
            .all()
        )

    def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """Get comprehensive user social stats"""
        profile = self.get_or_create_user_profile(user_id)

        # Get total likes and comments received
        posts = self.db.query(SocialPost).filter(SocialPost.user_id == user_id).all()
        total_likes_received = sum(post.likes_count for post in posts)
        total_comments_received = sum(post.comments_count for post in posts)

        return {
            "user_id": user_id,
            "connections_count": profile.connections_count,
            "followers_count": profile.followers_count,
            "following_count": profile.following_count,
            "posts_count": profile.posts_count,
            "reviews_count": profile.reviews_count,
            "events_attended_count": profile.events_attended_count,
            "total_likes_received": total_likes_received,
            "total_comments_received": total_comments_received,
        }

    # Search Users
    def search_users(self, search_params: UserSearchParams) -> Tuple[List[User], int]:
        """Search users with social features"""
        query = self.db.query(User).join(
            UserProfile, User.id == UserProfile.user_id, isouter=True
        )

        # Text search
        if search_params.q:
            search_term = f"%{search_params.q}%"
            query = query.filter(
                or_(
                    User.username.ilike(search_term),
                    User.first_name.ilike(search_term),
                    User.last_name.ilike(search_term),
                    UserProfile.display_name.ilike(search_term),
                )
            )

        # Location filter
        if search_params.location:
            query = query.filter(
                UserProfile.location.ilike(f"%{search_params.location}%")
            )

        # Interest filter
        if search_params.interests:
            for interest in search_params.interests:
                query = query.filter(UserProfile.interests.contains([interest]))

        # Badge filters
        if search_params.is_verified is not None:
            query = query.filter(UserProfile.is_verified == search_params.is_verified)

        if search_params.is_event_organizer is not None:
            query = query.filter(
                UserProfile.is_event_organizer == search_params.is_event_organizer
            )

        if search_params.is_venue_owner is not None:
            query = query.filter(
                UserProfile.is_venue_owner == search_params.is_venue_owner
            )

        # Order by activity and relevance
        query = query.order_by(
            desc(UserProfile.connections_count),
            desc(UserProfile.posts_count),
            User.username,
        )

        total = query.count()

        # Pagination
        offset = (search_params.page - 1) * search_params.size
        users = query.offset(offset).limit(search_params.size).all()

        return users, total

    # Helper Methods
    def _extract_hashtags(self, content: str) -> List[str]:
        """Extract hashtags from content"""
        if not content:
            return []

        hashtag_pattern = r"#(\w+)"
        hashtags = re.findall(hashtag_pattern, content.lower())
        return list(set(hashtags))  # Remove duplicates

    def _add_post_mentions(self, post_id: int, user_ids: List[int]):
        """Add user mentions to post"""
        for user_id in user_ids:
            # Check if user exists and create mention
            user = self.db.query(User).filter(User.id == user_id).first()
            if user:
                insert_stmt = post_mentions.insert().values(
                    post_id=post_id, user_id=user_id
                )
                self.db.execute(insert_stmt)

                # Create notification
                self._create_notification(
                    user_id=user_id,
                    notification_type=NotificationType.MENTION,
                    title="You were mentioned in a post",
                    post_id=post_id,
                )

    def _update_hashtag_trends(self, hashtags: List[str]):
        """Update hashtag trend statistics"""
        for hashtag in hashtags:
            trend = (
                self.db.query(HashtagTrend)
                .filter(HashtagTrend.hashtag == hashtag)
                .first()
            )
            if trend:
                trend.usage_count += 1
                trend.daily_usage += 1
                trend.last_used = datetime.utcnow()
            else:
                trend = HashtagTrend(hashtag=hashtag, usage_count=1, daily_usage=1)
                self.db.add(trend)

    def _update_user_post_count(self, user_id: int, delta: int):
        """Update user post count"""
        profile = self.get_or_create_user_profile(user_id)
        profile.posts_count = max(0, profile.posts_count + delta)

    def _update_user_connection_count(self, user_id: int, delta: int):
        """Update user connection count"""
        profile = self.get_or_create_user_profile(user_id)
        profile.connections_count = max(0, profile.connections_count + delta)

    def _update_user_following_count(self, user_id: int, delta: int):
        """Update user following count"""
        profile = self.get_or_create_user_profile(user_id)
        profile.following_count = max(0, profile.following_count + delta)

    def _update_user_followers_count(self, user_id: int, delta: int):
        """Update user followers count"""
        profile = self.get_or_create_user_profile(user_id)
        profile.followers_count = max(0, profile.followers_count + delta)

    def _get_user_connections(self, user_id: int) -> List[UserConnection]:
        """Get accepted user connections"""
        return (
            self.db.query(UserConnection)
            .filter(
                and_(
                    or_(
                        UserConnection.requester_id == user_id,
                        UserConnection.addressee_id == user_id,
                    ),
                    UserConnection.status == ConnectionStatus.ACCEPTED,
                )
            )
            .all()
        )

    def _get_user_following(self, user_id: int) -> List[UserFollow]:
        """Get users that the given user is following"""
        return self.db.query(UserFollow).filter(UserFollow.follower_id == user_id).all()

    def _create_notification(
        self, user_id: int, notification_type: NotificationType, title: str, **kwargs
    ):
        """Create a notification"""
        notification_data = SocialNotificationCreate(
            user_id=user_id, notification_type=notification_type, title=title, **kwargs
        )

        notification = SocialNotification(**notification_data.dict())
        self.db.add(notification)
