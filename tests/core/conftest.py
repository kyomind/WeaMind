"""Test fixtures for core module."""

import base64
import json
import time
from collections.abc import Callable
from pathlib import Path

import pytest


@pytest.fixture()
def temp_logs_dir(tmp_path: Path) -> Path:
    """Create a temporary logs directory for testing."""
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    return logs_dir


@pytest.fixture
def create_jwt_token() -> Callable[[str, int], str]:
    """Factory fixture for creating JWT tokens for testing."""

    def _create_token(line_user_id: str, exp_offset: int = 3600) -> str:
        """
        Create a valid JWT token for testing.

        Args:
            line_user_id: The LINE user ID to include in the token
            exp_offset: Expiration time offset in seconds from current time

        Returns:
            A JWT token string
        """
        current_time = int(time.time())

        header = {"alg": "RS256", "typ": "JWT"}
        payload = {
            "iss": "https://access.line.me",
            "sub": line_user_id,
            "exp": current_time + exp_offset,
        }

        # Base64 encode without padding
        header_encoded = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
        payload_encoded = (
            base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
        )
        signature = base64.urlsafe_b64encode(b"dummy_signature").decode().rstrip("=")

        return f"{header_encoded}.{payload_encoded}.{signature}"

    return _create_token


@pytest.fixture
def create_custom_jwt_token() -> Callable[[dict, dict], str]:
    """Factory fixture for creating custom JWT tokens with specific header/payload."""

    def _create_custom_token(header: dict, payload: dict) -> str:
        """
        Create a JWT token with custom header and payload.

        Args:
            header: JWT header dictionary
            payload: JWT payload dictionary

        Returns:
            A JWT token string
        """
        header_encoded = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().rstrip("=")
        payload_encoded = (
            base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
        )
        signature = base64.urlsafe_b64encode(b"dummy_signature").decode().rstrip("=")

        return f"{header_encoded}.{payload_encoded}.{signature}"

    return _create_custom_token
