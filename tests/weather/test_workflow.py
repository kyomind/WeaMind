"""Integration tests for the database-owning Weather Query workflow."""

from collections.abc import Iterator, Sequence
from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.core.database import Base
from app.user.models import User, UserQuery
from app.weather.location_resolution import QueryOutcome
from app.weather.models import Location, Weather
from app.weather.workflow import query_preset, query_shared_location, query_text


@pytest.fixture
def workflow_db() -> Iterator[tuple[sessionmaker[Session], Location]]:
    """Provide an isolated SQLite adapter populated with a location and forecast."""
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    factory = sessionmaker(engine, autoflush=False)
    with factory.begin() as session:
        location = Location(
            geocode="63000010",
            county="臺北市",
            district="松山區",
            full_name="臺北市松山區",
            latitude=25.0,
            longitude=121.0,
        )
        session.add(location)
        session.flush()
        session.add_all(
            [
                User(
                    line_user_id="known",
                    home_location_id=location.id,
                    work_location_id=location.id,
                ),
                Weather(
                    location_id=location.id,
                    start_time=datetime.now(UTC),
                    end_time=datetime.now(UTC) + timedelta(hours=3),
                    fetched_at=datetime.now(UTC),
                    weather_condition="晴",
                    weather_emoji="☀️",
                    precipitation_probability=10,
                    max_temperature=30,
                    raw_description="晴",
                ),
            ]
        )
    yield factory, location
    engine.dispose()


def test_text_query_records_history_and_returns_dtos(
    workflow_db: tuple[sessionmaker[Session], Location],
) -> None:
    """Resolve text, record history, and return no ORM entities."""
    factory, location = workflow_db
    result = query_text("松山區", "known", session_factory=factory)
    assert result.outcome == QueryOutcome.FORECAST
    assert result.locations[0].__class__.__name__ == "ResolvedLocation"
    assert result.forecast[0].__class__.__name__ == "ForecastData"
    with factory() as session:
        assert len(session.scalars(select(UserQuery)).all()) == 1


def test_shared_location_and_presets_use_adapter(
    workflow_db: tuple[sessionmaker[Session], Location],
) -> None:
    """Cover shared location, address precedence, and both presets via public seams."""
    factory, _ = workflow_db
    shared = query_shared_location(25.0, 121.0, None, "known", session_factory=factory)
    addressed = query_shared_location(35.0, 139.0, "臺北市松山區", "known", session_factory=factory)
    assert shared.selected_location == addressed.selected_location
    assert shared.selected_location is not None
    assert shared.selected_location.full_name == "臺北市松山區"
    assert query_preset("known", "home", session_factory=factory).outcome == QueryOutcome.FORECAST
    assert query_preset("known", "office", session_factory=factory).outcome == QueryOutcome.FORECAST


def test_no_weather_is_recorded_but_unknown_user_is_not(
    workflow_db: tuple[sessionmaker[Session], Location],
) -> None:
    """Record resolved no-weather queries while skipping unknown users."""
    factory, _ = workflow_db
    with factory.begin() as session:
        session.query(Weather).delete()
    result = query_text("松山", "known", session_factory=factory)
    assert result.outcome == QueryOutcome.NO_WEATHER
    assert result.selected_location is not None
    assert result.selected_location.full_name == "臺北市松山區"
    assert result.forecast == ()
    query_text("松山", "unknown", session_factory=factory)
    with factory() as session:
        assert len(session.scalars(select(UserQuery)).all()) == 1


def test_history_flush_failure_does_not_poison_transaction(
    workflow_db: tuple[sessionmaker[Session], Location],
) -> None:
    """Return forecast and commit outer transaction after savepoint flush failure."""
    factory, location = workflow_db
    original_flush = Session.flush
    calls = 0

    def fail_history_flush(session: Session, objects: Sequence[Any] | None = None) -> None:
        """Fail only the explicit history flush."""
        nonlocal calls
        if any(isinstance(item, UserQuery) for item in session.new):
            calls += 1
            if calls == 1:
                raise RuntimeError("history unavailable")
        original_flush(session, objects)

    with patch.object(Session, "flush", fail_history_flush):
        result = query_text("松山", "known", session_factory=factory)
    assert result.outcome == QueryOutcome.FORECAST
    assert result.forecast
    with factory() as session:
        assert session.scalars(select(UserQuery)).all() == []


def test_text_query_not_found_preserves_normalized_text(
    workflow_db: tuple[sessionmaker[Session], Location],
) -> None:
    """Map a missing Location to the Weather Query outcome and preserve its text."""
    factory, _ = workflow_db
    result = query_text("不存在", None, session_factory=factory)
    assert result.outcome == QueryOutcome.LOCATION_NOT_FOUND
    assert result.query_text == "不存在"


def test_shared_query_outside_taiwan(
    workflow_db: tuple[sessionmaker[Session], Location],
) -> None:
    """Map an unserviceable shared location to the Weather Query outcome."""
    factory, _ = workflow_db
    result = query_shared_location(35.0, 139.0, None, "known", session_factory=factory)
    assert result.outcome == QueryOutcome.OUTSIDE_TAIWAN


def test_invalid_preset_is_rejected_before_opening_a_session() -> None:
    """Reject unsupported preset names at the workflow boundary."""
    with pytest.raises(ValueError, match="preset must be"):
        query_preset("known", "holiday")


def test_text_query_distinguishes_too_many_matches(
    workflow_db: tuple[sessionmaker[Session], Location],
) -> None:
    """Preserve the distinct guidance for an overly broad Location query."""
    factory, _ = workflow_db
    with factory.begin() as session:
        for index in range(4):
            session.add(
                Location(
                    geocode=f"many-{index}",
                    county=f"測試{index}",
                    district="中正區",
                    full_name=f"測試{index}中正區",
                )
            )

    result = query_text("中正區", None, session_factory=factory)

    assert result.outcome == QueryOutcome.TOO_MANY_LOCATIONS


def test_text_query_rejects_invalid_input(
    workflow_db: tuple[sessionmaker[Session], Location],
) -> None:
    """Surface the resolver's invalid-input reason without touching Location data."""
    factory, _ = workflow_db
    result = query_text("a", None, session_factory=factory)
    assert result.outcome == QueryOutcome.INVALID_INPUT
    assert result.invalid_reason is not None
    assert result.locations == ()


def test_preset_query_for_unknown_user(
    workflow_db: tuple[sessionmaker[Session], Location],
) -> None:
    """Treat a preset query from an unregistered user as an unset preset."""
    factory, _ = workflow_db
    result = query_preset("nobody", "home", session_factory=factory)
    assert result.outcome == QueryOutcome.PRESET_NOT_SET


def test_preset_query_without_configured_location(
    workflow_db: tuple[sessionmaker[Session], Location],
) -> None:
    """Treat a user without a configured preset Location as an unset preset."""
    factory, _ = workflow_db
    with factory.begin() as session:
        session.add(User(line_user_id="blank"))
    result = query_preset("blank", "office", session_factory=factory)
    assert result.outcome == QueryOutcome.PRESET_NOT_SET
