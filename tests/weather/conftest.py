"""Test fixtures for weather module testing."""

from collections.abc import Callable, Iterator

import pytest
from sqlalchemy.orm import Session

from app.core.admin_divisions import initialize_admin_divisions
from app.core.database import get_session
from app.weather.models import Location


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


@pytest.fixture(autouse=True)
def setup_weather_tests() -> Iterator[None]:
    """Setup admin divisions and clean up after weather tests."""
    # Initialize admin divisions before tests
    initialize_admin_divisions()

    yield  # Run the test

    # Clean up after test
    session = next(get_session())
    try:
        session.query(Location).delete()
        session.commit()
    finally:
        session.close()
