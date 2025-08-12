"""Test LINE webhook and service functionality."""

from collections.abc import Callable
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient
from linebot.v3.webhooks import FollowEvent, MessageEvent, TextMessageContent, UnfollowEvent

from app.line.service import (
    handle_default_event,
    handle_follow_event,
    handle_message_event,
    handle_unfollow_event,
)


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
            with patch(
                "app.line.service.MessagingApi.reply_message", side_effect=Exception("API Error")
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

        with patch("app.line.service.get_db") as mock_get_db:
            mock_session = Mock()
            mock_get_db.return_value = iter([mock_session])

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

        with patch("app.line.service.get_db") as mock_get_db:
            mock_session = Mock()
            mock_get_db.return_value = iter([mock_session])

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

        with patch("app.line.service.get_db") as mock_get_db:
            mock_session = Mock()
            mock_get_db.return_value = iter([mock_session])

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

        with patch("app.line.service.get_db") as mock_get_db:
            mock_session = Mock()
            mock_get_db.return_value = iter([mock_session])

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

        with patch("app.line.service.get_db") as mock_get_db:
            mock_session = Mock()
            mock_get_db.return_value = iter([mock_session])

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
