"""Weather and Location database models and SQLAlchemy table definitions."""

from datetime import UTC, datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Location(Base):
    """
    Database model for administrative districts.
    Represents a specific county and district like '新北市永和區'.
    """

    __tablename__ = "location"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    geocode: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    county: Mapped[str] = mapped_column(String(10), nullable=False)
    district: Mapped[str] = mapped_column(String(10), nullable=False)
    full_name: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    latitude: Mapped[float | None] = mapped_column(Numeric(9, 6), nullable=True)
    longitude: Mapped[float | None] = mapped_column(Numeric(9, 6), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    # Relationship to Weather model
    forecasts: Mapped[list["Weather"]] = relationship(back_populates="location")


class Weather(Base):
    """
    Database model for weather forecasts.
    Each record represents a 3-hour forecast for a specific location.
    """

    __tablename__ = "weather"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    location_id: Mapped[int] = mapped_column(ForeignKey("location.id"), nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    end_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    weather_condition: Mapped[str] = mapped_column(String(30), nullable=False)
    weather_emoji: Mapped[str | None] = mapped_column(String(10), nullable=True)
    precipitation_probability: Mapped[int | None] = mapped_column(Integer, nullable=True)
    min_temperature: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_temperature: Mapped[int | None] = mapped_column(Integer, nullable=True)
    raw_description: Mapped[str] = mapped_column(Text, nullable=False)

    # Relationship to Location model
    location: Mapped["Location"] = relationship(back_populates="forecasts")

    __table_args__ = (
        CheckConstraint(
            "precipitation_probability >= 0 AND precipitation_probability <= 100",
            name="check_precipitation_probability",
        ),
        UniqueConstraint(
            "location_id",
            "start_time",
            "end_time",
            "fetched_at",
            name="unique_location_time_fetched",
        ),
    )


class Task(Base):
    """
    Database model for monitoring wea-data ETL service execution.
    Records task status, success/failure, and processing statistics.
    """

    __tablename__ = "task"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    county: Mapped[str] = mapped_column(String(10), nullable=False)
    start_time: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    end_time: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    is_success: Mapped[bool] = mapped_column(Boolean, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    attempt_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    records_processed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
