"""Test fixtures for user module testing."""

import pytest
from sqlalchemy.orm import Session

from app.core.database import get_session


@pytest.fixture()
def session() -> Session:
    """Provide a database session for testing."""
    return next(get_session())
