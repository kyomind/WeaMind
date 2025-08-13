"""restrict wea_bot weather permissions

Revision ID: 526d69e2321e
Revises: 67c6acf6e8df
Create Date: 2025-08-13 09:17:29.726426

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
import os

# revision identifiers, used by Alembic.
revision: str = '526d69e2321e'
down_revision: Union[str, None] = '67c6acf6e8df'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Restrict wea_bot to read-only access on weather table."""
    # 直接從環境變數讀取配置，避免與 Settings 類別耦合
    postgres_user = os.getenv('POSTGRES_USER')

    if not postgres_user:
        raise ValueError("POSTGRES_USER environment variable is required")

    # 移除 wea_bot 對 weather 的寫入權限
    op.execute(f"REVOKE INSERT, UPDATE, DELETE ON weather FROM {postgres_user}")

    # 確保保留讀取權限
    op.execute(f"GRANT SELECT ON weather TO {postgres_user}")


def downgrade() -> None:
    """Restore wea_bot full permissions on weather table."""
    # 直接從環境變數讀取配置，避免與 Settings 類別耦合
    postgres_user = os.getenv('POSTGRES_USER')

    if not postgres_user:
        raise ValueError("POSTGRES_USER environment variable is required")

    # 恢復全權限
    op.execute(f"GRANT ALL ON weather TO {postgres_user}")
