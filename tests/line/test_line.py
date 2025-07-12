"""Test LINE webhook and service functionality."""

import json
from collections.abc import Callable
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app.line.service import (
    handle_line_events,
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
    async def test_send_reply_message_success(
        self, mock_line_api_response: Callable[..., AsyncMock]
    ) -> None:
        """Test successful reply message sending."""
        mock_response = mock_line_api_response(200)

        with patch("app.core.config.settings.LINE_CHANNEL_ACCESS_TOKEN", "real_token"):
            with patch("httpx.AsyncClient.post", return_value=mock_response) as mock_post:
                await send_reply_message("test_token", "test_message")

                mock_post.assert_called_once()
                args, kwargs = mock_post.call_args
                assert kwargs["json"]["replyToken"] == "test_token"
                assert kwargs["json"]["messages"][0]["text"] == "test_message"

    @pytest.mark.asyncio
    async def test_send_reply_message_api_error(
        self, mock_line_api_response: Callable[..., AsyncMock]
    ) -> None:
        """Test reply message with API error."""
        mock_response = mock_line_api_response(400, "Bad Request")

        with patch("app.core.config.settings.LINE_CHANNEL_ACCESS_TOKEN", "real_token"):
            with patch("httpx.AsyncClient.post", return_value=mock_response):
                # Should not raise exception, just log error
                await send_reply_message("test_token", "test_message")

    @pytest.mark.asyncio
    async def test_send_reply_message_exception(self) -> None:
        """Test reply message with network exception."""
        with patch("app.core.config.settings.LINE_CHANNEL_ACCESS_TOKEN", "real_token"):
            with patch("httpx.AsyncClient.post", side_effect=Exception("Network error")):
                # Should not raise exception, just log error
                await send_reply_message("test_token", "test_message")

    @pytest.mark.asyncio
    async def test_handle_line_events_with_text_message(self, line_text_message_data: dict) -> None:
        """Test handling LINE events with text message."""
        with patch("app.line.service.send_reply_message") as mock_send:
            await handle_line_events(line_text_message_data)
            mock_send.assert_called_once_with("test_token", "Hello")

    @pytest.mark.asyncio
    async def test_handle_line_events_non_text_message(self, line_image_message_data: dict) -> None:
        """Test handling LINE events with non-text message."""
        with patch("app.line.service.send_reply_message") as mock_send:
            await handle_line_events(line_image_message_data)
            mock_send.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_line_events_non_message_event(self, line_follow_event_data: dict) -> None:
        """Test handling LINE events with non-message event."""
        with patch("app.line.service.send_reply_message") as mock_send:
            await handle_line_events(line_follow_event_data)
            mock_send.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_line_events_invalid_webhook(
        self, line_invalid_webhook_data: dict
    ) -> None:
        """Test handling invalid webhook body."""
        # Should not raise exception, just log error and return
        await handle_line_events(line_invalid_webhook_data)

    @pytest.mark.asyncio
    async def test_process_webhook_body_success(self, line_text_message_data: dict) -> None:
        """Test processing webhook body successfully."""
        body = json.dumps(line_text_message_data).encode("utf-8")

        with patch("app.line.service.handle_line_events") as mock_handle:
            await process_webhook_body(body)
            mock_handle.assert_called_once_with(line_text_message_data)

    @pytest.mark.asyncio
    async def test_process_webhook_body_invalid_json(self) -> None:
        """Test processing invalid JSON webhook body."""
        invalid_body = b"invalid json"

        # Should raise JSONDecodeError
        with pytest.raises(json.JSONDecodeError):
            await process_webhook_body(invalid_body)
