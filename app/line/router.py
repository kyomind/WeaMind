"""LINE Bot webhook router."""

import logging
from typing import Annotated

from fastapi import APIRouter, Header, HTTPException, Request
from linebot.v3.exceptions import InvalidSignatureError

from app.line.service import webhook_handler

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/line")


@router.post("/webhook")
async def line_webhook(
    request: Request,
    x_line_signature: Annotated[str, Header(alias="X-Line-Signature")],
) -> dict:
    """
    Receive LINE webhook and verify its signature using official SDK.

    Args:
        request: The FastAPI request object
        x_line_signature: The LINE signature header

    Returns:
        dict: Success message

    Raises:
        HTTPException: If signature verification fails
    """
    # Validate content type
    content_type = request.headers.get("content-type", "")
    if not content_type.startswith("application/json"):
        logger.warning("Invalid content type received")
        raise HTTPException(status_code=400, detail="Invalid content type")

    body: bytes = await request.body()
    """
    body example:
    {
      "destination": "<bot_userid>",  # This is your LINE Official Account (bot) userId
      "events": [
        {
          "type": "message",
          "message": {
            "id": "1234567890",
            "type": "text",
            "text": "Hello, world"
          },
          "timestamp": 1620000000000,
          "source": {
            "type": "user",
            "userId": "<user_userid>"  # This is the userId of the user who sent the message
          },
          "replyToken": "abcdefg1234567",
          "mode": "active"
        }
      ]
    }
    """
    body_as_text: str = body.decode("utf-8")
    logger.info(f"Received LINE webhook: {body_as_text}")

    # Handle webhook event using official SDK
    try:
        webhook_handler.handle(body_as_text, x_line_signature)
    except InvalidSignatureError:
        logger.warning("Invalid LINE signature received")
        raise HTTPException(status_code=400, detail="Invalid signature") from None
    except Exception:
        logger.exception("Error processing webhook")
        # For other errors, return 200 to prevent LINE from retrying
        # This includes invalid webhook data format, etc.
        return {"message": "OK"}
    else:
        logger.info("LINE webhook processed successfully")
        return {"message": "OK"}
