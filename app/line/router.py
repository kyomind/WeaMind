"""LINE Bot webhook router."""

import base64
import hashlib
import hmac
import logging
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Request
from linebot.v3.exceptions import InvalidSignatureError

from app.core.config import settings
from app.line.service import webhook_handler

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/line")


@router.post("/webhook")
async def line_webhook(
    request: Request,
    x_line_signature: Annotated[str, Header(alias="X-Line-Signature")],
    background_tasks: BackgroundTasks,
) -> dict:
    """
    Receive LINE webhook, validate basics quickly, ACK immediately, and defer processing.

    Behavior:
    - Validate content type and signature synchronously (cheap and secure)
    - Immediately return 200 OK (fast ACK)
    - Schedule the actual handling in a background task

    Args:
      request: FastAPI request object
      x_line_signature: The LINE signature header
      background_tasks: FastAPI background task scheduler

    Returns:
      dict: Success message (ACK)

    Raises:
      HTTPException: If content type or signature verification fails
    """
    # 1) Validate content type (cheap)
    content_type = request.headers.get("content-type", "")
    if not content_type.startswith("application/json"):
        logger.warning("Invalid content type received")
        raise HTTPException(status_code=400, detail="Invalid content type")

    # 2) Read body once (needed for both signature and handler)
    body: bytes = await request.body()

    # 3) Verify LINE signature synchronously (cheap, avoids scheduling invalid work)
    try:
        expected_signature = base64.b64encode(
            hmac.new(settings.LINE_CHANNEL_SECRET.encode("utf-8"), body, hashlib.sha256).digest()
        ).decode("utf-8")
    except Exception:
        logger.exception("Failed to compute LINE signature for verification")
        raise HTTPException(status_code=400, detail="Signature verification error") from None

    if not hmac.compare_digest(expected_signature, x_line_signature):
        logger.warning("Invalid LINE signature received")
        raise HTTPException(status_code=400, detail="Invalid signature")

    # 4) Log reception (avoid logging full body for security)
    body_as_text: str = body.decode("utf-8")
    logger.info(f"Received LINE webhook: length={len(body_as_text)} bytes")

    # 5) Schedule actual handling; any exceptions are logged without impacting ACK
    def _process_webhook(body_text: str, signature: str) -> None:
        try:
            webhook_handler.handle(body_text, signature)
            logger.info("LINE webhook completed")
        except InvalidSignatureError:
            # Should not happen since we verified already, but keep for safety
            logger.warning("Background processing failed due to invalid signature")
        except Exception:
            logger.exception("Error processing webhook in background")

    background_tasks.add_task(_process_webhook, body_as_text, x_line_signature)

    # 6) Fast ACK
    return {"message": "OK"}
