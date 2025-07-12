"""Test LINE webhook and service functionality."""

import json
from collections.abc import Callable
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.line.service import (
    process_webhook_body,
    send_reply_message,
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


class TestLineService:
    """Test LINE service functions."""

    @pytest.mark.asyncio
    async def test_send_reply_message_dev_mode(self) -> None:
        """Test send_reply_message in development mode."""
        # Should not make actual HTTP request in dev mode
        await send_reply_message("test_token", "test_message")
        # No exception should be raised

    @pytest.mark.asyncio
    async def test_send_reply_message_success(self) -> None:
        """Test successful reply message sending."""
        with patch("app.core.config.settings.LINE_CHANNEL_ACCESS_TOKEN", "real_token"):
            with patch("app.line.service.MessagingApi.reply_message") as mock_reply:
                await send_reply_message("test_token", "test_message")
                mock_reply.assert_called_once()
                # Check that the ReplyMessageRequest was created correctly
                call_args = mock_reply.call_args[0][0]
                assert call_args.reply_token == "test_token"
                assert call_args.messages[0].text == "test_message"

    @pytest.mark.asyncio
    async def test_send_reply_message_api_error(self) -> None:
        """Test reply message with API error."""
        with patch("app.core.config.settings.LINE_CHANNEL_ACCESS_TOKEN", "real_token"):
            with patch(
                "app.line.service.MessagingApi.reply_message",
                side_effect=Exception("API Error")
            ):
                # Should not raise exception, just log error
                await send_reply_message("test_token", "test_message")

    @pytest.mark.asyncio
    async def test_send_reply_message_exception(self) -> None:
        """Test reply message with network exception."""
        with patch("app.core.config.settings.LINE_CHANNEL_ACCESS_TOKEN", "real_token"):
            with patch(
                "app.line.service.MessagingApi.reply_message",
                side_effect=Exception("Network error")
            ):
                # Should not raise exception, just log error
                await send_reply_message("test_token", "test_message")

    @pytest.mark.asyncio
    async def test_handle_line_events_with_text_message(self, line_text_message_data: dict) -> None:
        """Test handling LINE events with text message."""
        body = json.dumps(line_text_message_data).encode("utf-8")
        # Mock the webhook handler's signature validation
        with patch("app.line.service.webhook_handler.handle") as mock_handle:
            await process_webhook_body(body)
            mock_handle.assert_called_once_with(body.decode("utf-8"), "")
        # We can't test the actual send_reply_message call because it happens
        # inside the webhook handler

    @pytest.mark.asyncio
    async def test_handle_line_events_non_text_message(self, line_image_message_data: dict) -> None:
        """Test handling LINE events with non-text message."""
        body = json.dumps(line_image_message_data).encode("utf-8")
        with patch("app.line.service.webhook_handler.handle") as mock_handle:
            await process_webhook_body(body)
            mock_handle.assert_called_once_with(body.decode("utf-8"), "")

    @pytest.mark.asyncio
    async def test_handle_line_events_non_message_event(self, line_follow_event_data: dict) -> None:
        """Test handling LINE events with non-message event."""
        body = json.dumps(line_follow_event_data).encode("utf-8")
        with patch("app.line.service.webhook_handler.handle") as mock_handle:
            await process_webhook_body(body)
            mock_handle.assert_called_once_with(body.decode("utf-8"), "")

    @pytest.mark.asyncio
    async def test_handle_line_events_invalid_webhook(
        self, line_invalid_webhook_data: dict
    ) -> None:
        """Test handling invalid webhook body."""
        # Should not raise exception, just log error and return
        body = json.dumps(line_invalid_webhook_data).encode("utf-8")
        with patch("app.line.service.webhook_handler.handle") as mock_handle:
            await process_webhook_body(body)
            mock_handle.assert_called_once_with(body.decode("utf-8"), "")

    @pytest.mark.asyncio
    async def test_process_webhook_body_success(self, line_text_message_data: dict) -> None:
        """Test processing webhook body successfully."""
        body = json.dumps(line_text_message_data).encode("utf-8")

        with patch("app.line.service.webhook_handler.handle") as mock_handle:
            await process_webhook_body(body)
            mock_handle.assert_called_once_with(body.decode("utf-8"), "")

    @pytest.mark.asyncio
    async def test_process_webhook_body_invalid_json(self) -> None:
        """Test processing invalid JSON webhook body."""
        invalid_body = b"invalid json"

        # Should not raise exception since we're mocking the handler
        with patch("app.line.service.webhook_handler.handle") as mock_handle:
            await process_webhook_body(invalid_body)
            mock_handle.assert_called_once_with(invalid_body.decode("utf-8"), "")
