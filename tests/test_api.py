"""Tests for core API endpoints.

Verify root and user operations.
"""

from collections.abc import Callable
from uuid import uuid4

from fastapi.testclient import TestClient


def test_root(client: TestClient) -> None:
    """Return welcome message.

    Ensure the API root endpoint responds correctly.
    """

    response = client.get("/")
    assert response.status_code == 200  # noqa: S101
    assert response.json() == {"message": "Welcome to WeaMind API"}  # noqa: S101


def test_create_user(client: TestClient) -> None:
    """Create a new user.

    Verify that registration succeeds with unique line ID.
    """

    data = {"line_user_id": str(uuid4()), "display_name": "Alice"}
    response = client.post("/users", json=data)
    assert response.status_code == 201  # noqa: S101
    body = response.json()
    assert body["line_user_id"] == data["line_user_id"]  # noqa: S101


def test_get_user(user: Callable[..., dict], client: TestClient) -> None:
    """Get an existing user.

    Should return the created record.
    """

    created = user()
    user_id = created["id"]
    response = client.get(f"/users/{user_id}")
    assert response.status_code == 200  # noqa: S101
    assert response.json()["id"] == user_id  # noqa: S101


def test_update_user(user: Callable[..., dict], client: TestClient) -> None:
    """Update user display name.

    Confirm the new name persists.
    """

    created = user()
    user_id = created["id"]
    response = client.patch(f"/users/{user_id}", json={"display_name": "Bob"})
    assert response.status_code == 200  # noqa: S101
    assert response.json()["display_name"] == "Bob"  # noqa: S101


def test_delete_user(user: Callable[..., dict], client: TestClient) -> None:
    """Delete a user.

    Ensure the record is removed.
    """

    created = user()
    user_id = created["id"]
    response = client.delete(f"/users/{user_id}")
    assert response.status_code == 204  # noqa: S101
    response = client.get(f"/users/{user_id}")
    assert response.status_code == 404  # noqa: S101
