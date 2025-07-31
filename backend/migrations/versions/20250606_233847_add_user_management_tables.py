"""Add user management and authentication tables

Revision ID: 20250606_233847
Revises: 20250606_233309
Create Date: 2025-06-06T23:38:47.803568

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20250606_233847'
down_revision = '013_add_venue_coordinates_table'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('username', sa.String(length=100), nullable=True),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=True),
        sa.Column('last_name', sa.String(length=100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('is_verified', sa.Boolean(), nullable=True, default=False),
        sa.Column('is_superuser', sa.Boolean(), nullable=True, default=False),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('date_of_birth', sa.DateTime(timezone=True), nullable=True),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('country', sa.String(length=100), nullable=True, default='Croatia'),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('avatar_url', sa.String(length=500), nullable=True),
        sa.Column('preferred_language', sa.String(length=10), nullable=True, default='hr'),
        sa.Column('email_notifications', sa.Boolean(), nullable=True, default=True),
        sa.Column('marketing_emails', sa.Boolean(), nullable=True, default=False),
        sa.Column('email_verification_token', sa.String(length=255), nullable=True),
        sa.Column('password_reset_token', sa.String(length=255), nullable=True),
        sa.Column('password_reset_expires', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('username')
    )
    
    # Create user_profiles table
    op.create_table('user_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('website', sa.String(length=500), nullable=True),
        sa.Column('social_links', sa.Text(), nullable=True),
        sa.Column('interests', sa.Text(), nullable=True),
        sa.Column('event_preferences', sa.Text(), nullable=True),
        sa.Column('profile_visibility', sa.String(length=20), nullable=True, default='public'),
        sa.Column('show_email', sa.Boolean(), nullable=True, default=False),
        sa.Column('show_phone', sa.Boolean(), nullable=True, default=False),
        sa.Column('show_location', sa.Boolean(), nullable=True, default=True),
        sa.Column('events_attended', sa.Integer(), nullable=True, default=0),
        sa.Column('events_favorited', sa.Integer(), nullable=True, default=0),
        sa.Column('reviews_written', sa.Integer(), nullable=True, default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    
    # Create user_roles table
    op.create_table('user_roles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('permissions', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    
    # Create user_role_assignments table
    op.create_table('user_role_assignments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.Column('assigned_by', sa.Integer(), nullable=True),
        sa.Column('assigned_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.ForeignKeyConstraint(['assigned_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['role_id'], ['user_roles.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create user_favorites association table
    op.create_table('user_favorites',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['event_id'], ['events.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('user_id', 'event_id')
    )
    
    # Create indexes
    op.create_index('idx_users_email', 'users', ['email'])
    op.create_index('idx_users_username', 'users', ['username'])
    op.create_index('idx_users_is_active', 'users', ['is_active'])
    op.create_index('idx_users_is_verified', 'users', ['is_verified'])
    op.create_index('idx_users_city', 'users', ['city'])
    op.create_index('idx_users_created_at', 'users', ['created_at'])
    
    op.create_index('idx_user_profiles_user_id', 'user_profiles', ['user_id'])
    op.create_index('idx_user_profiles_visibility', 'user_profiles', ['profile_visibility'])
    
    op.create_index('idx_user_role_assignments_user_id', 'user_role_assignments', ['user_id'])
    op.create_index('idx_user_role_assignments_role_id', 'user_role_assignments', ['role_id'])
    op.create_index('idx_user_role_assignments_active', 'user_role_assignments', ['is_active'])
    
    op.create_index('idx_user_favorites_user_id', 'user_favorites', ['user_id'])
    op.create_index('idx_user_favorites_event_id', 'user_favorites', ['event_id'])
    op.create_index('idx_user_favorites_created_at', 'user_favorites', ['created_at'])
    
    # Add foreign key constraint for events.organizer_id
    op.create_foreign_key('fk_events_organizer_id', 'events', 'users', ['organizer_id'], ['id'])
    
    # Insert default user roles
    op.execute("""
        INSERT INTO user_roles (name, description, permissions) VALUES
        ('admin', 'System administrator with full access', '["manage_users", "manage_events", "manage_venues", "manage_categories", "system_admin"]'),
        ('moderator', 'Content moderator', '["moderate_events", "moderate_reviews", "manage_reported_content"]'),
        ('organizer', 'Event organizer', '["create_events", "manage_own_events", "view_analytics"]'),
        ('user', 'Regular user', '["view_events", "favorite_events", "write_reviews"]');
    """)


def downgrade() -> None:
    # Drop foreign key constraint for events.organizer_id
    op.drop_constraint('fk_events_organizer_id', 'events', type_='foreignkey')
    
    # Drop indexes
    op.drop_index('idx_user_favorites_created_at', 'user_favorites')
    op.drop_index('idx_user_favorites_event_id', 'user_favorites')
    op.drop_index('idx_user_favorites_user_id', 'user_favorites')
    
    op.drop_index('idx_user_role_assignments_active', 'user_role_assignments')
    op.drop_index('idx_user_role_assignments_role_id', 'user_role_assignments')
    op.drop_index('idx_user_role_assignments_user_id', 'user_role_assignments')
    
    op.drop_index('idx_user_profiles_visibility', 'user_profiles')
    op.drop_index('idx_user_profiles_user_id', 'user_profiles')
    
    op.drop_index('idx_users_created_at', 'users')
    op.drop_index('idx_users_city', 'users')
    op.drop_index('idx_users_is_verified', 'users')
    op.drop_index('idx_users_is_active', 'users')
    op.drop_index('idx_users_username', 'users')
    op.drop_index('idx_users_email', 'users')
    
    # Drop tables
    op.drop_table('user_favorites')
    op.drop_table('user_role_assignments')
    op.drop_table('user_roles')
    op.drop_table('user_profiles')
    op.drop_table('users')
