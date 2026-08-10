"""Test cases for location service functionality."""

from collections.abc import Callable
from unittest.mock import patch

import pytest
from sqlalchemy.orm import Session

from app.weather.models import Location, Weather
from app.weather.service import (
    LocationParseError,
    LocationService,
    WeatherQueryResult,
    WeatherService,
)


class TestLocationService:
    """Test cases for LocationService class."""

    def test_validate_location_input_valid(self) -> None:
        """Test valid location input validation."""
        # Test valid inputs
        assert LocationService.validate_location_input("永和區") == "永和區"
        assert LocationService.validate_location_input("信義區") == "信義區"
        assert LocationService.validate_location_input("魚池鄉") == "魚池鄉"
        assert LocationService.validate_location_input(" 中山區 ") == "中山區"  # Whitespace removal
        assert LocationService.validate_location_input("台東縣太麻里鄉") == "臺東縣太麻里鄉"

        # Test "台" to "臺" conversion
        assert LocationService.validate_location_input("台北") == "臺北"
        assert LocationService.validate_location_input("台中") == "臺中"
        assert LocationService.validate_location_input("台南") == "臺南"

    def test_validate_location_input_invalid_length(self) -> None:
        """Test location input validation with invalid length."""
        # Test too short (1 character)
        with pytest.raises(LocationParseError) as exc_info:
            LocationService.validate_location_input("區")
        assert "輸入的字數不對" in exc_info.value.message

        # Test too long (8+ characters)
        with pytest.raises(LocationParseError) as exc_info:
            LocationService.validate_location_input("新北市永和區中正路")
        assert "輸入的字數不對" in exc_info.value.message

    def test_validate_location_input_empty(self) -> None:
        """Test location input validation with empty input."""
        with pytest.raises(LocationParseError) as exc_info:
            LocationService.validate_location_input("")
        assert "輸入不能為空" in exc_info.value.message

        with pytest.raises(LocationParseError) as exc_info:
            LocationService.validate_location_input("   ")
        assert "輸入不能為空" in exc_info.value.message

    def test_validate_location_input_non_chinese(self) -> None:
        """Test location input validation with non-Chinese characters."""
        with pytest.raises(LocationParseError) as exc_info:
            LocationService.validate_location_input("abc")
        assert "請輸入中文地名" in exc_info.value.message

        with pytest.raises(LocationParseError) as exc_info:
            LocationService.validate_location_input("永和123")
        assert "請輸入中文地名" in exc_info.value.message

    def test_search_locations_by_name(
        self, session: Session, create_location: Callable[..., Location]
    ) -> None:
        """Test location search by name functionality."""
        # Create test locations
        create_location(
            geocode="6500100001", county="新北市", district="永和區", full_name="新北市永和區"
        )
        create_location(
            geocode="1000800001", county="臺北市", district="信義區", full_name="臺北市信義區"
        )
        create_location(
            geocode="1001000001", county="基隆市", district="信義區", full_name="基隆市信義區"
        )

        # Test exact district name match
        results = LocationService.search_locations_by_name(session, "永和區")
        assert len(results) == 1

        assert results[0].full_name == "新北市永和區"

        # Test partial district name match
        results = LocationService.search_locations_by_name(session, "永和")
        assert len(results) == 1

        assert results[0].full_name == "新北市永和區"

        # Test multiple matches
        results = LocationService.search_locations_by_name(session, "信義區")
        assert len(results) == 2
        full_names = [r.full_name for r in results]
        assert "臺北市信義區" in full_names
        assert "基隆市信義區" in full_names

        # Test no matches
        results = LocationService.search_locations_by_name(session, "不存在區")
        assert len(results) == 0

    def test_parse_location_input_single_match(
        self, session: Session, create_location: Callable[..., Location]
    ) -> None:
        """Test location input parsing with single match."""
        create_location(
            geocode="6500100002", county="新北市", district="永和區", full_name="新北市永和區"
        )

        (
            locations,
            response,
        ) = LocationService.parse_location_input(session, "永和區")

        assert len(locations) == 1
        assert locations[0].full_name == "新北市永和區"
        assert "找到了 新北市永和區" in response

        assert "正在查詢天氣" in response

    def test_parse_location_input_multiple_matches(
        self, session: Session, create_location: Callable[..., Location]
    ) -> None:
        """Test location input parsing with multiple matches (2-3)."""
        create_location(
            geocode="1000800002", county="臺北市", district="信義區", full_name="臺北市信義區"
        )
        create_location(
            geocode="1001000002", county="基隆市", district="信義區", full_name="基隆市信義區"
        )

        (
            locations,
            response,
        ) = LocationService.parse_location_input(session, "信義區")

        assert len(locations) == 2
        full_names = [loc.full_name for loc in locations]
        assert "臺北市信義區" in full_names
        assert "基隆市信義區" in full_names
        assert "找到多個符合的地點" in response

    def test_parse_location_input_no_matches(self, session: Session) -> None:
        """Test location input parsing with no matches."""
        (
            locations,
            response,
        ) = LocationService.parse_location_input(session, "不存在區")

        assert len(locations) == 0
        assert "找不到「不存在區」這個地點" in response
        assert "建議輸入二級行政區名稱" in response

    def test_parse_location_input_too_many_matches(
        self, session: Session, create_location: Callable[..., Location]
    ) -> None:
        """Test location input parsing with too many matches (>3)."""
        # Create 4+ locations with "中正" in the name
        districts = ["中正區", "中正里", "中正鄉", "中正市"]
        for i, district in enumerate(districts):
            create_location(
                geocode=f"100010000{i}",
                county="測試縣",
                district=district,
                full_name=f"測試縣{district}",
            )

        (
            locations,
            response,
        ) = LocationService.parse_location_input(session, "中正")

        assert len(locations) == 0  # Should return empty when too many matches
        assert "找到太多符合的地點" in response

        assert "更具體的地名" in response

    def test_parse_location_input_invalid_format(self, session: Session) -> None:
        """Test location input parsing with invalid format."""
        with pytest.raises(LocationParseError) as exc_info:
            LocationService.parse_location_input(session, "區")  # Too short
        assert "輸入的字數不對" in exc_info.value.message

        with pytest.raises(LocationParseError) as exc_info:
            LocationService.parse_location_input(session, "abc")  # Non-Chinese
        assert "請輸入中文地名" in exc_info.value.message

    def test_parse_location_input_taiwan_character_conversion(
        self, session: Session, create_location: Callable[..., Location]
    ) -> None:
        """Test location input parsing with Taiwan character conversion (台→臺)."""
        # Create location with official "臺" character
        create_location(
            geocode="6300000001", county="臺北市", district="中正區", full_name="臺北市中正區"
        )
        create_location(
            geocode="6600000001", county="臺中市", district="西區", full_name="臺中市西區"
        )

        # Test user input with common "台" character should find results
        (
            locations,
            response,
        ) = LocationService.parse_location_input(session, "台北")
        assert len(locations) == 1
        assert locations[0].full_name == "臺北市中正區"
        assert "找到了 臺北市中正區" in response

        # Test partial match with converted character
        (
            locations,
            response,
        ) = LocationService.parse_location_input(session, "台中")
        assert len(locations) == 1
        assert locations[0].full_name == "臺中市西區"
        assert "找到了 臺中市西區" in response


class TestLocationServiceGeographic:
    """Test geographic functionality of LocationService."""

    def test_haversine_distance_calculation(self) -> None:
        """Test Haversine distance calculation."""
        # Test distance between Taipei and Taichung (approximately 135 km)
        taipei_lat, taipei_lon = 25.0330, 121.5654
        taichung_lat, taichung_lon = 24.1477, 120.6736

        distance = LocationService._calculate_haversine_distance(
            taipei_lat, taipei_lon, taichung_lat, taichung_lon
        )

        # Should be approximately 135 km (±10 km tolerance)
        assert 125 <= distance <= 145

    def test_haversine_distance_same_point(self) -> None:
        """Test Haversine distance for same point."""
        lat, lon = 25.0330, 121.5654

        distance = LocationService._calculate_haversine_distance(lat, lon, lat, lon)

        # Distance should be very close to 0 (within floating point precision)
        assert distance < 1e-10

    def test_is_in_taiwan_bounds_valid_coordinates(self) -> None:
        """Test Taiwan bounds check for valid coordinates."""
        # Taipei
        assert LocationService._is_in_taiwan_bounds(25.0330, 121.5654) is True
        # Kaohsiung
        assert LocationService._is_in_taiwan_bounds(22.6273, 120.3014) is True
        # Taitung
        assert LocationService._is_in_taiwan_bounds(22.7569, 121.1444) is True

    def test_is_in_taiwan_bounds_invalid_coordinates(self) -> None:
        """Test Taiwan bounds check for invalid coordinates."""
        # Tokyo, Japan
        assert LocationService._is_in_taiwan_bounds(35.6762, 139.6503) is False
        # Manila, Philippines
        assert LocationService._is_in_taiwan_bounds(14.5995, 120.9842) is False
        # Hong Kong
        assert LocationService._is_in_taiwan_bounds(22.3193, 114.1694) is False

    def test_is_in_taiwan_bounds_outlying_islands(self) -> None:
        """Test Taiwan bounds check includes outlying islands (Kinmen and Matsu)."""
        # Kinmen coordinates (should now be included)
        assert LocationService._is_in_taiwan_bounds(24.4315, 118.3175) is True
        # Matsu coordinates (should now be included)
        assert LocationService._is_in_taiwan_bounds(26.2, 119.9) is True
        # Penghu (should still be included)
        assert LocationService._is_in_taiwan_bounds(23.6, 119.6) is True

    def test_find_nearest_location_success(self, session: Session) -> None:
        """Test finding nearest location within Taiwan."""
        # Create test locations
        location1 = Location(
            geocode="6300100",
            county="臺北市",
            district="中正區",
            full_name="臺北市中正區",
            latitude=25.0330,
            longitude=121.5654,
        )
        location2 = Location(
            geocode="6600100",
            county="臺中市",
            district="西區",
            full_name="臺中市西區",
            latitude=24.1477,
            longitude=120.6736,
        )

        session.add_all([location1, location2])
        session.commit()

        # Test coordinates near Taipei (should find Taipei location)
        result = LocationService.find_nearest_location(session, 25.0340, 121.5660)

        assert result is not None
        assert result.full_name == "臺北市中正區"

    def test_find_nearest_location_outside_bounds(self, session: Session) -> None:
        """Test finding nearest location outside Taiwan bounds."""
        # Tokyo coordinates - outside Taiwan bounds
        result = LocationService.find_nearest_location(session, 35.6762, 139.6503)

        assert result is None

    def test_find_nearest_location_too_far(self, session: Session) -> None:
        """Test finding nearest location when distance exceeds threshold."""
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

        # Test coordinates within bounds but far from any location (simulated ocean)
        result = LocationService.find_nearest_location(session, 23.0, 119.5)

        assert result is None

    def test_find_nearest_location_no_locations(self, session: Session) -> None:
        """Test finding nearest location when no locations in database."""
        result = LocationService.find_nearest_location(session, 25.0330, 121.5654)

        assert result is None


class TestWeatherService:
    """Test WeatherService functionality."""

    def test_weather_query_result_multiple_locations_has_no_selection(self) -> None:
        """Keep multiple candidate Locations distinct from a selected Location."""
        first_location = Location(id=1, full_name="臺北市中正區")
        second_location = Location(id=2, full_name="臺南市中西區")

        query_result = WeatherQueryResult(
            response_message="找到多個符合的地點，請選擇：",
            locations=(first_location, second_location),
        )

        assert query_result.selected_location is None

    def test_handle_location_weather_query_success(
        self,
        session: Session,
        create_location: Callable[..., Location],
        add_test_weather_data: Callable[[Session, int], list[Weather]],
    ) -> None:
        """Test successful location weather query with actual weather data."""
        # Create a test location
        location = create_location(
            geocode="6300100",
            county="臺北市",
            district="中正區",
            full_name="臺北市中正區",
            latitude=25.0330,
            longitude=121.5654,
        )

        # Add test weather data using shared fixture
        add_test_weather_data(session, location.id)

        query_result = WeatherService.handle_location_weather_query(session, 25.0340, 121.5660)

        # Should return formatted weather data and the same selected location.
        assert "🗺️ 臺北市中正區" in query_result.response_message
        assert "⛅" in query_result.response_message
        assert "🌡️" in query_result.response_message
        assert query_result.selected_location is not None
        assert query_result.selected_location.id == location.id

    def test_handle_location_weather_query_outside_taiwan(self, session: Session) -> None:
        """Test location weather query outside Taiwan."""
        query_result = WeatherService.handle_location_weather_query(session, 35.6762, 139.6503)

        assert query_result.response_message == "抱歉，目前僅支援台灣地區的天氣查詢 🌏"
        assert query_result.selected_location is None

    def test_handle_text_weather_query_success(
        self,
        session: Session,
        create_location: Callable[..., Location],
        add_test_weather_data: Callable[[Session, int], list[Weather]],
    ) -> None:
        """Test successful text weather query with actual weather data."""
        # Create test locations
        location = create_location(
            geocode="6300100",
            county="臺北市",
            district="中正區",
            full_name="臺北市中正區",
            latitude=25.0330,
            longitude=121.5654,
        )

        # Add test weather data using shared fixture
        add_test_weather_data(session, location.id)

        with patch.object(
            LocationService,
            "parse_location_input",
            wraps=LocationService.parse_location_input,
        ) as mock_parse_location:
            query_result = WeatherService.handle_text_weather_query(session, "臺北")

        mock_parse_location.assert_called_once_with(session, "臺北")

        # Should return formatted weather data and the same selected location.
        assert "🗺️ 臺北市中正區" in query_result.response_message
        assert "⛅" in query_result.response_message
        assert "🌡️" in query_result.response_message
        assert query_result.selected_location is not None
        assert query_result.selected_location.id == location.id

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

    def test_weather_data_freshness_error_message(
        self,
        session: Session,
        create_freshness_test_location: Callable[[Session], Location],
        create_weather_data_with_fetchtime: Callable[..., list[Weather]],
    ) -> None:
        """Test error message when weather data is stale."""
        from datetime import UTC, datetime, timedelta

        # Create test location
        location = create_freshness_test_location(session)

        # Create stale weather data (8 hours ago fetched_at, but future time periods)
        fetched_at = datetime.now(UTC) - timedelta(hours=8)
        create_weather_data_with_fetchtime(
            session, location.id, fetched_at, use_current_time_for_periods=True
        )

        # Query weather through text handler
        query_result = WeatherService.handle_text_weather_query(session, "臺北市中正區")

        # Should preserve the selected Location even when weather data is unavailable.
        assert (
            query_result.response_message
            == "抱歉，目前無法取得 臺北市中正區 的天氣資料，請稍後再試。"
        )
        assert query_result.selected_location is not None
        assert query_result.selected_location.id == location.id


class TestLocationServiceAddressParsing:
    """Test address parsing functionality of LocationService."""

    def test_extract_location_from_address_basic(
        self, session: Session, create_location: Callable[..., Location]
    ) -> None:
        """Test basic address extraction for direct municipalities."""
        # Create test locations
        create_location(
            geocode="6300000001", county="臺北市", district="信義區", full_name="臺北市信義區"
        )
        create_location(
            geocode="6500000001", county="新北市", district="永和區", full_name="新北市永和區"
        )

        # Test address extraction
        address = "台北市信義區信義路五段7號"
        result = LocationService.extract_location_from_address(session, address)
        assert result is not None
        assert result.full_name == "臺北市信義區"

        # Test different format
        address = "新北市永和區中正路123號"
        result = LocationService.extract_location_from_address(session, address)
        assert result is not None
        assert result.full_name == "新北市永和區"

    def test_extract_location_from_address_county_format(
        self, session: Session, create_location: Callable[..., Location]
    ) -> None:
        """Test address extraction for county + town/city format."""
        # Create test locations
        create_location(
            geocode="1000700001", county="新竹縣", district="竹北市", full_name="新竹縣竹北市"
        )
        create_location(
            geocode="1000800001", county="南投縣", district="魚池鄉", full_name="南投縣魚池鄉"
        )

        # Test county + city format
        address = "新竹縣竹北市縣政九路146號"
        result = LocationService.extract_location_from_address(session, address)
        assert result is not None
        assert result.full_name == "新竹縣竹北市"

        # Test county + township format
        address = "南投縣魚池鄉水社村中山路123號"
        result = LocationService.extract_location_from_address(session, address)
        assert result is not None
        assert result.full_name == "南投縣魚池鄉"

    def test_extract_location_from_address_taiwan_character_normalization(
        self, session: Session, create_location: Callable[..., Location]
    ) -> None:
        """Test Taiwan character normalization in address parsing."""
        # Create test locations with official "臺" character
        create_location(
            geocode="6600000001", county="臺中市", district="西區", full_name="臺中市西區"
        )
        create_location(
            geocode="6700000001", county="臺南市", district="中西區", full_name="臺南市中西區"
        )

        # Test address with common "台" character should find results
        address = "台中市西區台灣大道二段123號"
        result = LocationService.extract_location_from_address(session, address)
        assert result is not None
        assert result.full_name == "臺中市西區"

        # Test address with official "臺" character
        address = "臺南市中西區民權路456號"
        result = LocationService.extract_location_from_address(session, address)
        assert result is not None
        assert result.full_name == "臺南市中西區"

    def test_extract_location_from_address_no_match(self, session: Session) -> None:
        """Test address extraction when no administrative area can be extracted."""
        # Test invalid/incomplete address
        result = LocationService.extract_location_from_address(session, "信義路五段7號")
        assert result is None

        # Test non-Taiwan address
        result = LocationService.extract_location_from_address(session, "東京都新宿區西新宿123號")
        assert result is None

        # Test empty address
        result = LocationService.extract_location_from_address(session, "")
        assert result is None


class TestWeatherServiceAddressIntegration:
    """Test WeatherService with address verification integration."""

    def test_handle_location_weather_query_with_address_verification(
        self,
        session: Session,
        create_location: Callable[..., Location],
        add_test_weather_data: Callable[[Session, int], list[Weather]],
    ) -> None:
        """Test location weather query with GPS and address verification."""
        # Create test location
        location = create_location(
            geocode="6300100",
            county="臺北市",
            district="信義區",
            full_name="臺北市信義區",
            latitude=25.0330,
            longitude=121.5654,
        )

        # Add test weather data using shared fixture
        add_test_weather_data(session, location.id)

        # Address success must not perform the GPS fallback.
        with (
            patch.object(
                LocationService,
                "extract_location_from_address",
                wraps=LocationService.extract_location_from_address,
            ) as mock_extract_location,
            patch.object(
                LocationService,
                "find_nearest_location",
                wraps=LocationService.find_nearest_location,
            ) as mock_find_location,
        ):
            query_result = WeatherService.handle_location_weather_query(
                session, 25.0340, 121.5660, "台北市信義區信義路五段7號"
            )

        mock_extract_location.assert_called_once_with(session, "台北市信義區信義路五段7號")
        mock_find_location.assert_not_called()

        # Should return formatted weather data and the address-selected Location.
        assert "🗺️ 臺北市信義區" in query_result.response_message
        assert "⛅" in query_result.response_message
        assert "🌡️" in query_result.response_message
        assert query_result.selected_location is not None
        assert query_result.selected_location.id == location.id

    def test_handle_location_weather_query_address_overrides_gps(
        self,
        session: Session,
        create_location: Callable[..., Location],
        add_test_weather_data: Callable[[Session, int], list[Weather]],
    ) -> None:
        """Test that address takes priority when GPS and address conflict."""
        # Create test locations
        _ = create_location(
            geocode="6300100",
            county="臺北市",
            district="信義區",
            full_name="臺北市信義區",
            latitude=25.0330,
            longitude=121.5654,
        )
        location2 = create_location(
            geocode="6500100",
            county="新北市",
            district="永和區",
            full_name="新北市永和區",
            latitude=25.0100,
            longitude=121.5150,
        )

        # Add test weather data for location2 (永和區) using shared fixture
        add_test_weather_data(session, location2.id)

        # GPS points to 信義區 but address says 永和區 - should use address
        query_result = WeatherService.handle_location_weather_query(
            session, 25.0340, 121.5660, "新北市永和區中正路123號"
        )

        # Should return formatted weather data for 永和區.
        assert "🗺️ 新北市永和區" in query_result.response_message
        assert "⛅" in query_result.response_message
        assert "🌡️" in query_result.response_message
        assert query_result.selected_location is not None
        assert query_result.selected_location.id == location2.id

    def test_handle_location_weather_query_gps_outside_address_inside(
        self,
        session: Session,
        create_location: Callable[..., Location],
        add_test_weather_data: Callable[[Session, int], list[Weather]],
    ) -> None:
        """Test GPS outside Taiwan but address indicates Taiwan location."""
        # Create test location
        location = create_location(
            geocode="6300100",
            county="臺北市",
            district="信義區",
            full_name="臺北市信義區",
            latitude=25.0330,
            longitude=121.5654,
        )

        # Add test weather data using shared fixture
        add_test_weather_data(session, location.id)

        # GPS outside Taiwan bounds but address is Taiwan - should use address
        query_result = WeatherService.handle_location_weather_query(
            session, 35.6762, 139.6503, "台北市信義區信義路五段7號"
        )

        # Should return formatted weather data from the address-selected Location.
        assert "🗺️ 臺北市信義區" in query_result.response_message
        assert "⛅" in query_result.response_message
        assert "🌡️" in query_result.response_message
        assert query_result.selected_location is not None
        assert query_result.selected_location.id == location.id

    def test_handle_location_weather_query_both_outside_taiwan(self, session: Session) -> None:
        """Test both GPS and address outside Taiwan."""
        # Address failure must perform exactly one GPS fallback.
        with (
            patch.object(
                LocationService,
                "extract_location_from_address",
                wraps=LocationService.extract_location_from_address,
            ) as mock_extract_location,
            patch.object(
                LocationService,
                "find_nearest_location",
                wraps=LocationService.find_nearest_location,
            ) as mock_find_location,
        ):
            query_result = WeatherService.handle_location_weather_query(
                session, 35.6762, 139.6503, "東京都新宿區西新宿123號"
            )

        mock_extract_location.assert_called_once_with(session, "東京都新宿區西新宿123號")
        mock_find_location.assert_called_once_with(session, 35.6762, 139.6503)
        assert query_result.response_message == "抱歉，目前僅支援台灣地區的天氣查詢 🌏"
        assert query_result.selected_location is None

    def test_extract_location_invalid_division(self, session: Session) -> None:
        """Test extract location with invalid administrative division."""
        # Invalid administrative division (not in valid Taiwan divisions)
        result = LocationService.extract_location_from_address(session, "火星市外星區123號")
        assert result is None

    def test_extract_location_not_in_database(self, session: Session) -> None:
        """Test extract location not found in database."""
        # Mock a valid division that doesn't exist in database
        with patch("app.weather.service.is_valid_taiwan_division", return_value=True):
            result = LocationService.extract_location_from_address(session, "臺北市不存在區123號")
            assert result is None
