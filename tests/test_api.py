"""Tests for demo API endpoints."""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root() -> None:
    """Should return welcome message."""
    response = client.get("/")
    assert response.status_code == 200  # noqa: S101
    assert response.json() == {"message": "Welcome to WeaMind API"}  # noqa: S101


def test_get_users() -> None:
    """Should return placeholder for user retrieval."""
    response = client.get("/api/v1/users")
    assert response.status_code == 200  # noqa: S101
    assert response.json() == {"message": "用戶資料檢索端點（佔位符）"}  # noqa: S101


def test_create_user() -> None:
    """Should return placeholder for user creation."""
    response = client.post("/api/v1/users")
    assert response.status_code == 200  # noqa: S101
    assert response.json() == {"message": "用戶創建端點（佔位符）"}  # noqa: S101


def test_get_user_quota() -> None:
    """Should return placeholder quota info for a user."""
    user_id = "123"
    response = client.get(f"/api/v1/users/{user_id}/quota")
    assert response.status_code == 200  # noqa: S101
    assert response.json() == {"message": f"用戶 {user_id} 的額度資訊（佔位符）"}  # noqa: S101
