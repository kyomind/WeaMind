"""Test fixtures for weather module testing."""

from collections.abc import Callable, Iterator
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.orm import Session

from app.core.admin_divisions import initialize_admin_divisions
from app.core.database import get_session
from app.weather.models import Location, Weather


@pytest.fixture()
def session() -> Session:
    """Provide a database session for testing."""
    return next(get_session())


@pytest.fixture()
def create_location() -> Callable[..., Location]:
    """Return a helper for creating test locations."""

    def _create(
        geocode: str,
        county: str,
        district: str,
        full_name: str,
        latitude: float | None = None,
        longitude: float | None = None,
    ) -> Location:
        session = next(get_session())
        try:
            location = Location(
                geocode=geocode,
                county=county,
                district=district,
                full_name=full_name,
                latitude=latitude,
                longitude=longitude,
            )
            session.add(location)
            session.commit()
            session.refresh(location)
            return location
        finally:
            session.close()

    return _create


@pytest.fixture()
def create_weather() -> Callable[..., Weather]:
    """Return a helper for creating individual Weather records."""

    def _create(
        location_id: int,
        start_time: datetime,
        end_time: datetime,
        fetched_at: datetime | None = None,
        weather_condition: str = "晴時多雲",
        weather_emoji: str = "⛅",
        precipitation_probability: int = 20,
        min_temperature: int = 25,
        max_temperature: int = 28,
        raw_description: str = "Test weather data",
    ) -> Weather:
        """Create a single Weather record with test data."""
        if fetched_at is None:
            fetched_at = datetime.now(UTC)

        session = next(get_session())
        try:
            weather = Weather(
                location_id=location_id,
                start_time=start_time,
                end_time=end_time,
                fetched_at=fetched_at,
                weather_condition=weather_condition,
                weather_emoji=weather_emoji,
                precipitation_probability=precipitation_probability,
                min_temperature=min_temperature,
                max_temperature=max_temperature,
                raw_description=raw_description,
            )
            session.add(weather)
            session.commit()
            session.refresh(weather)
            return weather
        finally:
            session.close()

    return _create


@pytest.fixture()
def add_test_weather_data() -> Callable[..., list[Weather]]:
    """Return a helper for adding standard test weather data to a location."""

    def _add_data(
        session: Session,
        location_id: int,
        num_records: int = 9,
        base_time: datetime | None = None,
    ) -> list[Weather]:
        """
        Add standard test weather data for a location.

        Args:
            session: Database session
            location_id: ID of the location to add weather data for
            num_records: Number of weather records to create (default: 9)
            base_time: Base time for weather records (default: now)

        Returns:
            List of created Weather records
        """
        if base_time is None:
            base_time = datetime.now(UTC)

        weather_records = []
        for i in range(num_records):
            start_time = base_time + timedelta(hours=i * 3)
            end_time = start_time + timedelta(hours=3)

            weather = Weather(
                location_id=location_id,
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
        return weather_records

    return _add_data


@pytest.fixture()
def create_freshness_test_location() -> Callable[[Session], Location]:
    """Return a helper for creating the standard location used in freshness tests."""

    def _create(session: Session) -> Location:
        """Create the standard test location for freshness testing."""
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
        session.refresh(location)
        return location

    return _create


@pytest.fixture()
def create_weather_data_with_fetchtime() -> Callable[..., list[Weather]]:
    """Return a helper for creating weather data with specific fetched_at time."""

    def _create(
        session: Session,
        location_id: int,
        fetched_at: datetime,
        use_current_time_for_periods: bool = False,
        num_records: int = 9,
    ) -> list[Weather]:
        """
        Create weather data with specified fetched_at time.

        Args:
            session: Database session
            location_id: ID of the location
            fetched_at: When the weather data was fetched
            use_current_time_for_periods: If True, use current time for start/end periods
                                        If False, use fetched_at as base time
            num_records: Number of weather records to create

        Returns:
            List of created Weather records
        """
        # Choose base time for start/end periods
        if use_current_time_for_periods:
            base_time = datetime.now(UTC)
        else:
            base_time = fetched_at

        weather_records = []
        for i in range(num_records):
            start_time = base_time + timedelta(hours=i * 3)
            end_time = start_time + timedelta(hours=3)

            weather = Weather(
                location_id=location_id,
                start_time=start_time,
                end_time=end_time,
                fetched_at=fetched_at,
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
        return weather_records

    return _create


@pytest.fixture(autouse=True)
def setup_weather_tests() -> Iterator[None]:
    """Setup admin divisions and clean up after weather tests."""
    # Initialize admin divisions before tests
    initialize_admin_divisions()

    yield  # Run the test

    # Clean up after test
    session = next(get_session())
    try:
        session.query(Weather).delete()  # Clean weather data first (has FK to location)
        session.query(Location).delete()
        session.commit()
    finally:
        session.close()
