"""Service layer for weather and location operations."""

import logging
import math
import re
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta, timezone

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.admin_divisions import is_valid_taiwan_division
from app.weather.models import Location, Weather

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class WeatherQueryResult:
    """
    Represent the response and resolved Locations for a Weather Query.

    The same resolved Locations drive the weather response, Quick Reply, and
    Query History so callers never need to repeat Location resolution.

    Attributes:
        response_message: User-facing weather or location-selection message.
        locations: Zero to three resolved candidate Locations.
    """

    response_message: str
    locations: tuple[Location, ...]

    @property
    def selected_location(self) -> Location | None:
        """Return the single resolved Location, if the query selected one."""
        if len(self.locations) == 1:
            return self.locations[0]
        return None


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

        # Check character count (2-7 Chinese characters)
        char_count = len(cleaned_text)
        if char_count < 2 or char_count > 7:
            raise LocationParseError("🤔 輸入的字數不對喔！請輸入 2 到 7 個字的地名", text)

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
            response = (
                f"找不到「{cleaned_input}」這個地點耶🙈，建議輸入二級行政區名稱，"
                f"比如「中壢」、「水上」或「信義區、魚池鄉」"
            )
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
            response = "找到多個符合的地點，請選擇："
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
        # Taiwan's approximate boundary rectangle (including outlying islands)
        # North: 26.5° (Matsu), South: 21.9°, East: 122.0°, West: 118.0° (Kinmen)
        return 21.9 <= lat <= 26.5 and 118.0 <= lon <= 122.0

    @staticmethod
    def find_nearest_location(session: Session, lat: float, lon: float) -> Location | None:
        """
        Find the nearest location to given GPS coordinates.

        Uses double validation:
        1. Boundary rectangle check for Taiwan
        2. Distance threshold check (15km) to exclude distant locations

        Args:
            session: Database session
            lat: Latitude in degrees
            lon: Longitude in degrees

        Returns:
            Location | None: Nearest location if within Taiwan, None otherwise
        """
        # First validation: boundary rectangle check
        if not LocationService._is_in_taiwan_bounds(lat, lon):
            logger.warning("Coordinates outside Taiwan boundary rectangle")
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

        # Second validation: distance threshold check (15km)
        if nearest_location is None or min_distance > 15.0:
            logger.info(
                f"Nearest location is {min_distance:.1f}km away, outside Taiwan service area"
            )
            return None

        logger.info(
            f"Found nearest location: {nearest_location.full_name} ({min_distance:.1f}km away)"
        )
        return nearest_location

    @staticmethod
    def extract_location_from_address(session: Session, address: str) -> Location | None:
        """
        Extract Taiwan administrative area from address string with validation.

        Uses strategy B: extract admin area first, then normalize Taiwan characters,
        and validate against known administrative divisions.

        Args:
            session: Database session
            address: Address string from LINE location sharing

        Returns:
            Location | None: Matching location if found in Taiwan, None otherwise
        """
        if not address or not address.strip():
            return None

        # Step 1: Extract administrative area using regex patterns
        # Taiwan address patterns: County + District format
        patterns = [
            # Direct municipality + district: 台北市信義區, 新北市永和區 etc.
            r"(台北市|臺北市|新北市|桃園市|台中市|臺中市|台南市|臺南市|高雄市)([\u4e00-\u9fff]{1,3}區)",
            # County + town/city/district: 新竹縣竹北市, 南投縣魚池鄉 etc.
            r"([\u4e00-\u9fff]{2,3}縣)([\u4e00-\u9fff]{1,3}[鄉鎮市區])",
            # Provincial city + district: 基隆市中正區, 新竹市東區, 嘉義市西區 etc.
            r"(基隆市|新竹市|嘉義市)([\u4e00-\u9fff]{1,3}區)",
        ]

        admin_area = None
        for pattern in patterns:
            match = re.search(pattern, address)
            if match:
                admin_area = match.group(0)  # Full match like "台北市信義區"
                break

        if not admin_area:
            logger.warning("Could not extract administrative area from address")
            return None

        # Step 2: Normalize Taiwan characters (台 → 臺) for admin area only
        normalized_admin = admin_area.replace("台", "臺")

        logger.info(f"Extracted admin area: '{admin_area}' → normalized: '{normalized_admin}'")

        # Step 3: Validate against known administrative divisions
        if not is_valid_taiwan_division(normalized_admin):
            logger.warning(f"Administrative area not in valid divisions: {normalized_admin}")
            return None

        # Step 4: Search in database using exact match
        location = session.query(Location).filter(Location.full_name == normalized_admin).first()

        if location:
            logger.info(f"Found location in database: {location.full_name}")
            return location
        else:
            logger.warning(f"Administrative area not found in database: {normalized_admin}")
            return None


class WeatherService:
    """Service for handling weather queries with different location sources."""

    @staticmethod
    def get_weather_forecast_by_location(session: Session, location_id: int) -> list[Weather]:
        """
        Get weather forecast using sliding window logic to ensure consistent 24-hour forecast.

        This function implements the sliding window strategy to guarantee users always see
        a complete 24-hour (8 time periods) forecast, regardless of query time.

        Args:
            session: Database session
            location_id: ID of the location to query weather for

        Returns:
            list[Weather]: List of 8 Weather objects representing 24-hour forecast,
                          ordered by start_time. Empty list if no data found.
        """
        try:
            # Get the latest fetched_at timestamp for this location (within freshness window)
            # Use explicit UTC time to ensure consistency with stored data
            utc_now = datetime.now(UTC)
            freshness_threshold = utc_now - timedelta(hours=6.5)

            latest_fetched_subquery = (
                session.query(func.max(Weather.fetched_at))
                .filter(
                    Weather.location_id == location_id, Weather.fetched_at >= freshness_threshold
                )
                .scalar_subquery()
            )

            # Sliding window query as defined in weather-query-logic.md
            # Use database-agnostic approach: get all recent data and filter in Python if needed
            weather_data = (
                session.query(Weather)
                .filter(
                    Weather.location_id == location_id,
                    # Filter out expired time periods (sliding window key) - use same UTC time
                    Weather.end_time > utc_now,
                    # Get data from the latest batch (already filtered for freshness)
                    Weather.fetched_at == latest_fetched_subquery,
                )
                .order_by(Weather.start_time)
                .limit(8)
                .all()
            )

            logger.info(
                f"Retrieved {len(weather_data)} weather records for location_id={location_id}"
            )

        except Exception:
            logger.exception(f"Error retrieving weather forecast for location_id={location_id}")
            return []
        else:
            return weather_data

    @staticmethod
    def format_weather_response(location: Location, weather_data: list[Weather]) -> str:
        """
        Format weather forecast data into LINE Bot message according to PRD specifications.

        Args:
            location: Location object with name information
            weather_data: List of Weather objects (should be 8 items for 24 hours)

        Returns:
            str: Formatted weather message for LINE Bot
        """
        if not weather_data:
            return f"抱歉，目前無法取得 {location.full_name} 的天氣資料，請稍後再試。"

        lines = [f"🗺️ {location.full_name}", ""]

        # Show up to 8 time periods, split into 2 groups (4 + 4) with a blank line between
        display_data = weather_data[:8]

        for idx, weather in enumerate(display_data, start=1):
            # Convert UTC to Taiwan time (UTC+8)
            taiwan_tz = timezone(timedelta(hours=8))
            local_start = weather.start_time.replace(tzinfo=UTC).astimezone(taiwan_tz)
            local_end = weather.end_time.replace(tzinfo=UTC).astimezone(taiwan_tz)

            # Format time range
            start_hour = local_start.strftime("%H")
            end_hour = local_end.strftime("%H")
            time_range = f"{start_hour}-{end_hour}"

            # Format temperature - only show max temperature
            temp_str = f"{weather.max_temperature}°"

            # Format precipitation
            if weather.precipitation_probability is not None:
                precip_str = f"💧{weather.precipitation_probability}%"
            else:
                precip_str = "💧0%"

            # Combine line - new compact format
            emoji = weather.weather_emoji or "⛅"
            weather_line = f"{emoji} {time_range} 🌡️{temp_str}{precip_str}"
            lines.append(weather_line)

            # Insert a blank line after the first 4 items when there are more than 4
            if idx == 4 and len(display_data) > 4:
                lines.append("")

        # Add last updated timestamp
        if weather_data:
            taiwan_tz = timezone(timedelta(hours=8))
            last_updated = weather_data[0].fetched_at.replace(tzinfo=UTC).astimezone(taiwan_tz)
            update_time_str = last_updated.strftime("%m/%d %H:%M")
            lines.extend(["", f"{update_time_str} 更新"])

        return "\n".join(lines)

    @staticmethod
    def handle_text_weather_query(session: Session, text_input: str) -> WeatherQueryResult:
        """
        Handle a text Weather Query with one Location resolution pass.

        Args:
            session: Database session.
            text_input: User text input.

        Returns:
            Weather Query Result containing the response and candidate Locations.

        Raises:
            LocationParseError: If the input format is invalid.
        """
        locations, response_message = LocationService.parse_location_input(session, text_input)
        resolved_locations = tuple(locations)

        if len(resolved_locations) == 1:
            location = resolved_locations[0]
            weather_data = WeatherService.get_weather_forecast_by_location(session, location.id)
            if weather_data:
                response_message = WeatherService.format_weather_response(location, weather_data)
            else:
                response_message = (
                    f"抱歉，目前無法取得 {location.full_name} 的天氣資料，請稍後再試。"
                )

        return WeatherQueryResult(
            response_message=response_message,
            locations=resolved_locations,
        )

    @staticmethod
    def handle_location_weather_query(
        session: Session, lat: float, lon: float, address: str | None = None
    ) -> WeatherQueryResult:
        """
        Handle a GPS Weather Query with address priority and GPS fallback.

        Args:
            session: Database session.
            lat: Latitude in degrees.
            lon: Longitude in degrees.
            address: Optional address string from LINE location sharing.

        Returns:
            Weather Query Result containing the response and resolved Location.
        """
        location = None

        # Step 1: Address-first strategy (if available)
        if address:
            address_location = LocationService.extract_location_from_address(session, address)
            if address_location:
                # Address parsing succeeded - use it directly
                logger.info("Address parsing succeeded")
                location = address_location
            else:
                # Address parsing failed - log and continue to GPS fallback
                logger.warning("Address parsing failed, falling back to GPS")

        # Step 2: GPS fallback (if address failed or not available)
        if not location:
            gps_location = LocationService.find_nearest_location(session, lat, lon)
            if gps_location:
                logger.info(f"GPS calculation succeeded: {gps_location.full_name}")
                location = gps_location

        # Step 3: Get weather data if location found
        if location:
            weather_data = WeatherService.get_weather_forecast_by_location(session, location.id)
            if weather_data:
                response_message = WeatherService.format_weather_response(location, weather_data)
            else:
                response_message = (
                    f"抱歉，目前無法取得 {location.full_name} 的天氣資料，請稍後再試。"
                )
            return WeatherQueryResult(
                response_message=response_message,
                locations=(location,),
            )

        # Step 4: Both methods failed
        logger.warning("Both address parsing and GPS calculation failed")
        return WeatherQueryResult(
            response_message="抱歉，目前僅支援台灣地區的天氣查詢 🌏",
            locations=(),
        )
