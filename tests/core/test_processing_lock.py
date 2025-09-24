"""Tests for processing lock functionality."""

import logging
from unittest.mock import Mock, patch

import pytest
from redis.exceptions import ConnectionError, RedisError

from app.core.processing_lock import ProcessingLockService


class TestProcessingLockService:
    """Test cases for ProcessingLockService."""

    def test_init(self) -> None:
        """Test service initialization."""
        service = ProcessingLockService()
        assert service._redis_client is None

    @patch("app.core.processing_lock.settings")
    def test_get_redis_client_no_url(self, mock_settings: Mock) -> None:
        """Test Redis client when URL is not configured."""
        mock_settings.REDIS_URL = None
        service = ProcessingLockService()

        result = service._get_redis_client()

        assert result is None

    @patch("app.core.processing_lock.redis.from_url")
    @patch("app.core.processing_lock.settings")
    def test_get_redis_client_success(self, mock_settings: Mock, mock_from_url: Mock) -> None:
        """Test successful Redis client creation."""
        mock_settings.REDIS_URL = "redis://localhost:6379/0"
        mock_redis = Mock()
        mock_redis.ping.return_value = True
        mock_from_url.return_value = mock_redis

        service = ProcessingLockService()
        result = service._get_redis_client()

        assert result == mock_redis
        mock_from_url.assert_called_once_with("redis://localhost:6379/0", decode_responses=True)
        mock_redis.ping.assert_called_once()

    @patch("app.core.processing_lock.redis.from_url")
    @patch("app.core.processing_lock.settings")
    def test_get_redis_client_connection_error(
        self, mock_settings: Mock, mock_from_url: Mock, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test Redis client creation with connection error."""
        mock_settings.REDIS_URL = "redis://localhost:6379/0"
        mock_from_url.side_effect = ConnectionError("Connection failed")

        service = ProcessingLockService()

        # caplog: pytest fixture to capture log messages
        with caplog.at_level(logging.WARNING):
            result = service._get_redis_client()

        assert result is None
        assert "Failed to connect to Redis" in caplog.text

    @patch("app.core.processing_lock.settings")
    def test_try_acquire_lock_disabled(self, mock_settings: Mock) -> None:
        """Test lock acquisition when processing lock is disabled."""
        mock_settings.PROCESSING_LOCK_ENABLED = False

        service = ProcessingLockService()
        result = service.try_acquire_lock("test:key")

        assert result is True

    @patch("app.core.processing_lock.settings")
    def test_try_acquire_lock_no_redis(
        self, mock_settings: Mock, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test lock acquisition when Redis is unavailable."""
        mock_settings.PROCESSING_LOCK_ENABLED = True
        mock_settings.REDIS_URL = None

        service = ProcessingLockService()

        # caplog: pytest fixture to capture log messages
        with caplog.at_level(logging.WARNING):
            result = service.try_acquire_lock("test:key")

        assert result is True
        assert "Redis unavailable, allowing processing without lock" in caplog.text

    @patch("app.core.processing_lock.settings")
    def test_try_acquire_lock_success(
        self, mock_settings: Mock, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test successful lock acquisition."""
        mock_settings.PROCESSING_LOCK_ENABLED = True
        mock_settings.PROCESSING_LOCK_TTL_SECONDS = 1
        mock_settings.REDIS_URL = "redis://localhost:6379/0"

        mock_redis = Mock()
        mock_redis.ping.return_value = True
        mock_redis.set.return_value = True  # Lock acquired

        service = ProcessingLockService()
        service._redis_client = mock_redis

        # caplog: pytest fixture to capture log messages
        with caplog.at_level(logging.DEBUG):
            result = service.try_acquire_lock("test:key")

        assert result is True
        mock_redis.set.assert_called_once_with("test:key", "1", ex=1, nx=True)
        assert "Processing lock acquired with 1-second TTL" in caplog.text

    @patch("app.core.processing_lock.settings")
    def test_try_acquire_lock_already_exists(
        self, mock_settings: Mock, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test lock acquisition when lock already exists."""
        mock_settings.PROCESSING_LOCK_ENABLED = True
        mock_settings.PROCESSING_LOCK_TTL_SECONDS = 1
        mock_settings.REDIS_URL = "redis://localhost:6379/0"

        mock_redis = Mock()
        mock_redis.ping.return_value = True
        mock_redis.set.return_value = False  # Lock already exists

        service = ProcessingLockService()
        service._redis_client = mock_redis

        # caplog: pytest fixture to capture log messages
        with caplog.at_level(logging.DEBUG):
            result = service.try_acquire_lock("test:key")

        assert result is False
        mock_redis.set.assert_called_once_with("test:key", "1", ex=1, nx=True)
        assert "Processing lock acquisition failed - another request is in progress" in caplog.text

    @patch("app.core.processing_lock.settings")
    def test_try_acquire_lock_redis_error(
        self, mock_settings: Mock, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test lock acquisition with Redis operation error."""
        mock_settings.PROCESSING_LOCK_ENABLED = True
        mock_settings.PROCESSING_LOCK_TTL_SECONDS = 1
        mock_settings.REDIS_URL = "redis://localhost:6379/0"

        mock_redis = Mock()
        mock_redis.ping.return_value = True
        mock_redis.set.side_effect = RedisError("Redis operation failed")

        service = ProcessingLockService()
        service._redis_client = mock_redis

        # caplog: pytest fixture to capture log messages
        with caplog.at_level(logging.WARNING):
            result = service.try_acquire_lock("test:key")

        assert result is True  # Fail open
        assert "Failed to acquire processing lock, allowing processing" in caplog.text

    def test_build_lock_key_success(self) -> None:
        """Test successful lock key building."""
        mock_source = Mock()
        mock_source.user_id = "U12345"

        service = ProcessingLockService()
        result = service.build_lock_key(mock_source)

        assert result == "processing:user:U12345"

    def test_build_lock_key_no_user_id(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test lock key building when user_id is missing."""
        mock_source = Mock()
        del mock_source.user_id  # Simulate missing user_id

        service = ProcessingLockService()

        # caplog: pytest fixture to capture log messages
        with caplog.at_level(logging.WARNING):
            result = service.build_lock_key(mock_source)

        assert result is None
        assert "No user_id found in event source" in caplog.text

    def test_build_lock_key_attribute_error(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test lock key building with invalid source structure."""
        service = ProcessingLockService()

        # caplog: pytest fixture to capture log messages
        with caplog.at_level(logging.WARNING):
            result = service.build_lock_key(None)

        assert result is None
        assert "No user_id found in event source" in caplog.text

    def test_build_lock_key_getattr_exception(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test lock key building when getattr raises AttributeError."""
        service = ProcessingLockService()
        mock_source = Mock()
        mock_source.user_id = "U12345"

        # Patch getattr in the specific module context
        with patch("app.core.processing_lock.getattr") as mock_getattr:
            mock_getattr.side_effect = AttributeError("Getattr failed")

            with caplog.at_level(logging.WARNING):
                result = service.build_lock_key(mock_source)

            assert result is None
            assert "Invalid event source structure" in caplog.text
