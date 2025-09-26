"""
Test cases for the new weather data fetching functionality.
"""

from collections.abc import Callable
from datetime import UTC, datetime, timedelta

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

    def test_format_weather_response(
        self,
        session: Session,
        create_location: Callable[..., Location],
        add_test_weather_data: Callable[..., list[Weather]],
    ) -> None:
        """Test weather response formatting."""
        # Create a test location
        location = create_location(
            geocode="6300100",
            county="臺北市",
            district="中正區",
            full_name="臺北市中正區",
            latitude=25.0330,
            longitude=121.5654,
        )

        # Create minimal test weather data (just 3 records for testing format)
        weather_records = add_test_weather_data(session, location.id, 3)

        # Test formatting
        formatted_response = WeatherService.format_weather_response(location, weather_records)

        # Check basic structure
        assert "🗺️ 臺北市中正區" in formatted_response
        assert "\n\n" in formatted_response  # Contains empty line after location
        assert "⛅" in formatted_response  # Weather emoji
        assert "🌡️" in formatted_response  # Temperature emoji
        assert "💧20%" in formatted_response  # Precipitation

    def test_format_weather_response_blank_line_after_four(
        self,
        session: Session,
        create_location: Callable[..., Location],
        add_test_weather_data: Callable[..., list[Weather]],
    ) -> None:
        """Ensure a blank line is inserted after the first 4 items when 5-8 items exist."""
        # Create a test location
        location = create_location(
            geocode="6300100",
            county="臺北市",
            district="中正區",
            full_name="臺北市中正區",
            latitude=25.0330,
            longitude=121.5654,
        )

        # Create 8 weather records to cover the full output
        base_time = datetime.now(UTC)
        records: list[Weather] = []
        for i in range(8):
            start_time = base_time + timedelta(hours=i * 3)
            end_time = start_time + timedelta(hours=3)
            records.append(
                Weather(
                    location_id=location.id,
                    start_time=start_time,
                    end_time=end_time,
                    fetched_at=base_time,
                    weather_condition="晴時多雲",
                    weather_emoji="☀️" if i < 4 else "🌦️",
                    precipitation_probability=10 * (i % 4),
                    min_temperature=25,
                    max_temperature=28 + i,
                    raw_description=f"Test {i}",
                )
            )
        session.add_all(records)
        session.commit()

        formatted = WeatherService.format_weather_response(location, records)
        # Split by lines and verify an empty line exists exactly after the 4th item
        lines = formatted.split("\n")
        # header + empty + 8 items + 1 empty (after 4th) + 1 empty + 1 update time = 13 lines total
        assert len(lines) == 13
        assert lines[0].startswith("🗺️ ")
        assert lines[1] == ""
        # Items 2..5 are first 4 items
        assert all(lines[i] for i in range(2, 6))
        # Blank line after the 4th item
        assert lines[6] == ""
        # Items 7..10 are next 4 items
        assert all(lines[i] for i in range(7, 11))
        # Blank line before update time
        assert lines[11] == ""
        # Update time line
        assert lines[12].startswith("✅ ") and lines[12].endswith(" 更新")

    def test_handle_text_weather_query_with_data(
        self,
        session: Session,
        create_location: Callable[..., Location],
        add_test_weather_data: Callable[..., list[Weather]],
    ) -> None:
        """Test complete text weather query flow with data."""
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

        # Test the complete flow
        result = WeatherService.handle_text_weather_query(session, "臺北市中正區")

        # Should return formatted weather data
        assert "🗺️ 臺北市中正區" in result
        assert "⛅" in result
        assert "🌡️" in result
        assert not result.startswith("找到了")  # New behavior - direct weather data

    def test_handle_text_weather_query_no_data(
        self, session: Session, create_location: Callable[..., Location]
    ) -> None:
        """Test text weather query with location but no weather data."""
        # Clean up any existing weather data first
        session.query(Weather).delete()
        session.commit()

        # Create a test location without weather data using shared fixture
        create_location(
            geocode="6300200",  # Different geocode to avoid conflicts
            county="新北市",
            district="永和區",
            full_name="新北市永和區",
            latitude=25.0100,
            longitude=121.5100,
        )

        # Test the query
        result = WeatherService.handle_text_weather_query(session, "新北市永和區")

        # Should return error message
        assert "抱歉，目前無法取得 新北市永和區 的天氣資料" in result
