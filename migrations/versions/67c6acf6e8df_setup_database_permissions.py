"""setup database permissions

Revision ID: 67c6acf6e8df
Revises: f557a1959851
Create Date: 2025-08-13 09:16:46.463749

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
import os

# revision identifiers, used by Alembic.
revision: str = '67c6acf6e8df'
down_revision: Union[str, None] = 'f557a1959851'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Setup database roles and permissions."""
    # 直接從環境變數讀取配置，避免與 Settings 類別耦合
    postgres_user = os.getenv('POSTGRES_USER')
    postgres_db = os.getenv('POSTGRES_DB')
    wea_data_user = os.getenv('WEA_DATA_USER')
    wea_data_password = os.getenv('WEA_DATA_PASSWORD')

    if not postgres_user:
        raise ValueError("POSTGRES_USER environment variable is required")
    if not postgres_db:
        raise ValueError("POSTGRES_DB environment variable is required")
    if not wea_data_user:
        raise ValueError("WEA_DATA_USER environment variable is required")
    if not wea_data_password:
        raise ValueError("WEA_DATA_PASSWORD environment variable is required")

    # 1. 提升 wea_bot 權限（讓它能創建其他用戶）
    op.execute(f"ALTER USER {postgres_user} WITH CREATEROLE")

    # 2. 建立 wea_data 用戶（如果不存在）
    op.execute(f"""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '{wea_data_user}') THEN
                CREATE USER {wea_data_user} WITH PASSWORD '{wea_data_password}';
            END IF;
        END
        $$;
    """)

    # 3. 設定基本連線權限
    op.execute(f"GRANT CONNECT ON DATABASE {postgres_db} TO {wea_data_user}")
    op.execute(f"GRANT USAGE ON SCHEMA public TO {wea_data_user}")

    # 4. 設定 table 權限
    # wea_data 對 location 的權限：只讀
    op.execute(f"GRANT SELECT ON location TO {wea_data_user}")

    # wea_data 對 weather 的權限：全權限
    op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON weather TO {wea_data_user}")

    # 5. 設定 sequence 權限（讓 wea_data 可以插入資料）
    op.execute(f"GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO {wea_data_user}")

    # 註：wea_bot 作為 tables 的 owner，本來就有全權限
    # 註：wea_bot 對 weather 的讀取權限會在下個步驟中調整


def downgrade() -> None:
    """Remove database permissions."""
    # 直接從環境變數讀取配置，避免與 Settings 類別耦合
    postgres_db = os.getenv('POSTGRES_DB')
    wea_data_user = os.getenv('WEA_DATA_USER')

    if not postgres_db:
        raise ValueError("POSTGRES_DB environment variable is required")
    if not wea_data_user:
        raise ValueError("WEA_DATA_USER environment variable is required")

    # 移除權限
    op.execute(f"REVOKE ALL ON weather FROM {wea_data_user}")
    op.execute(f"REVOKE ALL ON location FROM {wea_data_user}")
    op.execute(f"REVOKE ALL ON SCHEMA public FROM {wea_data_user}")
    op.execute(f"REVOKE CONNECT ON DATABASE {postgres_db} FROM {wea_data_user}")

    # 刪除用戶
    op.execute(f"DROP USER IF EXISTS {wea_data_user}")
