"""Test user module API endpoints."""

import base64
import hashlib
import hmac
from collections.abc import Callable
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.user.models import User
from app.user.service import create_user_if_not_exists, deactivate_user, get_user_by_line_id


def test_root(client: TestClient) -> None:
    """Return the welcome message."""

    response = client.get("/")
    assert response.status_code == 200  # noqa: S101
    assert response.json() == {"message": "Welcome to WeaMind API"}  # noqa: S101


def test_create_user(client: TestClient) -> None:
    """Create a new user."""

    data = {"line_user_id": str(uuid4()), "display_name": "Alice"}
    response = client.post("/users", json=data)
    assert response.status_code == 201  # noqa: S101
    body = response.json()
    assert body["line_user_id"] == data["line_user_id"]  # noqa: S101


def test_get_user(create_user: Callable[..., dict], client: TestClient) -> None:
    """Retrieve an existing user."""

    created = create_user()
    user_id = created["id"]
    response = client.get(f"/users/{user_id}")
    assert response.status_code == 200  # noqa: S101
    assert response.json()["id"] == user_id  # noqa: S101


def test_update_user(create_user: Callable[..., dict], client: TestClient) -> None:
    """Update a user's display name."""

    created = create_user()
    user_id = created["id"]
    response = client.patch(f"/users/{user_id}", json={"display_name": "Bob"})
    assert response.status_code == 200  # noqa: S101
    assert response.json()["display_name"] == "Bob"  # noqa: S101


def test_delete_user(create_user: Callable[..., dict], client: TestClient) -> None:
    """Delete a user."""

    created = create_user()
    user_id = created["id"]
    response = client.delete(f"/users/{user_id}")
    assert response.status_code == 204  # noqa: S101
    response = client.get(f"/users/{user_id}")
    assert response.status_code == 404  # noqa: S101


def test_line_webhook_signature_ok(client: TestClient) -> None:
    """Signature verification passes."""

    body = b"{}"
    digest = hmac.new(b"TEST_SECRET", body, hashlib.sha256).digest()
    signature = base64.b64encode(digest).decode()

    response = client.post(
        "/line/webhook",
        content=body,
        headers={"X-Line-Signature": signature, "Content-Type": "application/json"},
    )
    assert response.status_code == 200  # noqa: S101
    assert response.json() == {"message": "OK"}  # noqa: S101


def test_line_webhook_signature_invalid(client: TestClient) -> None:
    """Invalid signature returns 400."""

    body = b"{}"
    response = client.post(
        "/line/webhook",
        content=body,
        headers={"X-Line-Signature": "bad", "Content-Type": "application/json"},
    )
    assert response.status_code == 400  # noqa: S101


class TestUserService:
    """Test user service functions."""

    def test_get_user_by_line_id_exists(self, session: Session) -> None:
        """Test getting user by LINE ID when user exists."""
        line_user_id = str(uuid4())
        user = User(line_user_id=line_user_id, display_name="Test User")
        session.add(user)
        session.commit()

        result = get_user_by_line_id(session, line_user_id)
        assert result is not None  # noqa: S101
        assert result.line_user_id == line_user_id  # noqa: S101

    def test_get_user_by_line_id_not_exists(self, session: Session) -> None:
        """Test getting user by LINE ID when user doesn't exist."""
        result = get_user_by_line_id(session, "nonexistent_user")
        assert result is None  # noqa: S101

    def test_create_user_if_not_exists_new_user(self, session: Session) -> None:
        """Test creating new user when user doesn't exist."""
        line_user_id = str(uuid4())
        display_name = "New User"

        user = create_user_if_not_exists(session, line_user_id, display_name)

        assert user.line_user_id == line_user_id  # noqa: S101
        assert user.display_name == display_name  # noqa: S101
        assert user.is_active  # noqa: S101

        # Verify user was saved to database
        db_user = get_user_by_line_id(session, line_user_id)
        assert db_user is not None  # noqa: S101
        assert db_user.id == user.id  # noqa: S101

    def test_create_user_if_not_exists_existing_active_user(self, session: Session) -> None:
        """Test creating user when active user already exists."""
        line_user_id = str(uuid4())
        existing_user = User(line_user_id=line_user_id, display_name="Existing User")
        session.add(existing_user)
        session.commit()
        existing_id = existing_user.id

        user = create_user_if_not_exists(session, line_user_id, "New Display Name")

        assert user.id == existing_id  # noqa: S101
        assert user.line_user_id == line_user_id  # noqa: S101
        assert user.display_name == "Existing User"  # noqa: S101
        assert user.is_active  # noqa: S101

    def test_create_user_if_not_exists_existing_inactive_user(self, session: Session) -> None:
        """Test creating user when inactive user already exists."""
        line_user_id = str(uuid4())
        existing_user = User(line_user_id=line_user_id, display_name="Existing User")
        existing_user.is_active = False
        session.add(existing_user)
        session.commit()
        existing_id = existing_user.id

        user = create_user_if_not_exists(session, line_user_id, "New Display Name")

        assert user.id == existing_id  # noqa: S101
        assert user.line_user_id == line_user_id  # noqa: S101
        assert user.display_name == "New Display Name"  # noqa: S101
        assert user.is_active  # noqa: S101

    def test_create_user_if_not_exists_no_display_name(self, session: Session) -> None:
        """Test creating user without display name."""
        line_user_id = str(uuid4())

        user = create_user_if_not_exists(session, line_user_id)

        assert user.line_user_id == line_user_id  # noqa: S101
        assert user.display_name is None  # noqa: S101
        assert user.is_active  # noqa: S101

    def test_deactivate_user_exists(self, session: Session) -> None:
        """Test deactivating user when user exists."""
        line_user_id = str(uuid4())
        user = User(line_user_id=line_user_id, display_name="Test User")
        session.add(user)
        session.commit()
        user_id = user.id

        result = deactivate_user(session, line_user_id)

        assert result is not None  # noqa: S101
        assert result.id == user_id  # noqa: S101
        assert not result.is_active  # noqa: S101

    def test_deactivate_user_not_exists(self, session: Session) -> None:
        """Test deactivating user when user doesn't exist."""
        result = deactivate_user(session, "nonexistent_user")
        assert result is None  # noqa: S101
