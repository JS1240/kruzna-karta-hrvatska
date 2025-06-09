"""Add multi-language translation tables

Revision ID: 20250606_234628
Revises: 20250606_233847
Create Date: 2025-06-06T23:46:28.683842

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20250606_234628'
down_revision = '20250606_233847'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create languages table
    op.create_table('languages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('code', sa.String(length=10), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('native_name', sa.String(length=100), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('is_default', sa.Boolean(), nullable=True, default=False),
        sa.Column('flag_emoji', sa.String(length=10), nullable=True),
        sa.Column('rtl', sa.Boolean(), nullable=True, default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('code')
    )
    
    # Create event_translations table
    op.create_table('event_translations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False),
        sa.Column('language_code', sa.String(length=10), nullable=False),
        sa.Column('name', sa.String(length=500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('location', sa.String(length=500), nullable=True),
        sa.Column('organizer', sa.String(length=255), nullable=True),
        sa.Column('slug', sa.String(length=600), nullable=True),
        sa.Column('meta_title', sa.String(length=200), nullable=True),
        sa.Column('meta_description', sa.String(length=300), nullable=True),
        sa.Column('is_machine_translated', sa.Boolean(), nullable=True, default=False),
        sa.Column('translation_quality', sa.String(length=20), nullable=True, default='pending'),
        sa.Column('translated_by', sa.Integer(), nullable=True),
        sa.Column('reviewed_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['event_id'], ['events.id'], ),
        sa.ForeignKeyConstraint(['language_code'], ['languages.code'], ),
        sa.ForeignKeyConstraint(['reviewed_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['translated_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('event_id', 'language_code', name='_event_language_uc')
    )
    
    # Create category_translations table
    op.create_table('category_translations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('category_id', sa.Integer(), nullable=False),
        sa.Column('language_code', sa.String(length=10), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('slug', sa.String(length=100), nullable=True),
        sa.Column('is_machine_translated', sa.Boolean(), nullable=True, default=False),
        sa.Column('translation_quality', sa.String(length=20), nullable=True, default='pending'),
        sa.Column('translated_by', sa.Integer(), nullable=True),
        sa.Column('reviewed_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['category_id'], ['event_categories.id'], ),
        sa.ForeignKeyConstraint(['language_code'], ['languages.code'], ),
        sa.ForeignKeyConstraint(['reviewed_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['translated_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('category_id', 'language_code', name='_category_language_uc')
    )
    
    # Create venue_translations table
    op.create_table('venue_translations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('venue_id', sa.Integer(), nullable=False),
        sa.Column('language_code', sa.String(length=10), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_machine_translated', sa.Boolean(), nullable=True, default=False),
        sa.Column('translation_quality', sa.String(length=20), nullable=True, default='pending'),
        sa.Column('translated_by', sa.Integer(), nullable=True),
        sa.Column('reviewed_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['language_code'], ['languages.code'], ),
        sa.ForeignKeyConstraint(['reviewed_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['translated_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['venue_id'], ['venues.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('venue_id', 'language_code', name='_venue_language_uc')
    )
    
    # Create static_content_translations table
    op.create_table('static_content_translations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(length=200), nullable=False),
        sa.Column('language_code', sa.String(length=10), nullable=False),
        sa.Column('value', sa.Text(), nullable=False),
        sa.Column('context', sa.String(length=100), nullable=True),
        sa.Column('is_machine_translated', sa.Boolean(), nullable=True, default=False),
        sa.Column('translation_quality', sa.String(length=20), nullable=True, default='pending'),
        sa.Column('translated_by', sa.Integer(), nullable=True),
        sa.Column('reviewed_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['language_code'], ['languages.code'], ),
        sa.ForeignKeyConstraint(['reviewed_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['translated_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key', 'language_code', name='_content_language_uc')
    )
    
    # Create indexes
    op.create_index('idx_languages_code', 'languages', ['code'])
    op.create_index('idx_languages_active', 'languages', ['is_active'])
    op.create_index('idx_languages_default', 'languages', ['is_default'])
    
    op.create_index('idx_event_translations_event_id', 'event_translations', ['event_id'])
    op.create_index('idx_event_translations_language', 'event_translations', ['language_code'])
    op.create_index('idx_event_translations_quality', 'event_translations', ['translation_quality'])
    
    op.create_index('idx_category_translations_category_id', 'category_translations', ['category_id'])
    op.create_index('idx_category_translations_language', 'category_translations', ['language_code'])
    
    op.create_index('idx_venue_translations_venue_id', 'venue_translations', ['venue_id'])
    op.create_index('idx_venue_translations_language', 'venue_translations', ['language_code'])
    
    op.create_index('idx_static_translations_key', 'static_content_translations', ['key'])
    op.create_index('idx_static_translations_language', 'static_content_translations', ['language_code'])
    
    # Insert default languages
    op.execute("""
        INSERT INTO languages (code, name, native_name, is_active, is_default, flag_emoji, rtl) VALUES
        ('hr', 'Croatian', 'Hrvatski', true, true, '🇭🇷', false),
        ('en', 'English', 'English', true, false, '🇬🇧', false),
        ('de', 'German', 'Deutsch', true, false, '🇩🇪', false),
        ('it', 'Italian', 'Italiano', true, false, '🇮🇹', false),
        ('sl', 'Slovenian', 'Slovenščina', true, false, '🇸🇮', false);
    """)
    
    # Insert sample Croatian translations for categories
    op.execute("""
        INSERT INTO category_translations (category_id, language_code, name, description, slug) 
        SELECT 
            c.id,
            'hr' as language_code,
            CASE c.slug
                WHEN 'music' THEN 'Glazba'
                WHEN 'technology' THEN 'Tehnologija'
                WHEN 'culture' THEN 'Kultura'
                WHEN 'food-drink' THEN 'Hrana i piće'
                WHEN 'sports' THEN 'Sport'
                WHEN 'arts' THEN 'Umjetnost'
                WHEN 'entertainment' THEN 'Zabava'
                WHEN 'festival' THEN 'Festival'
                WHEN 'business' THEN 'Poslovanje'
                WHEN 'education' THEN 'Edukacija'
                ELSE c.name
            END as name,
            CASE c.slug
                WHEN 'music' THEN 'Koncerti, festivali i glazbene izvedbe'
                WHEN 'technology' THEN 'Tehnološke konferencije, radionice i meetupovi'
                WHEN 'culture' THEN 'Kulturni događaji, izložbe i tradicionalne izvedbe'
                WHEN 'food-drink' THEN 'Festivali hrane, degustacije vina i kulinarski događaji'
                WHEN 'sports' THEN 'Sportski događaji, turniri i aktivnosti'
                WHEN 'arts' THEN 'Umjetničke galerije, izložbe i kreativne radionice'
                WHEN 'entertainment' THEN 'Filmovi, kazalište, komedije i opća zabava'
                WHEN 'festival' THEN 'Veliki festivali i proslave'
                WHEN 'business' THEN 'Mrežni događaji, poslovne konferencije i seminari'
                WHEN 'education' THEN 'Radionice, tečajevi i obrazovni događaji'
                ELSE c.description
            END as description,
            CASE c.slug
                WHEN 'music' THEN 'glazba'
                WHEN 'technology' THEN 'tehnologija'
                WHEN 'culture' THEN 'kultura'
                WHEN 'food-drink' THEN 'hrana-i-pice'
                WHEN 'sports' THEN 'sport'
                WHEN 'arts' THEN 'umjetnost'
                WHEN 'entertainment' THEN 'zabava'
                WHEN 'festival' THEN 'festival'
                WHEN 'business' THEN 'poslovanje'
                WHEN 'education' THEN 'edukacija'
                ELSE c.slug
            END as slug
        FROM event_categories c;
    """)
    
    # Insert basic static content translations
    op.execute("""
        INSERT INTO static_content_translations (key, language_code, value, context) VALUES
        ('welcome_message', 'hr', 'Dobrodošli na Kruzna Karta Hrvatska', 'Main welcome message'),
        ('welcome_message', 'en', 'Welcome to Kruzna Karta Hrvatska', 'Main welcome message'),
        ('search_placeholder', 'hr', 'Pretražite događaje...', 'Search box placeholder'),
        ('search_placeholder', 'en', 'Search events...', 'Search box placeholder'),
        ('no_events_found', 'hr', 'Nema pronađenih događaja', 'No results message'),
        ('no_events_found', 'en', 'No events found', 'No results message'),
        ('load_more', 'hr', 'Učitaj više', 'Load more button'),
        ('load_more', 'en', 'Load more', 'Load more button'),
        ('featured_events', 'hr', 'Istaknuti događaji', 'Featured events section title'),
        ('featured_events', 'en', 'Featured events', 'Featured events section title');
    """)


def downgrade() -> None:
    # Drop indexes
    op.drop_index('idx_static_translations_language', 'static_content_translations')
    op.drop_index('idx_static_translations_key', 'static_content_translations')
    op.drop_index('idx_venue_translations_language', 'venue_translations')
    op.drop_index('idx_venue_translations_venue_id', 'venue_translations')
    op.drop_index('idx_category_translations_language', 'category_translations')
    op.drop_index('idx_category_translations_category_id', 'category_translations')
    op.drop_index('idx_event_translations_quality', 'event_translations')
    op.drop_index('idx_event_translations_language', 'event_translations')
    op.drop_index('idx_event_translations_event_id', 'event_translations')
    op.drop_index('idx_languages_default', 'languages')
    op.drop_index('idx_languages_active', 'languages')
    op.drop_index('idx_languages_code', 'languages')
    
    # Drop tables
    op.drop_table('static_content_translations')
    op.drop_table('venue_translations')
    op.drop_table('category_translations')
    op.drop_table('event_translations')
    op.drop_table('languages')
