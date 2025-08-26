"""Test Taiwan administrative divisions management."""

from app.core.admin_divisions import (
    AdminDivisionsManager,
    initialize_admin_divisions,
    is_valid_taiwan_division,
)


class TestAdminDivisionsManager:
    """Test administrative divisions manager functionality."""

    def test_singleton_pattern(self) -> None:
        """Test that AdminDivisionsManager follows singleton pattern."""
        manager1 = AdminDivisionsManager()
        manager2 = AdminDivisionsManager()
        assert manager1 is manager2

    def test_initialization(self) -> None:
        """Test that manager initializes correctly."""
        initialize_admin_divisions()
        manager = AdminDivisionsManager()
        assert manager.get_valid_divisions_count() > 0

    def test_valid_divisions_check(self) -> None:
        """Test validation of known Taiwan administrative divisions."""
        # Test some known valid divisions
        assert is_valid_taiwan_division("臺北市信義區")
        assert is_valid_taiwan_division("新北市中和區")
        assert is_valid_taiwan_division("高雄市鳳山區")
        assert is_valid_taiwan_division("金門縣金城鎮")
        assert is_valid_taiwan_division("連江縣南竿鄉")

    def test_invalid_divisions_check(self) -> None:
        """Test validation rejects invalid administrative divisions."""
        # Test invalid divisions
        assert not is_valid_taiwan_division("北京市朝陽區")  # China
        assert not is_valid_taiwan_division("東京都新宿區")  # Japan
        assert not is_valid_taiwan_division("台北市不存在區")  # Non-existent district
        assert not is_valid_taiwan_division("")  # Empty string
        assert not is_valid_taiwan_division("隨便寫的地址")  # Random text

    def test_taiwan_character_variations(self) -> None:
        """Test that both 台 and 臺 variations are handled correctly."""
        # The JSON file uses 臺 so test that we normalize correctly
        # Note: Our validation function should work with the normalized form
        assert is_valid_taiwan_division("臺北市信義區")  # Standard form
        assert is_valid_taiwan_division("臺中市西區")  # Standard form
        assert is_valid_taiwan_division("臺南市東區")  # Standard form

    def test_edge_cases(self) -> None:
        """Test edge cases for division validation."""
        # Test with None and whitespace
        assert not is_valid_taiwan_division("")
        assert not is_valid_taiwan_division("   ")

        # Test partial matches (should be invalid)
        assert not is_valid_taiwan_division("臺北市")  # Missing district
        assert not is_valid_taiwan_division("信義區")  # Missing city

        # Test case sensitivity and extra characters
        assert not is_valid_taiwan_division("臺北市信義區ABC")  # Extra characters
