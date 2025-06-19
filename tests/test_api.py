"""測試核心 API 端點"""

import base64
import hashlib
import hmac
from collections.abc import Callable
from uuid import uuid4

from fastapi.testclient import TestClient


def test_root(client: TestClient) -> None:
    """回傳歡迎訊息"""

    response = client.get("/")
    assert response.status_code == 200  # noqa: S101
    assert response.json() == {"message": "Welcome to WeaMind API"}  # noqa: S101


def test_create_user(client: TestClient) -> None:
    """建立新使用者"""

    data = {"line_user_id": str(uuid4()), "display_name": "Alice"}
    response = client.post("/users", json=data)
    assert response.status_code == 201  # noqa: S101
    body = response.json()
    assert body["line_user_id"] == data["line_user_id"]  # noqa: S101


def test_get_user(create_user: Callable[..., dict], client: TestClient) -> None:
    """獲取現有使用者"""

    created = create_user()
    user_id = created["id"]
    response = client.get(f"/users/{user_id}")
    assert response.status_code == 200  # noqa: S101
    assert response.json()["id"] == user_id  # noqa: S101


def test_update_user(create_user: Callable[..., dict], client: TestClient) -> None:
    """更新使用者顯示名稱"""

    created = create_user()
    user_id = created["id"]
    response = client.patch(f"/users/{user_id}", json={"display_name": "Bob"})
    assert response.status_code == 200  # noqa: S101
    assert response.json()["display_name"] == "Bob"  # noqa: S101


def test_delete_user(create_user: Callable[..., dict], client: TestClient) -> None:
    """刪除使用者"""

    created = create_user()
    user_id = created["id"]
    response = client.delete(f"/users/{user_id}")
    assert response.status_code == 204  # noqa: S101
    response = client.get(f"/users/{user_id}")
    assert response.status_code == 404  # noqa: S101


def test_line_webhook_signature_ok(client: TestClient) -> None:
    """驗證簽名通過"""

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
    """簽名錯誤回傳 400"""

    body = b"{}"
    response = client.post(
        "/line/webhook",
        content=body,
        headers={"X-Line-Signature": "bad", "Content-Type": "application/json"},
    )
    assert response.status_code == 400  # noqa: S101
