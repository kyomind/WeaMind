"""optimize weather table indexes

Revision ID: 8fda37b4a59c
Revises: 526d69e2321e
Create Date: 2025-08-14 10:15:13.389574

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8fda37b4a59c'
down_revision: Union[str, None] = '526d69e2321e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Optimize weather table indexes for better write performance."""
    # Remove single-column index (covered by composite index)
    op.drop_index(op.f('ix_weather_start_time'), table_name='weather')

    # Add composite index to optimize query performance
    op.create_index(
        'ix_weather_location_start_time',
        'weather',
        ['location_id', 'start_time'],
        unique=False
    )

    # Add index on fetched_at to optimize sliding window queries
    op.create_index(
        'ix_weather_location_fetched_at',
        'weather',
        ['location_id', 'fetched_at'],
        unique=False
    )


def downgrade() -> None:
    """Restore original weather table indexes."""
    # Remove the added composite indexes
    op.drop_index('ix_weather_location_fetched_at', table_name='weather')
    op.drop_index('ix_weather_location_start_time', table_name='weather')

    # Restore the original single-column index
    op.create_index(op.f('ix_weather_start_time'), 'weather', ['start_time'], unique=False)
