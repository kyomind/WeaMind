"""Test cases for location service functionality."""

from collections.abc import Callable

import pytest
from sqlalchemy.orm import Session

from app.weather.models import Location
from app.weather.service import LocationParseError, LocationService


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

        locations, response = LocationService.parse_location_input(session, "永和區")

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

        locations, response = LocationService.parse_location_input(session, "信義區")

        assert len(locations) == 2
        full_names = [loc.full_name for loc in locations]
        assert "臺北市信義區" in full_names
        assert "基隆市信義區" in full_names
        assert "找到多個符合的地點" in response
        assert "👉 臺北市信義區" in response
        assert "👉 基隆市信義區" in response

    def test_parse_location_input_no_matches(self, session: Session) -> None:
        """Test location input parsing with no matches."""
        locations, response = LocationService.parse_location_input(session, "不存在區")

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

        locations, response = LocationService.parse_location_input(session, "中正")

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
        locations, response = LocationService.parse_location_input(session, "台北")
        assert len(locations) == 1
        assert locations[0].full_name == "臺北市中正區"
        assert "找到了 臺北市中正區" in response

        # Test partial match with converted character
        locations, response = LocationService.parse_location_input(session, "台中")
        assert len(locations) == 1
        assert locations[0].full_name == "臺中市西區"
        assert "找到了 臺中市西區" in response
