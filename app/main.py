import base64
import hashlib
import hmac
from typing import Annotated

from fastapi import FastAPI, Header, HTTPException, Request

from app.core.config import settings
from app.user.router import router as user_router

app = FastAPI(title="WeaMind API", description="API for WeaMind Weather LINE BOT")


def verify_line_signature(body: bytes, signature: str) -> bool:
    """
    Compare HMAC-SHA256 signature with LINE payload

    Returns:
        bool: 驗證結果
    """
    digest = hmac.new(settings.LINE_CHANNEL_SECRET.encode(), body, hashlib.sha256).digest()
    expected = base64.b64encode(digest).decode()
    return hmac.compare_digest(expected, signature)


@app.get("/")
async def root() -> dict:
    """
    歡迎使用 WeaMind API 的根路由

    Returns:
        dict: API 的歡迎訊息
    """
    return {"message": "Welcome to WeaMind API"}


# Include routers from modules
app.include_router(user_router, tags=["user"])


@app.post("/line/webhook")
async def line_webhook(
    request: Request,
    x_line_signature: Annotated[str, Header(...)],
) -> dict:
    """
    接收 LINE webhook 並驗證簽名
    """
    body = await request.body()
    if not verify_line_signature(body, x_line_signature):
        raise HTTPException(status_code=400, detail="Invalid signature")
    # 未來可在此處理 event
    return {"message": "OK"}
