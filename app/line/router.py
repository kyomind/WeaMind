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
    # 驗證內容類型
    content_type = request.headers.get("content-type", "")
    if not content_type.startswith("application/json"):
        logger.warning("Invalid content type received")
        raise HTTPException(status_code=400, detail="Invalid content type")

    body = await request.body()

    # 使用官方 SDK 處理 webhook 事件
    try:
        webhook_handler.handle(body.decode("utf-8"), x_line_signature)
    except InvalidSignatureError:
        logger.warning("Invalid LINE signature received")
        raise HTTPException(status_code=400, detail="Invalid signature") from None
    except Exception:
        logger.exception("Error processing webhook")
        # 對於其他錯誤，返回 200 以防止 LINE 重試
        # 這包括無效的 webhook 數據格式等
        return {"message": "OK"}
    else:
        logger.info("LINE webhook processed successfully")
        return {"message": "OK"}
