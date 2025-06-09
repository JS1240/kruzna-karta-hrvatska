"""Add comprehensive social features system

Revision ID: 010_add_social_features
Revises: 009_add_venue_management
Create Date: 2025-01-08 17:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '010_add_social_features'
down_revision = '009_add_venue_management'
branch_labels = None
depends_on = None


def upgrade():
    # Create enum types for social features
    connection_status_enum = postgresql.ENUM(
        'pending', 'accepted', 'blocked', 'declined',
        name='connection_status_enum'
    )
    connection_status_enum.create(op.get_bind())
    
    post_type_enum = postgresql.ENUM(
        'text', 'image', 'video', 'event_share', 'venue_share', 'poll', 'announcement',
        name='post_type_enum'
    )
    post_type_enum.create(op.get_bind())
    
    reaction_type_enum = postgresql.ENUM(
        'like', 'love', 'laugh', 'wow', 'sad', 'angry',
        name='reaction_type_enum'
    )
    reaction_type_enum.create(op.get_bind())
    
    notification_type_enum = postgresql.ENUM(
        'connection_request', 'connection_accepted', 'post_like', 'post_comment',
        'comment_reply', 'event_invitation', 'event_reminder', 'review_response', 'mention',
        name='notification_type_enum'
    )
    notification_type_enum.create(op.get_bind())
    
    report_reason_enum = postgresql.ENUM(
        'spam', 'harassment', 'inappropriate_content', 'false_information', 'copyright_violation', 'other',
        name='report_reason_enum'
    )
    report_reason_enum.create(op.get_bind())
    
    # Create user_social_profiles table
    op.create_table(
        'user_social_profiles',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False),
        
        # Social profile information
        sa.Column('display_name', sa.String(100)),
        sa.Column('tagline', sa.String(200)),
        sa.Column('about', sa.Text),
        sa.Column('interests', postgresql.ARRAY(sa.String)),
        sa.Column('favorite_event_types', postgresql.ARRAY(sa.String)),
        sa.Column('location', sa.String(100)),
        
        # Privacy settings
        sa.Column('profile_visibility', sa.String(20), default='public'),
        sa.Column('show_email', sa.Boolean, default=False),
        sa.Column('show_phone', sa.Boolean, default=False),
        sa.Column('show_location', sa.Boolean, default=True),
        sa.Column('show_events_attended', sa.Boolean, default=True),
        sa.Column('allow_connection_requests', sa.Boolean, default=True),
        sa.Column('allow_event_invitations', sa.Boolean, default=True),
        
        # Social stats (cached for performance)
        sa.Column('connections_count', sa.Integer, default=0),
        sa.Column('posts_count', sa.Integer, default=0),
        sa.Column('events_attended_count', sa.Integer, default=0),
        sa.Column('reviews_count', sa.Integer, default=0),
        sa.Column('followers_count', sa.Integer, default=0),
        sa.Column('following_count', sa.Integer, default=0),
        
        # Verification and badges
        sa.Column('is_verified', sa.Boolean, default=False),
        sa.Column('is_event_organizer', sa.Boolean, default=False),
        sa.Column('is_venue_owner', sa.Boolean, default=False),
        sa.Column('badges', postgresql.ARRAY(sa.String)),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now())
    )
    
    # Create social_posts table
    op.create_table(
        'social_posts',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        
        # Post content
        sa.Column('post_type', post_type_enum, default='text', index=True),
        sa.Column('content', sa.Text),
        sa.Column('title', sa.String(200)),
        
        # Media attachments
        sa.Column('images', postgresql.ARRAY(sa.String)),
        sa.Column('videos', postgresql.ARRAY(sa.String)),
        
        # Related content
        sa.Column('event_id', sa.Integer, sa.ForeignKey('events.id'), index=True),
        sa.Column('venue_id', sa.Integer, sa.ForeignKey('venues.id'), index=True),
        
        # Poll data
        sa.Column('poll_options', postgresql.JSONB),
        sa.Column('poll_expires_at', sa.DateTime(timezone=True)),
        sa.Column('poll_multiple_choice', sa.Boolean, default=False),
        
        # Post metadata
        sa.Column('is_pinned', sa.Boolean, default=False),
        sa.Column('is_featured', sa.Boolean, default=False),
        sa.Column('visibility', sa.String(20), default='public'),
        sa.Column('allow_comments', sa.Boolean, default=True),
        sa.Column('allow_reactions', sa.Boolean, default=True),
        
        # Engagement stats
        sa.Column('likes_count', sa.Integer, default=0),
        sa.Column('comments_count', sa.Integer, default=0),
        sa.Column('shares_count', sa.Integer, default=0),
        sa.Column('views_count', sa.Integer, default=0),
        
        # Content moderation
        sa.Column('is_flagged', sa.Boolean, default=False),
        sa.Column('is_hidden', sa.Boolean, default=False),
        sa.Column('moderation_notes', sa.Text),
        
        # SEO and search
        sa.Column('hashtags', postgresql.ARRAY(sa.String)),
        sa.Column('search_vector', sa.Text),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now())
    )
    
    # Create post_mentions association table
    op.create_table(
        'post_mentions',
        sa.Column('post_id', sa.Integer, sa.ForeignKey('social_posts.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now())
    )
    
    # Create post_comments table
    op.create_table(
        'post_comments',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('post_id', sa.Integer, sa.ForeignKey('social_posts.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('parent_comment_id', sa.Integer, sa.ForeignKey('post_comments.id'), index=True),
        
        # Comment content
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('images', postgresql.ARRAY(sa.String)),
        
        # Engagement
        sa.Column('likes_count', sa.Integer, default=0),
        sa.Column('replies_count', sa.Integer, default=0),
        
        # Moderation
        sa.Column('is_flagged', sa.Boolean, default=False),
        sa.Column('is_hidden', sa.Boolean, default=False),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now())
    )
    
    # Create post_reactions table
    op.create_table(
        'post_reactions',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('post_id', sa.Integer, sa.ForeignKey('social_posts.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('reaction_type', reaction_type_enum, default='like'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        
        # Constraints
        sa.UniqueConstraint('post_id', 'user_id', name='unique_post_user_reaction')
    )
    
    # Create comment_reactions table
    op.create_table(
        'comment_reactions',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('comment_id', sa.Integer, sa.ForeignKey('post_comments.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('reaction_type', reaction_type_enum, default='like'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        
        # Constraints
        sa.UniqueConstraint('comment_id', 'user_id', name='unique_comment_user_reaction')
    )
    
    # Create event_reviews table
    op.create_table(
        'event_reviews',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('event_id', sa.Integer, sa.ForeignKey('events.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('booking_id', sa.Integer, sa.ForeignKey('bookings.id'), index=True),
        
        # Review content
        sa.Column('rating', sa.Integer, nullable=False),
        sa.Column('title', sa.String(200)),
        sa.Column('review_text', sa.Text),
        
        # Detailed ratings
        sa.Column('organization_rating', sa.Integer),
        sa.Column('value_rating', sa.Integer),
        sa.Column('venue_rating', sa.Integer),
        sa.Column('content_rating', sa.Integer),
        sa.Column('atmosphere_rating', sa.Integer),
        
        # Review metadata
        sa.Column('is_verified', sa.Boolean, default=False),
        sa.Column('is_public', sa.Boolean, default=True),
        sa.Column('helpful_votes', sa.Integer, default=0),
        
        # Media attachments
        sa.Column('images', postgresql.ARRAY(sa.String)),
        sa.Column('videos', postgresql.ARRAY(sa.String)),
        
        # Response from organizer
        sa.Column('organizer_response', sa.Text),
        sa.Column('organizer_responded_at', sa.DateTime(timezone=True)),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        
        # Constraints
        sa.CheckConstraint('rating >= 1 AND rating <= 5', name='event_review_rating_check'),
        sa.CheckConstraint('organization_rating IS NULL OR (organization_rating >= 1 AND organization_rating <= 5)', name='organization_rating_check'),
        sa.CheckConstraint('value_rating IS NULL OR (value_rating >= 1 AND value_rating <= 5)', name='value_rating_check'),
        sa.CheckConstraint('venue_rating IS NULL OR (venue_rating >= 1 AND venue_rating <= 5)', name='venue_rating_check'),
        sa.CheckConstraint('content_rating IS NULL OR (content_rating >= 1 AND content_rating <= 5)', name='content_rating_check'),
        sa.CheckConstraint('atmosphere_rating IS NULL OR (atmosphere_rating >= 1 AND atmosphere_rating <= 5)', name='atmosphere_rating_check'),
        sa.UniqueConstraint('event_id', 'user_id', name='unique_event_user_review')
    )
    
    # Create user_social_connections table
    op.create_table(
        'user_social_connections',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('requester_id', sa.Integer, sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('addressee_id', sa.Integer, sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        
        sa.Column('status', connection_status_enum, default='pending', index=True),
        sa.Column('connection_message', sa.Text),
        
        # Connection metadata
        sa.Column('connection_strength', sa.Integer, default=1),
        sa.Column('mutual_connections_count', sa.Integer, default=0),
        sa.Column('interaction_score', sa.Integer, default=0),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('accepted_at', sa.DateTime(timezone=True)),
        
        # Constraints
        sa.CheckConstraint('requester_id != addressee_id', name='no_self_connection'),
        sa.UniqueConstraint('requester_id', 'addressee_id', name='unique_user_connection')
    )
    
    # Create user_follows table
    op.create_table(
        'user_follows',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('follower_id', sa.Integer, sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('following_id', sa.Integer, sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        
        # Follow settings
        sa.Column('receive_notifications', sa.Boolean, default=True),
        
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        
        # Constraints
        sa.CheckConstraint('follower_id != following_id', name='no_self_follow'),
        sa.UniqueConstraint('follower_id', 'following_id', name='unique_user_follow')
    )
    
    # Create event_attendance table
    op.create_table(
        'event_attendance',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('event_id', sa.Integer, sa.ForeignKey('events.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        
        # Attendance status
        sa.Column('attendance_status', sa.String(20), default='going'),
        sa.Column('visibility', sa.String(20), default='public'),
        
        # Check-in information
        sa.Column('checked_in', sa.Boolean, default=False),
        sa.Column('check_in_time', sa.DateTime(timezone=True)),
        sa.Column('check_in_location', sa.String(255)),
        
        # Social sharing
        sa.Column('shared_on_timeline', sa.Boolean, default=False),
        
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        
        # Constraints
        sa.UniqueConstraint('event_id', 'user_id', name='unique_event_attendance')
    )
    
    # Create social_notifications table
    op.create_table(
        'social_notifications',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        
        # Notification details
        sa.Column('notification_type', notification_type_enum, nullable=False, index=True),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('message', sa.Text),
        
        # Related entities
        sa.Column('from_user_id', sa.Integer, sa.ForeignKey('users.id'), index=True),
        sa.Column('post_id', sa.Integer, sa.ForeignKey('social_posts.id'), index=True),
        sa.Column('comment_id', sa.Integer, sa.ForeignKey('post_comments.id'), index=True),
        sa.Column('event_id', sa.Integer, sa.ForeignKey('events.id'), index=True),
        sa.Column('connection_id', sa.Integer, sa.ForeignKey('user_social_connections.id'), index=True),
        
        # Notification state
        sa.Column('is_read', sa.Boolean, default=False, index=True),
        sa.Column('is_seen', sa.Boolean, default=False),
        
        # Action data
        sa.Column('action_url', sa.String(500)),
        sa.Column('action_data', postgresql.JSONB),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('read_at', sa.DateTime(timezone=True))
    )
    
    # Create content_reports table
    op.create_table(
        'content_reports',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('reporter_id', sa.Integer, sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        
        # Reported content
        sa.Column('post_id', sa.Integer, sa.ForeignKey('social_posts.id'), index=True),
        sa.Column('comment_id', sa.Integer, sa.ForeignKey('post_comments.id'), index=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id'), index=True),
        
        # Report details
        sa.Column('reason', report_reason_enum, nullable=False),
        sa.Column('description', sa.Text),
        
        # Moderation
        sa.Column('status', sa.String(20), default='pending', index=True),
        sa.Column('moderator_id', sa.Integer, sa.ForeignKey('users.id'), index=True),
        sa.Column('moderator_notes', sa.Text),
        sa.Column('action_taken', sa.String(100)),
        
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('resolved_at', sa.DateTime(timezone=True))
    )
    
    # Create hashtag_trends table
    op.create_table(
        'hashtag_trends',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('hashtag', sa.String(100), nullable=False, unique=True, index=True),
        
        # Trend metrics
        sa.Column('usage_count', sa.Integer, default=0),
        sa.Column('weekly_usage', sa.Integer, default=0),
        sa.Column('daily_usage', sa.Integer, default=0),
        sa.Column('peak_usage_date', sa.DateTime(timezone=True)),
        
        # Trend analysis
        sa.Column('trend_score', sa.Integer, default=0),
        sa.Column('is_trending', sa.Boolean, default=False, index=True),
        sa.Column('category', sa.String(50)),
        
        # Timestamps
        sa.Column('first_used', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('last_used', sa.DateTime(timezone=True), server_default=sa.func.now())
    )
    
    # Create social_groups table
    op.create_table(
        'social_groups',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('creator_id', sa.Integer, sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        
        # Group details
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('category', sa.String(50)),
        
        # Group settings
        sa.Column('group_type', sa.String(20), default='public'),
        sa.Column('join_approval_required', sa.Boolean, default=False),
        sa.Column('allow_member_posts', sa.Boolean, default=True),
        
        # Group image and branding
        sa.Column('cover_image', sa.String(500)),
        sa.Column('avatar_image', sa.String(500)),
        
        # Stats
        sa.Column('members_count', sa.Integer, default=1),
        sa.Column('posts_count', sa.Integer, default=0),
        
        # Moderation
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('is_featured', sa.Boolean, default=False),
        
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now())
    )
    
    # Create group_memberships table
    op.create_table(
        'group_memberships',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('group_id', sa.Integer, sa.ForeignKey('social_groups.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        
        # Membership details
        sa.Column('role', sa.String(20), default='member'),
        sa.Column('status', sa.String(20), default='active'),
        
        # Permissions
        sa.Column('can_post', sa.Boolean, default=True),
        sa.Column('can_moderate', sa.Boolean, default=False),
        sa.Column('can_invite', sa.Boolean, default=True),
        
        sa.Column('joined_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        
        # Constraints
        sa.UniqueConstraint('group_id', 'user_id', name='unique_group_membership')
    )
    
    # Create group_posts table
    op.create_table(
        'group_posts',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('group_id', sa.Integer, sa.ForeignKey('social_groups.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        
        # Post content
        sa.Column('title', sa.String(200)),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('post_type', post_type_enum, default='text'),
        
        # Media and attachments
        sa.Column('images', postgresql.ARRAY(sa.String)),
        sa.Column('videos', postgresql.ARRAY(sa.String)),
        
        # Engagement
        sa.Column('likes_count', sa.Integer, default=0),
        sa.Column('comments_count', sa.Integer, default=0),
        
        # Moderation
        sa.Column('is_pinned', sa.Boolean, default=False),
        sa.Column('is_approved', sa.Boolean, default=True),
        sa.Column('is_flagged', sa.Boolean, default=False),
        
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now())
    )
    
    # Create optimized indexes for social features
    op.create_index('idx_social_posts_user_date', 'social_posts', ['user_id', 'created_at', 'visibility'])
    op.create_index('idx_social_posts_hashtags', 'social_posts', ['hashtags'], postgresql_using='gin')
    op.create_index('idx_social_posts_engagement', 'social_posts', ['likes_count', 'comments_count', 'created_at'])
    op.create_index('idx_social_posts_trending', 'social_posts', ['is_featured', 'likes_count', 'comments_count'])
    
    op.create_index('idx_post_comments_post_date', 'post_comments', ['post_id', 'created_at'])
    op.create_index('idx_post_comments_parent', 'post_comments', ['parent_comment_id', 'created_at'])
    
    op.create_index('idx_post_reactions_post_type', 'post_reactions', ['post_id', 'reaction_type'])
    op.create_index('idx_comment_reactions_comment_type', 'comment_reactions', ['comment_id', 'reaction_type'])
    
    op.create_index('idx_event_reviews_event_rating', 'event_reviews', ['event_id', 'rating', 'is_public'])
    op.create_index('idx_event_reviews_user', 'event_reviews', ['user_id', 'created_at'])
    
    op.create_index('idx_user_connections_status', 'user_social_connections', ['status', 'created_at'])
    op.create_index('idx_user_connections_requester', 'user_social_connections', ['requester_id', 'status'])
    op.create_index('idx_user_connections_addressee', 'user_social_connections', ['addressee_id', 'status'])
    
    op.create_index('idx_user_follows_follower', 'user_follows', ['follower_id'])
    op.create_index('idx_user_follows_following', 'user_follows', ['following_id'])
    
    op.create_index('idx_event_attendance_user', 'event_attendance', ['user_id', 'attendance_status'])
    op.create_index('idx_event_attendance_event', 'event_attendance', ['event_id', 'attendance_status'])
    
    op.create_index('idx_social_notifications_user_read', 'social_notifications', ['user_id', 'is_read', 'created_at'])
    op.create_index('idx_social_notifications_type', 'social_notifications', ['notification_type', 'created_at'])
    
    op.create_index('idx_hashtag_trending', 'hashtag_trends', ['is_trending', 'trend_score'])
    op.create_index('idx_hashtag_usage', 'hashtag_trends', ['usage_count', 'daily_usage'])
    
    # Add search indexes for full-text search
    op.execute("""
        CREATE INDEX idx_social_posts_search ON social_posts 
        USING gin(to_tsvector('english', COALESCE(title, '') || ' ' || COALESCE(content, '')))
    """)
    
    op.execute("""
        CREATE INDEX idx_user_profiles_search ON user_social_profiles 
        USING gin(to_tsvector('english', COALESCE(display_name, '') || ' ' || COALESCE(about, '')))
    """)


def downgrade():
    # Drop indexes first
    op.drop_index('idx_social_posts_user_date')
    op.drop_index('idx_social_posts_hashtags')
    op.drop_index('idx_social_posts_engagement')
    op.drop_index('idx_social_posts_trending')
    op.drop_index('idx_post_comments_post_date')
    op.drop_index('idx_post_comments_parent')
    op.drop_index('idx_post_reactions_post_type')
    op.drop_index('idx_comment_reactions_comment_type')
    op.drop_index('idx_event_reviews_event_rating')
    op.drop_index('idx_event_reviews_user')
    op.drop_index('idx_user_connections_status')
    op.drop_index('idx_user_connections_requester')
    op.drop_index('idx_user_connections_addressee')
    op.drop_index('idx_user_follows_follower')
    op.drop_index('idx_user_follows_following')
    op.drop_index('idx_event_attendance_user')
    op.drop_index('idx_event_attendance_event')
    op.drop_index('idx_social_notifications_user_read')
    op.drop_index('idx_social_notifications_type')
    op.drop_index('idx_hashtag_trending')
    op.drop_index('idx_hashtag_usage')
    
    # Drop search indexes
    op.execute('DROP INDEX IF EXISTS idx_social_posts_search')
    op.execute('DROP INDEX IF EXISTS idx_user_profiles_search')
    
    # Drop tables in reverse order
    op.drop_table('group_posts')
    op.drop_table('group_memberships')
    op.drop_table('social_groups')
    op.drop_table('hashtag_trends')
    op.drop_table('content_reports')
    op.drop_table('social_notifications')
    op.drop_table('event_attendance')
    op.drop_table('user_follows')
    op.drop_table('user_social_connections')
    op.drop_table('event_reviews')
    op.drop_table('comment_reactions')
    op.drop_table('post_reactions')
    op.drop_table('post_comments')
    op.drop_table('post_mentions')
    op.drop_table('social_posts')
    op.drop_table('user_social_profiles')
    
    # Drop enum types
    op.execute('DROP TYPE report_reason_enum')
    op.execute('DROP TYPE notification_type_enum')
    op.execute('DROP TYPE reaction_type_enum')
    op.execute('DROP TYPE post_type_enum')
    op.execute('DROP TYPE connection_status_enum')