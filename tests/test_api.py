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



def test_user_crud() -> None:
    """Should handle user CRUD operations."""
    data = {"line_user_id": "uid123", "display_name": "John"}
    response = client.post("/users", json=data)
    assert response.status_code == 201  # noqa: S101
    created = response.json()
    assert created["line_user_id"] == data["line_user_id"]  # noqa: S101
    user_id = created["id"]

    response = client.get(f"/users/{user_id}")

    assert response.status_code == 200  # noqa: S101
    assert response.json()["id"] == user_id  # noqa: S101

    update = {"display_name": "Jane"}
    response = client.patch(f"/users/{user_id}", json=update)

    assert response.status_code == 200  # noqa: S101
    assert response.json()["display_name"] == "Jane"  # noqa: S101

    response = client.delete(f"/users/{user_id}")

    assert response.status_code == 200  # noqa: S101
    assert response.json() == {"ok": True}  # noqa: S101

    response = client.get(f"/users/{user_id}")
    assert response.status_code == 404  # noqa: S101
