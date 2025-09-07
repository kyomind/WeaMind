"""Test announcement loading and Flex Message generation."""

import json
from unittest.mock import Mock, patch

from app.line.service import (
    create_announcements_flex_message,
    handle_announcements,
)


class TestAnnouncementFeatures:
    """Test announcement-related features."""

    def test_create_announcements_flex_message(self) -> None:
        """Test creating Flex Message from announcements."""
        announcements = [
            {
                "id": "test-1",
                "title": "Test Announcement 1",
                "body": "This is a test announcement body content.",
                "level": "info",
                "start_at": "2025-08-27T10:00:00+08:00",
                "visible": True,
            },
            {
                "id": "test-2",
                "title": "Test Maintenance",
                "body": "System will be under maintenance.",
                "level": "maintenance",
                "start_at": "2025-08-27T09:00:00+08:00",
                "visible": True,
            },
        ]

        flex_message = create_announcements_flex_message(announcements)

        # Just check that a FlexMessage is returned without checking internal structure
        assert flex_message is not None

    def test_handle_announcements_success(self) -> None:
        """Test successful announcement handling."""
        # Mock the entire announcements path and file reading
        announcements_data = {
            "version": 1,
            "updated_at": "2025-08-27T10:00:00Z",
            "items": [
                {
                    "id": "test-1",
                    "title": "Test Announcement",
                    "body": "Test content",
                    "level": "info",
                    "start_at": "2025-08-27T10:00:00+08:00",
                    "visible": True,
                }
            ],
        }

        with patch("app.line.service.Path") as mock_path:
            # Mock Path.exists() to return True
            mock_path.return_value.exists.return_value = True

            # Mock the file opening and JSON loading
            with patch("app.line.service.json.load", return_value=announcements_data):
                with patch("app.line.service.ApiClient"):
                    with patch("app.line.service.MessagingApi") as mock_messaging_api:
                        mock_api_instance = Mock()
                        mock_messaging_api.return_value = mock_api_instance

                        handle_announcements("test_reply_token")

                        # Verify that reply_message was called
                        mock_api_instance.reply_message.assert_called_once()

    def test_handle_announcements_file_not_found(self) -> None:
        """Test handling when announcements file doesn't exist."""
        with patch("app.line.service.Path") as mock_path:
            mock_file = Mock()
            mock_file.exists.return_value = False
            mock_path.return_value = mock_file

            with patch("app.line.service.send_error_response") as mock_send_error:
                handle_announcements("test_reply_token")
                mock_send_error.assert_called_once_with("test_reply_token", "公告資料載入失敗")

    def test_handle_announcements_no_visible_items(self) -> None:
        """Test handling when no visible announcements exist."""
        announcements_data = {
            "version": 1,
            "updated_at": "2025-08-27T10:00:00Z",
            "items": [
                {
                    "id": "test-1",
                    "title": "Hidden Announcement",
                    "body": "This is hidden",
                    "level": "info",
                    "start_at": "2025-08-27T10:00:00+08:00",
                    "visible": False,
                }
            ],
        }

        with patch("app.line.service.Path") as mock_path:
            mock_path.return_value.exists.return_value = True

            with patch("app.line.service.json.load", return_value=announcements_data):
                with patch("app.line.service.send_text_response") as mock_send_text:
                    handle_announcements("test_reply_token")
                    mock_send_text.assert_called_once_with("test_reply_token", "目前沒有新公告")

    def test_handle_announcements_json_error(self) -> None:
        """Test handling JSON parsing errors."""
        with patch("app.line.service.Path") as mock_path:
            mock_path.return_value.exists.return_value = True

            # Simulate JSON decoding error
            error = json.JSONDecodeError("msg", "doc", 0)
            with patch("app.line.service.json.load", side_effect=error):
                with patch("app.line.service.send_error_response") as mock_send_error:
                    handle_announcements("test_reply_token")
                    mock_send_error.assert_called_once_with(
                        "test_reply_token", "載入公告時發生錯誤"
                    )
