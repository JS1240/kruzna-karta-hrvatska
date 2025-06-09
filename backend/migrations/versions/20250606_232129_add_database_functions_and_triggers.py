"""Add database functions and triggers

Revision ID: 20250606_232129
Revises: 20250606_232105
Create Date: 2025-06-06T23:21:29.758419

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20250606_232129'
down_revision = '20250606_232105'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create function to update the updated_at timestamp
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)
    
    # Create function to update the search vector for full-text search
    op.execute("""
        CREATE OR REPLACE FUNCTION update_search_vector()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.search_vector := to_tsvector('english', 
                COALESCE(NEW.name, '') || ' ' ||
                COALESCE(NEW.description, '') || ' ' ||
                COALESCE(NEW.location, '') || ' ' ||
                COALESCE(NEW.organizer, '') || ' ' ||
                COALESCE(array_to_string(NEW.tags, ' '), '')
            );
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)
    
    # Create trigger to automatically update updated_at for events
    op.execute("""
        CREATE TRIGGER update_events_updated_at 
            BEFORE UPDATE ON events 
            FOR EACH ROW 
            EXECUTE FUNCTION update_updated_at_column();
    """)
    
    # Create trigger to automatically update search vector for events
    op.execute("""
        CREATE TRIGGER update_events_search_vector 
            BEFORE INSERT OR UPDATE ON events 
            FOR EACH ROW 
            EXECUTE FUNCTION update_search_vector();
    """)
    
    # Create trigger to automatically update venues updated_at
    op.execute("""
        CREATE TRIGGER update_venues_updated_at 
            BEFORE UPDATE ON venues 
            FOR EACH ROW 
            EXECUTE FUNCTION update_updated_at_column();
    """)


def downgrade() -> None:
    # Drop triggers
    op.execute("DROP TRIGGER IF EXISTS update_venues_updated_at ON venues")
    op.execute("DROP TRIGGER IF EXISTS update_events_search_vector ON events")
    op.execute("DROP TRIGGER IF EXISTS update_events_updated_at ON events")
    
    # Drop functions
    op.execute("DROP FUNCTION IF EXISTS update_search_vector()")
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column()")
