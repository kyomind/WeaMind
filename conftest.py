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

# 為了讓 SQLAlchemy 正確註冊所有 table，必須 import models（即使沒直接用到）
from app.user import models  # noqa: F401

Base.metadata.create_all(bind=engine)
# 使用模組級單例，比直接在 fixture 裡建立更有效率
_client = TestClient(app)


@pytest.fixture()
def client() -> TestClient:
    """提供 FastAPI 測試 client."""

    return _client


@pytest.fixture()
def user(client: TestClient) -> Callable[..., dict]:
    """Return a helper for creating test users

    採用回傳 helper 函式而非直接回傳 user 物件的理由：
    1. 提高彈性，可依需求建立不同 display_name 或多個 user
    2. 支援同一測試多次建立 user
    3. 減少 fixture 數量，便於維護與擴充
    """

    def _create(display_name: str = "Alice") -> dict:
        data = {"line_user_id": str(uuid4()), "display_name": display_name}
        response = client.post("/users", json=data)
        assert response.status_code == 201  # noqa: S101
        return response.json()

    return _create
