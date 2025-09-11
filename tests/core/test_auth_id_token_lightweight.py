"""Lightweight ID token checks (signature disabled) additional tests."""

import base64
import json
import time

import pytest
from fastapi import HTTPException

from app.core import auth as auth_module


def _b64url_no_pad(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode().rstrip("=")


def _make_token(header: dict, payload: dict) -> str:
    return (
        f"{_b64url_no_pad(json.dumps(header).encode())}."
        f"{_b64url_no_pad(json.dumps(payload).encode())}.sig"
    )


def test_lightweight_audience_as_list_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Signature disabled: aud as list passes when it contains the channel id."""
    # Ensure lightweight path
    auth_module.settings.ENABLE_ID_TOKEN_SIGNATURE_VERIFICATION = False  # type: ignore[attr-defined]
    # Provide a channel id so aud check is enabled
    auth_module.settings.LINE_CHANNEL_ID = "chan-x"  # type: ignore[attr-defined]

    now = int(time.time())
    header = {"alg": "RS256", "typ": "JWT"}
    payload = {
        "iss": "https://access.line.me",
        "sub": "U" + "a" * 32,
        "exp": now + 3600,
        "aud": ["foo", "chan-x", "bar"],
    }

    token = _make_token(header, payload)
    user_id = auth_module.verify_line_id_token(token)
    assert user_id == payload["sub"]


def test_invalid_header_base64() -> None:
    """Invalid base64 header triggers 'Invalid header' branch (401)."""
    auth_module.settings.ENABLE_ID_TOKEN_SIGNATURE_VERIFICATION = False  # type: ignore[attr-defined]
    # Craft invalid base64 in header part
    bad_header = "!not_base64!"
    now = int(time.time())
    payload = {
        "iss": "https://access.line.me",
        "sub": "U" + "b" * 32,
        "exp": now + 3600,
    }
    payload_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().rstrip("=")
    token = f"{bad_header}.{payload_b64}.sig"

    with pytest.raises(HTTPException):  # header decode fails → HTTPException
        auth_module.verify_line_id_token(token)


def test_production_safeguard_disabled_signature(monkeypatch: pytest.MonkeyPatch) -> None:
    """In production, disabling signature verification should raise 500."""
    # Simulate production
    auth_module.settings.ENV = "production"  # type: ignore[attr-defined]
    auth_module.settings.ENABLE_ID_TOKEN_SIGNATURE_VERIFICATION = False  # type: ignore[attr-defined]
    auth_module.settings.LINE_CHANNEL_ID = "123"  # type: ignore[attr-defined]

    header = {"alg": "RS256", "typ": "JWT"}
    payload = {
        "iss": "https://access.line.me",
        "sub": "U" + "c" * 32,
        "exp": int(time.time()) + 3600,
    }
    token = _make_token(header, payload)

    with pytest.raises(HTTPException):
        auth_module.verify_line_id_token(token)
    # Reset ENV
    auth_module.settings.ENV = "development"  # type: ignore[attr-defined]


def test_production_safeguard_missing_channel_id(monkeypatch: pytest.MonkeyPatch) -> None:
    """In production, missing LINE_CHANNEL_ID should raise 500."""
    auth_module.settings.ENV = "production"  # type: ignore[attr-defined]
    auth_module.settings.ENABLE_ID_TOKEN_SIGNATURE_VERIFICATION = True  # type: ignore[attr-defined]
    auth_module.settings.LINE_CHANNEL_ID = None  # type: ignore[attr-defined]

    header = {"alg": "RS256", "typ": "JWT"}
    payload = {
        "iss": "https://access.line.me",
        "sub": "U" + "d" * 32,
        "exp": int(time.time()) + 3600,
    }
    token = _make_token(header, payload)

    with pytest.raises(HTTPException):
        auth_module.verify_line_id_token(token)
    # Reset ENV
    auth_module.settings.ENV = "development"  # type: ignore[attr-defined]
