"""Utility functions for LINE Bot operations."""

import base64
import hashlib
import hmac
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


def verify_line_signature(body: bytes, signature: str) -> bool:
    """
    Verify LINE webhook signature using HMAC-SHA256.

    Args:
        body: The raw request body as bytes
        signature: The X-Line-Signature header value

    Returns:
        bool: True if signature is valid, False otherwise
    """
    digest = hmac.new(settings.LINE_CHANNEL_SECRET.encode(), body, hashlib.sha256).digest()
    expected = base64.b64encode(digest).decode()
    return hmac.compare_digest(expected, signature)
