"""User database models and SQLAlchemy table definitions."""

from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.weather.models import Location


class User(Base):
    """
    Database model for users.
    """

    __tablename__ = "user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    line_user_id: Mapped[str] = mapped_column(String, unique=True, index=True)
    display_name: Mapped[str | None] = mapped_column(String, nullable=True)
    home_location_id: Mapped[int | None] = mapped_column(ForeignKey("location.id"), nullable=True)
    work_location_id: Mapped[int | None] = mapped_column(ForeignKey("location.id"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    # Relationships to Location model
    home_location: Mapped["Location"] = relationship(
        "Location", foreign_keys=[home_location_id], lazy="select"
    )
    work_location: Mapped["Location"] = relationship(
        "Location", foreign_keys=[work_location_id], lazy="select"
    )


class UserQuery(Base):
    """
    Database model for user query history.

    Records each location query made by users to enable recent query features
    and provide usage analytics.
    """

    __tablename__ = "user_query"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("user.id"), nullable=False, index=True)
    location_id: Mapped[int] = mapped_column(ForeignKey("location.id"), nullable=False)
    query_time: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC), index=True
    )

    # Relationships
    user: Mapped["User"] = relationship("User", lazy="select")
    location: Mapped["Location"] = relationship("Location", lazy="select")
