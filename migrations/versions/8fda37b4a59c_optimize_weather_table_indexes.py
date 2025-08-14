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
    # 移除單列索引（會被複合索引涵蓋）
    op.drop_index(op.f('ix_weather_start_time'), table_name='weather')

    # 新增複合索引以優化查詢效能
    op.create_index(
        'ix_weather_location_start_time',
        'weather',
        ['location_id', 'start_time'],
        unique=False
    )

    # 新增 fetched_at 索引以優化滑動窗口查詢
    op.create_index(
        'ix_weather_location_fetched_at',
        'weather',
        ['location_id', 'fetched_at'],
        unique=False
    )


def downgrade() -> None:
    """Restore original weather table indexes."""
    # 移除新增的複合索引
    op.drop_index('ix_weather_location_fetched_at', table_name='weather')
    op.drop_index('ix_weather_location_start_time', table_name='weather')

    # 恢復原始的單列索引
    op.create_index(op.f('ix_weather_start_time'), 'weather', ['start_time'], unique=False)
