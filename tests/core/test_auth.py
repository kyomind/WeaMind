"""Test authentication utilities."""

import time
from collections.abc import Callable
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import httpx
import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app.core.auth import (
    get_current_line_user_id,
    get_current_line_user_id_from_access_token,
    verify_line_access_token,
    verify_line_id_token,
)


class TestVerifyLineAccessToken:
    """Test LINE Access Token verification."""

    @pytest.mark.asyncio
    async def test_verify_line_access_token_success(self) -> None:
        """Test successful LINE Access Token verification."""
        access_token = "test_access_token"
        line_user_id = str(uuid4())

        # Mock verify response
        verify_response_mock = Mock()
        verify_response_mock.status_code = 200
        verify_response_mock.json.return_value = {
            "client_id": "test_client_id",
            "expires_in": 3600,
        }

        # Mock profile response
        profile_response_mock = Mock()
        profile_response_mock.status_code = 200
        profile_response_mock.json.return_value = {"userId": line_user_id}

        with patch("httpx.AsyncClient") as mock_client:
            mock_client_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_client_instance
            mock_client_instance.get.side_effect = [verify_response_mock, profile_response_mock]

            result = await verify_line_access_token(access_token)

            assert result == line_user_id


            assert mock_client_instance.get.call_count == 2

    @pytest.mark.asyncio
    async def test_verify_line_access_token_verify_failed(self) -> None:
        """Test LINE Access Token verification when verify API fails."""
        access_token = "invalid_token"

        verify_response_mock = Mock()
        verify_response_mock.status_code = 401

        with patch("httpx.AsyncClient") as mock_client:
            mock_client_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_client_instance
            mock_client_instance.get.return_value = verify_response_mock

            with pytest.raises(HTTPException) as exc_info:
                await verify_line_access_token(access_token)

            assert exc_info.value.status_code == 401
            assert "Invalid LINE Access Token" in exc_info.value.detail
    @pytest.mark.asyncio
    async def test_verify_line_access_token_no_client_id(self) -> None:
        """Test LINE Access Token verification when response has no client_id."""
        access_token = "test_access_token"

        verify_response_mock = Mock()
        verify_response_mock.status_code = 200
        verify_response_mock.json.return_value = {"expires_in": 3600}  # No client_id

        with patch("httpx.AsyncClient") as mock_client:
            mock_client_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_client_instance
            mock_client_instance.get.return_value = verify_response_mock

            with pytest.raises(HTTPException) as exc_info:
                await verify_line_access_token(access_token)

            assert exc_info.value.status_code == 401
    @pytest.mark.asyncio
    async def test_verify_line_access_token_expired(self) -> None:
        """Test LINE Access Token verification when token is expired."""
        access_token = "expired_token"

        verify_response_mock = Mock()
        verify_response_mock.status_code = 200
        verify_response_mock.json.return_value = {
            "client_id": "test_client_id",
            "expires_in": 0,  # Expired
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_client_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_client_instance
            mock_client_instance.get.return_value = verify_response_mock

            with pytest.raises(HTTPException) as exc_info:
                await verify_line_access_token(access_token)

            assert exc_info.value.status_code == 401
    @pytest.mark.asyncio
    async def test_verify_line_access_token_profile_failed(self) -> None:
        """Test LINE Access Token verification when profile API fails."""
        access_token = "test_access_token"

        verify_response_mock = Mock()
        verify_response_mock.status_code = 200
        verify_response_mock.json.return_value = {
            "client_id": "test_client_id",
            "expires_in": 3600,
        }

        profile_response_mock = Mock()
        profile_response_mock.status_code = 401

        with patch("httpx.AsyncClient") as mock_client:
            mock_client_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_client_instance
            mock_client_instance.get.side_effect = [verify_response_mock, profile_response_mock]

            with pytest.raises(HTTPException) as exc_info:
                await verify_line_access_token(access_token)

            assert exc_info.value.status_code == 401
    @pytest.mark.asyncio
    async def test_verify_line_access_token_no_user_id(self) -> None:
        """Test LINE Access Token verification when profile has no userId."""
        access_token = "test_access_token"

        verify_response_mock = Mock()
        verify_response_mock.status_code = 200
        verify_response_mock.json.return_value = {
            "client_id": "test_client_id",
            "expires_in": 3600,
        }

        profile_response_mock = Mock()
        profile_response_mock.status_code = 200
        profile_response_mock.json.return_value = {}  # No userId

        with patch("httpx.AsyncClient") as mock_client:
            mock_client_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_client_instance
            mock_client_instance.get.side_effect = [verify_response_mock, profile_response_mock]

            with pytest.raises(HTTPException) as exc_info:
                await verify_line_access_token(access_token)

            assert exc_info.value.status_code == 401
    @pytest.mark.asyncio
    async def test_verify_line_access_token_network_error(self) -> None:
        """Test LINE Access Token verification with network error."""
        access_token = "test_access_token"

        with patch("httpx.AsyncClient") as mock_client:
            mock_client_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_client_instance
            mock_client_instance.get.side_effect = httpx.RequestError("Network error")

            with pytest.raises(HTTPException) as exc_info:
                await verify_line_access_token(access_token)

            assert exc_info.value.status_code == 503
            assert "network error" in exc_info.value.detail

class TestVerifyLineIdToken:
    """Test LINE ID Token verification."""

    def test_verify_line_id_token_success(
        self, create_jwt_token: Callable[[str, int], str]
    ) -> None:
        """Test successful LINE ID Token verification."""
        line_user_id = str(uuid4())
        token = create_jwt_token(line_user_id, 3600)

        result = verify_line_id_token(token)

        assert result == line_user_id
    def test_verify_line_id_token_invalid_format(self) -> None:
        """Test LINE ID Token verification with invalid format."""
        invalid_token = "invalid.token"

        with pytest.raises(HTTPException) as exc_info:
            verify_line_id_token(invalid_token)

        assert exc_info.value.status_code == 401
        assert "Invalid LINE ID Token" in exc_info.value.detail
    def test_verify_line_id_token_unsupported_algorithm(
        self, create_custom_jwt_token: Callable[[dict, dict], str]
    ) -> None:
        """Test LINE ID Token verification with unsupported algorithm."""
        header = {"alg": "HS256", "typ": "JWT"}  # Unsupported algorithm
        payload = {
            "iss": "https://access.line.me",
            "sub": "test_user",
            "exp": int(time.time()) + 3600,
        }

        token = create_custom_jwt_token(header, payload)

        with pytest.raises(HTTPException) as exc_info:
            verify_line_id_token(token)

        assert exc_info.value.status_code == 401
    def test_verify_line_id_token_no_expiration(
        self, create_custom_jwt_token: Callable[[dict, dict], str]
    ) -> None:
        """Test LINE ID Token verification without expiration time."""
        header = {"alg": "RS256", "typ": "JWT"}
        payload = {
            "iss": "https://access.line.me",
            "sub": "test_user",
            # No exp field
        }

        token = create_custom_jwt_token(header, payload)

        with pytest.raises(HTTPException) as exc_info:
            verify_line_id_token(token)

        assert exc_info.value.status_code == 401
    def test_verify_line_id_token_expired(
        self, create_jwt_token: Callable[[str, int], str]
    ) -> None:
        """Test LINE ID Token verification with expired token."""
        line_user_id = str(uuid4())
        token = create_jwt_token(line_user_id, -3600)  # Expired 1 hour ago

        with pytest.raises(HTTPException) as exc_info:
            verify_line_id_token(token)

        assert exc_info.value.status_code == 401
    def test_verify_line_id_token_invalid_issuer(
        self, create_custom_jwt_token: Callable[[dict, dict], str]
    ) -> None:
        """Test LINE ID Token verification with invalid issuer."""
        header = {"alg": "RS256", "typ": "JWT"}
        payload = {
            "iss": "https://invalid.issuer.com",  # Invalid issuer
            "sub": "test_user",
            "exp": int(time.time()) + 3600,
        }

        token = create_custom_jwt_token(header, payload)

        with pytest.raises(HTTPException) as exc_info:
            verify_line_id_token(token)

        assert exc_info.value.status_code == 401
    def test_verify_line_id_token_no_user_id(
        self, create_custom_jwt_token: Callable[[dict, dict], str]
    ) -> None:
        """Test LINE ID Token verification without user ID."""
        header = {"alg": "RS256", "typ": "JWT"}
        payload = {
            "iss": "https://access.line.me",
            "exp": int(time.time()) + 3600,
            # No sub field
        }

        token = create_custom_jwt_token(header, payload)

        with pytest.raises(HTTPException) as exc_info:
            verify_line_id_token(token)

        assert exc_info.value.status_code == 401

class TestAuthDependencies:
    """Test FastAPI authentication dependencies."""

    @pytest.mark.asyncio
    async def test_get_current_line_user_id_from_access_token(self) -> None:
        """Test get current LINE user ID from access token dependency."""
        line_user_id = str(uuid4())
        token = HTTPAuthorizationCredentials(scheme="Bearer", credentials="test_token")

        with patch("app.core.auth.verify_line_access_token") as mock_verify:
            mock_verify.return_value = line_user_id

            result = await get_current_line_user_id_from_access_token(token)

            assert result == line_user_id
            mock_verify.assert_called_once_with("test_token")
    def test_get_current_line_user_id(self) -> None:
        """Test get current LINE user ID from ID token dependency."""
        line_user_id = str(uuid4())
        token = HTTPAuthorizationCredentials(scheme="Bearer", credentials="test_token")

        with patch("app.core.auth.verify_line_id_token") as mock_verify:
            mock_verify.return_value = line_user_id

            result = get_current_line_user_id(token)

            assert result == line_user_id
            mock_verify.assert_called_once_with("test_token")
