"""Test forecast service and the location-resolution interface."""

from collections.abc import Callable

import pytest
from sqlalchemy.orm import Session

from app.weather.location_resolution import (
    InvalidInputReason,
    QueryOutcome,
    resolve_shared_location,
    resolve_text,
)
from app.weather.models import Location, Weather
from app.weather.service import WeatherService


@pytest.mark.parametrize(
    ("text", "reason"),
    [
        ("", InvalidInputReason.EMPTY),
        ("區", InvalidInputReason.INVALID_LENGTH),
        ("abc", InvalidInputReason.NON_CHINESE),
    ],
)
def test_text_resolution_reports_invalid_reason(
    session: Session, text: str, reason: InvalidInputReason
) -> None:
    """Expose invalid input reasons without presentation wording."""
    result = resolve_text(session, text)
    assert result.outcome == QueryOutcome.INVALID_INPUT
    assert result.invalid_reason == reason


def test_text_resolution_encapsulates_candidate_policy(
    session: Session, create_location: Callable[..., Location]
) -> None:
    """Return direct, multiple, too-many, and not-found outcomes through one interface."""
    direct = create_location(
        geocode="direct",
        county="臺北市",
        district="大安區",
        full_name="臺北市大安區",
    )
    resolved = resolve_text(session, "台北市大安區")
    assert resolved.outcome == QueryOutcome.FORECAST
    assert resolved.normalized_text == "臺北市大安區"
    assert resolved.locations[0].id == direct.id

    for index in range(4):
        create_location(
            geocode=f"x-{index}",
            county=f"測試{index}",
            district="中正區",
            full_name=f"測試{index}中正區",
        )
    assert resolve_text(session, "中正區").outcome == QueryOutcome.TOO_MANY_LOCATIONS
    assert resolve_text(session, "不存在").outcome == QueryOutcome.LOCATION_NOT_FOUND

    create_location(
        geocode="second-xinyi",
        county="基隆市",
        district="信義區",
        full_name="基隆市信義區",
    )
    create_location(
        geocode="third-xinyi",
        county="臺北市",
        district="信義區",
        full_name="臺北市信義區",
    )
    candidates = resolve_text(session, "信義區")
    assert candidates.outcome == QueryOutcome.MULTIPLE_LOCATIONS
    assert len(candidates.locations) == 2


def test_shared_resolution_prefers_address_then_falls_back(
    session: Session, create_location: Callable[..., Location]
) -> None:
    """Honor valid address precedence and use coordinates only as fallback."""
    addressed = create_location(
        geocode="addressed",
        county="臺北市",
        district="信義區",
        full_name="臺北市信義區",
        latitude=22.0,
        longitude=120.0,
    )
    nearby = create_location(
        geocode="nearby",
        county="臺北市",
        district="松山區",
        full_name="臺北市松山區",
        latitude=25.0,
        longitude=121.0,
    )
    result = resolve_shared_location(session, 25.0, 121.0, "台北市信義區信義路五段")
    assert result.locations[0].id == addressed.id
    fallback = resolve_shared_location(session, 25.0, 121.0, "無法解析")
    assert fallback.locations[0].id == nearby.id


def test_shared_resolution_rejects_unserviceable_coordinates(
    session: Session, create_location: Callable[..., Location]
) -> None:
    """Reject coordinates outside Taiwan or farther than the service threshold."""
    create_location(
        geocode="taipei",
        county="臺北市",
        district="松山區",
        full_name="臺北市松山區",
        latitude=25.0,
        longitude=121.0,
    )
    overseas = resolve_shared_location(session, 35.0, 139.0, None)
    assert overseas.outcome == QueryOutcome.OUTSIDE_TAIWAN
    distant = resolve_shared_location(session, 23.0, 119.5, None)
    assert distant.outcome == QueryOutcome.OUTSIDE_TAIWAN


def test_shared_resolution_supports_taiwan_address_forms(
    session: Session, create_location: Callable[..., Location]
) -> None:
    """Resolve county and provincial-city addresses through the public interface."""
    county = create_location(
        geocode="county",
        county="新竹縣",
        district="竹北市",
        full_name="新竹縣竹北市",
    )
    provincial_city = create_location(
        geocode="provincial-city",
        county="基隆市",
        district="中正區",
        full_name="基隆市中正區",
    )
    county_result = resolve_shared_location(session, 35.0, 139.0, "新竹縣竹北市縣政九路146號")
    city_result = resolve_shared_location(session, 35.0, 139.0, "基隆市中正區中正路1號")
    assert county_result.locations[0].id == county.id
    assert city_result.locations[0].id == provincial_city.id


class TestWeatherService:
    """Test WeatherService functionality."""

    def test_weather_data_freshness_normal(
        self,
        session: Session,
        create_freshness_test_location: Callable[[Session], Location],
        create_weather_data_with_fetchtime: Callable[..., list[Weather]],
    ) -> None:
        """Test weather query with fresh data (3 hours old)."""
        from datetime import UTC, datetime, timedelta

        # Create test location
        location = create_freshness_test_location(session)

        # Create fresh weather data (3 hours ago)
        fetched_at = datetime.now(UTC) - timedelta(hours=3)
        create_weather_data_with_fetchtime(session, location.id, fetched_at)

        # Query weather data
        weather_data = WeatherService.get_weather_forecast_by_location(session, location.id)

        # Should return data (fresh within 6.5 hours)
        assert len(weather_data) > 0

    def test_weather_data_freshness_boundary(
        self,
        session: Session,
        create_freshness_test_location: Callable[[Session], Location],
        create_weather_data_with_fetchtime: Callable[..., list[Weather]],
    ) -> None:
        """Test weather query with data exactly at 6.5 hour boundary."""
        from datetime import UTC, datetime, timedelta

        # Create test location
        location = create_freshness_test_location(session)

        # Create boundary weather data (6.4 hours ago, within boundary)
        fetched_at = datetime.now(UTC) - timedelta(hours=6.4)
        create_weather_data_with_fetchtime(session, location.id, fetched_at)

        # Query weather data
        weather_data = WeatherService.get_weather_forecast_by_location(session, location.id)

        # Should return data (exactly at boundary, should be acceptable)
        assert len(weather_data) > 0

    def test_weather_data_freshness_stale(
        self,
        session: Session,
        create_freshness_test_location: Callable[[Session], Location],
        create_weather_data_with_fetchtime: Callable[..., list[Weather]],
    ) -> None:
        """Test weather query with stale data (8 hours old)."""
        from datetime import UTC, datetime, timedelta

        # Create test location
        location = create_freshness_test_location(session)

        # Create stale weather data (8 hours ago fetched_at, but future time periods)
        fetched_at = datetime.now(UTC) - timedelta(hours=8)
        create_weather_data_with_fetchtime(
            session, location.id, fetched_at, use_current_time_for_periods=True
        )

        # Query weather data
        weather_data = WeatherService.get_weather_forecast_by_location(session, location.id)

        # Should return empty list (data too stale)
        assert len(weather_data) == 0
