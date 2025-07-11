import base64
import hashlib
import hmac
import os
import sys
from collections.abc import Callable
from pathlib import Path
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"
os.environ["LINE_CHANNEL_SECRET"] = "TEST_SECRET"

sys.path.append(str(Path(__file__).resolve().parent))

from app.core.database import Base, engine
from app.main import app

# Import models so SQLAlchemy registers tables correctly even if unused
from app.user import models  # noqa: F401

Base.metadata.create_all(bind=engine)
# Use a module-level singleton instead of creating a new client per fixture
_client = TestClient(app)


@pytest.fixture()
def client() -> TestClient:
    """
    Provide a FastAPI test client
    """
    return _client


@pytest.fixture()
def create_user(client: TestClient) -> Callable[..., dict]:
    """
    Return a helper for creating test users

    Reasons for returning a helper instead of the user object:
    1. Flexibility to create different display names or multiple users
    2. Supports creating users multiple times in one test
    3. Fewer fixtures to maintain and extend
    """

    def _create(display_name: str = "Alice") -> dict:
        data = {"line_user_id": str(uuid4()), "display_name": display_name}
        response = client.post("/users", json=data)
        assert response.status_code == 201  # noqa: S101
        return response.json()

    return _create


@pytest.fixture()
def generate_line_signature() -> Callable[[bytes], str]:
    """
    Generate a LINE webhook signature for testing
    """

    def _generate(body: bytes) -> str:
        digest = hmac.new(b"TEST_SECRET", body, hashlib.sha256).digest()
        return base64.b64encode(digest).decode()

    return _generate


@pytest.fixture()
def line_text_message_data() -> dict:
    """
    Return a standard text message webhook body for testing
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
    Return a non-text (image) message webhook body for testing
    """
    return {
        "events": [{"type": "message", "replyToken": "test_token", "message": {"type": "image"}}]
    }


@pytest.fixture()
def line_follow_event_data() -> dict:
    """
    Return a follow event webhook body for testing
    """
    return {"events": [{"type": "follow", "replyToken": "test_token"}]}


@pytest.fixture()
def line_invalid_webhook_data() -> dict:
    """
    Return an invalid webhook body for testing error handling
    """
    return {"invalid": "data"}


@pytest.fixture()
def mock_line_api_response() -> Callable[..., AsyncMock]:
    """
    Create a mock LINE API response for testing
    """

    def _create(status_code: int = 200, text: str = "OK") -> AsyncMock:
        mock_response = AsyncMock()
        mock_response.status_code = status_code
        mock_response.text = text
        return mock_response

    return _create
