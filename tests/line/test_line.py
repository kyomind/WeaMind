"""Test LINE webhook and service functionality."""

from collections.abc import Callable
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient
from linebot.v3.webhooks import FollowEvent, MessageEvent, TextMessageContent, UnfollowEvent

from app.core.config import settings
from app.line.service import (
    handle_default_event,
    handle_follow_event,
    handle_message_event,
    handle_unfollow_event,
    send_liff_location_setting_response,
)
from app.weather.models import Location


class TestLineWebhook:
    """Test LINE webhook endpoint."""

    def test_invalid_content_type(self, client: TestClient) -> None:
        """Test webhook with invalid content type."""
        response = client.post(
            "/line/webhook",
            content=b"{}",
            headers={"X-Line-Signature": "test", "Content-Type": "text/plain"},
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "Invalid content type"

    def test_webhook_processing_error(
        self, client: TestClient, generate_line_signature: Callable[[bytes], str]
    ) -> None:
        """Test webhook processing error handling."""
        body = b'{"invalid": "json"}'
        signature = generate_line_signature(body)

        response = client.post(
            "/line/webhook",
            content=body,
            headers={"X-Line-Signature": signature, "Content-Type": "application/json"},
        )
        # Invalid webhook data should return 200 to stop LINE from retrying
        assert response.status_code == 200
        assert response.json() == {"message": "OK"}

    def test_webhook_processing_success(
        self, client: TestClient, generate_line_signature: Callable[[bytes], str]
    ) -> None:
        """Test successful webhook processing."""
        # Valid LINE webhook payload with text message
        body = (
            b'{"events":[{"type":"message","replyToken":"test_token",'
            b'"message":{"type":"text","text":"Hello"}}]}'
        )
        signature = generate_line_signature(body)

        # Mock the webhook handler to not raise any exceptions
        with patch("app.line.service.webhook_handler.handle"):
            response = client.post(
                "/line/webhook",
                content=body,
                headers={"X-Line-Signature": signature, "Content-Type": "application/json"},
            )
            assert response.status_code == 200
            assert response.json() == {"message": "OK"}

    def test_webhook_invalid_signature(self, client: TestClient) -> None:
        """Test webhook with invalid signature."""
        body = b'{"events":[]}'

        response = client.post(
            "/line/webhook",
            content=body,
            headers={"X-Line-Signature": "invalid_signature", "Content-Type": "application/json"},
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "Invalid signature"


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


class TestQuickReplyFeature:
    """Test Quick Reply functionality for location selection."""

    def test_handle_message_event_with_multiple_locations(self) -> None:
        """Test message handling with multiple location results creates Quick Reply."""
        mock_event = Mock(spec=MessageEvent)
        mock_event.reply_token = "test_reply_token"
        mock_message = Mock(spec=TextMessageContent)
        mock_message.text = "永和"
        mock_event.message = mock_message

        # Mock locations returned by service
        mock_location1 = Mock(spec=Location)
        mock_location1.full_name = "新北市永和區"
        mock_location2 = Mock(spec=Location)
        mock_location2.full_name = "臺南市永和區"

        with patch("app.line.service.get_session") as mock_get_session:
            mock_session = Mock()
            mock_get_session.return_value = iter([mock_session])

            with patch(
                "app.line.service.LocationService.parse_location_input"
            ) as mock_parse_location:
                # Mock returning 2 locations (triggers Quick Reply)
                mock_parse_location.return_value = (
                    [mock_location1, mock_location2],
                    "😕 找到多個符合的地點，請選擇：",
                )

                with patch("app.line.service.MessagingApi") as mock_messaging_api:
                    mock_api_instance = Mock()
                    mock_messaging_api.return_value = mock_api_instance

                    with patch("app.line.service.ApiClient"):
                        handle_message_event(mock_event)

                        # Verify the reply_message was called with Quick Reply
                        mock_api_instance.reply_message.assert_called_once()
                        call_args = mock_api_instance.reply_message.call_args[0]
                        request = call_args[0]  # First positional argument

                        # Check that the message includes Quick Reply
                        message = request.messages[0]
                        assert hasattr(message, "quick_reply")
                        quick_reply = message.quick_reply
                        assert quick_reply is not None

                        assert len(quick_reply.items) == 2

                        # Check Quick Reply items
                        quick_reply_items = quick_reply.items
                        assert quick_reply_items[0].action.text == "新北市永和區"
                        assert quick_reply_items[1].action.text == "臺南市永和區"

    def test_handle_message_event_single_location_no_quick_reply(self) -> None:
        """Test message handling with single location result (no Quick Reply)."""
        mock_event = Mock(spec=MessageEvent)
        mock_event.reply_token = "test_reply_token"
        mock_message = Mock(spec=TextMessageContent)
        mock_message.text = "臺北市"
        mock_event.message = mock_message

        mock_location = Mock(spec=Location)
        mock_location.full_name = "臺北市中山區"

        with patch("app.line.service.get_session") as mock_get_session:
            mock_session = Mock()
            mock_get_session.return_value = iter([mock_session])

            with patch(
                "app.line.service.LocationService.parse_location_input"
            ) as mock_parse_location:
                # Mock returning 1 location (no Quick Reply)
                mock_parse_location.return_value = (
                    [mock_location],
                    "找到了 臺北市中山區，正在查詢天氣...",
                )

                with patch("app.line.service.MessagingApi") as mock_messaging_api:
                    mock_api_instance = Mock()
                    mock_messaging_api.return_value = mock_api_instance

                    with patch("app.line.service.ApiClient"):
                        handle_message_event(mock_event)

                        # Verify the reply_message was called without Quick Reply
                        mock_api_instance.reply_message.assert_called_once()
                        call_args = mock_api_instance.reply_message.call_args[0]
                        request = call_args[0]  # First positional argument

                        # Check that there's no Quick Reply
                        message = request.messages[0]
                        assert message.quick_reply is None


class TestPostBackEventHandlers:
    """Test PostBack event handlers for Rich Menu functionality."""

    def test_parse_postback_data_success(self) -> None:
        """Test successful PostBack data parsing."""
        from app.line.service import parse_postback_data

        # Test weather action
        result = parse_postback_data("action=weather&type=home")
        assert result == {"action": "weather", "type": "home"}

        # Test recent queries action
        result = parse_postback_data("action=recent_queries")
        assert result == {"action": "recent_queries"}

        # Test menu action
        result = parse_postback_data("action=menu&type=more")
        assert result == {"action": "menu", "type": "more"}

    def test_parse_postback_data_empty(self) -> None:
        """Test parsing empty PostBack data."""
        from app.line.service import parse_postback_data

        result = parse_postback_data("")
        assert result == {}

    def test_parse_postback_data_invalid(self) -> None:
        """Test parsing invalid PostBack data."""
        from app.line.service import parse_postback_data

        result = parse_postback_data("invalid_format")
        # Should return empty dictionary for invalid format
        assert result == {}

    def test_handle_postback_event_no_reply_token(self) -> None:
        """Test PostBack event without reply token."""
        from linebot.v3.webhooks import PostbackEvent

        from app.line.service import handle_postback_event

        mock_event = Mock(spec=PostbackEvent)
        mock_event.reply_token = None
        mock_event.postback = Mock()
        mock_event.postback.data = "action=weather&type=home"

        # Should return early without processing
        handle_postback_event(mock_event)
        # No exception should be raised

    def test_handle_postback_event_no_user_id(self) -> None:
        """Test PostBack event without user ID."""
        from linebot.v3.webhooks import PostbackEvent

        from app.line.service import handle_postback_event

        mock_event = Mock(spec=PostbackEvent)
        mock_event.reply_token = "test_token"
        mock_event.postback = Mock()
        mock_event.postback.data = "action=weather&type=home"
        mock_event.source = None

        # Should return early without processing
        handle_postback_event(mock_event)
        # No exception should be raised

    def test_handle_weather_postback_home_success(self) -> None:
        """Test successful home weather PostBack."""
        from linebot.v3.webhooks import PostbackEvent

        from app.line.service import handle_weather_postback
        from app.user.models import User

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
        from linebot.v3.webhooks import PostbackEvent

        from app.line.service import handle_weather_postback
        from app.user.models import User

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
        from linebot.v3.webhooks import PostbackEvent

        from app.line.service import handle_weather_postback
        from app.user.models import User

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
        """Test weather PostBack when user not found."""
        from linebot.v3.webhooks import PostbackEvent

        from app.line.service import handle_weather_postback

        mock_event = Mock(spec=PostbackEvent)
        mock_event.reply_token = "test_token"

        with patch("app.line.service.get_session") as mock_get_session:
            mock_session = Mock()
            mock_get_session.return_value = iter([mock_session])

            with patch("app.line.service.get_user_by_line_id", return_value=None):
                with patch("app.line.service.send_error_response") as mock_send:
                    handle_weather_postback(
                        mock_event, "test_user_id", {"action": "weather", "type": "home"}
                    )

                    mock_send.assert_called_once_with("test_token", "用戶不存在，請重新加入好友")

    def test_handle_current_location_weather_placeholder(self) -> None:
        """Test current location weather placeholder."""
        from linebot.v3.webhooks import PostbackEvent

        from app.line.service import handle_current_location_weather

        mock_event = Mock(spec=PostbackEvent)
        mock_event.reply_token = "test_token"

        with patch("app.line.service.send_text_response") as mock_send:
            handle_current_location_weather(mock_event)

            mock_send.assert_called_once_with("test_token", "📍 目前位置功能即將推出，敬請期待！")

    def test_handle_recent_queries_postback_placeholder(self) -> None:
        """Test recent queries PostBack placeholder."""
        from linebot.v3.webhooks import PostbackEvent

        from app.line.service import handle_recent_queries_postback

        mock_event = Mock(spec=PostbackEvent)
        mock_event.reply_token = "test_token"

        with patch("app.line.service.send_text_response") as mock_send:
            handle_recent_queries_postback(mock_event)

            mock_send.assert_called_once_with("test_token", "📜 最近查過功能即將推出，敬請期待！")

    def test_handle_menu_postback_placeholder(self) -> None:
        """Test menu PostBack placeholder."""
        from linebot.v3.webhooks import PostbackEvent

        from app.line.service import handle_menu_postback

        mock_event = Mock(spec=PostbackEvent)
        mock_event.reply_token = "test_token"

        with patch("app.line.service.send_text_response") as mock_send:
            handle_menu_postback(mock_event, {"type": "more"})

            mock_send.assert_called_once_with("test_token", "📢 更多功能即將推出，敬請期待！")

    def test_send_text_response_success(self) -> None:
        """Test successful text response sending."""
        from app.line.service import send_text_response

        with patch("app.line.service.MessagingApi") as mock_messaging_api:
            mock_api_instance = Mock()
            mock_messaging_api.return_value = mock_api_instance

            with patch("app.line.service.ApiClient"):
                send_text_response("test_token", "Hello World")

                mock_api_instance.reply_message.assert_called_once()

    def test_send_text_response_no_reply_token(self) -> None:
        """Test text response with no reply token."""
        from app.line.service import send_text_response

        # Should return early without API call
        send_text_response(None, "Hello World")
        # No exception should be raised

    def test_send_location_not_set_response(self) -> None:
        """Test location not set response."""
        from app.line.service import send_location_not_set_response

        with patch("app.line.service.send_text_response") as mock_send:
            send_location_not_set_response("test_token", "住家")

            expected_message = "請先設定住家地址，點擊下方「設定地點」按鈕即可設定。"
            mock_send.assert_called_once_with("test_token", expected_message)

    def test_send_error_response(self) -> None:
        """Test error response."""
        from app.line.service import send_error_response

        with patch("app.line.service.send_text_response") as mock_send:
            send_error_response("test_token", "錯誤訊息")

            mock_send.assert_called_once_with("test_token", "錯誤訊息")

    def test_send_liff_location_setting_response_no_reply_token(self) -> None:
        """Test LIFF location setting response with no reply token."""
        from app.line.service import send_liff_location_setting_response

        # Should return early without API call
        send_liff_location_setting_response(None)
        # No exception should be raised

    def test_parse_postback_data_exception(self) -> None:
        """Test parsing PostBack data with exception."""
        from app.line.service import parse_postback_data

        with patch("app.line.service.parse_qs", side_effect=Exception("Parse error")):
            result = parse_postback_data("action=weather&type=home")
            assert result == {}

    def test_handle_weather_postback_unknown_type(self) -> None:
        """Test weather PostBack with unknown type."""
        from linebot.v3.webhooks import PostbackEvent

        from app.line.service import handle_weather_postback

        mock_event = Mock(spec=PostbackEvent)
        mock_event.reply_token = "test_token"

        with patch("app.line.service.send_error_response") as mock_send:
            handle_weather_postback(
                mock_event, "test_user_id", {"action": "weather", "type": "unknown"}
            )

            mock_send.assert_called_once_with("test_token", "未知的地點類型")

    def test_handle_user_location_weather_exception(self) -> None:
        """Test user location weather with exception."""
        from linebot.v3.webhooks import PostbackEvent

        from app.line.service import handle_user_location_weather

        mock_event = Mock(spec=PostbackEvent)
        mock_event.reply_token = "test_token"

        with patch("app.line.service.get_session") as mock_get_session:
            mock_session = Mock()
            mock_get_session.return_value = iter([mock_session])

            with patch("app.line.service.get_user_by_line_id", side_effect=Exception("DB error")):
                with patch("app.line.service.send_error_response") as mock_send:
                    handle_user_location_weather(mock_event, "test_user_id", "home")

                    mock_send.assert_called_once_with(
                        "test_token", "😅 查詢時發生錯誤，請稍後再試。"
                    )

    def test_handle_settings_postback_location_type(self) -> None:
        """Test settings PostBack with location type."""
        from linebot.v3.webhooks import PostbackEvent

        from app.line.service import handle_settings_postback

        mock_event = Mock(spec=PostbackEvent)
        mock_event.reply_token = "test_token"

        with patch("app.line.service.send_liff_location_setting_response") as mock_send:
            handle_settings_postback(mock_event, {"action": "settings", "type": "location"})

            mock_send.assert_called_once_with("test_token")

    def test_handle_settings_postback_unknown_type(self) -> None:
        """Test settings PostBack with unknown type."""
        from linebot.v3.webhooks import PostbackEvent

        from app.line.service import handle_settings_postback

        mock_event = Mock(spec=PostbackEvent)
        mock_event.reply_token = "test_token"

        with patch("app.line.service.send_error_response") as mock_send:
            handle_settings_postback(mock_event, {"action": "settings", "type": "unknown"})

            mock_send.assert_called_once_with("test_token", "未知的設定類型")

    def test_handle_postback_event_unknown_action(self) -> None:
        """Test PostBack event with unknown action."""
        from linebot.v3.webhooks import PostbackEvent

        from app.line.service import handle_postback_event

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
        from linebot.v3.webhooks import PostbackEvent

        from app.line.service import handle_postback_event

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

                mock_send.assert_called_once_with(
                    "test_token", "😅 系統暫時有點忙，請稍後再試一次。"
                )

    def test_send_text_response_api_exception(self) -> None:
        """Test text response with API exception."""
        from app.line.service import send_text_response

        with patch(
            "app.line.service.MessagingApi.reply_message", side_effect=Exception("API Error")
        ):
            with patch("app.line.service.ApiClient"):
                # Should not raise exception, just log error
                send_text_response("test_token", "Hello World")

    def test_handle_postback_event_weather_action(self) -> None:
        """Test PostBack event with weather action."""
        from linebot.v3.webhooks import PostbackEvent

        from app.line.service import handle_postback_event

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
        from linebot.v3.webhooks import PostbackEvent

        from app.line.service import handle_postback_event

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
        from linebot.v3.webhooks import PostbackEvent

        from app.line.service import handle_postback_event

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

    def test_handle_postback_event_menu_action(self) -> None:
        """Test PostBack event with menu action."""
        from linebot.v3.webhooks import PostbackEvent

        from app.line.service import handle_postback_event

        mock_event = Mock(spec=PostbackEvent)
        mock_event.reply_token = "test_token"
        mock_event.postback = Mock()
        mock_event.postback.data = "action=menu&type=more"
        mock_source = Mock()
        mock_source.user_id = "test_user_id"
        mock_event.source = mock_source

        with patch("app.line.service.handle_menu_postback") as mock_handle:
            handle_postback_event(mock_event)

            mock_handle.assert_called_once_with(mock_event, {"action": "menu", "type": "more"})

    def test_handle_weather_postback_current_location(self) -> None:
        """Test weather PostBack with current location."""
        from linebot.v3.webhooks import PostbackEvent

        from app.line.service import handle_weather_postback

        mock_event = Mock(spec=PostbackEvent)
        mock_event.reply_token = "test_token"

        with patch("app.line.service.handle_current_location_weather") as mock_handle:
            handle_weather_postback(
                mock_event, "test_user_id", {"action": "weather", "type": "current"}
            )

            mock_handle.assert_called_once_with(mock_event)
