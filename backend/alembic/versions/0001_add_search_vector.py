from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '0001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('events', sa.Column('search_vector', postgresql.TSVECTOR(), nullable=True))
    op.execute("UPDATE events SET search_vector = to_tsvector('simple', coalesce(name,'') || ' ' || coalesce(description,''))")
    op.execute("CREATE INDEX IF NOT EXISTS idx_events_search ON events USING GIN(search_vector)")
    op.execute("""CREATE TRIGGER tsvectorupdate BEFORE INSERT OR UPDATE ON events FOR EACH ROW EXECUTE FUNCTION tsvector_update_trigger(search_vector, 'pg_catalog.simple', name, description)""")

def downgrade():
    op.execute("DROP TRIGGER IF EXISTS tsvectorupdate ON events")
    op.drop_index('idx_events_search', table_name='events')
    op.drop_column('events', 'search_vector')
