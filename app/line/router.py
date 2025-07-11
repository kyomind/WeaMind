"""LINE Bot webhook router."""

import logging
from typing import Annotated

from fastapi import APIRouter, Header, HTTPException, Request

from app.line.service import process_webhook_body
from app.line.utils import verify_line_signature

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/line")


@router.post("/webhook")
async def line_webhook(
    request: Request,
    x_line_signature: Annotated[str, Header(alias="X-Line-Signature")],
) -> dict:
    """
    Receive LINE webhook and verify its signature.

    Args:
        request: The FastAPI request object
        x_line_signature: The LINE signature header

    Returns:
        dict: Success message

    Raises:
        HTTPException: If signature verification fails
    """
    # 驗證內容類型
    content_type = request.headers.get("content-type", "")
    if not content_type.startswith("application/json"):
        logger.warning(f"Invalid content type: {content_type}")
        raise HTTPException(status_code=400, detail="Invalid content type")

    body = await request.body()

    # 驗證 LINE 簽名
    if not verify_line_signature(body, x_line_signature):
        logger.warning("Invalid LINE signature received")
        raise HTTPException(status_code=400, detail="Invalid signature")

    # 處理 webhook 事件
    try:
        await process_webhook_body(body)
    except Exception as e:
        logger.exception("Error processing webhook")
        raise HTTPException(status_code=500, detail="Internal server error") from e
    else:
        logger.info("LINE webhook processed successfully")
        return {"message": "OK"}
