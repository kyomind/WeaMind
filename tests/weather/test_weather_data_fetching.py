"""
Test cases for the new weather data fetching functionality.
"""

from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.weather.models import Location, Weather
from app.weather.service import WeatherService


class TestWeatherDataFetching:
    """Test cases for weather data fetching and formatting."""

    def test_get_weather_forecast_by_location_with_data(self, session: Session) -> None:
        """Test weather forecast retrieval with actual data."""
        # Create a test location
        location = Location(
            geocode="6300100",
            county="臺北市",
            district="中正區",
            full_name="臺北市中正區",
            latitude=25.0330,
            longitude=121.5654,
        )
        session.add(location)
        session.commit()

        # Create test weather data
        base_time = datetime.now(UTC)
        fetched_time = base_time

        weather_records = []
        for i in range(9):
            start_time = base_time + timedelta(hours=i * 3)
            end_time = start_time + timedelta(hours=3)

            weather = Weather(
                location_id=location.id,
                start_time=start_time,
                end_time=end_time,
                fetched_at=fetched_time,
                weather_condition="晴時多雲",
                weather_emoji="⛅",
                precipitation_probability=20 + (i % 3) * 20,
                min_temperature=25 + i,
                max_temperature=28 + i,
                raw_description=f"Test weather data {i + 1}",
            )
            weather_records.append(weather)

        session.add_all(weather_records)
        session.commit()

        # Test the query
        result = WeatherService.get_weather_forecast_by_location(session, location.id)
        # Should return 8 records (sliding window for next 24 hours)
        assert len(result) == 8
        assert all(weather.location_id == location.id for weather in result)
        assert result[0].start_time < result[-1].start_time  # Ordered by time

    def test_format_weather_response(self, session: Session) -> None:
        """Test weather response formatting."""
        # Create a test location
        location = Location(
            geocode="6300100",
            county="臺北市",
            district="中正區",
            full_name="臺北市中正區",
            latitude=25.0330,
            longitude=121.5654,
        )
        session.add(location)
        session.commit()

        # Create minimal test weather data
        base_time = datetime.now(UTC)
        weather_records = []
        for i in range(3):  # Just 3 records for testing format
            start_time = base_time + timedelta(hours=i * 3)
            end_time = start_time + timedelta(hours=3)

            weather = Weather(
                location_id=location.id,
                start_time=start_time,
                end_time=end_time,
                fetched_at=base_time,
                weather_condition="晴時多雲",
                weather_emoji="⛅",
                precipitation_probability=20,
                min_temperature=25,
                max_temperature=28,
                raw_description="Test weather data",
            )
            weather_records.append(weather)

        # Test formatting
        formatted_response = WeatherService.format_weather_response(location, weather_records)

        # Check basic structure
        assert "🗺️ 臺北市中正區" in formatted_response
        assert "\n\n" in formatted_response  # Contains empty line after location
        assert "⛅" in formatted_response  # Weather emoji
        assert "🌡️" in formatted_response  # Temperature emoji
        assert "💧20%" in formatted_response  # Precipitation

    def test_format_weather_response_blank_line_after_four(self, session: Session) -> None:
        """Ensure a blank line is inserted after the first 4 items when 5-8 items exist."""
        # Create a test location
        location = Location(
            geocode="6300100",
            county="臺北市",
            district="中正區",
            full_name="臺北市中正區",
            latitude=25.0330,
            longitude=121.5654,
        )
        session.add(location)
        session.commit()

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

        formatted = WeatherService.format_weather_response(location, records)
        # Split by lines and verify an empty line exists exactly after the 4th item
        lines = formatted.split("\n")
        # header + empty + 8 items + 1 empty (after 4th) = 11 lines total
        assert len(lines) == 11
        assert lines[0].startswith("🗺️ ")
        assert lines[1] == ""
        # Items 2..5 are first 4 items
        assert all(lines[i] for i in range(2, 6))
        # Blank line after the 4th item
        assert lines[6] == ""
        # Items 7..10 are next 4 items
        assert all(lines[i] for i in range(7, 11))

    def test_handle_text_weather_query_with_data(self, session: Session) -> None:
        """Test complete text weather query flow with data."""
        # Create a test location
        location = Location(
            geocode="6300100",
            county="臺北市",
            district="中正區",
            full_name="臺北市中正區",
            latitude=25.0330,
            longitude=121.5654,
        )
        session.add(location)
        session.commit()

        # Create test weather data
        base_time = datetime.now(UTC)
        weather_records = []
        for i in range(9):
            start_time = base_time + timedelta(hours=i * 3)
            end_time = start_time + timedelta(hours=3)

            weather = Weather(
                location_id=location.id,
                start_time=start_time,
                end_time=end_time,
                fetched_at=base_time,
                weather_condition="晴時多雲",
                weather_emoji="⛅",
                precipitation_probability=20,
                min_temperature=25,
                max_temperature=28,
                raw_description="Test weather data",
            )
            weather_records.append(weather)

        session.add_all(weather_records)
        session.commit()

        # Test the complete flow
        result = WeatherService.handle_text_weather_query(session, "臺北市中正區")

        # Should return formatted weather data
        assert "🗺️ 臺北市中正區" in result
        assert "⛅" in result
        assert "🌡️" in result
        assert not result.startswith("找到了")  # New behavior - direct weather data

    def test_handle_text_weather_query_no_data(self, session: Session) -> None:
        """Test text weather query with location but no weather data."""
        # Clean up any existing weather data first
        session.query(Weather).delete()
        session.commit()

        # Create a test location without weather data
        location = Location(
            geocode="6300200",  # Different geocode to avoid conflicts
            county="新北市",
            district="永和區",
            full_name="新北市永和區",
            latitude=25.0100,
            longitude=121.5100,
        )
        session.add(location)
        session.commit()

        # Test the query
        result = WeatherService.handle_text_weather_query(session, "新北市永和區")

        # Should return error message
        assert "抱歉，目前無法取得 新北市永和區 的天氣資料" in result
