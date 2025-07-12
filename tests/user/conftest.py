"""Test fixtures for user module testing."""

from collections.abc import Callable
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient


@pytest.fixture()
def create_user(client: TestClient) -> Callable[..., dict]:
    """
    Return a helper for creating test users.

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
