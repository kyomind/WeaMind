"""Test user module API endpoints."""

import base64
import hashlib
import hmac
from unittest.mock import patch
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


class TestUserServiceAdditional:
    """Additional test cases for user service functions."""

    def test_get_location_by_county_district(self, session: Session) -> None:
        """Test getting location by county and district."""
        from app.user.service import get_location_by_county_district
        from app.weather.models import Location

        # Create a location
        location = Location(
            geocode="test001",
            county="台北市",
            district="中正區",
            full_name="台北市中正區",
        )
        session.add(location)
        session.commit()

        retrieved_location = get_location_by_county_district(session, "台北市", "中正區")

        assert retrieved_location is not None  # noqa: S101
        assert retrieved_location.county == "台北市"  # noqa: S101
        assert retrieved_location.district == "中正區"  # noqa: S101

    def test_get_location_by_county_district_not_exists(self, session: Session) -> None:
        """Test getting location that doesn't exist."""
        from app.user.service import get_location_by_county_district

        result = get_location_by_county_district(session, "不存在縣市", "不存在區域")
        assert result is None  # noqa: S101

    def test_set_user_location_invalid_type(self, session: Session) -> None:
        """Test setting user location with invalid location type."""
        from app.user.service import set_user_location

        line_user_id = str(uuid4())
        success, message, location = set_user_location(
            session, line_user_id, "invalid_type", "台北市", "中正區"
        )

        assert success is False  # noqa: S101
        assert message == "無效的地點類型"  # noqa: S101
        assert location is None  # noqa: S101

    def test_set_user_location_location_not_exists(self, session: Session) -> None:
        """Test setting user location when location doesn't exist."""
        from app.user.service import set_user_location

        line_user_id = str(uuid4())
        success, message, location = set_user_location(
            session, line_user_id, "home", "不存在縣市", "不存在區域"
        )

        assert success is False  # noqa: S101
        assert message == "地點不存在"  # noqa: S101
        assert location is None  # noqa: S101

    def test_set_user_location_home_success(self, session: Session) -> None:
        """Test successfully setting user home location."""
        from app.user.service import set_user_location
        from app.weather.models import Location

        # Create location
        location = Location(
            geocode="test002",
            county="台北市",
            district="中正區",
            full_name="台北市中正區",
        )
        session.add(location)
        session.commit()

        line_user_id = str(uuid4())
        success, message, returned_location = set_user_location(
            session, line_user_id, "home", "台北市", "中正區"
        )

        assert success is True  # noqa: S101
        assert message == "地點設定成功"  # noqa: S101
        assert returned_location is not None  # noqa: S101
        assert returned_location.county == "台北市"  # noqa: S101
        assert returned_location.district == "中正區"  # noqa: S101

        # Verify user was created and location was set
        from app.user.service import get_user_by_line_id

        user = get_user_by_line_id(session, line_user_id)
        assert user is not None  # noqa: S101
        assert user.home_location_id == returned_location.id  # noqa: S101

    def test_set_user_location_work_success(self, session: Session) -> None:
        """Test successfully setting user work location."""
        from app.user.service import set_user_location
        from app.weather.models import Location

        # Create location
        location = Location(
            geocode="test003",
            county="新北市",
            district="永和區",
            full_name="新北市永和區",
        )
        session.add(location)
        session.commit()

        line_user_id = str(uuid4())
        success, message, returned_location = set_user_location(
            session, line_user_id, "work", "新北市", "永和區"
        )

        assert success is True  # noqa: S101
        assert message == "地點設定成功"  # noqa: S101
        assert returned_location is not None  # noqa: S101

        # Verify work location was set
        from app.user.service import get_user_by_line_id

        user = get_user_by_line_id(session, line_user_id)
        assert user is not None  # noqa: S101
        assert user.work_location_id == location.id  # noqa: S101

    def test_set_user_location_existing_user(self, session: Session) -> None:
        """Test setting location for existing user."""
        from app.user.service import set_user_location
        from app.weather.models import Location

        # Create user and location
        line_user_id = str(uuid4())
        user = User(line_user_id=line_user_id, display_name="Existing User")
        session.add(user)

        location = Location(
            geocode="test004",
            county="台北市",
            district="中正區",
            full_name="台北市中正區",
        )
        session.add(location)
        session.commit()

        success, message, returned_location = set_user_location(
            session, line_user_id, "home", "台北市", "中正區"
        )

        assert success is True  # noqa: S101
        assert returned_location is not None  # noqa: S101
        # Refresh user to get updated data from database
        session.refresh(user)
        assert user.home_location_id == returned_location.id  # noqa: S101


class TestUserRouterAdditional:
    """Additional test cases for user router endpoints."""

    def test_set_user_location_success(self, client: TestClient, session: Session) -> None:
        """Test successfully setting user location via LIFF."""
        from app.weather.models import Location

        # Create location
        location = Location(
            geocode="test005",
            county="台北市",
            district="中正區",
            full_name="台北市中正區",
        )
        session.add(location)
        session.commit()

        # Mock LINE authentication
        with patch("app.core.auth.verify_line_access_token") as mock_auth:
            mock_auth.return_value = "test_line_user_id"

            payload = {
                "location_type": "home",
                "county": "台北市",
                "district": "中正區",
            }
            response = client.post(
                "/users/locations",
                json=payload,
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 200  # noqa: S101
            response_body = response.json()
            assert response_body["success"] is True  # noqa: S101
            assert response_body["location_type"] == "住家"  # noqa: S101
            assert response_body["location"] == "台北市中正區"  # noqa: S101

    def test_set_user_location_work(self, client: TestClient, session: Session) -> None:
        """Test setting work location via LIFF."""
        from app.weather.models import Location

        # Create location
        location = Location(
            geocode="test006",
            county="新北市",
            district="永和區",
            full_name="新北市永和區",
        )
        session.add(location)
        session.commit()

        # Mock LINE authentication
        with patch("app.core.auth.verify_line_access_token") as mock_auth:
            mock_auth.return_value = "test_line_user_id"

            payload = {
                "location_type": "work",
                "county": "新北市",
                "district": "永和區",
            }
            response = client.post(
                "/users/locations",
                json=payload,
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 200  # noqa: S101
            response_body = response.json()
            assert response_body["success"] is True  # noqa: S101
            assert response_body["location_type"] == "公司"  # noqa: S101
            assert response_body["location"] == "新北市永和區"  # noqa: S101

    def test_set_user_location_invalid_type(self, client: TestClient) -> None:
        """Test setting user location with invalid type."""
        # Mock LINE authentication
        with patch("app.core.auth.verify_line_access_token") as mock_auth:
            mock_auth.return_value = "test_line_user_id"

            payload = {
                "location_type": "invalid",
                "county": "台北市",
                "district": "中正區",
            }
            response = client.post(
                "/users/locations",
                json=payload,
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 400  # noqa: S101
            assert "無效的地點類型" in response.json()["detail"]  # noqa: S101

    def test_set_user_location_not_exists(self, client: TestClient) -> None:
        """Test setting user location that doesn't exist."""
        # Mock LINE authentication
        with patch("app.core.auth.verify_line_access_token") as mock_auth:
            mock_auth.return_value = "test_line_user_id"

            payload = {
                "location_type": "home",
                "county": "不存在縣市",
                "district": "不存在區域",
            }
            response = client.post(
                "/users/locations",
                json=payload,
                headers={"Authorization": "Bearer test_token"},
            )

            assert response.status_code == 400  # noqa: S101
            assert "地點不存在" in response.json()["detail"]  # noqa: S101

    def test_set_user_location_auth_failed(self, client: TestClient) -> None:
        """Test setting user location without proper authentication."""
        payload = {
            "location_type": "home",
            "county": "台北市",
            "district": "中正區",
        }
        response = client.post("/users/locations", json=payload)

        assert response.status_code == 403  # noqa: S101
