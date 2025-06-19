import os
import sys
from collections.abc import Callable
from pathlib import Path
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
