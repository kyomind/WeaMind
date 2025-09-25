"""Test fixtures for LINE Bot module testing."""

import base64
import hashlib
import hmac
from collections.abc import Callable
from unittest.mock import Mock

import pytest
from linebot.v3.webhooks import (
    FollowEvent,
    LocationMessageContent,
    MessageEvent,
    PostbackEvent,
    TextMessageContent,
    UnfollowEvent,
)


@pytest.fixture()
def generate_line_signature() -> Callable[[bytes], str]:
    """Generate a LINE webhook signature for testing."""

    def _generate(body: bytes) -> str:
        digest = hmac.new(b"TEST_SECRET", body, hashlib.sha256).digest()
        return base64.b64encode(digest).decode()

    return _generate


@pytest.fixture()
def line_text_message_data() -> dict:
    """Return a standard text message webhook body for testing."""
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
    """Return a non-text (image) message webhook body for testing."""
    return {
        "events": [{"type": "message", "replyToken": "test_token", "message": {"type": "image"}}]
    }


@pytest.fixture()
def line_follow_event_data() -> dict:
    """Return a follow event webhook body for testing."""
    return {"events": [{"type": "follow", "replyToken": "test_token"}]}


@pytest.fixture()
def line_invalid_webhook_data() -> dict:
    """Return an invalid webhook body for testing error handling."""
    return {"invalid": "data"}


# Mock Event Fixtures for Service Testing


@pytest.fixture()
def create_mock_message_event() -> Callable[..., Mock]:
    """Return a helper for creating mock MessageEvent instances."""

    def _create(
        reply_token: str = "test_token",
        text: str = "Hello",
        user_id: str | None = "test_user_id",
    ) -> Mock:
        mock_event = Mock(spec=MessageEvent)
        mock_event.reply_token = reply_token
        mock_event.message = Mock(spec=TextMessageContent)
        mock_event.message.text = text

        if user_id:
            mock_source = Mock()
            mock_source.user_id = user_id
            mock_event.source = mock_source
        else:
            mock_event.source = None

        return mock_event

    return _create


@pytest.fixture()
def create_mock_follow_event() -> Callable[..., Mock]:
    """Return a helper for creating mock FollowEvent instances."""

    def _create(reply_token: str = "test_token", user_id: str = "test_user_id") -> Mock:
        mock_event = Mock(spec=FollowEvent)
        mock_event.reply_token = reply_token

        mock_source = Mock()
        mock_source.user_id = user_id
        mock_event.source = mock_source

        return mock_event

    return _create


@pytest.fixture()
def create_mock_unfollow_event() -> Callable[..., Mock]:
    """Return a helper for creating mock UnfollowEvent instances."""

    def _create(user_id: str = "test_user_id") -> Mock:
        mock_event = Mock(spec=UnfollowEvent)

        mock_source = Mock()
        mock_source.user_id = user_id
        mock_event.source = mock_source

        return mock_event

    return _create


@pytest.fixture()
def create_mock_location_message_event() -> Callable[..., Mock]:
    """Return a helper for creating mock LocationMessageContent MessageEvent instances."""

    def _create(
        reply_token: str = "test_token",
        latitude: float = 25.0330,
        longitude: float = 121.5654,
        address: str | None = None,
        user_id: str = "test_user_id",
    ) -> Mock:
        mock_event = Mock(spec=MessageEvent)
        mock_event.reply_token = reply_token

        mock_message = Mock(spec=LocationMessageContent)
        mock_message.latitude = latitude
        mock_message.longitude = longitude
        mock_message.address = address
        mock_event.message = mock_message

        mock_source = Mock()
        mock_source.user_id = user_id
        mock_event.source = mock_source

        return mock_event

    return _create


@pytest.fixture()
def create_mock_postback_event() -> Callable[..., Mock]:
    """Return a helper for creating mock PostbackEvent instances."""

    def _create(reply_token: str = "test_token") -> Mock:
        mock_event = Mock(spec=PostbackEvent)
        mock_event.reply_token = reply_token

        return mock_event

    return _create


@pytest.fixture()
def mock_db_session() -> Mock:
    """Return a mock database session."""
    return Mock()
