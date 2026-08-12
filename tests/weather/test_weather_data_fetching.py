"""
Test cases for the new weather data fetching functionality.
"""

from collections.abc import Callable
from unittest.mock import Mock

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.weather.models import Location, Weather
from app.weather.service import WeatherService


class TestWeatherDataFetching:
    """Test cases for weather data fetching and formatting."""

    def test_get_weather_forecast_by_location_with_data(
        self,
        session: Session,
        create_location: Callable[..., Location],
        add_test_weather_data: Callable[..., list[Weather]],
    ) -> None:
        """Test weather forecast retrieval with actual data."""
        # Create a test location
        location = create_location(
            geocode="6300100",
            county="臺北市",
            district="中正區",
            full_name="臺北市中正區",
            latitude=25.0330,
            longitude=121.5654,
        )

        # Create test weather data using shared fixture
        add_test_weather_data(session, location.id)

        # Test the query
        result = WeatherService.get_weather_forecast_by_location(session, location.id)
        # Should return 8 records (sliding window for next 24 hours)
        assert len(result) == 8
        assert all(weather.location_id == location.id for weather in result)
        assert result[0].start_time < result[-1].start_time  # Ordered by time

    def test_get_weather_forecast_returns_empty_list_on_database_error(self) -> None:
        """Contain database failures so a broken query never breaks the reply flow."""
        broken_session = Mock(spec=Session)
        broken_session.query.side_effect = SQLAlchemyError("connection lost")

        result = WeatherService.get_weather_forecast_by_location(broken_session, 1)

        assert result == []
