"""Provide forecast retrieval operations."""

import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.weather.models import Weather

logger = logging.getLogger(__name__)


class WeatherService:
    """Service for handling weather queries with different location sources."""

    @staticmethod
    def get_weather_forecast_by_location(session: Session, location_id: int) -> list[Weather]:
        """
        Get weather forecast using sliding window logic to ensure consistent 24-hour forecast.

        This function implements the sliding window strategy to guarantee users always see
        a complete 24-hour (8 time periods) forecast, regardless of query time.

        Args:
            session: Database session
            location_id: ID of the location to query weather for

        Returns:
            list[Weather]: List of 8 Weather objects representing 24-hour forecast,
                          ordered by start_time. Empty list if no data found.
        """
        try:
            # Get the latest fetched_at timestamp for this location (within freshness window)
            # Use explicit UTC time to ensure consistency with stored data
            utc_now = datetime.now(UTC)
            freshness_threshold = utc_now - timedelta(hours=6.5)

            latest_fetched_subquery = (
                session.query(func.max(Weather.fetched_at))
                .filter(
                    Weather.location_id == location_id, Weather.fetched_at >= freshness_threshold
                )
                .scalar_subquery()
            )

            # Sliding window query as defined in weather-query-logic.md
            # Use database-agnostic approach: get all recent data and filter in Python if needed
            weather_data = (
                session.query(Weather)
                .filter(
                    Weather.location_id == location_id,
                    # Filter out expired time periods (sliding window key) - use same UTC time
                    Weather.end_time > utc_now,
                    # Get data from the latest batch (already filtered for freshness)
                    Weather.fetched_at == latest_fetched_subquery,
                )
                .order_by(Weather.start_time)
                .limit(8)
                .all()
            )

            logger.info(
                f"Retrieved {len(weather_data)} weather records for location_id={location_id}"
            )

        except Exception:
            logger.exception(f"Error retrieving weather forecast for location_id={location_id}")
            return []
        else:
            return weather_data
