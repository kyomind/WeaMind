"""Test basic LINE service functionality."""

from unittest.mock import Mock, patch

from linebot.v3.webhooks import (
    FollowEvent,
    LocationMessageContent,
    MessageEvent,
    TextMessageContent,
    UnfollowEvent,
)

from app.core.config import settings
from app.line.service import (
    handle_default_event,
    handle_follow_event,
    handle_location_message_event,
    handle_message_event,
    handle_unfollow_event,
    send_liff_location_setting_response,
)
from app.weather.models import Location


class TestLineService:
    """Test LINE webhook handler functions."""

    def test_handle_message_event_non_text_message(self) -> None:
        """Test handling non-text message events."""
        # Create mock event with non-text message
        mock_event = Mock(spec=MessageEvent)
        mock_event.message = Mock()  # Not TextMessageContent
        mock_event.reply_token = "test_token"

        # Should return early without processing
        handle_message_event(mock_event)
        # No exception should be raised

    def test_handle_message_event_empty_reply_token(self) -> None:
        """Test handling events with empty reply token."""
        mock_event = Mock(spec=MessageEvent)
        mock_event.message = Mock(spec=TextMessageContent)
        mock_event.message.text = "Hello"
        mock_event.reply_token = None

        # Should return early without processing
        handle_message_event(mock_event)
        # No exception should be raised

    def test_handle_message_event_dev_mode(self) -> None:
        """Test handling message events in development mode."""
        mock_event = Mock(spec=MessageEvent)
        mock_event.message = Mock(spec=TextMessageContent)
        mock_event.message.text = "Hello"
        mock_event.reply_token = "test_token"

        # In dev mode (CHANGE_ME token), should just log
        handle_message_event(mock_event)
        # No exception should be raised

    def test_handle_message_event_api_success(self) -> None:
        """Test successful message handling with real API token."""
        mock_event = Mock(spec=MessageEvent)
        mock_event.message = Mock(spec=TextMessageContent)
        mock_event.message.text = "Hello"
        mock_event.reply_token = "test_token"

        with patch("app.core.config.settings.LINE_CHANNEL_ACCESS_TOKEN", "real_token"):
            with patch("app.line.service.get_session") as mock_get_session:
                mock_session = Mock()
                mock_get_session.return_value = iter([mock_session])

                with patch("app.line.service.LocationService.parse_location_input") as mock_parse:
                    mock_parse.return_value = ([], "Sorry, I don't understand.")

                    with patch("app.line.service.MessagingApi.reply_message") as mock_reply:
                        handle_message_event(mock_event)
                        mock_reply.assert_called_once()

    def test_handle_message_event_api_error(self) -> None:
        """Test message handling with API error."""
        mock_event = Mock(spec=MessageEvent)
        mock_event.message = Mock(spec=TextMessageContent)
        mock_event.message.text = "Hello"
        mock_event.reply_token = "test_token"

        with patch("app.core.config.settings.LINE_CHANNEL_ACCESS_TOKEN", "real_token"):
            with patch("app.line.service.get_session") as mock_get_session:
                mock_session = Mock()
                mock_get_session.return_value = iter([mock_session])

                with patch("app.line.service.LocationService.parse_location_input") as mock_parse:
                    mock_parse.return_value = ([], "Sorry, I don't understand.")

                    with patch(
                        "app.line.service.MessagingApi.reply_message",
                        side_effect=Exception("API Error"),
                    ):
                        # Should not raise exception, just log error
                        handle_message_event(mock_event)

    def test_handle_default_event(self) -> None:
        """Test handling default events."""
        mock_event = {"type": "unknown", "replyToken": "test_token"}

        # Should just log the event without raising exception
        handle_default_event(mock_event)
        # No exception should be raised

    def test_handle_follow_event_success(self) -> None:
        """Test successful follow event handling."""
        mock_event = Mock(spec=FollowEvent)
        mock_event.reply_token = "test_token"
        mock_source = Mock()
        mock_source.user_id = "test_user_id"
        mock_event.source = mock_source

        with patch("app.line.service.get_session") as mock_get_session:
            mock_session = Mock()
            mock_get_session.return_value = iter([mock_session])

            with patch("app.line.service.create_user_if_not_exists") as mock_create_user:
                mock_user = Mock()
                mock_user.id = 1
                mock_create_user.return_value = mock_user

                with patch("app.line.service.MessagingApi.reply_message") as mock_reply:
                    handle_follow_event(mock_event)

                    mock_create_user.assert_called_once_with(mock_session, "test_user_id")
                    mock_reply.assert_called_once()
                    mock_session.close.assert_called_once()

    def test_handle_follow_event_no_user_id(self) -> None:
        """Test follow event without user_id."""
        mock_event = Mock(spec=FollowEvent)
        mock_event.source = None
        mock_event.reply_token = "test_token"

        # Should return early without processing
        handle_follow_event(mock_event)
        # No exception should be raised

    def test_handle_follow_event_no_reply_token(self) -> None:
        """Test follow event without reply token."""
        mock_event = Mock(spec=FollowEvent)
        mock_event.reply_token = None
        mock_source = Mock()
        mock_source.user_id = "test_user_id"
        mock_event.source = mock_source

        with patch("app.line.service.get_session") as mock_get_session:
            mock_session = Mock()
            mock_get_session.return_value = iter([mock_session])

            with patch("app.line.service.create_user_if_not_exists") as mock_create_user:
                mock_user = Mock()
                mock_user.id = 1
                mock_create_user.return_value = mock_user

                handle_follow_event(mock_event)

                mock_create_user.assert_called_once_with(mock_session, "test_user_id")
                mock_session.close.assert_called_once()

    def test_handle_follow_event_api_error(self) -> None:
        """Test follow event with messaging API error."""
        mock_event = Mock(spec=FollowEvent)
        mock_event.reply_token = "test_token"
        mock_source = Mock()
        mock_source.user_id = "test_user_id"
        mock_event.source = mock_source

        with patch("app.line.service.get_session") as mock_get_session:
            mock_session = Mock()
            mock_get_session.return_value = iter([mock_session])

            with patch("app.line.service.create_user_if_not_exists") as mock_create_user:
                mock_user = Mock()
                mock_user.id = 1
                mock_create_user.return_value = mock_user

                with patch(
                    "app.line.service.MessagingApi.reply_message",
                    side_effect=Exception("API Error"),
                ):
                    # Should not raise exception, just log error
                    handle_follow_event(mock_event)

                    mock_create_user.assert_called_once_with(mock_session, "test_user_id")
                    mock_session.close.assert_called_once()

    def test_handle_unfollow_event_success(self) -> None:
        """Test successful unfollow event handling."""
        mock_event = Mock(spec=UnfollowEvent)
        mock_source = Mock()
        mock_source.user_id = "test_user_id"
        mock_event.source = mock_source

        with patch("app.line.service.get_session") as mock_get_session:
            mock_session = Mock()
            mock_get_session.return_value = iter([mock_session])

            with patch("app.line.service.deactivate_user") as mock_deactivate_user:
                mock_user = Mock()
                mock_user.id = 1
                mock_deactivate_user.return_value = mock_user

                handle_unfollow_event(mock_event)

                mock_deactivate_user.assert_called_once_with(mock_session, "test_user_id")
                mock_session.close.assert_called_once()

    def test_handle_unfollow_event_user_not_found(self) -> None:
        """Test unfollow event for unknown user."""
        mock_event = Mock(spec=UnfollowEvent)
        mock_source = Mock()
        mock_source.user_id = "test_user_id"
        mock_event.source = mock_source

        with patch("app.line.service.get_session") as mock_get_session:
            mock_session = Mock()
            mock_get_session.return_value = iter([mock_session])

            with patch("app.line.service.deactivate_user") as mock_deactivate_user:
                mock_deactivate_user.return_value = None

                handle_unfollow_event(mock_event)

                mock_deactivate_user.assert_called_once_with(mock_session, "test_user_id")
                mock_session.close.assert_called_once()

    def test_handle_unfollow_event_no_user_id(self) -> None:
        """Test unfollow event without user_id."""
        mock_event = Mock(spec=UnfollowEvent)
        mock_event.source = None

        # Should return early without processing
        handle_unfollow_event(mock_event)
        # No exception should be raised

    def test_handle_message_event_location_parse_exception(self) -> None:
        """Test handling unexpected exception during location parsing."""
        mock_event = Mock(spec=MessageEvent)
        mock_event.reply_token = "test_token"
        mock_message = Mock(spec=TextMessageContent)
        mock_message.text = "台北"
        mock_event.message = mock_message

        with patch("app.line.service.get_session") as mock_get_session:
            mock_session = Mock()
            mock_get_session.return_value = iter([mock_session])

            with patch(
                "app.line.service.LocationService.parse_location_input",
                side_effect=Exception("Unexpected error"),
            ):
                with patch("app.line.service.MessagingApi") as mock_messaging_api:
                    mock_api_instance = Mock()
                    mock_messaging_api.return_value = mock_api_instance

                    with patch("app.line.service.ApiClient"):
                        handle_message_event(mock_event)

                        # Should send generic error message
                        mock_api_instance.reply_message.assert_called_once()
                        call_args = mock_api_instance.reply_message.call_args[0]
                        request = call_args[0]
                        message = request.messages[0]
                        assert "系統暫時有點忙" in message.text

    def test_handle_follow_event_exception(self) -> None:
        """Test follow event with general exception."""
        mock_event = Mock(spec=FollowEvent)
        mock_source = Mock()
        mock_source.user_id = "test_user_id"
        mock_event.source = mock_source

        with patch(
            "app.line.service.get_session",
            side_effect=Exception("Database error"),
        ):
            # Should not raise exception, just log error
            handle_follow_event(mock_event)

    def test_handle_unfollow_event_exception(self) -> None:
        """Test unfollow event with general exception."""
        mock_event = Mock(spec=UnfollowEvent)
        mock_source = Mock()
        mock_source.user_id = "test_user_id"
        mock_event.source = mock_source

        with patch(
            "app.line.service.get_session",
            side_effect=Exception("Database error"),
        ):
            # Should not raise exception, just log error
            handle_unfollow_event(mock_event)

    def test_send_liff_location_setting_response_success(self) -> None:
        """Test successful LIFF location setting response."""

        with patch("app.line.service.MessagingApi") as mock_messaging_api:
            mock_api_instance = Mock()
            mock_messaging_api.return_value = mock_api_instance

            with patch("app.line.service.ApiClient"):
                send_liff_location_setting_response("test_token")

                mock_api_instance.reply_message.assert_called_once()
                call_args = mock_api_instance.reply_message.call_args[0]
                request = call_args[0]
                message = request.messages[0]
                assert "地點設定" in message.text
                assert settings.BASE_URL in message.text

    def test_send_liff_location_setting_response_error(self) -> None:
        """Test LIFF location setting response with API error."""

        with patch(
            "app.line.service.MessagingApi.reply_message",
            side_effect=Exception("API Error"),
        ):
            with patch("app.line.service.ApiClient"):
                # Should not raise exception, just log error
                send_liff_location_setting_response("test_token")

    def test_send_liff_location_setting_response_no_reply_token(self) -> None:
        """Test LIFF location setting response with no reply token."""
        # Should return early without API call
        send_liff_location_setting_response(None)
        # No exception should be raised

    def test_handle_message_event_with_user_query_recording(self) -> None:
        """Test message handling with user query recording."""
        mock_event = Mock(spec=MessageEvent)
        mock_event.reply_token = "test_token"
        mock_event.message = Mock(spec=TextMessageContent)
        mock_event.message.text = "台北"
        mock_source = Mock()
        mock_source.user_id = "test_line_user_id"
        mock_event.source = mock_source

        # Mock single location result to trigger recording
        mock_location = Mock(spec=Location)
        mock_location.id = 123
        mock_location.full_name = "臺北市中正區"

        with (
            patch("app.line.service.get_session") as mock_get_session,
            patch("app.line.service.LocationService.parse_location_input") as mock_parse,
            patch("app.line.service.get_user_by_line_id") as mock_get_user,
            patch("app.line.service.record_user_query") as mock_record_query,
            patch("app.line.service.MessagingApi") as mock_messaging_api,
            patch("app.line.service.ApiClient"),
        ):
            mock_session = Mock()
            mock_get_session.return_value = iter([mock_session])

            # Single location triggers recording
            mock_parse.return_value = ([mock_location], "天氣查詢結果")

            # Mock user found for recording
            mock_user = Mock()
            mock_user.id = 456
            mock_get_user.return_value = mock_user

            mock_api_instance = Mock()
            mock_messaging_api.return_value = mock_api_instance

            handle_message_event(mock_event)

            # Verify query was recorded
            mock_record_query.assert_called_once_with(mock_session, 456, 123)

    def test_handle_message_event_no_user_for_recording(self) -> None:
        """Test message handling when user not found for recording."""
        mock_event = Mock(spec=MessageEvent)
        mock_event.reply_token = "test_token"
        mock_event.message = Mock(spec=TextMessageContent)
        mock_event.message.text = "台北"
        mock_source = Mock()
        mock_source.user_id = "test_line_user_id"
        mock_event.source = mock_source

        mock_location = Mock(spec=Location)
        mock_location.id = 123
        mock_location.full_name = "臺北市中正區"

        with (
            patch("app.line.service.get_session") as mock_get_session,
            patch("app.line.service.LocationService.parse_location_input") as mock_parse,
            patch("app.line.service.get_user_by_line_id") as mock_get_user,
            patch("app.line.service.record_user_query") as mock_record_query,
            patch("app.line.service.MessagingApi") as mock_messaging_api,
            patch("app.line.service.ApiClient"),
        ):
            mock_session = Mock()
            mock_get_session.return_value = iter([mock_session])

            # Single location triggers recording attempt
            mock_parse.return_value = ([mock_location], "天氣查詢結果")

            # User not found - no recording
            mock_get_user.return_value = None

            mock_api_instance = Mock()
            mock_messaging_api.return_value = mock_api_instance

            handle_message_event(mock_event)

            # Verify query was NOT recorded
            mock_record_query.assert_not_called()

    def test_handle_message_event_no_source_for_recording(self) -> None:
        """Test message handling when no source for recording."""
        mock_event = Mock(spec=MessageEvent)
        mock_event.reply_token = "test_token"
        mock_event.message = Mock(spec=TextMessageContent)
        mock_event.message.text = "台北"
        mock_event.source = None  # No source

        mock_location = Mock(spec=Location)
        mock_location.id = 123
        mock_location.full_name = "臺北市中正區"

        with (
            patch("app.line.service.get_session") as mock_get_session,
            patch("app.line.service.LocationService.parse_location_input") as mock_parse,
            patch("app.line.service.record_user_query") as mock_record_query,
            patch("app.line.service.MessagingApi") as mock_messaging_api,
            patch("app.line.service.ApiClient"),
        ):
            mock_session = Mock()
            mock_get_session.return_value = iter([mock_session])

            # Single location triggers recording attempt
            mock_parse.return_value = ([mock_location], "天氣查詢結果")

            mock_api_instance = Mock()
            mock_messaging_api.return_value = mock_api_instance

            handle_message_event(mock_event)

            # Verify query was NOT recorded (no user_id available)
            mock_record_query.assert_not_called()


class TestLocationMessageHandler:
    """Test location message handler functionality."""

    def test_handle_location_message_event_success(self) -> None:
        """Test successful location message handling."""
        mock_event = Mock(spec=MessageEvent)
        mock_event.reply_token = "test_token"
        mock_message = Mock(spec=LocationMessageContent)
        mock_message.latitude = 25.0330
        mock_message.longitude = 121.5654
        mock_event.message = mock_message
        mock_source = Mock()
        mock_source.user_id = "test_user_id"
        mock_event.source = mock_source

        with (
            patch("app.line.service.get_session") as mock_get_session,
            patch("app.line.service.WeatherService.handle_location_weather_query") as mock_weather,
            patch("app.line.service.LocationService.find_nearest_location") as mock_find,
            patch("app.line.service.get_user_by_line_id") as mock_get_user,
            patch("app.line.service.record_user_query") as mock_record,
            patch("app.line.service.send_text_response") as mock_send,
        ):
            mock_session = Mock()
            mock_get_session.return_value = iter([mock_session])

            # Mock successful location query
            mock_weather.return_value = "找到了 臺北市中正區，正在查詢天氣..."

            # Mock location found for recording
            mock_location = Mock()
            mock_location.id = 123
            mock_find.return_value = mock_location

            # Mock user for recording
            mock_user = Mock()
            mock_user.id = 456
            mock_get_user.return_value = mock_user

            handle_location_message_event(mock_event)

            # Should query weather with coordinates
            mock_weather.assert_called_once_with(mock_session, 25.0330, 121.5654)

            # Should record query for user history
            mock_record.assert_called_once_with(mock_session, 456, 123)

            # Should send response
            mock_send.assert_called_once_with("test_token", "找到了 臺北市中正區，正在查詢天氣...")

    def test_handle_location_message_event_empty_reply_token(self) -> None:
        """Test location message handling with empty reply token."""
        mock_event = Mock(spec=MessageEvent)
        mock_event.reply_token = None

        # Should return early without processing
        handle_location_message_event(mock_event)

    def test_handle_location_message_event_wrong_message_type(self) -> None:
        """Test location message handling with wrong message type."""
        mock_event = Mock(spec=MessageEvent)
        mock_event.reply_token = "test_token"
        mock_event.message = Mock()  # Not LocationMessageContent

        # Should return early without processing
        handle_location_message_event(mock_event)

    def test_handle_location_message_event_outside_taiwan(self) -> None:
        """Test location message handling for coordinates outside Taiwan."""
        mock_event = Mock(spec=MessageEvent)
        mock_event.reply_token = "test_token"
        mock_message = Mock(spec=LocationMessageContent)
        mock_message.latitude = 35.6762  # Tokyo coordinates
        mock_message.longitude = 139.6503
        mock_event.message = mock_message
        mock_event.source = None  # No source for this test

        with (
            patch("app.line.service.get_session") as mock_get_session,
            patch("app.line.service.WeatherService.handle_location_weather_query") as mock_weather,
            patch("app.line.service.send_text_response") as mock_send,
        ):
            mock_session = Mock()
            mock_get_session.return_value = iter([mock_session])

            # Mock location outside Taiwan response
            mock_weather.return_value = "抱歉，目前僅支援台灣地區的天氣查詢 🌏"

            handle_location_message_event(mock_event)

            # Should query weather with coordinates
            mock_weather.assert_called_once_with(mock_session, 35.6762, 139.6503)

            # Should send outside Taiwan response
            mock_send.assert_called_once_with("test_token", "抱歉，目前僅支援台灣地區的天氣查詢 🌏")

    def test_handle_location_message_event_exception(self) -> None:
        """Test location message handling with exception."""
        mock_event = Mock(spec=MessageEvent)
        mock_event.reply_token = "test_token"
        mock_message = Mock(spec=LocationMessageContent)
        mock_message.latitude = 25.0330
        mock_message.longitude = 121.5654
        mock_event.message = mock_message

        with (
            patch("app.line.service.get_session") as mock_get_session,
            patch(
                "app.line.service.WeatherService.handle_location_weather_query",
                side_effect=Exception("Database error"),
            ),
            patch("app.line.service.send_text_response") as mock_send,
        ):
            mock_session = Mock()
            mock_get_session.return_value = iter([mock_session])

            handle_location_message_event(mock_event)

            # Should send error response
            mock_send.assert_called_once_with("test_token", "😅 系統暫時有點忙，請稍後再試一次。")
