"""grant location insert update permissions to wea_data

Revision ID: 69db147baaec
Revises: 8fda37b4a59c
Create Date: 2025-08-14 13:53:31.675702

"""
from typing import Sequence, Union
import os

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '69db147baaec'
down_revision: Union[str, None] = '8fda37b4a59c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Grant INSERT and UPDATE permissions on location table to wea_data user."""
    # 從環境變數讀取 wea_data 用戶名稱
    wea_data_user = os.getenv('WEA_DATA_USER')

    if not wea_data_user:
        raise ValueError("WEA_DATA_USER environment variable is required")

    # 授予 wea_data 對 location 表的 INSERT 和 UPDATE 權限
    op.execute(f"GRANT INSERT, UPDATE ON location TO {wea_data_user}")


def downgrade() -> None:
    """Revoke INSERT and UPDATE permissions on location table from wea_data user."""
    # 從環境變數讀取 wea_data 用戶名稱
    wea_data_user = os.getenv('WEA_DATA_USER')

    if not wea_data_user:
        raise ValueError("WEA_DATA_USER environment variable is required")

    # 撤銷 wea_data 對 location 表的 INSERT 和 UPDATE 權限
    op.execute(f"REVOKE INSERT, UPDATE ON location FROM {wea_data_user}")
