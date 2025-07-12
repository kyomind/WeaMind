"""Test LINE webhook and service functionality."""

from collections.abc import Callable
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient
from linebot.v3.webhooks import MessageEvent, TextMessageContent

from app.line.service import handle_default_event, handle_message_event


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
        mock_event = {"type": "follow", "replyToken": "test_token"}

        # Should just log the event without raising exception
        handle_default_event(mock_event)
        # No exception should be raised
