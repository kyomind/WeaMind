"""Service layer for weather and location operations."""

import logging
import math
import re
from collections.abc import Sequence

from sqlalchemy.orm import Session

from app.weather.models import Location

logger = logging.getLogger(__name__)


class LocationParseError(Exception):
    """Exception raised when location input parsing fails."""

    def __init__(self, message: str, input_text: str) -> None:
        self.message = message
        self.input_text = input_text
        super().__init__(message)


class LocationService:
    """Service for handling location-related operations."""

    @staticmethod
    def validate_location_input(text: str) -> str:
        """
        Validate location input format according to PRD requirements.

        Args:
            text: User input text

        Returns:
            str: Cleaned input text

        Raises:
            LocationParseError: If input format is invalid
        """
        # Remove whitespace
        cleaned_text = text.strip()

        # Check if input is empty
        if not cleaned_text:
            raise LocationParseError("輸入不能為空", text)

        # Check character count (2-6 Chinese characters)
        char_count = len(cleaned_text)
        if char_count < 2 or char_count > 6:
            raise LocationParseError("🤔 輸入的字數不對喔！請輸入 2 到 6 個字的地名", text)

        # Check if input contains only Chinese characters (and some common district suffixes)
        if not re.match(r"^[\u4e00-\u9fff]+$", cleaned_text):
            raise LocationParseError("請輸入中文地名", text)

        # Replace "台" with "臺" for compatibility with official data
        # This handles common cases like "台北" -> "臺北"
        normalized_text = cleaned_text.replace("台", "臺")

        return normalized_text

    @staticmethod
    def search_locations_by_name(session: Session, location_name: str) -> Sequence[Location]:
        """
        Search locations by name using fuzzy matching.

        Args:
            session: Database session
            location_name: Location name to search for

        Returns:
            Sequence[Location]: List of matching locations
        """
        return (
            session.query(Location)
            .filter(Location.full_name.like(f"%{location_name}%"))
            .order_by(Location.full_name)
            .all()
        )

    @staticmethod
    def parse_location_input(session: Session, text: str) -> tuple[Sequence[Location], str]:
        """
        Parse user location input and return matching locations with appropriate response.

        Based on PRD specification:
        - 1 result: Return weather directly
        - 2-3 results: Return options for user to choose
        - >3 results or 0 results: Return error message

        Args:
            session: Database session
            text: User input text

        Returns:
            tuple: (locations, response_message)
                - locations: List of matching Location objects (empty if >3 matches)
                - response_message: User-friendly response message

        Raises:
            LocationParseError: If input format is invalid
        """
        # Validate input format first
        cleaned_input = LocationService.validate_location_input(text)

        # Search for matching locations
        locations = LocationService.search_locations_by_name(session, cleaned_input)
        result_count = len(locations)

        if result_count == 0:
            # No matches found
            response = f"😕 找不到「{cleaned_input}」這個地點耶，要不要檢查看看有沒有打錯字？"
            # Return empty list with error message
            return locations, response

        elif result_count == 1:
            # Single match - will proceed to weather query
            location = locations[0]
            response = f"找到了 {location.full_name}，正在查詢天氣..."
            # Return single location for weather query
            return locations, response

        elif 2 <= result_count <= 3:
            # Multiple matches - provide options with Quick Reply
            response = "😕 找到多個符合的地點，請選擇："
            # Return locations for Quick Reply selection
            return locations, response

        else:
            # Too many matches
            response = "🤔 找到太多符合的地點了！請輸入更具體的地名"
            # Return empty list when too many matches (>3)
            return [], response

    @staticmethod
    def _calculate_haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate the great circle distance between two points on Earth using Haversine formula.

        Args:
            lat1: Latitude of first point in degrees
            lon1: Longitude of first point in degrees
            lat2: Latitude of second point in degrees
            lon2: Longitude of second point in degrees

        Returns:
            float: Distance between points in kilometers
        """
        # Convert decimal degrees to radians
        lat1_radians = math.radians(lat1)
        lon1_radians = math.radians(lon1)
        lat2_radians = math.radians(lat2)
        lon2_radians = math.radians(lon2)

        # Haversine formula
        delta_lat = lat2_radians - lat1_radians
        delta_lon = lon2_radians - lon1_radians
        sin_half_delta_lat = math.sin(delta_lat / 2) ** 2
        sin_half_delta_lon = math.sin(delta_lon / 2) ** 2
        haversine_a = (
            sin_half_delta_lat
            + math.cos(lat1_radians) * math.cos(lat2_radians) * sin_half_delta_lon
        )
        central_angle = 2 * math.asin(math.sqrt(haversine_a))

        # Earth radius in kilometers
        earth_radius_km = 6371.0

        return earth_radius_km * central_angle

    @staticmethod
    def _is_in_taiwan_bounds(lat: float, lon: float) -> bool:
        """
        Check if coordinates are roughly within Taiwan's boundaries.

        Args:
            lat: Latitude in degrees
            lon: Longitude in degrees

        Returns:
            bool: True if coordinates are within Taiwan's rough boundary rectangle
        """
        # Taiwan's approximate boundary rectangle
        # North: 25.3°, South: 21.9°, East: 122.0°, West: 119.3°
        return 21.9 <= lat <= 25.3 and 119.3 <= lon <= 122.0

    @staticmethod
    def find_nearest_location(session: Session, lat: float, lon: float) -> Location | None:
        """
        Find the nearest location to given GPS coordinates.

        Uses double validation:
        1. Boundary rectangle check for Taiwan
        2. Distance threshold check (50km) to exclude overseas locations

        Args:
            session: Database session
            lat: Latitude in degrees
            lon: Longitude in degrees

        Returns:
            Location | None: Nearest location if within Taiwan, None otherwise
        """
        # First validation: boundary rectangle check
        if not LocationService._is_in_taiwan_bounds(lat, lon):
            logger.info(f"Coordinates ({lat}, {lon}) outside Taiwan boundary rectangle")
            return None

        # Get all locations with coordinates
        locations = (
            session.query(Location)
            .filter(Location.latitude.isnot(None), Location.longitude.isnot(None))
            .all()
        )

        if not locations:
            logger.warning("No locations with coordinates found in database")
            return None

        # Calculate distances to all locations
        min_distance = float("inf")
        nearest_location = None

        for location in locations:
            # No need to check for None since SQL filter already excludes them
            # Type assertion: we know latitude and longitude are not None due to SQL filter
            latitude = float(location.latitude)  # type: ignore[arg-type]
            longitude = float(location.longitude)  # type: ignore[arg-type]

            distance = LocationService._calculate_haversine_distance(lat, lon, latitude, longitude)

            if distance < min_distance:
                min_distance = distance
                nearest_location = location

        # Second validation: distance threshold check (50km)
        if nearest_location is None or min_distance > 50.0:
            logger.info(
                f"Nearest location is {min_distance:.1f}km away, outside Taiwan service area"
            )
            return None

        logger.info(
            f"Found nearest location: {nearest_location.full_name} ({min_distance:.1f}km away)"
        )
        return nearest_location


class WeatherService:
    """Service for handling weather queries with different location sources."""

    @staticmethod
    def handle_text_weather_query(session: Session, text_input: str) -> str:
        """
        Handle weather query from text input.

        Args:
            session: Database session
            text_input: User text input

        Returns:
            str: Weather response message

        Raises:
            LocationParseError: If input format is invalid
        """
        # Use existing location parsing logic
        locations, response_message = LocationService.parse_location_input(session, text_input)
        return response_message

    @staticmethod
    def handle_location_weather_query(session: Session, lat: float, lon: float) -> str:
        """
        Handle weather query from GPS coordinates.

        Args:
            session: Database session
            lat: Latitude in degrees
            lon: Longitude in degrees

        Returns:
            str: Weather response message
        """
        # Find nearest location
        location = LocationService.find_nearest_location(session, lat, lon)

        if location is None:
            return "抱歉，目前僅支援台灣地區的天氣查詢 🌏"

        # Use the same logic as text input for single location
        return f"找到了 {location.full_name}，正在查詢天氣..."
