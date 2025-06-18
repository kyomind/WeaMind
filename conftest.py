import os
import sys
from collections.abc import Callable
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"

sys.path.append(str(Path(__file__).resolve().parent))

from app.core.database import Base, engine
from app.main import app
from app.user import models  # noqa: F401

Base.metadata.create_all(bind=engine)
_client = TestClient(app)


@pytest.fixture()
def client() -> TestClient:
    """提供 FastAPI 測試 client."""

    return _client


@pytest.fixture()
def create_user(client: TestClient) -> Callable[[str], dict]:
    """建立測試用戶並回傳資料."""

    def _create(display_name: str = "Alice") -> dict:
        data = {"line_user_id": str(uuid4()), "display_name": display_name}
        response = client.post("/users", json=data)
        assert response.status_code == 201  # noqa: S101
        return response.json()

    return _create
