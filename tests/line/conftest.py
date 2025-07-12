"""Test fixtures for LINE Bot module testing."""

import base64
import hashlib
import hmac
from collections.abc import Callable

import pytest


@pytest.fixture()
def generate_line_signature() -> Callable[[bytes], str]:
    """
    Generate a LINE webhook signature for testing.
    """

    def _generate(body: bytes) -> str:
        digest = hmac.new(b"TEST_SECRET", body, hashlib.sha256).digest()
        return base64.b64encode(digest).decode()

    return _generate


@pytest.fixture()
def line_text_message_data() -> dict:
    """
    Return a standard text message webhook body for testing.
    """
    return {
        "events": [
            {
                "type": "message",
                "replyToken": "test_token",
                "message": {"type": "text", "text": "Hello"},
            }
        ]
    }


@pytest.fixture()
def line_image_message_data() -> dict:
    """
    Return a non-text (image) message webhook body for testing.
    """
    return {
        "events": [{"type": "message", "replyToken": "test_token", "message": {"type": "image"}}]
    }


@pytest.fixture()
def line_follow_event_data() -> dict:
    """
    Return a follow event webhook body for testing.
    """
    return {"events": [{"type": "follow", "replyToken": "test_token"}]}


@pytest.fixture()
def line_invalid_webhook_data() -> dict:
    """
    Return an invalid webhook body for testing error handling.
    """
    return {"invalid": "data"}
