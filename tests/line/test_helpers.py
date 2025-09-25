"""Test helper functions for LINE Bot service testing."""

from collections.abc import Generator
from contextlib import contextmanager
from unittest.mock import Mock, patch

from app.weather.models import Location


@contextmanager
def mock_database_session() -> Generator[Mock, None, None]:
    """Context manager that provides a mock database session with standard setup."""
    with patch("app.line.service.get_session") as mock_get_session:
        mock_session = Mock()
        mock_get_session.return_value = iter([mock_session])
        yield mock_session


@contextmanager
def mock_messaging_api() -> Generator[Mock, None, None]:
    """Context manager that provides a mock MessagingApi."""
    with patch("app.line.service.MessagingApi") as mock_messaging_api:
        mock_api_instance = Mock()
        mock_messaging_api.return_value = mock_api_instance
        with patch("app.line.service.ApiClient"):
            yield mock_api_instance


def create_mock_location(location_id: int = 123, full_name: str = "臺北市中正區") -> Mock:
    """Create a mock Location object."""
    mock_location = Mock(spec=Location)
    mock_location.id = location_id
    mock_location.full_name = full_name
    return mock_location


def create_mock_user(user_id: int = 456, line_user_id: str = "test_line_user_id") -> Mock:
    """Create a mock User object."""
    mock_user = Mock()
    mock_user.id = user_id
    mock_user.line_user_id = line_user_id
    return mock_user


class ServiceTestHelper:
    """Helper class for common service testing patterns."""

    @staticmethod
    def assert_message_api_called_with_error(mock_api: Mock, expected_text: str) -> None:
        """Assert that messaging API was called with an error message."""
        mock_api.reply_message.assert_called_once()
        call_args = mock_api.reply_message.call_args[0]
        request = call_args[0]
        message = request.messages[0]
        assert expected_text in message.text  # noqa: S101

    @staticmethod
    def setup_location_parse_single_result(mock_location: Mock) -> None:
        """Setup location parsing to return a single location result."""
        with patch("app.line.service.LocationService.parse_location_input") as mock_parse:
            mock_parse.return_value = ([mock_location], "天氣查詢結果")
            return mock_parse

    @staticmethod
    def setup_location_parse_no_result() -> Mock:
        """Setup location parsing to return no results."""
        with patch("app.line.service.LocationService.parse_location_input") as mock_parse:
            mock_parse.return_value = ([], "Sorry, I don't understand.")
            return mock_parse

    @staticmethod
    def setup_location_parse_error() -> Mock:
        """Setup location parsing to raise an exception."""
        with patch(
            "app.line.service.LocationService.parse_location_input",
            side_effect=Exception("Unexpected error"),
        ) as mock_parse:
            return mock_parse


@contextmanager
def mock_user_service_functions(
    create_user_return: Mock | None = None,
    get_user_return: Mock | None = None,
    deactivate_user_return: Mock | None = None,
    record_query_side_effect: Exception | None = None,
) -> Generator[tuple[Mock, Mock, Mock, Mock], None, None]:
    """Context manager that mocks all user service functions."""
    with (
        patch("app.line.service.create_user_if_not_exists") as mock_create_user,
        patch("app.line.service.get_user_by_line_id") as mock_get_user,
        patch("app.line.service.deactivate_user") as mock_deactivate_user,
        patch("app.line.service.record_user_query") as mock_record_query,
    ):
        # Set return values
        if create_user_return is not None:
            mock_create_user.return_value = create_user_return
        if get_user_return is not None:
            mock_get_user.return_value = get_user_return
        if deactivate_user_return is not None:
            mock_deactivate_user.return_value = deactivate_user_return

        # Set side effects if needed
        if record_query_side_effect:
            mock_record_query.side_effect = record_query_side_effect

        yield mock_create_user, mock_get_user, mock_deactivate_user, mock_record_query
