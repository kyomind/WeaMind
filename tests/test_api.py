"""Tests for core API endpoints."""

import os
import sys
from pathlib import Path

os.environ["DATABASE_URL"] = "sqlite+pysqlite:///:memory:"

sys.path.append(str(Path(__file__).resolve().parents[1]))
from fastapi.testclient import TestClient

from app.core.database import Base, engine
from app.main import app
from app.user import models  # noqa: F401

Base.metadata.create_all(bind=engine)
client = TestClient(app)


def test_root() -> None:
    """Should return welcome message."""
    response = client.get("/")
    assert response.status_code == 200  # noqa: S101
    assert response.json() == {"message": "Welcome to WeaMind API"}  # noqa: S101


def test_user_crud() -> None:
    """Should create, read, update and delete a user."""
    data = {"line_user_id": "U123", "display_name": "Alice"}
    resp = client.post("/users", json=data)
    assert resp.status_code == 201  # noqa: S101
    created = resp.json()
    assert created["line_user_id"] == "U123"  # noqa: S101

    user_id = created["id"]
    resp = client.get(f"/users/{user_id}")
    assert resp.status_code == 200  # noqa: S101

    resp = client.patch(f"/users/{user_id}", json={"display_name": "Bob"})
    assert resp.status_code == 200  # noqa: S101
    assert resp.json()["display_name"] == "Bob"  # noqa: S101

    resp = client.delete(f"/users/{user_id}")
    assert resp.status_code == 204  # noqa: S101

    resp = client.get(f"/users/{user_id}")
    assert resp.status_code == 404  # noqa: S101
