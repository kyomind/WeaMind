"""Behavior tests for app.core.config.setup_logging using real emitted log output."""

import logging
from collections.abc import Callable, Generator
from pathlib import Path

import httpx
import pytest

from app.core import config
from app.core.config import setup_logging

# Fake values only; nothing here is a real credential or endpoint.
FAKE_TOKEN = "fake-token-for-logging-test"  # noqa: S105
FAKE_REQUEST_URL = "https://fake-line.invalid/verify"
APP_MESSAGE = "application info message still emitted"

NAMED_LOGGERS = (
    "httpx",
    "httpcore",
    "sqlalchemy.engine",
    "uvicorn",
    "uvicorn.access",
    config.__name__,
)


@pytest.fixture
def run_setup_logging(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> Generator[Callable[[], Path], None, None]:
    """
    Create a helper that runs setup_logging against isolated global logging state.

    pytest re-attaches its capture handlers to the root logger for every test phase,
    and basicConfig is a no-op when root has handlers, so root handlers are detached
    right before setup_logging runs. Root and named logger state is restored on
    teardown, and only handlers created by setup_logging are closed.

    Yields:
        A callable that runs setup_logging and returns the temporary logs directory.
    """
    root = logging.getLogger()
    saved_root_level = root.level
    saved_named = {
        name: (
            logging.getLogger(name).level,
            list(logging.getLogger(name).handlers),
            logging.getLogger(name).propagate,
        )
        for name in NAMED_LOGGERS
    }
    detached_root_handlers: list[logging.Handler] = []
    monkeypatch.setattr(config, "BASE_DIR", tmp_path)

    def _run() -> Path:
        """Detach existing root handlers, then run setup_logging."""
        detached_root_handlers.extend(root.handlers)
        for handler in detached_root_handlers:
            root.removeHandler(handler)
        setup_logging()
        return tmp_path / "logs"

    yield _run

    created_handlers = list(root.handlers)
    for name, (_, handlers, _) in saved_named.items():
        created_handlers.extend(h for h in logging.getLogger(name).handlers if h not in handlers)
    for handler in set(created_handlers):
        root.removeHandler(handler)
        for name in NAMED_LOGGERS:
            logging.getLogger(name).removeHandler(handler)
        handler.close()

    root.setLevel(saved_root_level)
    for handler in detached_root_handlers:
        root.addHandler(handler)
    for name, (level, handlers, propagate) in saved_named.items():
        named_logger = logging.getLogger(name)
        named_logger.setLevel(level)
        named_logger.handlers[:] = handlers
        named_logger.propagate = propagate


@pytest.fixture
def configure_settings(monkeypatch: pytest.MonkeyPatch) -> Callable[[str, bool], None]:
    """Create a helper that applies fake ENV and DEBUG settings."""

    def _configure(env: str, debug: bool) -> None:
        """Apply fake ENV and DEBUG values to the application settings."""
        monkeypatch.setattr(config.settings, "ENV", env)
        monkeypatch.setattr(config.settings, "DEBUG", debug)

    return _configure


def send_fake_query_request() -> None:
    """Send a query-bearing request through httpx with a mock transport (no network)."""

    def handler(request: httpx.Request) -> httpx.Response:
        """Return an empty successful response for any request."""
        return httpx.Response(200, json={})

    with httpx.Client(transport=httpx.MockTransport(handler)) as client:
        client.get(FAKE_REQUEST_URL, params={"access_token": FAKE_TOKEN})


@pytest.mark.parametrize(
    ("env", "debug"),
    [("production", False), ("production", True), ("development", False), ("development", True)],
)
def test_http_client_request_not_logged_to_console_or_file(
    run_setup_logging: Callable[[], Path],
    configure_settings: Callable[[str, bool], None],
    capsys: pytest.CaptureFixture[str],
    env: str,
    debug: bool,
) -> None:
    """Test that a query-bearing httpx request leaks into neither console nor file output."""
    configure_settings(env, debug)
    logs_dir = run_setup_logging()

    send_fake_query_request()
    logging.getLogger("app.test").info(APP_MESSAGE)
    for handler in logging.getLogger().handlers:
        handler.flush()

    console_output = capsys.readouterr().out
    file_output = (logs_dir / "app.log").read_text(encoding="utf-8")
    for output in (console_output, file_output):
        assert APP_MESSAGE in output  # noqa: S101
        assert FAKE_TOKEN not in output  # noqa: S101
        assert FAKE_REQUEST_URL not in output  # noqa: S101


@pytest.mark.parametrize(
    ("env", "debug", "expected_root_level"),
    [
        ("production", False, logging.INFO),
        ("production", True, logging.INFO),
        ("prod", True, logging.INFO),
        ("development", False, logging.INFO),
        ("development", True, logging.DEBUG),
        ("dev", True, logging.DEBUG),
    ],
)
def test_log_levels_by_environment_and_debug(
    run_setup_logging: Callable[[], Path],
    configure_settings: Callable[[str, bool], None],
    env: str,
    debug: bool,
    expected_root_level: int,
) -> None:
    """Test root level follows ENV/DEBUG while HTTP client loggers stay at WARNING in all modes."""
    configure_settings(env, debug)
    run_setup_logging()

    assert logging.getLogger().level == expected_root_level  # noqa: S101
    assert logging.getLogger("httpx").level == logging.WARNING  # noqa: S101
    assert logging.getLogger("httpcore").level == logging.WARNING  # noqa: S101


@pytest.mark.parametrize(("env", "debug"), [("production", True), ("development", False)])
def test_uvicorn_info_logs_still_reach_file(
    run_setup_logging: Callable[[], Path],
    configure_settings: Callable[[str, bool], None],
    env: str,
    debug: bool,
) -> None:
    """Test that uvicorn INFO operational logs are still written to the log file."""
    configure_settings(env, debug)
    logs_dir = run_setup_logging()

    logging.getLogger("uvicorn").info("uvicorn operational message")
    logging.getLogger("uvicorn.access").info("uvicorn access message")
    for handler in logging.getLogger("uvicorn").handlers:
        handler.flush()

    file_output = (logs_dir / "app.log").read_text(encoding="utf-8")
    assert "uvicorn operational message" in file_output  # noqa: S101
    assert "uvicorn access message" in file_output  # noqa: S101
