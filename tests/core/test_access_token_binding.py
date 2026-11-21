"""Test that LINE Access Tokens are bound to the configured LINE Login channel."""

import logging
from collections.abc import Callable, Generator
from typing import Any
from unittest.mock import patch

import httpx
import pytest
from fastapi import HTTPException

from app.core import auth as auth_module
from app.core.auth import verify_line_access_token

LINE_LOGIN_CHANNEL_ID = "1234567890"
FAKE_ACCESS_TOKEN = "fake-access-token-0123456789"
FAKE_USER_ID = "U" + "a" * 32

VERIFY_PATH = "/oauth2/v2.1/verify"
PROFILE_PATH = "/v2/profile"

LineApiHandler = Callable[[httpx.Request], httpx.Response]


@pytest.fixture
def line_login_channel_id(monkeypatch: pytest.MonkeyPatch) -> str:
    """Configure the fake expected LINE Login channel and restore settings at teardown."""
    monkeypatch.setattr(auth_module.settings, "LINE_CHANNEL_ID", LINE_LOGIN_CHANNEL_ID)
    return LINE_LOGIN_CHANNEL_ID


@pytest.fixture
def line_requests() -> list[httpx.Request]:
    """Collect every request that reaches the mocked LINE HTTP boundary."""
    return []


@pytest.fixture
def install_line_api(
    line_requests: list[httpx.Request],
) -> Generator[Callable[[LineApiHandler], None], None, None]:
    """
    Install a handler as the only transport used by `httpx.AsyncClient` in the auth module.

    Real `httpx.AsyncClient` instances are still created, so no traffic leaves the process.
    """
    handlers: list[LineApiHandler] = []
    real_client_class = httpx.AsyncClient

    def handle(request: httpx.Request) -> httpx.Response:
        """Record the request and delegate to the installed handler."""
        line_requests.append(request)
        return handlers[0](request)

    def build_client(*args: Any, **kwargs: Any) -> httpx.AsyncClient:  # noqa: ANN401
        """Build a real client wired to the mocked transport."""
        kwargs["transport"] = httpx.MockTransport(handle)
        return real_client_class(*args, **kwargs)

    with patch("app.core.auth.httpx.AsyncClient", side_effect=build_client):
        yield handlers.append


def make_line_api(verify_json: dict[str, Any], profile_json: dict[str, Any]) -> LineApiHandler:
    """Create a handler answering LINE verify and profile calls with the given JSON bodies."""

    def handler(request: httpx.Request) -> httpx.Response:
        """Answer verify and profile requests; any other path is a test failure."""
        if request.url.path == VERIFY_PATH:
            return httpx.Response(200, json=verify_json)
        if request.url.path == PROFILE_PATH:
            return httpx.Response(200, json=profile_json)
        pytest.fail(f"Unexpected LINE request: {request.url.path}")

    return handler


def requested_paths(line_requests: list[httpx.Request]) -> list[str]:
    """Return the URL paths requested so far, in order."""
    return [request.url.path for request in line_requests]


@pytest.mark.asyncio
async def test_token_from_another_channel_is_rejected_before_profile_lookup(
    line_login_channel_id: str,
    install_line_api: Callable[[LineApiHandler], None],
    line_requests: list[httpx.Request],
) -> None:
    """A token issued to a different, non-empty client_id is rejected with 401."""
    install_line_api(
        make_line_api(
            {"client_id": line_login_channel_id + "9", "expires_in": 3600},
            {"userId": FAKE_USER_ID},
        )
    )

    with pytest.raises(HTTPException) as exc_info:
        await verify_line_access_token(FAKE_ACCESS_TOKEN)

    assert exc_info.value.status_code == 401  # noqa: S101
    assert requested_paths(line_requests) == [VERIFY_PATH]  # noqa: S101


@pytest.mark.asyncio
@pytest.mark.parametrize("configured_channel_id", [None, "", "   "])
@pytest.mark.parametrize("env", ["development", "production"])
async def test_missing_configured_channel_fails_closed_with_500_before_any_request(
    monkeypatch: pytest.MonkeyPatch,
    install_line_api: Callable[[LineApiHandler], None],
    line_requests: list[httpx.Request],
    configured_channel_id: str | None,
    env: str,
) -> None:
    """A missing or blank LINE_CHANNEL_ID is a server error in every mode, not a 401."""
    monkeypatch.setattr(auth_module.settings, "ENV", env)
    monkeypatch.setattr(auth_module.settings, "LINE_CHANNEL_ID", configured_channel_id)
    # Without a configured channel, a token that also lacks client_id must not "match" it
    install_line_api(make_line_api({"expires_in": 3600}, {"userId": FAKE_USER_ID}))

    with pytest.raises(HTTPException) as exc_info:
        await verify_line_access_token(FAKE_ACCESS_TOKEN)

    assert exc_info.value.status_code == 500  # noqa: S101
    assert "configuration" in exc_info.value.detail.lower()  # noqa: S101
    assert FAKE_ACCESS_TOKEN not in exc_info.value.detail  # noqa: S101
    assert line_requests == []  # noqa: S101


@pytest.mark.asyncio
async def test_token_from_configured_channel_returns_user_id(
    line_login_channel_id: str,
    install_line_api: Callable[[LineApiHandler], None],
    line_requests: list[httpx.Request],
) -> None:
    """A non-expired token issued to the configured channel resolves to the LINE user ID."""
    install_line_api(
        make_line_api(
            {"client_id": line_login_channel_id, "expires_in": 3600},
            {"userId": FAKE_USER_ID},
        )
    )

    user_id = await verify_line_access_token(FAKE_ACCESS_TOKEN)

    assert user_id == FAKE_USER_ID  # noqa: S101
    assert requested_paths(line_requests) == [VERIFY_PATH, PROFILE_PATH]  # noqa: S101


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "verify_json",
    [
        pytest.param({"expires_in": 3600}, id="client_id-absent"),
        pytest.param({"client_id": "", "expires_in": 3600}, id="client_id-empty"),
        pytest.param({"client_id": None, "expires_in": 3600}, id="client_id-null"),
        pytest.param({"client_id": 1234567890, "expires_in": 3600}, id="client_id-int"),
        pytest.param(
            {"client_id": [LINE_LOGIN_CHANNEL_ID], "expires_in": 3600}, id="client_id-list"
        ),
        pytest.param({"client_id": LINE_LOGIN_CHANNEL_ID, "expires_in": 0}, id="expired"),
        pytest.param({"client_id": LINE_LOGIN_CHANNEL_ID, "expires_in": -5}, id="expired-negative"),
        pytest.param({"client_id": LINE_LOGIN_CHANNEL_ID}, id="expires_in-absent"),
        pytest.param(
            {"client_id": LINE_LOGIN_CHANNEL_ID, "expires_in": "3600"}, id="expires_in-string"
        ),
    ],
)
async def test_unbound_or_expired_token_is_rejected_before_profile_lookup(
    line_login_channel_id: str,
    install_line_api: Callable[[LineApiHandler], None],
    line_requests: list[httpx.Request],
    verify_json: dict[str, Any],
) -> None:
    """Absent, empty, malformed client_id or an expired token gives 401 without a profile call."""
    assert line_login_channel_id == LINE_LOGIN_CHANNEL_ID  # noqa: S101 - channel is configured
    install_line_api(make_line_api(verify_json, {"userId": FAKE_USER_ID}))

    with pytest.raises(HTTPException) as exc_info:
        await verify_line_access_token(FAKE_ACCESS_TOKEN)

    assert exc_info.value.status_code == 401  # noqa: S101
    assert requested_paths(line_requests) == [VERIFY_PATH]  # noqa: S101


NETWORK_ERROR_DETAIL = "Unable to verify token due to network error"
INVALID_TOKEN_DETAIL = "Invalid LINE Access Token"  # noqa: S105 - fixed error text, not a secret
LEAKY_URL = f"https://api.line.me/oauth2/v2.1/verify?access_token={FAKE_ACCESS_TOKEN}"


def make_failing_line_api(failing_path: str, error: Exception) -> LineApiHandler:
    """Create a handler that raises `error` on `failing_path` and succeeds elsewhere."""

    def handler(request: httpx.Request) -> httpx.Response:
        """Raise the error on the failing path; otherwise answer like a healthy LINE API."""
        if request.url.path == failing_path:
            raise error
        if request.url.path == VERIFY_PATH:
            return httpx.Response(200, json={"client_id": LINE_LOGIN_CHANNEL_ID, "expires_in": 60})
        return httpx.Response(200, json={"userId": FAKE_USER_ID})

    return handler


@pytest.mark.asyncio
@pytest.mark.parametrize("failing_path", [VERIFY_PATH, PROFILE_PATH])
@pytest.mark.parametrize(
    ("error", "expected_status", "expected_detail"),
    [
        pytest.param(
            httpx.ConnectError(f"connection failed for {LEAKY_URL}"),
            503,
            NETWORK_ERROR_DETAIL,
            id="network-error",
        ),
        pytest.param(
            httpx.ReadTimeout(f"timed out, token={FAKE_ACCESS_TOKEN}"),
            503,
            NETWORK_ERROR_DETAIL,
            id="timeout",
        ),
        pytest.param(
            RuntimeError(f"malformed data for {FAKE_ACCESS_TOKEN}"),
            401,
            INVALID_TOKEN_DETAIL,
            id="unexpected-error",
        ),
        pytest.param(
            ValueError(f"bad response from {LEAKY_URL}"),
            401,
            INVALID_TOKEN_DETAIL,
            id="value-error",
        ),
    ],
)
async def test_failures_return_and_log_generic_text_without_credentials(
    line_login_channel_id: str,
    install_line_api: Callable[[LineApiHandler], None],
    caplog: pytest.LogCaptureFixture,
    failing_path: str,
    error: Exception,
    expected_status: int,
    expected_detail: str,
) -> None:
    """Transport or data errors keep their status but never expose the token or exception text."""
    assert line_login_channel_id == LINE_LOGIN_CHANNEL_ID  # noqa: S101 - channel is configured
    install_line_api(make_failing_line_api(failing_path, error))
    caplog.set_level(logging.DEBUG, logger=auth_module.logger.name)

    with pytest.raises(HTTPException) as exc_info:
        await verify_line_access_token(FAKE_ACCESS_TOKEN)

    assert exc_info.value.status_code == expected_status  # noqa: S101
    assert exc_info.value.detail == expected_detail  # noqa: S101
    auth_records = [record for record in caplog.records if record.name == auth_module.logger.name]
    assert auth_records  # noqa: S101 - the failure must still be logged
    for record in auth_records:
        assert FAKE_ACCESS_TOKEN not in record.getMessage()  # noqa: S101
        assert "access_token=" not in record.getMessage()  # noqa: S101
        assert record.exc_info is None  # noqa: S101
        assert record.exc_text is None  # noqa: S101
    # Fully formatted output (including any traceback) of the auth logger only; httpx's own
    # request logging is suppressed separately and is not part of this seam.
    formatter = logging.Formatter()
    auth_output = "\n".join(formatter.format(record) for record in auth_records)
    assert FAKE_ACCESS_TOKEN not in auth_output  # noqa: S101
