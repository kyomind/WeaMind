"""Own database lifecycles for complete Weather Query workflows."""

import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.user.models import User, UserQuery
from app.weather.location_resolution import (
    InvalidInputReason,
    ResolutionOutcome,
    resolve_shared_location,
    resolve_text,
)
from app.weather.models import Location, Weather
from app.weather.service import WeatherService

logger = logging.getLogger(__name__)
SessionFactory = Callable[[], Session]


class QueryOutcome(StrEnum):
    """Describe the structured outcome of a Weather Query."""

    FORECAST = "forecast"
    NO_WEATHER = "no_weather"
    MULTIPLE_LOCATIONS = "multiple_locations"
    TOO_MANY_LOCATIONS = "too_many_locations"
    LOCATION_NOT_FOUND = "location_not_found"
    OUTSIDE_TAIWAN = "outside_taiwan"
    INVALID_INPUT = "invalid_input"
    PRESET_NOT_SET = "preset_not_set"


@dataclass(frozen=True)
class LocationData:
    """Represent immutable Location data crossing the Session boundary."""

    id: int
    full_name: str


@dataclass(frozen=True)
class ForecastData:
    """Represent immutable forecast data needed by LINE presentation."""

    start_time: datetime
    end_time: datetime
    fetched_at: datetime
    weather_emoji: str | None
    precipitation_probability: int | None
    max_temperature: int | None


@dataclass(frozen=True)
class WeatherQueryResult:
    """Return structured, ORM-free Weather Query output."""

    outcome: QueryOutcome
    locations: tuple[LocationData, ...] = ()
    forecast: tuple[ForecastData, ...] = ()
    query_text: str | None = None
    invalid_reason: InvalidInputReason | None = None

    @property
    def selected_location(self) -> LocationData | None:
        """Return the uniquely selected Location data, when present."""
        return self.locations[0] if len(self.locations) == 1 else None


def _location_data(location: Location) -> LocationData:
    """Copy a Location ORM entity into immutable data."""
    return LocationData(id=location.id, full_name=location.full_name)


def _forecast_data(weather: Weather) -> ForecastData:
    """Copy a Weather ORM entity into immutable presentation data."""
    return ForecastData(
        start_time=weather.start_time,
        end_time=weather.end_time,
        fetched_at=weather.fetched_at,
        weather_emoji=weather.weather_emoji,
        precipitation_probability=weather.precipitation_probability,
        max_temperature=weather.max_temperature,
    )


def _record_history(session: Session, user: User | None, location_id: int) -> None:
    """
    Record secondary Query History inside a savepoint.

    A savepoint keeps a failed history flush from poisoning the workflow's
    surrounding transaction. Unknown users are intentionally ignored.
    """
    if user is None:
        return
    try:
        with session.begin_nested():
            session.add(UserQuery(user_id=user.id, location_id=location_id))
            session.flush()
    except Exception:
        logger.exception("Failed to record Query History", extra={"location_id": location_id})


def _result_for_location(
    session: Session, location: Location, user: User | None
) -> WeatherQueryResult:
    """Query weather and record history for an already resolved Location."""
    weather = WeatherService.get_weather_forecast_by_location(session, location.id)
    _record_history(session, user, location.id)
    return WeatherQueryResult(
        outcome=QueryOutcome.FORECAST if weather else QueryOutcome.NO_WEATHER,
        locations=(_location_data(location),),
        forecast=tuple(_forecast_data(item) for item in weather),
    )


def query_text(
    text: str, line_user_id: str | None, *, session_factory: SessionFactory | None = None
) -> WeatherQueryResult:
    """Run a text Weather Query with an internally owned Session."""
    factory = session_factory or SessionLocal
    with factory() as session, session.begin():
        user = (
            session.query(User).filter(User.line_user_id == line_user_id).first()
            if line_user_id
            else None
        )
        resolution = resolve_text(session, text)
        if resolution.outcome == ResolutionOutcome.INVALID:
            return WeatherQueryResult(
                QueryOutcome.INVALID_INPUT, invalid_reason=resolution.invalid_reason
            )
        if resolution.outcome == ResolutionOutcome.RESOLVED:
            location = session.get(Location, resolution.locations[0].id)
            if location is None:  # The resolver and workflow share one transaction.
                return WeatherQueryResult(QueryOutcome.LOCATION_NOT_FOUND)
            return _result_for_location(session, location, user)
        outcome = {
            ResolutionOutcome.MULTIPLE: QueryOutcome.MULTIPLE_LOCATIONS,
            ResolutionOutcome.TOO_MANY: QueryOutcome.TOO_MANY_LOCATIONS,
            ResolutionOutcome.NOT_FOUND: QueryOutcome.LOCATION_NOT_FOUND,
        }[resolution.outcome]
        copied = tuple(LocationData(item.id, item.full_name) for item in resolution.locations)
        return WeatherQueryResult(
            outcome=outcome, locations=copied, query_text=resolution.normalized_text
        )


def query_shared_location(
    latitude: float,
    longitude: float,
    address: str | None,
    line_user_id: str | None,
    *,
    session_factory: SessionFactory | None = None,
) -> WeatherQueryResult:
    """Run a shared-location Weather Query with address-first resolution."""
    factory = session_factory or SessionLocal
    with factory() as session, session.begin():
        user = (
            session.query(User).filter(User.line_user_id == line_user_id).first()
            if line_user_id
            else None
        )
        resolution = resolve_shared_location(session, latitude, longitude, address)
        if resolution.outcome != ResolutionOutcome.RESOLVED:
            return WeatherQueryResult(QueryOutcome.OUTSIDE_TAIWAN)
        location = session.get(Location, resolution.locations[0].id)
        if location is None:
            return WeatherQueryResult(QueryOutcome.OUTSIDE_TAIWAN)
        return _result_for_location(session, location, user)


def query_preset(
    line_user_id: str, preset: str, *, session_factory: SessionFactory | None = None
) -> WeatherQueryResult:
    """Run home or office Weather Query directly from its configured Location ID."""
    if preset not in {"home", "office"}:
        raise ValueError("preset must be 'home' or 'office'")
    factory = session_factory or SessionLocal
    with factory() as session, session.begin():
        user = session.query(User).filter(User.line_user_id == line_user_id).first()
        if user is None:
            return WeatherQueryResult(QueryOutcome.PRESET_NOT_SET)
        location_id = user.home_location_id if preset == "home" else user.work_location_id
        location = session.get(Location, location_id) if location_id is not None else None
        if location is None:
            return WeatherQueryResult(QueryOutcome.PRESET_NOT_SET)
        return _result_for_location(session, location, user)
