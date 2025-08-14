"""Service layer for weather and location operations."""

import logging
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
            raise LocationParseError("🤔 輸入的字數不對喔！請輸入 2 到 6 個字的地名。", text)

        # Check if input contains only Chinese characters (and some common district suffixes)
        if not re.match(r"^[\u4e00-\u9fff]+$", cleaned_text):
            raise LocationParseError("請輸入中文地名。", text)

        return cleaned_text

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
                - locations: List of matching Location objects
                - response_message: Response message for user

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
            return locations, response

        elif result_count == 1:
            # Single match - will proceed to weather query
            location = locations[0]
            response = f"找到了 {location.full_name}，正在查詢天氣..."
            return locations, response

        elif 2 <= result_count <= 3:
            # Multiple matches - provide options
            options = "\n".join([f"👉 {loc.full_name}" for loc in locations])
            response = f"😕 找到多個符合的地點，請選擇：\n{options}"
            return locations, response

        else:
            # Too many matches
            response = (
                f"🤔 找到太多符合的地點了！請輸入更具體的地名，例如：\n"
                f"「{cleaned_input}區」而不是「{cleaned_input}」"
            )
            return [], response
