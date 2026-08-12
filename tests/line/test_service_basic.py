"""Test basic LINE service functionality."""

from collections.abc import Callable
from unittest.mock import Mock, patch

from linebot.v3.webhooks import (
    FollowEvent,
    UnfollowEvent,
)

from app.core.config import settings
from app.line.service import (
    handle_current_location_weather,
    handle_default_event,
    handle_follow_event,
    handle_location_message_event,
    handle_message_event,
    handle_unfollow_event,
    send_liff_location_setting_response,
)


class TestLineService:
    """Test LINE webhook handler functions."""

    def test_handle_message_event_non_text_message(
        self, create_mock_message_event: Callable[..., Mock]
    ) -> None:
        """Test handling non-text message events."""
        # Create mock event with non-text message
        mock_event = create_mock_message_event()
        mock_event.message = Mock()  # Not TextMessageContent

        # Should return early without processing
        handle_message_event(mock_event)
        # No exception should be raised

    def test_handle_message_event_empty_reply_token(
        self, create_mock_message_event: Callable[..., Mock]
    ) -> None:
        """Test handling events with empty reply token."""
        mock_event = create_mock_message_event(reply_token=None)

        # Should return early without processing
        handle_message_event(mock_event)
        # No exception should be raised

    def test_handle_message_event_dev_mode(
        self, create_mock_message_event: Callable[..., Mock]
    ) -> None:
        """Test handling message events in development mode."""
        mock_event = create_mock_message_event()

        # In dev mode (CHANGE_ME token), should just log
        handle_message_event(mock_event)
        # No exception should be raised

    def test_handle_default_event(self) -> None:
        """Test handling default events."""
        mock_event = {"type": "unknown", "replyToken": "test_token"}

        # Should just log the event without raising exception
        handle_default_event(mock_event)
        # No exception should be raised

    def test_handle_follow_event_success(
        self,
        create_mock_follow_event: Callable[..., Mock],
        mock_db_session: Mock,
    ) -> None:
        """Test successful follow event handling."""
        mock_event = create_mock_follow_event()

        with patch("app.line.service.SessionLocal") as mock_session_factory:
            mock_session = mock_db_session
            mock_session_factory.return_value.__enter__.return_value = mock_session

            with patch("app.line.service.create_user_if_not_exists") as mock_create_user:
                mock_user = Mock()
                mock_user.id = 1
                mock_create_user.return_value = mock_user

                with patch("app.line.service.MessagingApi.reply_message") as mock_reply:

                    def assert_session_closed_before_reply(
                        *_args: object, **_kwargs: object
                    ) -> None:
                        """Verify the LINE API call starts after the Session scope ends."""
                        mock_session_factory.return_value.__exit__.assert_called_once()

                    mock_reply.side_effect = assert_session_closed_before_reply
                    handle_follow_event(mock_event)

                    mock_create_user.assert_called_once_with(mock_session, "test_user_id")
                    mock_reply.assert_called_once()
                    mock_session_factory.return_value.__exit__.assert_called_once()

    def test_handle_follow_event_no_user_id(
        self, create_mock_follow_event: Callable[..., Mock]
    ) -> None:
        """Test follow event without user_id."""
        mock_event = create_mock_follow_event()
        mock_event.source = None

        # Should return early without processing
        handle_follow_event(mock_event)
        # No exception should be raised

    def test_handle_follow_event_no_reply_token(
        self,
        create_mock_follow_event: Callable[..., Mock],
        mock_db_session: Mock,
    ) -> None:
        """Test follow event without reply token."""
        mock_event = create_mock_follow_event(reply_token=None)

        with patch("app.line.service.SessionLocal") as mock_session_factory:
            mock_session = mock_db_session
            mock_session_factory.return_value.__enter__.return_value = mock_session

            with patch("app.line.service.create_user_if_not_exists") as mock_create_user:
                mock_user = Mock()
                mock_user.id = 1
                mock_create_user.return_value = mock_user

                handle_follow_event(mock_event)

                mock_create_user.assert_called_once_with(mock_session, "test_user_id")
                mock_session_factory.return_value.__exit__.assert_called_once()

    def test_handle_follow_event_api_error(self) -> None:
        """Test follow event with messaging API error."""
        mock_event = Mock(spec=FollowEvent)
        mock_event.reply_token = "test_token"
        mock_source = Mock()
        mock_source.user_id = "test_user_id"
        mock_event.source = mock_source

        with patch("app.line.service.SessionLocal") as mock_session_factory:
            mock_session = Mock()
            mock_session_factory.return_value.__enter__.return_value = mock_session

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
                    mock_session_factory.return_value.__exit__.assert_called_once()

    def test_handle_unfollow_event_success(
        self,
        create_mock_unfollow_event: Callable[..., Mock],
        mock_db_session: Mock,
    ) -> None:
        """Test successful unfollow event handling."""
        mock_event = create_mock_unfollow_event()

        with patch("app.line.service.SessionLocal") as mock_session_factory:
            mock_session = mock_db_session
            mock_session_factory.return_value.__enter__.return_value = mock_session

            with patch("app.line.service.deactivate_user") as mock_deactivate_user:
                mock_user = Mock()
                mock_user.id = 1
                mock_deactivate_user.return_value = mock_user

                handle_unfollow_event(mock_event)

                mock_deactivate_user.assert_called_once_with(mock_session, "test_user_id")
                mock_session_factory.return_value.__exit__.assert_called_once()

    def test_handle_unfollow_event_user_not_found(self) -> None:
        """Test unfollow event for unknown user."""
        mock_event = Mock(spec=UnfollowEvent)
        mock_source = Mock()
        mock_source.user_id = "test_user_id"
        mock_event.source = mock_source

        with patch("app.line.service.SessionLocal") as mock_session_factory:
            mock_session = Mock()
            mock_session_factory.return_value.__enter__.return_value = mock_session

            with patch("app.line.service.deactivate_user") as mock_deactivate_user:
                mock_deactivate_user.return_value = None

                handle_unfollow_event(mock_event)

                mock_deactivate_user.assert_called_once_with(mock_session, "test_user_id")
                mock_session_factory.return_value.__exit__.assert_called_once()

    def test_handle_unfollow_event_no_user_id(self) -> None:
        """Test unfollow event without user_id."""
        mock_event = Mock(spec=UnfollowEvent)
        mock_event.source = None

        # Should return early without processing
        handle_unfollow_event(mock_event)
        # No exception should be raised

    def test_handle_follow_event_exception(
        self, create_mock_follow_event: Callable[..., Mock]
    ) -> None:
        """Test follow event with general exception."""
        mock_event = create_mock_follow_event()

        with patch(
            "app.line.service.SessionLocal",
            side_effect=Exception("Database error"),
        ):
            # Should not raise exception, just log error
            handle_follow_event(mock_event)

    def test_handle_unfollow_event_exception(
        self, create_mock_unfollow_event: Callable[..., Mock]
    ) -> None:
        """Test unfollow event with general exception."""
        mock_event = create_mock_unfollow_event()

        with patch(
            "app.line.service.SessionLocal",
            side_effect=Exception("Database error"),
        ):
            # Should not raise exception, just log error
            handle_unfollow_event(mock_event)

    def test_send_liff_location_setting_response_success(self) -> None:
        """Test successful LIFF location setting response."""

        with patch("app.line.messaging.MessagingApi") as mock_messaging_api:
            mock_api_instance = Mock()
            mock_messaging_api.return_value = mock_api_instance

            with patch("app.line.messaging.ApiClient"):
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
            "app.line.messaging.MessagingApi.reply_message",
            side_effect=Exception("API Error"),
        ):
            with patch("app.line.messaging.ApiClient"):
                # Should not raise exception, just log error
                send_liff_location_setting_response("test_token")

    def test_send_liff_location_setting_response_no_reply_token(self) -> None:
        """Test LIFF location setting response with no reply token."""
        # Should return early without API call
        send_liff_location_setting_response(None)
        # No exception should be raised


class TestLocationMessageHandler:
    """Test location message handler functionality."""

    def test_handle_location_message_event_empty_reply_token(
        self, create_mock_location_message_event: Callable[..., Mock]
    ) -> None:
        """Test location message handling with empty reply token."""
        mock_event = create_mock_location_message_event(reply_token=None)

        # Should return early without processing
        handle_location_message_event(mock_event)

    def test_handle_location_message_event_wrong_message_type(
        self, create_mock_location_message_event: Callable[..., Mock]
    ) -> None:
        """Test location message handling with wrong message type."""
        mock_event = create_mock_location_message_event()
        mock_event.message = Mock()  # Not LocationMessageContent

        # Should return early without processing
        handle_location_message_event(mock_event)


class TestCurrentLocationWeatherHandler:
    """Test current location weather handler functionality."""

    def test_handle_current_location_weather_no_reply_token(self) -> None:
        """Test current location weather with no reply token."""
        from linebot.v3.webhooks import PostbackEvent

        mock_event = Mock(spec=PostbackEvent)
        mock_event.reply_token = None

        # Should return early without processing
        handle_current_location_weather(mock_event)

    def test_handle_current_location_weather_success(self) -> None:
        """Test successful current location weather request."""
        from linebot.v3.webhooks import PostbackEvent

        mock_event = Mock(spec=PostbackEvent)
        mock_event.reply_token = "test_token"

        with patch("app.line.postback.MessagingApi") as mock_messaging_api:
            mock_api_instance = Mock()
            mock_messaging_api.return_value = mock_api_instance

            with patch("app.line.postback.ApiClient"):
                handle_current_location_weather(mock_event)

                mock_api_instance.reply_message.assert_called_once()

    def test_handle_current_location_weather_api_error(self) -> None:
        """Test current location weather with API error."""
        from linebot.v3.webhooks import PostbackEvent

        mock_event = Mock(spec=PostbackEvent)
        mock_event.reply_token = "test_token"

        with patch(
            "app.line.postback.MessagingApi.reply_message",
            side_effect=Exception("API Error"),
        ):
            with patch("app.line.postback.ApiClient"):
                # Should not raise exception, just log error
                handle_current_location_weather(mock_event)
