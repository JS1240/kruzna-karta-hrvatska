"""Add earthdistance extension for geographic queries

Revision ID: 20250606_233309
Revises: 20250606_232301
Create Date: 2025-06-06T23:33:09.325488

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20250606_233309'
down_revision = '20250606_232301'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable cube extension (required for earthdistance)
    op.execute('CREATE EXTENSION IF NOT EXISTS cube')
    
    # Enable earthdistance extension for geographic calculations
    op.execute('CREATE EXTENSION IF NOT EXISTS earthdistance')


def downgrade() -> None:
    # Remove extensions (be careful in production)
    op.execute('DROP EXTENSION IF EXISTS earthdistance')
    op.execute('DROP EXTENSION IF EXISTS cube')
