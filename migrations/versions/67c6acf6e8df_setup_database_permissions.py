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
    # Read configuration directly from environment variables to avoid coupling with the Settings class
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

    # 1. Elevate wea_bot permissions (allowing it to create other users)
    op.execute(f"ALTER USER {postgres_user} WITH CREATEROLE")

    # 2. Create wea_data user (if it does not exist)
    op.execute(f"""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '{wea_data_user}') THEN
                CREATE USER {wea_data_user} WITH PASSWORD '{wea_data_password}';
            END IF;
        END
        $$;
    """)

    # 3. Set basic connection permissions
    op.execute(f"GRANT CONNECT ON DATABASE {postgres_db} TO {wea_data_user}")
    op.execute(f"GRANT USAGE ON SCHEMA public TO {wea_data_user}")

    # 4. Set table permissions
    # Permissions for wea_data on location: read-only
    op.execute(f"GRANT SELECT ON location TO {wea_data_user}")

    # Permissions for wea_data on weather: full access
    op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON weather TO {wea_data_user}")

    # 5. Set sequence permissions (allowing wea_data to insert data)
    op.execute(f"GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO {wea_data_user}")

    # Note: As the owner of the tables, wea_bot already has full permissions
    # Note: wea_bot's read permissions on weather will be adjusted in the next step


def downgrade() -> None:
    """Remove database permissions."""
    # Read configuration directly from environment variables to avoid coupling with the Settings class
    postgres_db = os.getenv('POSTGRES_DB')
    wea_data_user = os.getenv('WEA_DATA_USER')

    if not postgres_db:
        raise ValueError("POSTGRES_DB environment variable is required")
    if not wea_data_user:
        raise ValueError("WEA_DATA_USER environment variable is required")

    # Revoke permissions
    op.execute(f"REVOKE ALL ON weather FROM {wea_data_user}")
    op.execute(f"REVOKE ALL ON location FROM {wea_data_user}")
    op.execute(f"REVOKE ALL ON SCHEMA public FROM {wea_data_user}")
    op.execute(f"REVOKE CONNECT ON DATABASE {postgres_db} FROM {wea_data_user}")

    # Drop user
    op.execute(f"DROP USER IF EXISTS {wea_data_user}")
