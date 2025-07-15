"""Test fixtures for core module."""

from pathlib import Path

import pytest


@pytest.fixture()
def temp_logs_dir(tmp_path: Path) -> Path:
    """Create a temporary logs directory for testing."""
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    return logs_dir
