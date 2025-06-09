"""Add comprehensive venue management system

Revision ID: 009_add_venue_management
Revises: 008_add_recurring_events
Create Date: 2025-01-08 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '009_add_venue_management'
down_revision = '008_add_recurring_events'
branch_labels = None
depends_on = None


def upgrade():
    # Create enum types
    venue_status_enum = postgresql.ENUM(
        'active', 'inactive', 'maintenance', 'permanently_closed',
        name='venue_status_enum'
    )
    venue_status_enum.create(op.get_bind())
    
    facility_type_enum = postgresql.ENUM(
        'accessibility', 'audio_visual', 'catering', 'parking', 'security', 'utilities', 'amenities',
        name='facility_type_enum'
    )
    facility_type_enum.create(op.get_bind())
    
    availability_status_enum = postgresql.ENUM(
        'available', 'booked', 'maintenance', 'blocked',
        name='availability_status_enum'
    )
    availability_status_enum.create(op.get_bind())
    
    booking_status_enum = postgresql.ENUM(
        'pending', 'confirmed', 'cancelled', 'completed',
        name='booking_status_enum'
    )
    booking_status_enum.create(op.get_bind())
    
    # Create facilities table
    op.create_table(
        'facilities',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('name', sa.String(100), nullable=False, unique=True),
        sa.Column('description', sa.Text),
        sa.Column('facility_type', facility_type_enum, nullable=False, index=True),
        sa.Column('icon', sa.String(50)),
        sa.Column('is_essential', sa.Boolean, default=False),
        sa.Column('default_cost', sa.Numeric(10, 2), default=0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now())
    )
    
    # Create enhanced_venues table
    op.create_table(
        'enhanced_venues',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        
        # Basic venue information
        sa.Column('name', sa.String(255), nullable=False, index=True),
        sa.Column('slug', sa.String(300), unique=True),
        sa.Column('description', sa.Text),
        sa.Column('address', sa.Text),
        sa.Column('city', sa.String(100), nullable=False, index=True),
        sa.Column('postal_code', sa.String(20)),
        sa.Column('country', sa.String(100), default='Croatia'),
        sa.Column('region', sa.String(100)),
        
        # Geographic data
        sa.Column('latitude', sa.Numeric(10, 8)),
        sa.Column('longitude', sa.Numeric(11, 8)),
        
        # Venue specifications
        sa.Column('capacity', sa.Integer),
        sa.Column('max_capacity', sa.Integer),
        sa.Column('min_capacity', sa.Integer),
        sa.Column('venue_type', sa.String(50), index=True),
        sa.Column('venue_status', venue_status_enum, default='active', index=True),
        
        # Contact information
        sa.Column('website', sa.String(500)),
        sa.Column('phone', sa.String(50)),
        sa.Column('email', sa.String(255)),
        sa.Column('contact_person', sa.String(255)),
        sa.Column('emergency_contact', sa.String(50)),
        
        # Business details
        sa.Column('tax_id', sa.String(50)),
        sa.Column('registration_number', sa.String(50)),
        sa.Column('business_hours', postgresql.JSONB),
        
        # Venue features
        sa.Column('floor_plan', sa.Text),
        sa.Column('virtual_tour_url', sa.String(500)),
        sa.Column('photos', postgresql.ARRAY(sa.Text)),
        sa.Column('videos', postgresql.ARRAY(sa.Text)),
        
        # Pricing and policies
        sa.Column('base_price_per_hour', sa.Numeric(10, 2)),
        sa.Column('base_price_per_day', sa.Numeric(10, 2)),
        sa.Column('security_deposit', sa.Numeric(10, 2)),
        sa.Column('cleaning_fee', sa.Numeric(10, 2)),
        sa.Column('cancellation_policy', sa.Text),
        sa.Column('payment_terms', sa.Text),
        
        # Operational details
        sa.Column('setup_time_minutes', sa.Integer, default=60),
        sa.Column('breakdown_time_minutes', sa.Integer, default=60),
        sa.Column('minimum_booking_hours', sa.Integer, default=2),
        sa.Column('maximum_booking_days', sa.Integer, default=30),
        sa.Column('advance_booking_days', sa.Integer, default=90),
        
        # Technical specifications
        sa.Column('technical_specs', postgresql.JSONB),
        sa.Column('accessibility_features', postgresql.JSONB),
        sa.Column('safety_certifications', postgresql.ARRAY(sa.String)),
        
        # Management info
        sa.Column('owner_id', sa.Integer, sa.ForeignKey('users.id'), index=True),
        sa.Column('manager_id', sa.Integer, sa.ForeignKey('users.id'), index=True),
        sa.Column('is_verified', sa.Boolean, default=False),
        sa.Column('verification_date', sa.DateTime(timezone=True)),
        
        # Statistics
        sa.Column('total_bookings', sa.Integer, default=0),
        sa.Column('total_revenue', sa.Numeric(12, 2), default=0),
        sa.Column('average_rating', sa.Numeric(3, 2)),
        sa.Column('total_reviews', sa.Integer, default=0),
        
        # SEO and search
        sa.Column('search_keywords', postgresql.ARRAY(sa.String)),
        sa.Column('meta_description', sa.String(300)),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('last_booking_at', sa.DateTime(timezone=True)),
        
        # Constraints
        sa.CheckConstraint('max_capacity >= capacity', name='venue_capacity_check'),
        sa.CheckConstraint('min_capacity <= capacity', name='venue_min_capacity_check'),
        sa.CheckConstraint('base_price_per_hour >= 0', name='venue_hourly_price_check'),
        sa.CheckConstraint('base_price_per_day >= 0', name='venue_daily_price_check'),
        sa.CheckConstraint('average_rating >= 0 AND average_rating <= 5', name='venue_rating_check')
    )
    
    # Create venue_facilities association table
    op.create_table(
        'venue_facilities',
        sa.Column('venue_id', sa.Integer, sa.ForeignKey('enhanced_venues.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('facility_id', sa.Integer, sa.ForeignKey('facilities.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('notes', sa.Text),
        sa.Column('is_included', sa.Boolean, default=True),
        sa.Column('additional_cost', sa.Numeric(10, 2)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now())
    )
    
    # Create venue_bookings table
    op.create_table(
        'venue_bookings',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('venue_id', sa.Integer, sa.ForeignKey('enhanced_venues.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('customer_id', sa.Integer, sa.ForeignKey('users.id'), index=True),
        
        # Event details
        sa.Column('event_name', sa.String(500), nullable=False),
        sa.Column('event_type', sa.String(100)),
        sa.Column('event_description', sa.Text),
        sa.Column('expected_attendance', sa.Integer),
        
        # Booking details
        sa.Column('booking_reference', sa.String(50), unique=True, nullable=False),
        sa.Column('booking_status', booking_status_enum, default='pending', index=True),
        
        # Time details
        sa.Column('start_datetime', sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column('end_datetime', sa.DateTime(timezone=True), nullable=False),
        sa.Column('setup_start', sa.DateTime(timezone=True)),
        sa.Column('breakdown_end', sa.DateTime(timezone=True)),
        
        # Pricing
        sa.Column('base_cost', sa.Numeric(10, 2), nullable=False),
        sa.Column('facility_costs', sa.Numeric(10, 2), default=0),
        sa.Column('additional_costs', sa.Numeric(10, 2), default=0),
        sa.Column('discount_amount', sa.Numeric(10, 2), default=0),
        sa.Column('tax_amount', sa.Numeric(10, 2), default=0),
        sa.Column('total_cost', sa.Numeric(10, 2), nullable=False),
        
        # Payment details
        sa.Column('deposit_amount', sa.Numeric(10, 2)),
        sa.Column('deposit_paid_at', sa.DateTime(timezone=True)),
        sa.Column('payment_due_date', sa.DateTime(timezone=True)),
        sa.Column('payment_completed_at', sa.DateTime(timezone=True)),
        
        # Contact details
        sa.Column('contact_name', sa.String(255), nullable=False),
        sa.Column('contact_email', sa.String(255), nullable=False),
        sa.Column('contact_phone', sa.String(50)),
        
        # Special requirements
        sa.Column('special_requirements', sa.Text),
        sa.Column('catering_requirements', sa.Text),
        sa.Column('av_requirements', sa.Text),
        sa.Column('accessibility_requirements', sa.Text),
        
        # Insurance and liability
        sa.Column('insurance_certificate', sa.String(500)),
        sa.Column('liability_acknowledged', sa.Boolean, default=False),
        
        # Status tracking
        sa.Column('confirmed_at', sa.DateTime(timezone=True)),
        sa.Column('cancelled_at', sa.DateTime(timezone=True)),
        sa.Column('cancellation_reason', sa.Text),
        sa.Column('completed_at', sa.DateTime(timezone=True)),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        
        # Constraints
        sa.CheckConstraint('end_datetime > start_datetime', name='booking_time_check'),
        sa.CheckConstraint('total_cost >= 0', name='booking_cost_check'),
        sa.CheckConstraint('expected_attendance >= 0', name='booking_attendance_check')
    )
    
    # Create venue_availability table
    op.create_table(
        'venue_availability',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('venue_id', sa.Integer, sa.ForeignKey('enhanced_venues.id', ondelete='CASCADE'), nullable=False, index=True),
        
        # Time slots
        sa.Column('date', sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=False),
        
        # Availability details
        sa.Column('status', availability_status_enum, default='available', index=True),
        sa.Column('capacity_override', sa.Integer),
        sa.Column('price_override', sa.Numeric(10, 2)),
        
        # Booking information
        sa.Column('booking_id', sa.Integer, sa.ForeignKey('venue_bookings.id'), index=True),
        sa.Column('blocked_reason', sa.String(500)),
        sa.Column('notes', sa.Text),
        
        # Metadata
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        
        # Constraints
        sa.CheckConstraint('end_time > start_time', name='availability_time_check'),
        sa.UniqueConstraint('venue_id', 'start_time', 'end_time', name='venue_availability_unique')
    )
    
    # Create venue_payments table
    op.create_table(
        'venue_payments',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('booking_id', sa.Integer, sa.ForeignKey('venue_bookings.id', ondelete='CASCADE'), nullable=False, index=True),
        
        # Payment details
        sa.Column('amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('payment_type', sa.String(50), nullable=False),
        sa.Column('payment_method', sa.String(50)),
        sa.Column('payment_status', sa.String(50), default='pending'),
        
        # External payment data
        sa.Column('transaction_id', sa.String(255)),
        sa.Column('payment_processor', sa.String(50)),
        sa.Column('payment_reference', sa.String(255)),
        
        # Timestamps
        sa.Column('due_date', sa.DateTime(timezone=True)),
        sa.Column('paid_at', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now())
    )
    
    # Create venue_reviews table
    op.create_table(
        'venue_reviews',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('venue_id', sa.Integer, sa.ForeignKey('enhanced_venues.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id'), index=True),
        sa.Column('booking_id', sa.Integer, sa.ForeignKey('venue_bookings.id'), index=True),
        
        # Review content
        sa.Column('rating', sa.Integer, nullable=False),
        sa.Column('title', sa.String(200)),
        sa.Column('review_text', sa.Text),
        
        # Detailed ratings
        sa.Column('cleanliness_rating', sa.Integer),
        sa.Column('staff_rating', sa.Integer),
        sa.Column('facilities_rating', sa.Integer),
        sa.Column('value_rating', sa.Integer),
        sa.Column('location_rating', sa.Integer),
        
        # Metadata
        sa.Column('is_verified', sa.Boolean, default=False),
        sa.Column('is_public', sa.Boolean, default=True),
        sa.Column('helpful_votes', sa.Integer, default=0),
        
        # Response from venue
        sa.Column('venue_response', sa.Text),
        sa.Column('venue_responded_at', sa.DateTime(timezone=True)),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now()),
        
        # Constraints
        sa.CheckConstraint('rating >= 1 AND rating <= 5', name='review_rating_check'),
        sa.CheckConstraint('cleanliness_rating IS NULL OR (cleanliness_rating >= 1 AND cleanliness_rating <= 5)', name='cleanliness_rating_check'),
        sa.CheckConstraint('staff_rating IS NULL OR (staff_rating >= 1 AND staff_rating <= 5)', name='staff_rating_check'),
        sa.CheckConstraint('facilities_rating IS NULL OR (facilities_rating >= 1 AND facilities_rating <= 5)', name='facilities_rating_check'),
        sa.CheckConstraint('value_rating IS NULL OR (value_rating >= 1 AND value_rating <= 5)', name='value_rating_check'),
        sa.CheckConstraint('location_rating IS NULL OR (location_rating >= 1 AND location_rating <= 5)', name='location_rating_check'),
        sa.UniqueConstraint('venue_id', 'user_id', 'booking_id', name='unique_venue_review')
    )
    
    # Create venue_images table
    op.create_table(
        'venue_images',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('venue_id', sa.Integer, sa.ForeignKey('enhanced_venues.id', ondelete='CASCADE'), nullable=False, index=True),
        
        # Image details
        sa.Column('url', sa.String(1000), nullable=False),
        sa.Column('filename', sa.String(255)),
        sa.Column('title', sa.String(200)),
        sa.Column('description', sa.Text),
        sa.Column('alt_text', sa.String(200)),
        
        # Image metadata
        sa.Column('image_type', sa.String(50)),
        sa.Column('is_primary', sa.Boolean, default=False),
        sa.Column('display_order', sa.Integer, default=0),
        
        # Technical details
        sa.Column('width', sa.Integer),
        sa.Column('height', sa.Integer),
        sa.Column('file_size', sa.Integer),
        sa.Column('mime_type', sa.String(50)),
        
        # Timestamps
        sa.Column('uploaded_at', sa.DateTime(timezone=True), server_default=sa.func.now())
    )
    
    # Create venue_pricing_rules table
    op.create_table(
        'venue_pricing_rules',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('venue_id', sa.Integer, sa.ForeignKey('enhanced_venues.id', ondelete='CASCADE'), nullable=False, index=True),
        
        # Rule details
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('rule_type', sa.String(50), nullable=False),
        
        # Conditions
        sa.Column('conditions', postgresql.JSONB, nullable=False),
        
        # Pricing adjustments
        sa.Column('price_adjustment_type', sa.String(20), nullable=False),
        sa.Column('price_adjustment_value', sa.Numeric(10, 2), nullable=False),
        
        # Validity
        sa.Column('valid_from', sa.DateTime(timezone=True)),
        sa.Column('valid_to', sa.DateTime(timezone=True)),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('priority', sa.Integer, default=0),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now())
    )
    
    # Create venue_maintenance_logs table
    op.create_table(
        'venue_maintenance_logs',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('venue_id', sa.Integer, sa.ForeignKey('enhanced_venues.id', ondelete='CASCADE'), nullable=False, index=True),
        
        # Maintenance details
        sa.Column('maintenance_type', sa.String(100), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('description', sa.Text),
        
        # Scheduling
        sa.Column('scheduled_date', sa.DateTime(timezone=True)),
        sa.Column('completed_date', sa.DateTime(timezone=True)),
        sa.Column('estimated_duration_hours', sa.Integer),
        sa.Column('actual_duration_hours', sa.Integer),
        
        # Personnel
        sa.Column('assigned_to', sa.String(255)),
        sa.Column('contractor_company', sa.String(255)),
        sa.Column('contact_person', sa.String(255)),
        
        # Status and impact
        sa.Column('status', sa.String(50), default='scheduled'),
        sa.Column('affects_availability', sa.Boolean, default=True),
        sa.Column('affected_areas', postgresql.ARRAY(sa.String)),
        
        # Costs
        sa.Column('estimated_cost', sa.Numeric(10, 2)),
        sa.Column('actual_cost', sa.Numeric(10, 2)),
        sa.Column('invoice_number', sa.String(100)),
        
        # Documentation
        sa.Column('before_photos', postgresql.ARRAY(sa.String)),
        sa.Column('after_photos', postgresql.ARRAY(sa.String)),
        sa.Column('documentation_urls', postgresql.ARRAY(sa.String)),
        sa.Column('notes', sa.Text),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now())
    )
    
    # Create indexes for better performance
    op.create_index('idx_enhanced_venues_city_status', 'enhanced_venues', ['city', 'venue_status'])
    op.create_index('idx_enhanced_venues_location', 'enhanced_venues', ['latitude', 'longitude'])
    op.create_index('idx_enhanced_venues_capacity', 'enhanced_venues', ['capacity'])
    op.create_index('idx_enhanced_venues_rating', 'enhanced_venues', ['average_rating'])
    op.create_index('idx_enhanced_venues_pricing', 'enhanced_venues', ['base_price_per_hour', 'base_price_per_day'])
    
    op.create_index('idx_venue_availability_date_status', 'venue_availability', ['venue_id', 'date', 'status'])
    op.create_index('idx_venue_availability_time_range', 'venue_availability', ['start_time', 'end_time'])
    
    op.create_index('idx_venue_bookings_venue_dates', 'venue_bookings', ['venue_id', 'start_datetime', 'end_datetime'])
    op.create_index('idx_venue_bookings_customer_status', 'venue_bookings', ['customer_id', 'booking_status'])
    op.create_index('idx_venue_bookings_reference', 'venue_bookings', ['booking_reference'])
    
    op.create_index('idx_venue_reviews_venue_rating', 'venue_reviews', ['venue_id', 'rating', 'is_public'])
    op.create_index('idx_venue_reviews_user', 'venue_reviews', ['user_id'])
    
    # Add relationship columns to existing tables if they don't exist
    # Update user table to include venue relationships
    try:
        op.add_column('users', sa.Column('venue_owner', sa.Boolean, default=False))
        op.add_column('users', sa.Column('venue_manager', sa.Boolean, default=False))
    except:
        # Columns might already exist
        pass
    
    # Insert default facilities
    op.execute("""
        INSERT INTO facilities (name, description, facility_type, icon, is_essential, default_cost) VALUES
        ('Wheelchair Access', 'Full wheelchair accessibility', 'accessibility', '♿', true, 0),
        ('Audio System', 'Professional sound system', 'audio_visual', '🔊', false, 50),
        ('Projector', 'HD projector with screen', 'audio_visual', '📽️', false, 75),
        ('Lighting System', 'Professional stage lighting', 'audio_visual', '💡', false, 100),
        ('Catering Kitchen', 'Fully equipped kitchen', 'catering', '🍽️', false, 150),
        ('Bar Service', 'Licensed bar with bartender', 'catering', '🍸', false, 200),
        ('Parking Lot', 'On-site parking available', 'parking', '🅿️', false, 0),
        ('Valet Parking', 'Valet parking service', 'parking', '🚗', false, 100),
        ('Security Guards', '24/7 security personnel', 'security', '🛡️', false, 300),
        ('CCTV System', 'Security camera monitoring', 'security', '📹', false, 50),
        ('WiFi', 'High-speed wireless internet', 'utilities', '📶', true, 0),
        ('Power Outlets', 'Adequate electrical outlets', 'utilities', '🔌', true, 0),
        ('Air Conditioning', 'Climate control system', 'amenities', '❄️', false, 100),
        ('Heating', 'Central heating system', 'amenities', '🔥', false, 80),
        ('Restrooms', 'Clean restroom facilities', 'amenities', '🚻', true, 0),
        ('Coat Check', 'Coat and bag checking service', 'amenities', '🧥', false, 25),
        ('Green Room', 'Private preparation area', 'amenities', '🎭', false, 75),
        ('Loading Dock', 'Equipment loading access', 'utilities', '🚚', false, 0)
    """)


def downgrade():
    # Drop tables in reverse order
    op.drop_table('venue_maintenance_logs')
    op.drop_table('venue_pricing_rules')
    op.drop_table('venue_images')
    op.drop_table('venue_reviews')
    op.drop_table('venue_payments')
    op.drop_table('venue_availability')
    op.drop_table('venue_bookings')
    op.drop_table('venue_facilities')
    op.drop_table('enhanced_venues')
    op.drop_table('facilities')
    
    # Drop enum types
    op.execute('DROP TYPE booking_status_enum')
    op.execute('DROP TYPE availability_status_enum')
    op.execute('DROP TYPE facility_type_enum')
    op.execute('DROP TYPE venue_status_enum')
    
    # Remove columns from users table
    try:
        op.drop_column('users', 'venue_owner')
        op.drop_column('users', 'venue_manager')
    except:
        pass