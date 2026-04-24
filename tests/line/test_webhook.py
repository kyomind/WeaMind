"""Test LINE webhook endpoint functionality."""

import json
from collections.abc import Callable
from unittest.mock import patch

from fastapi.testclient import TestClient


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

        with patch("app.line.router.line_metrics.record_webhook_received") as mock_received:
            with patch("app.line.service.line_metrics.record_webhook_error") as mock_error:
                with patch(
                    "app.line.service.line_metrics.record_webhook_duration"
                ) as mock_duration:
                    response = client.post(
                        "/line/webhook",
                        content=body,
                        headers={"X-Line-Signature": signature, "Content-Type": "application/json"},
                    )

        # Invalid webhook data should return 200 to stop LINE from retrying
        assert response.status_code == 200
        assert response.json() == {"message": "OK"}
        mock_received.assert_called_once_with(["unknown"])
        mock_error.assert_called_once_with(["unknown"], "handler_error")
        mock_duration.assert_called_once()

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

        with patch("app.line.router.process_webhook_events") as mock_process_webhook_events:
            with patch("app.line.router.line_metrics.record_webhook_received") as mock_received:
                response = client.post(
                    "/line/webhook",
                    content=body,
                    headers={
                        "X-Line-Signature": signature,
                        "Content-Type": "application/json",
                    },
                )

        assert response.status_code == 200
        assert response.json() == {"message": "OK"}
        mock_received.assert_called_once_with(["message_text"])
        mock_process_webhook_events.assert_called_once_with(
            body.decode(), signature, ["message_text"]
        )

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

    def test_webhook_signature_computation_error(self, client: TestClient) -> None:
        """Test webhook signature computation error."""
        body = b'{"events":[]}'

        with patch("hmac.new") as mock_hmac:
            # Mock hmac to raise exception during signature computation
            mock_hmac.side_effect = Exception("HMAC computation failed")

            response = client.post(
                "/line/webhook",
                content=body,
                headers={"X-Line-Signature": "test_signature", "Content-Type": "application/json"},
            )
            assert response.status_code == 400
            assert response.json()["detail"] == "Signature verification error"

    def test_webhook_records_follow_event_type(
        self, client: TestClient, generate_line_signature: Callable[[bytes], str]
    ) -> None:
        """Test webhook metrics classify a follow event correctly."""
        body = json.dumps({"events": [{"type": "follow", "replyToken": "test_token"}]}).encode()
        signature = generate_line_signature(body)

        with patch("app.line.router.process_webhook_events"):
            with patch("app.line.router.line_metrics.record_webhook_received") as mock_received:
                response = client.post(
                    "/line/webhook",
                    content=body,
                    headers={"X-Line-Signature": signature, "Content-Type": "application/json"},
                )

        assert response.status_code == 200
        mock_received.assert_called_once_with(["follow"])
