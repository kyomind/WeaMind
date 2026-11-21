"""
Behavior tests for app.core.config.setup_logging using real emitted log output.

Each case runs setup_logging in a separate Python process with fake settings and a
temporary logs directory. This keeps the global logging state of the pytest process
untouched, so no root or named logger state needs to be restored.
"""

import json
import subprocess  # noqa: S404
import sys
from pathlib import Path
from typing import NamedTuple

import pytest

# Fake values only; nothing here is a real credential or endpoint.
FAKE_TOKEN = "fake-token-for-logging-test"  # noqa: S105
FAKE_REQUEST_URL = "https://fake-line.invalid/verify"
APP_MESSAGE = "application info message still emitted"
UVICORN_MESSAGE = "uvicorn operational message"
UVICORN_ACCESS_MESSAGE = "uvicorn access message"

REPO_ROOT = Path(__file__).resolve().parents[2]

# Runs in the child process: configure logging through the public setup_logging function,
# send a query-bearing request through httpx's MockTransport (no network), emit normal
# INFO messages, then record the resulting logger thresholds.
PROBE_SCRIPT = f"""
import json
import logging
import sys
from pathlib import Path

import httpx

from app.core import config

config.BASE_DIR = Path(sys.argv[1])
config.setup_logging()

def handler(request: httpx.Request) -> httpx.Response:
    return httpx.Response(200, json={{}})

with httpx.Client(transport=httpx.MockTransport(handler)) as client:
    client.get({FAKE_REQUEST_URL!r}, params={{"access_token": {FAKE_TOKEN!r}}})

logging.getLogger("app.test").info({APP_MESSAGE!r})
logging.getLogger("uvicorn").info({UVICORN_MESSAGE!r})
logging.getLogger("uvicorn.access").info({UVICORN_ACCESS_MESSAGE!r})
logging.shutdown()

levels = {{
    "root": logging.getLogger().level,
    "httpx": logging.getLogger("httpx").level,
    "httpcore": logging.getLogger("httpcore").level,
}}
Path(sys.argv[1], "levels.json").write_text(json.dumps(levels))
"""


class ProbeResult(NamedTuple):
    """Observable outcome of one setup_logging run in a child process."""

    console_output: str
    file_output: str
    root_level: int
    httpx_level: int
    httpcore_level: int


def run_logging_probe(base_dir: Path, env: str, debug: bool) -> ProbeResult:
    """
    Run setup_logging in a child process and collect what it actually emitted.

    Args:
        base_dir: Temporary directory used as the application base (logs go to base_dir/logs).
        env: Fake ENV setting for the child process.
        debug: Fake DEBUG setting for the child process.

    Returns:
        Console output, log file content, and resulting logger thresholds.
    """
    child_env = {
        "PATH": "/usr/bin:/bin",
        "PYTHONPATH": str(REPO_ROOT),
        "PYTHONDONTWRITEBYTECODE": "1",
        "ENV": env,
        "DEBUG": str(debug).lower(),
        "POSTGRES_USER": "test_user",
        "POSTGRES_PASSWORD": "test_password",  # noqa: S105
        "POSTGRES_HOST": "localhost",
        "POSTGRES_DB": "test_db",
        "LINE_CHANNEL_SECRET": "TEST_SECRET",  # noqa: S105
        "LINE_CHANNEL_ACCESS_TOKEN": "TEST_ACCESS_TOKEN",  # noqa: S105
    }
    # cwd is the temp dir so no .env file can be picked up by the settings loader.
    completed = subprocess.run(  # noqa: S603
        [sys.executable, "-c", PROBE_SCRIPT, str(base_dir)],
        cwd=base_dir,
        env=child_env,
        capture_output=True,
        text=True,
        timeout=60,
        check=True,
    )
    levels = json.loads((base_dir / "levels.json").read_text(encoding="utf-8"))
    return ProbeResult(
        console_output=completed.stdout,
        file_output=(base_dir / "logs" / "app.log").read_text(encoding="utf-8"),
        root_level=levels["root"],
        httpx_level=levels["httpx"],
        httpcore_level=levels["httpcore"],
    )


@pytest.mark.parametrize(
    ("env", "debug"),
    [("production", False), ("production", True), ("development", False), ("development", True)],
)
def test_http_client_request_not_logged_to_console_or_file(
    tmp_path: Path, env: str, debug: bool
) -> None:
    """Test that a query-bearing httpx request leaks into neither console nor file output."""
    result = run_logging_probe(tmp_path, env, debug)

    for output in (result.console_output, result.file_output):
        assert APP_MESSAGE in output  # noqa: S101
        assert FAKE_TOKEN not in output  # noqa: S101
        assert FAKE_REQUEST_URL not in output  # noqa: S101


@pytest.mark.parametrize(
    ("env", "debug", "expected_root_level"),
    [
        ("production", False, 20),
        ("production", True, 20),
        ("prod", True, 20),
        ("development", False, 20),
        ("development", True, 10),
        ("dev", True, 10),
    ],
)
def test_log_levels_by_environment_and_debug(
    tmp_path: Path, env: str, debug: bool, expected_root_level: int
) -> None:
    """Test root level follows ENV/DEBUG while HTTP client loggers stay at WARNING in all modes."""
    result = run_logging_probe(tmp_path, env, debug)

    assert result.root_level == expected_root_level  # noqa: S101
    assert result.httpx_level == 30  # noqa: S101
    assert result.httpcore_level == 30  # noqa: S101


@pytest.mark.parametrize(("env", "debug"), [("production", True), ("development", False)])
def test_uvicorn_info_logs_still_reach_console_and_file(
    tmp_path: Path, env: str, debug: bool
) -> None:
    """Test that uvicorn INFO operational logs are still emitted to console and file."""
    result = run_logging_probe(tmp_path, env, debug)

    for output in (result.console_output, result.file_output):
        assert UVICORN_MESSAGE in output  # noqa: S101
        assert UVICORN_ACCESS_MESSAGE in output  # noqa: S101
