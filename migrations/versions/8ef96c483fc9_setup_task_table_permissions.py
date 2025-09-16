"""setup_task_table_permissions

Revision ID: 8ef96c483fc9
Revises: 1a4a3abc97f6
Create Date: 2025-09-16 13:21:40.024189

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8ef96c483fc9'
down_revision: Union[str, None] = '1a4a3abc97f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Setup task table permissions for wea_data and wea_bot users."""
    # Grant full permissions to wea_data (ETL service needs to write monitoring data)
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON task TO wea_data")
    op.execute("GRANT USAGE, SELECT ON SEQUENCE task_id_seq TO wea_data")

    # Restrict wea_bot to read-only access (main app only needs to view monitoring data)
    op.execute("REVOKE INSERT, UPDATE, DELETE ON task FROM wea_bot")
    op.execute("GRANT SELECT ON task TO wea_bot")


def downgrade() -> None:
    """Revert task table permissions."""
    # Revoke all permissions from both users
    op.execute("REVOKE ALL ON task FROM wea_data")
    op.execute("REVOKE ALL ON SEQUENCE task_id_seq FROM wea_data")
    op.execute("REVOKE ALL ON task FROM wea_bot")
