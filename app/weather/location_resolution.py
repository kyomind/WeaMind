"""Resolve user-provided location sources behind one structured interface."""

import logging
import math
import re
from dataclasses import dataclass
from enum import StrEnum

from sqlalchemy.orm import Session

from app.core.admin_divisions import is_valid_taiwan_division
from app.weather.models import Location

logger = logging.getLogger(__name__)


class ResolutionOutcome(StrEnum):
    """Describe a location resolution result without presentation text."""

    RESOLVED = "resolved"
    MULTIPLE = "multiple"
    TOO_MANY = "too_many"
    NOT_FOUND = "not_found"
    INVALID = "invalid"
    OUTSIDE_SERVICE_AREA = "outside_service_area"


class InvalidInputReason(StrEnum):
    """Describe why text input cannot be resolved."""

    EMPTY = "empty"
    INVALID_LENGTH = "invalid_length"
    NON_CHINESE = "non_chinese"


@dataclass(frozen=True)
class ResolvedLocation:
    """Carry immutable location identity across the resolution seam."""

    id: int
    full_name: str


@dataclass(frozen=True)
class LocationResolution:
    """Represent the complete structured result of location resolution."""

    outcome: ResolutionOutcome
    locations: tuple[ResolvedLocation, ...] = ()
    normalized_text: str | None = None
    invalid_reason: InvalidInputReason | None = None


def resolve_text(session: Session, text: str) -> LocationResolution:
    """Resolve text while encapsulating validation and candidate policy."""
    normalized = text.strip()
    if not normalized:
        return LocationResolution(
            ResolutionOutcome.INVALID, invalid_reason=InvalidInputReason.EMPTY
        )
    if not 2 <= len(normalized) <= 7:
        return LocationResolution(
            ResolutionOutcome.INVALID, invalid_reason=InvalidInputReason.INVALID_LENGTH
        )
    if re.fullmatch(r"[\u4e00-\u9fff]+", normalized) is None:
        return LocationResolution(
            ResolutionOutcome.INVALID, invalid_reason=InvalidInputReason.NON_CHINESE
        )
    normalized = normalized.replace("台", "臺")
    matches = (
        session.query(Location)
        .filter(Location.full_name.like(f"%{normalized}%"))
        .order_by(Location.full_name)
        .all()
    )
    locations = tuple(ResolvedLocation(item.id, item.full_name) for item in matches)
    if len(locations) == 1:
        outcome = ResolutionOutcome.RESOLVED
    elif 2 <= len(locations) <= 3:
        outcome = ResolutionOutcome.MULTIPLE
    elif len(locations) > 3:
        outcome = ResolutionOutcome.TOO_MANY
        locations = ()
    else:
        outcome = ResolutionOutcome.NOT_FOUND
    return LocationResolution(outcome, locations, normalized)


def resolve_shared_location(
    session: Session, latitude: float, longitude: float, address: str | None
) -> LocationResolution:
    """Resolve a shared location by address first, then coordinate fallback."""
    location = _from_address(session, address) if address else None
    location = location or _from_coordinates(session, latitude, longitude)
    if location is None:
        return LocationResolution(ResolutionOutcome.OUTSIDE_SERVICE_AREA)
    return LocationResolution(
        ResolutionOutcome.RESOLVED,
        (ResolvedLocation(location.id, location.full_name),),
    )


def _from_address(session: Session, address: str) -> Location | None:
    """Find an exact persisted division extracted from a Taiwan address."""
    patterns = (
        r"(台北市|臺北市|新北市|桃園市|台中市|臺中市|台南市|臺南市|高雄市)([\u4e00-\u9fff]{1,3}區)",
        r"([\u4e00-\u9fff]{2,3}縣)([\u4e00-\u9fff]{1,3}[鄉鎮市區])",
        r"(基隆市|新竹市|嘉義市)([\u4e00-\u9fff]{1,3}區)",
    )
    for pattern in patterns:
        match = re.search(pattern, address)
        if match:
            division = match.group(0).replace("台", "臺")
            if is_valid_taiwan_division(division):
                return session.query(Location).filter(Location.full_name == division).first()
            return None
    return None


def _from_coordinates(session: Session, latitude: float, longitude: float) -> Location | None:
    """Find the nearest service location when coordinates are plausibly in Taiwan."""
    if not (21.9 <= latitude <= 26.5 and 118.0 <= longitude <= 122.0):
        return None
    locations = session.query(Location).filter(
        Location.latitude.isnot(None), Location.longitude.isnot(None)
    )
    nearest: Location | None = None
    nearest_distance = float("inf")
    for location in locations:
        # Keep the model's nullable annotation safe even if adapter filtering changes.
        if location.latitude is None or location.longitude is None:
            continue
        candidate_distance = _distance(
            latitude, longitude, float(location.latitude), float(location.longitude)
        )
        if candidate_distance < nearest_distance:
            nearest, nearest_distance = location, candidate_distance
    # A broad bounds check alone would incorrectly serve users over nearby water.
    return nearest if nearest_distance <= 15.0 else None


def _distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate great-circle distance in kilometres."""
    lat1_r, lon1_r, lat2_r, lon2_r = map(math.radians, (lat1, lon1, lat2, lon2))
    delta_lat, delta_lon = lat2_r - lat1_r, lon2_r - lon1_r
    value = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1_r) * math.cos(lat2_r) * math.sin(delta_lon / 2) ** 2
    )
    return 6371.0 * 2 * math.asin(math.sqrt(value))
