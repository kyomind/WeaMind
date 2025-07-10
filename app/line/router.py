"""LINE Bot webhook router."""

from typing import Annotated

from fastapi import APIRouter, Header, HTTPException, Request

from app.line.service import process_webhook_body
from app.line.utils import should_skip_signature_verification, verify_line_signature

router = APIRouter(prefix="/line")


@router.post("/webhook")
async def line_webhook(
    request: Request,
    x_line_signature: Annotated[str, Header(...)],
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
    body = await request.body()

    # 如果是開發環境或者環境變數還是預設值，跳過簽名驗證
    if should_skip_signature_verification():
        print("Development mode or default secret: skipping signature verification")
        await process_webhook_body(body)
        return {"message": "OK"}

    if not verify_line_signature(body, x_line_signature):
        raise HTTPException(status_code=400, detail="Invalid signature")

    # 處理 webhook 事件
    await process_webhook_body(body)
    return {"message": "OK"}
