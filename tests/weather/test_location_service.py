"""Test cases for location service functionality."""

from collections.abc import Callable

import pytest
from sqlalchemy.orm import Session

from app.weather.models import Location
from app.weather.service import LocationParseError, LocationService, WeatherService


class TestLocationService:
    """Test cases for LocationService class."""

    def test_validate_location_input_valid(self) -> None:
        """Test valid location input validation."""
        # Test valid inputs
        assert LocationService.validate_location_input("永和區") == "永和區"
        assert LocationService.validate_location_input("信義區") == "信義區"
        assert LocationService.validate_location_input("魚池鄉") == "魚池鄉"
        assert LocationService.validate_location_input(" 中山區 ") == "中山區"  # Whitespace removal

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

        # Test too long (7+ characters)
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

        assert "檢查看看有沒有打錯字" in response

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

        # Distance should be 0
        assert distance == 0.0

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

    def test_handle_location_weather_query_success(self, session: Session) -> None:
        """Test successful location weather query."""
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

        result = WeatherService.handle_location_weather_query(session, 25.0340, 121.5660)

        assert result == "找到了 臺北市中正區，正在查詢天氣..."

    def test_handle_location_weather_query_outside_taiwan(self, session: Session) -> None:
        """Test location weather query outside Taiwan."""
        result = WeatherService.handle_location_weather_query(session, 35.6762, 139.6503)

        assert result == "抱歉，目前僅支援台灣地區的天氣查詢 🌏"

    def test_handle_text_weather_query_success(self, session: Session) -> None:
        """Test successful text weather query."""
        # Create test locations
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

        result = WeatherService.handle_text_weather_query(session, "臺北")

        assert "找到了 臺北市中正區" in result
