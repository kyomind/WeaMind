from datetime import UTC, datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String

from app.core.database import Base


class User(Base):
    """
    Database model for users.
    """

    __tablename__ = "user"

    id = Column(Integer, primary_key=True, autoincrement=True)
    line_user_id = Column(String, unique=True, index=True, nullable=False)
    display_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=False,
    )
