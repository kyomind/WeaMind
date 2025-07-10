"""Utility functions for LINE Bot operations."""

import base64
import hashlib
import hmac

from app.core.config import settings


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


def should_skip_signature_verification() -> bool:
    """
    Determine if signature verification should be skipped.

    Returns:
        bool: True if should skip verification (development mode with default secrets)
    """
    # 只在開發環境且使用預設 secrets 時跳過簽名驗證
    # TEST_SECRET 不在此列表中，確保測試環境會執行簽名驗證
    default_secrets = ["CHANGE_ME", "your_line_channel_secret", "your-channel-secret"]
    return settings.is_development and settings.LINE_CHANNEL_SECRET in default_secrets
