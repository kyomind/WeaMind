"""Test PostBack event handlers for Rich Menu functionality."""

from unittest.mock import Mock, patch

from linebot.v3.webhooks import PostbackEvent

from app.line.service import (
    handle_announcements,
    handle_current_location_weather,
    handle_other_postback,
    handle_postback_event,
    handle_recent_queries_postback,
    handle_settings_postback,
    handle_user_location_weather,
    handle_weather_postback,
    parse_postback_data,
    send_error_response,
    send_location_not_set_response,
    send_other_menu_quick_reply,
    send_text_response,
)
from app.user.models import User
from app.weather.models import Location


class TestPostBackEventHandlers:
    """Test PostBack event handlers for Rich Menu functionality."""

    def test_parse_postback_data_success(self) -> None:
        """Test successful PostBack data parsing."""
        # Test weather action
        result = parse_postback_data("action=weather&type=home")
        assert result == {"action": "weather", "type": "home"}

        # Test recent queries action
        result = parse_postback_data("action=recent_queries")
        assert result == {"action": "recent_queries"}

    def test_parse_postback_data_empty(self) -> None:
        """Test parsing empty PostBack data."""
        result = parse_postback_data("")
        assert result == {}

    def test_parse_postback_data_invalid(self) -> None:
        """Test parsing invalid PostBack data."""
        result = parse_postback_data("invalid_format")
        # Should return empty dictionary for invalid format
        assert result == {}

    def test_parse_postback_data_exception(self) -> None:
        """Test parsing PostBack data with exception."""
        with patch("app.line.service.parse_qs", side_effect=Exception("Parse error")):
            result = parse_postback_data("action=weather&type=home")
            assert result == {}

    def test_handle_postback_event_no_reply_token(self) -> None:
        """Test PostBack event without reply token."""
        mock_event = Mock(spec=PostbackEvent)
        mock_event.reply_token = None
        mock_event.postback = Mock()
        mock_event.postback.data = "action=weather&type=home"

        # Should return early without processing
        handle_postback_event(mock_event)
        # No exception should be raised

    def test_handle_postback_event_no_user_id(self) -> None:
        """Test PostBack event without user ID."""
        mock_event = Mock(spec=PostbackEvent)
        mock_event.reply_token = "test_token"
        mock_event.postback = Mock()
        mock_event.postback.data = "action=weather&type=home"
        mock_event.source = None

        # Should return early without processing
        handle_postback_event(mock_event)
        # No exception should be raised

    def test_handle_postback_event_unknown_action(self) -> None:
        """Test PostBack event with unknown action."""
        mock_event = Mock(spec=PostbackEvent)
        mock_event.reply_token = "test_token"
        mock_event.postback = Mock()
        mock_event.postback.data = "action=unknown"
        mock_source = Mock()
        mock_source.user_id = "test_user_id"
        mock_event.source = mock_source

        with patch("app.line.service.send_error_response") as mock_send:
            handle_postback_event(mock_event)

            mock_send.assert_called_once_with("test_token", "未知的操作")

    def test_handle_postback_event_exception(self) -> None:
        """Test PostBack event with exception."""
        mock_event = Mock(spec=PostbackEvent)
        mock_event.reply_token = "test_token"
        mock_event.postback = Mock()
        mock_event.postback.data = "action=weather&type=home"
        mock_source = Mock()
        mock_source.user_id = "test_user_id"
        mock_event.source = mock_source

        with patch("app.line.service.parse_postback_data", side_effect=Exception("Parse error")):
            with patch("app.line.service.send_error_response") as mock_send:
                handle_postback_event(mock_event)

                mock_send.assert_called_once_with("test_token", "系統暫時有點忙，請稍後再試一次。")

    def test_handle_postback_event_exception_no_reply_token(self) -> None:
        """Test PostBack event exception when reply_token is None."""
        mock_event = Mock(spec=PostbackEvent)
        mock_event.reply_token = None  # This triggers the 341->exit branch
        mock_event.postback = Mock()
        mock_event.postback.data = "action=weather&type=home"
        mock_source = Mock()
        mock_source.user_id = "test_user_id"
        mock_event.source = mock_source

        with patch("app.line.service.parse_postback_data", side_effect=Exception("Parse error")):
            # Should not call send_error_response since reply_token is None
            handle_postback_event(mock_event)
            # No exception should be raised, function should exit silently

    def test_handle_postback_event_weather_action(self) -> None:
        """Test PostBack event with weather action."""
        mock_event = Mock(spec=PostbackEvent)
        mock_event.reply_token = "test_token"
        mock_event.postback = Mock()
        mock_event.postback.data = "action=weather&type=home"
        mock_source = Mock()
        mock_source.user_id = "test_user_id"
        mock_event.source = mock_source

        with patch("app.line.service.handle_weather_postback") as mock_handle:
            handle_postback_event(mock_event)

            mock_handle.assert_called_once_with(
                mock_event, "test_user_id", {"action": "weather", "type": "home"}
            )

    def test_handle_postback_event_settings_action(self) -> None:
        """Test PostBack event with settings action."""
        mock_event = Mock(spec=PostbackEvent)
        mock_event.reply_token = "test_token"
        mock_event.postback = Mock()
        mock_event.postback.data = "action=settings&type=location"
        mock_source = Mock()
        mock_source.user_id = "test_user_id"
        mock_event.source = mock_source

        with patch("app.line.service.handle_settings_postback") as mock_handle:
            handle_postback_event(mock_event)

            mock_handle.assert_called_once_with(
                mock_event, {"action": "settings", "type": "location"}
            )

    def test_handle_postback_event_recent_queries_action(self) -> None:
        """Test PostBack event with recent queries action."""
        mock_event = Mock(spec=PostbackEvent)
        mock_event.reply_token = "test_token"
        mock_event.postback = Mock()
        mock_event.postback.data = "action=recent_queries"
        mock_source = Mock()
        mock_source.user_id = "test_user_id"
        mock_event.source = mock_source

        with patch("app.line.service.handle_recent_queries_postback") as mock_handle:
            handle_postback_event(mock_event)

            mock_handle.assert_called_once_with(mock_event)

    def test_handle_postback_event_other_action(self) -> None:
        """Test PostBack event with other action."""
        mock_event = Mock(spec=PostbackEvent)
        mock_event.reply_token = "test_token"
        mock_event.postback = Mock()
        mock_event.postback.data = "action=other&type=menu"
        mock_source = Mock()
        mock_source.user_id = "test_user_id"
        mock_event.source = mock_source

        with patch("app.line.service.handle_other_postback") as mock_handle:
            handle_postback_event(mock_event)

            mock_handle.assert_called_once_with(mock_event, {"action": "other", "type": "menu"})

    def test_handle_weather_postback_home_success(self) -> None:
        """Test successful home weather PostBack."""
        mock_event = Mock(spec=PostbackEvent)
        mock_event.reply_token = "test_token"

        with patch("app.line.service.get_session") as mock_get_session:
            mock_session = Mock()
            mock_get_session.return_value = iter([mock_session])

            # Mock user with home location
            mock_user = Mock(spec=User)
            mock_location = Mock()
            mock_location.full_name = "台北市中正區"
            mock_user.home_location = mock_location

            with patch("app.line.service.get_user_by_line_id", return_value=mock_user):
                with patch("app.line.service.LocationService.parse_location_input") as mock_parse:
                    mock_parse.return_value = ([], "台北市中正區的天氣...")

                    with patch("app.line.service.send_text_response") as mock_send:
                        handle_weather_postback(
                            mock_event, "test_user_id", {"action": "weather", "type": "home"}
                        )

                        mock_send.assert_called_once_with("test_token", "台北市中正區的天氣...")

    def test_handle_weather_postback_home_no_location(self) -> None:
        """Test home weather PostBack when user has no home location set."""
        mock_event = Mock(spec=PostbackEvent)
        mock_event.reply_token = "test_token"

        with patch("app.line.service.get_session") as mock_get_session:
            mock_session = Mock()
            mock_get_session.return_value = iter([mock_session])

            # Mock user without home location
            mock_user = Mock(spec=User)
            mock_user.home_location = None

            with patch("app.line.service.get_user_by_line_id", return_value=mock_user):
                with patch("app.line.service.send_location_not_set_response") as mock_send:
                    handle_weather_postback(
                        mock_event, "test_user_id", {"action": "weather", "type": "home"}
                    )

                    mock_send.assert_called_once_with("test_token", "住家")

    def test_handle_weather_postback_office_success(self) -> None:
        """Test successful office weather PostBack."""
        mock_event = Mock(spec=PostbackEvent)
        mock_event.reply_token = "test_token"

        with patch("app.line.service.get_session") as mock_get_session:
            mock_session = Mock()
            mock_get_session.return_value = iter([mock_session])

            # Mock user with work location
            mock_user = Mock(spec=User)
            mock_location = Mock()
            mock_location.full_name = "新北市板橋區"
            mock_user.work_location = mock_location

            with patch("app.line.service.get_user_by_line_id", return_value=mock_user):
                with patch("app.line.service.LocationService.parse_location_input") as mock_parse:
                    mock_parse.return_value = ([], "新北市板橋區的天氣...")

                    with patch("app.line.service.send_text_response") as mock_send:
                        handle_weather_postback(
                            mock_event, "test_user_id", {"action": "weather", "type": "office"}
                        )

                        mock_send.assert_called_once_with("test_token", "新北市板橋區的天氣...")

    def test_handle_weather_postback_user_not_found(self) -> None:
        """Test weather PostBack when user not found - should auto-create user."""
        mock_event = Mock(spec=PostbackEvent)
        mock_event.reply_token = "test_token"

        with patch("app.line.service.get_session") as mock_get_session:
            mock_session = Mock()
            mock_get_session.return_value = iter([mock_session])

            # Mock auto-created user without home location
            mock_user = Mock()
            mock_user.home_location = None
            mock_user.work_location = None

            with patch("app.line.service.get_user_by_line_id", return_value=None):
                with patch("app.line.service.create_user_if_not_exists", return_value=mock_user):
                    with patch("app.line.service.send_location_not_set_response") as mock_send:
                        handle_weather_postback(
                            mock_event, "test_user_id", {"action": "weather", "type": "home"}
                        )

                        mock_send.assert_called_once_with("test_token", "住家")

    def test_handle_weather_postback_current_location(self) -> None:
        """Test weather PostBack with current location."""
        mock_event = Mock(spec=PostbackEvent)
        mock_event.reply_token = "test_token"

        with patch("app.line.service.handle_current_location_weather") as mock_handle:
            handle_weather_postback(
                mock_event, "test_user_id", {"action": "weather", "type": "current"}
            )

            mock_handle.assert_called_once_with(mock_event)

    def test_handle_weather_postback_unknown_type(self) -> None:
        """Test weather PostBack with unknown type."""
        mock_event = Mock(spec=PostbackEvent)
        mock_event.reply_token = "test_token"

        with patch("app.line.service.send_error_response") as mock_send:
            handle_weather_postback(
                mock_event, "test_user_id", {"action": "weather", "type": "unknown"}
            )

            mock_send.assert_called_once_with("test_token", "未知的地點類型")

    def test_handle_user_location_weather_exception(self) -> None:
        """Test user location weather with exception."""
        mock_event = Mock(spec=PostbackEvent)
        mock_event.reply_token = "test_token"

        with patch("app.line.service.get_session") as mock_get_session:
            mock_session = Mock()
            mock_get_session.return_value = iter([mock_session])

            with patch("app.line.service.get_user_by_line_id", side_effect=Exception("DB error")):
                with patch("app.line.service.send_error_response") as mock_send:
                    handle_user_location_weather(mock_event, "test_user_id", "home")

                    mock_send.assert_called_once_with("test_token", "查詢時發生錯誤，請稍後再試。")

    def test_handle_current_location_weather_request(self) -> None:
        """Test current location weather sends location request."""
        mock_event = Mock(spec=PostbackEvent)
        mock_event.reply_token = "test_token"

        with patch("app.line.service.MessagingApi") as mock_messaging_api:
            mock_api_instance = Mock()
            mock_messaging_api.return_value = mock_api_instance

            with patch("app.line.service.ApiClient"):
                handle_current_location_weather(mock_event)

                # Should send location request message with Quick Reply
                mock_api_instance.reply_message.assert_called_once()
                call_args = mock_api_instance.reply_message.call_args[0]
                request = call_args[0]

                # Check message content
                message = request.messages[0]
                assert message.text == "請點擊地圖上的任意位置，我將為您查詢該地天氣"

                # Check Quick Reply contains location action
                assert message.quick_reply is not None
                assert len(message.quick_reply.items) == 1
                assert message.quick_reply.items[0].action.type == "location"
                assert message.quick_reply.items[0].action.label == "開啟地圖選擇"

    def test_handle_settings_postback_location_type(self) -> None:
        """Test settings PostBack with location type."""
        mock_event = Mock(spec=PostbackEvent)
        mock_event.reply_token = "test_token"

        with patch("app.line.service.send_liff_location_setting_response") as mock_send:
            handle_settings_postback(mock_event, {"action": "settings", "type": "location"})

            mock_send.assert_called_once_with("test_token")

    def test_handle_settings_postback_unknown_type(self) -> None:
        """Test settings PostBack with unknown type."""
        mock_event = Mock(spec=PostbackEvent)
        mock_event.reply_token = "test_token"

        with patch("app.line.service.send_error_response") as mock_send:
            handle_settings_postback(mock_event, {"action": "settings", "type": "unknown"})

            mock_send.assert_called_once_with("test_token", "未知的設定類型")

    def test_handle_recent_queries_postback_no_history(self) -> None:
        """Test recent queries PostBack when user has no query history."""
        mock_event = Mock(spec=PostbackEvent)
        mock_event.reply_token = "test_token"
        mock_event.source = Mock()
        mock_event.source.user_id = "test_line_user_id"

        with (
            patch("app.line.service.get_session") as mock_get_session,
            patch("app.line.service.get_user_by_line_id") as mock_get_user,
            patch("app.line.service.get_recent_queries") as mock_get_recent,
            patch("app.line.service.send_text_response") as mock_send,
        ):
            mock_session = Mock()
            mock_get_session.return_value = iter([mock_session])
            mock_user = Mock()
            mock_user.id = 1
            mock_get_user.return_value = mock_user
            mock_get_recent.return_value = []  # No recent queries

            handle_recent_queries_postback(mock_event)

            mock_send.assert_called_once_with(
                "test_token", "您還沒有查詢過其他地點的天氣\n\n試試看輸入地點名稱來查詢天氣吧！"
            )

    def test_handle_recent_queries_postback_user_not_found(self) -> None:
        """Test recent queries PostBack when user not found - should auto-create user."""
        mock_event = Mock(spec=PostbackEvent)
        mock_event.reply_token = "test_token"
        mock_event.source = Mock()
        mock_event.source.user_id = "test_line_user_id"

        with (
            patch("app.line.service.get_session") as mock_get_session,
            patch("app.line.service.get_user_by_line_id") as mock_get_user,
            patch("app.line.service.create_user_if_not_exists") as mock_create_user,
            patch("app.line.service.get_recent_queries") as mock_get_recent,
            patch("app.line.service.send_text_response") as mock_send,
        ):
            mock_session = Mock()
            mock_get_session.return_value = iter([mock_session])
            mock_get_user.return_value = None  # User not found initially

            # Mock auto-created user
            mock_user = Mock()
            mock_user.id = 1
            mock_create_user.return_value = mock_user
            mock_get_recent.return_value = []  # No recent queries for new user

            handle_recent_queries_postback(mock_event)

            # Verify user was auto-created
            mock_create_user.assert_called_once_with(
                mock_session, "test_line_user_id", display_name=None
            )
            # Verify appropriate message was sent for new user with no history
            mock_send.assert_called_once_with(
                "test_token", "您還沒有查詢過其他地點的天氣\n\n試試看輸入地點名稱來查詢天氣吧！"
            )

    def test_handle_recent_queries_postback_with_history(self) -> None:
        """Test recent queries PostBack with Quick Reply history."""
        mock_event = Mock(spec=PostbackEvent)
        mock_event.reply_token = "test_token"
        mock_event.source = Mock()
        mock_event.source.user_id = "test_line_user_id"

        # Mock recent locations
        mock_location1 = Mock(spec=Location)
        mock_location1.full_name = "台北市中正區"
        mock_location2 = Mock(spec=Location)
        mock_location2.full_name = "新北市板橋區"

        with (
            patch("app.line.service.get_session") as mock_get_session,
            patch("app.line.service.get_user_by_line_id") as mock_get_user,
            patch("app.line.service.get_recent_queries") as mock_get_recent,
            patch("app.line.service.MessagingApi") as mock_messaging_api,
            patch("app.line.service.ApiClient"),
        ):
            mock_session = Mock()
            mock_get_session.return_value = iter([mock_session])
            mock_user = Mock()
            mock_user.id = 1
            mock_get_user.return_value = mock_user
            mock_get_recent.return_value = [mock_location1, mock_location2]

            mock_api_instance = Mock()
            mock_messaging_api.return_value = mock_api_instance

            handle_recent_queries_postback(mock_event)

            # Verify API was called with Quick Reply
            mock_api_instance.reply_message.assert_called_once()
            call_args = mock_api_instance.reply_message.call_args[0]
            request = call_args[0]
            message = request.messages[0]
            assert message.quick_reply is not None
            assert len(message.quick_reply.items) == 2

    def test_handle_recent_queries_postback_no_user_id(self) -> None:
        """Test recent queries PostBack without user ID."""
        mock_event = Mock(spec=PostbackEvent)
        mock_event.reply_token = "test_token"
        mock_event.source = None  # No user_id

        with patch("app.line.service.send_error_response") as mock_send:
            handle_recent_queries_postback(mock_event)

            mock_send.assert_called_once_with("test_token", "用戶識別錯誤")

    def test_handle_recent_queries_postback_api_error(self) -> None:
        """Test recent queries PostBack with API error."""
        mock_event = Mock(spec=PostbackEvent)
        mock_event.reply_token = "test_token"
        mock_event.source = Mock()
        mock_event.source.user_id = "test_line_user_id"

        mock_location = Mock(spec=Location)
        mock_location.full_name = "台北市中正區"

        with (
            patch("app.line.service.get_session") as mock_get_session,
            patch("app.line.service.get_user_by_line_id") as mock_get_user,
            patch("app.line.service.get_recent_queries") as mock_get_recent,
            patch(
                "app.line.service.MessagingApi.reply_message", side_effect=Exception("API Error")
            ),
            patch("app.line.service.send_error_response") as mock_send,
            patch("app.line.service.ApiClient"),
        ):
            mock_session = Mock()
            mock_get_session.return_value = iter([mock_session])
            mock_user = Mock()
            mock_user.id = 1
            mock_get_user.return_value = mock_user
            mock_get_recent.return_value = [mock_location]

            handle_recent_queries_postback(mock_event)

            # Should send fallback error message
            mock_send.assert_called_once_with("test_token", "查詢時發生錯誤，請稍後再試。")

    def test_handle_recent_queries_postback_general_exception(self) -> None:
        """Test recent queries PostBack with general exception."""
        mock_event = Mock(spec=PostbackEvent)
        mock_event.reply_token = "test_token"
        mock_event.source = Mock()
        mock_event.source.user_id = "test_line_user_id"

        with (
            patch("app.line.service.get_session", side_effect=Exception("DB Error")),
            patch("app.line.service.send_error_response") as mock_send,
        ):
            handle_recent_queries_postback(mock_event)

            # Should send general error message
            mock_send.assert_called_once_with("test_token", "系統暫時有點忙，請稍後再試一次。")

    def test_send_text_response_success(self) -> None:
        """Test successful text response sending."""
        with patch("app.line.service.MessagingApi") as mock_messaging_api:
            mock_api_instance = Mock()
            mock_messaging_api.return_value = mock_api_instance

            with patch("app.line.service.ApiClient"):
                send_text_response("test_token", "Hello World")

                mock_api_instance.reply_message.assert_called_once()

    def test_send_text_response_no_reply_token(self) -> None:
        """Test text response with no reply token."""
        # Should return early without API call
        send_text_response(None, "Hello World")
        # No exception should be raised

    def test_send_text_response_api_exception(self) -> None:
        """Test text response with API exception."""
        with patch(
            "app.line.service.MessagingApi.reply_message", side_effect=Exception("API Error")
        ):
            with patch("app.line.service.ApiClient"):
                # Should not raise exception, just log error
                send_text_response("test_token", "Hello World")

    def test_send_location_not_set_response(self) -> None:
        """Test location not set response."""
        with patch("app.line.service.send_text_response") as mock_send:
            send_location_not_set_response("test_token", "住家")

            expected_message = "請先設定住家地址，點擊下方「設定地點」按鈕即可設定。"
            mock_send.assert_called_once_with("test_token", expected_message)

    def test_send_error_response(self) -> None:
        """Test error response."""
        with patch("app.line.service.send_text_response") as mock_send:
            send_error_response("test_token", "錯誤訊息")

            mock_send.assert_called_once_with("test_token", "錯誤訊息")

    def test_handle_other_postback_menu(self) -> None:
        """Test handling other PostBack with menu type."""
        mock_event = Mock(spec=PostbackEvent)
        mock_event.reply_token = "test_reply_token"

        data = {"action": "other", "type": "menu"}

        with patch("app.line.service.send_other_menu_quick_reply") as mock_send:
            handle_other_postback(mock_event, data)
            mock_send.assert_called_once_with("test_reply_token")

    def test_handle_other_postback_announcements(self) -> None:
        """Test handling other PostBack with announcements type."""
        mock_event = Mock(spec=PostbackEvent)
        mock_event.reply_token = "test_reply_token"

        data = {"action": "other", "type": "announcements"}

        with patch("app.line.service.handle_announcements") as mock_handle:
            handle_other_postback(mock_event, data)
            mock_handle.assert_called_once_with("test_reply_token")

    def test_handle_other_postback_unknown_type(self) -> None:
        """Test handling other PostBack with unknown type."""
        mock_event = Mock(spec=PostbackEvent)
        mock_event.reply_token = "test_reply_token"

        data = {"action": "other", "type": "unknown"}

        with patch("app.line.service.send_error_response") as mock_send:
            handle_other_postback(mock_event, data)
            mock_send.assert_called_once_with("test_reply_token", "未知的操作")

    def test_send_other_menu_no_reply_token(self) -> None:
        """Test send other menu with no reply token."""
        # Should return early without processing
        send_other_menu_quick_reply(None)

    def test_send_other_menu_success(self) -> None:
        """Test successful other menu sending."""
        with patch("app.line.service.MessagingApi") as mock_messaging_api:
            mock_api_instance = Mock()
            mock_messaging_api.return_value = mock_api_instance

            with patch("app.line.service.ApiClient"):
                send_other_menu_quick_reply("test_token")

                mock_api_instance.reply_message.assert_called_once()

    def test_send_other_menu_api_error(self) -> None:
        """Test other menu sending with API error."""
        with patch(
            "app.line.service.MessagingApi.reply_message",
            side_effect=Exception("API Error"),
        ):
            with patch("app.line.service.ApiClient"):
                # Should not raise exception, just log error
                send_other_menu_quick_reply("test_token")

    def test_handle_announcements_no_reply_token(self) -> None:
        """Test handle announcements with no reply token."""
        # Should return early without processing
        handle_announcements(None)

    def test_handle_announcements_success(self) -> None:
        """Test successful announcements handling."""
        with patch("app.line.service.Path.exists", return_value=True):
            with patch("app.line.service.Path.open") as mock_open:
                mock_file = Mock()
                mock_file.read.return_value = (
                    '{"announcements": [{"title": "Test", "content": "Test content", '
                    '"date": "2024-01-01"}]}'
                )
                mock_open.return_value.__enter__.return_value = mock_file

                with patch("app.line.service.MessagingApi") as mock_messaging_api:
                    mock_api_instance = Mock()
                    mock_messaging_api.return_value = mock_api_instance

                    with patch("app.line.service.ApiClient"):
                        handle_announcements("test_token")

                        mock_api_instance.reply_message.assert_called_once()
