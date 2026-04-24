"""LINE Bot webhook router."""

import base64
import hashlib
import hmac
import logging
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Header, HTTPException, Request
from linebot.v3.exceptions import InvalidSignatureError

from app.core.config import settings
from app.line import metrics as line_metrics
from app.line.service import process_webhook_events

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/line")


@router.post("/webhook")
async def line_webhook(
    request: Request,
    x_line_signature: Annotated[str, Header(alias="X-Line-Signature")],
    background_tasks: BackgroundTasks,
) -> dict:
    """
        Receive a LINE webhook, validate it quickly, and defer event processing.

        This route owns only the synchronous boundary concerns: content type
        validation, signature verification, request-body decoding, and the received
        metric. Event-level success, error, and duration metrics are delegated to
        the service-layer dispatch path so they can be recorded per event instead of
        per request.

    Behavior:
    - Validate content type and signature synchronously (cheap and secure)
    - Immediately return 200 OK (fast ACK)
        - Record the received webhook event types before background work starts
        - Schedule the actual handling in a background task

    Args:
                request: FastAPI request object.
                x_line_signature: The LINE signature header.
                background_tasks: FastAPI background task scheduler.

    Returns:
                Success message returned to LINE as the fast ACK payload.

    Raises:
                HTTPException: If content type or signature verification fails.
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
    event_types = line_metrics.extract_event_types_from_body(body_as_text)
    line_metrics.record_webhook_received(event_types)
    logger.info(f"Received LINE webhook: length={len(body_as_text)} bytes")

    # 5) Schedule actual handling; any exceptions are logged without impacting ACK
    def _process_webhook(body_text: str, signature: str, current_event_types: list[str]) -> None:
        """
        Process a verified webhook request inside the background task boundary.

        Args:
            body_text: Raw webhook request body decoded as UTF-8 text.
            signature: Verified LINE signature header value.
            current_event_types: Event types classified at the router boundary,
                reused as fallback metric labels if parsing fails later.
        """
        try:
            process_webhook_events(body_text, signature, current_event_types)
            logger.info("LINE webhook completed")
        except InvalidSignatureError:
            # Should not happen since we verified already, but keep for safety
            logger.warning("Background processing failed due to invalid signature")
        except Exception:
            logger.exception("Error processing webhook in background")

    background_tasks.add_task(_process_webhook, body_as_text, x_line_signature, event_types)

    # 6) Fast ACK
    return {"message": "OK"}
