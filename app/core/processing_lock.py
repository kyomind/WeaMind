"""
Processing lock module for preventing duplicate user requests.

This module implements a distributed lock mechanism using Redis to prevent
duplicate processing of user requests across multiple process instances.
The lock uses a "fail-open" strategy - if Redis is unavailable, requests
are allowed to proceed rather than being blocked. This prioritizes service
availability over duplicate prevention.

Key features:
- Atomic lock acquisition using Redis SET NX EX command
- Automatic TTL-based lock expiration (configurable timeout)
- Graceful degradation when Redis is unavailable
- Support for LINE Bot webhook event sources
"""

import logging
from typing import TYPE_CHECKING

import redis
from redis.exceptions import ConnectionError, RedisError

from app.core.config import settings

if TYPE_CHECKING:
    from linebot.v3.webhooks.models.source import Source

logger = logging.getLogger(__name__)


class ProcessingLockService:
    """Service for managing processing locks using Redis."""

    def __init__(self) -> None:
        """Initialize the processing lock service."""
        self._redis_client: redis.Redis | None = None

    def _get_redis_client(self) -> redis.Redis | None:
        """Get Redis client connection."""
        if not settings.REDIS_URL:
            logger.warning("Redis URL not configured, processing lock disabled")
            return None

        # Reuse existing connection if available
        if self._redis_client is None:
            try:
                self._redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
                # Test connection to ensure Redis is reachable
                self._redis_client.ping()
                logger.info("Redis connection established for processing lock")
            except (ConnectionError, RedisError) as e:
                logger.warning(f"Failed to connect to Redis, processing lock disabled: {e}")
                self._redis_client = None

        return self._redis_client

    def try_acquire_lock(self, key: str) -> bool:
        """
        Try to acquire a processing lock with fixed 1-second TTL.

        Uses Redis SET key value EX 1 NX command for atomic operation.
        The lock automatically expires after 1 second regardless of processing completion.
        This provides better protection against rapid successive requests while maintaining
        simplicity by eliminating manual lock release requirements.

        Args:
            key: The lock key to acquire

        Returns:
            bool: True if lock acquired, False if already locked or Redis unavailable
        """
        if not settings.PROCESSING_LOCK_ENABLED:
            return True

        redis_client = self._get_redis_client()
        if redis_client is None:
            # Fail-open strategy: prioritize service availability over duplicate prevention
            # Allow processing to continue when Redis is unavailable
            logger.warning("Redis unavailable, allowing processing without lock")
            return True

        try:
            # SET key 1 EX 1 NX - atomic operation with fixed 1-second TTL
            # Note: The value "1" is arbitrary - we only care about key existence
            is_lock_acquired = redis_client.set(key, "1", ex=1, nx=True)
            if is_lock_acquired:
                logger.debug("Processing lock acquired with 1-second TTL")
                return True
            else:
                logger.debug("Processing lock acquisition failed - another request is in progress")
                return False
        except (ConnectionError, RedisError) as e:
            logger.warning(f"Failed to acquire processing lock, allowing processing: {e}")
            # Fail-open strategy: continue processing despite Redis errors
            return True

    def build_actor_key(self, source: "Source | None") -> str | None:
        """
        Build processing lock key from LINE event source.

        Extracts user_id from various LINE event source types (UserSource,
        GroupSource, RoomSource) to create a unique lock key. Returns None
        if user_id cannot be determined (e.g., system events, malformed data).

        Args:
            source: LINE event source object

        Returns:
            str | None: Lock key if userId found, None otherwise
        """
        try:
            # Use getattr for safe access - user_id may not exist in all source types
            user_id = getattr(source, "user_id", None)
            if user_id:
                return f"processing:user:{user_id}"
            else:
                # This can happen with system events or when user_id is not available
                logger.warning("No user_id found in event source")
                return None
        except AttributeError:
            # Handle cases where source is None or has unexpected structure
            logger.warning("Invalid event source structure")
            return None


# Global instance - module-level singleton pattern
# This ensures consistent lock state across the application while
# allowing Redis connection reuse and avoiding repeated initialization
processing_lock_service = ProcessingLockService()
