import base64
import hashlib
import hmac
from typing import Annotated

from fastapi import FastAPI, Header, HTTPException, Request

from app.core.config import settings
from app.user.router import router as user_router

# 根據 FastAPI 最佳實踐：僅在生產環境中隱藏 docs
if settings.is_development:
    app = FastAPI(
        title="WeaMind API",
        description="API for WeaMind Weather LINE BOT",
    )
else:
    # 生產環境：隱藏所有 API 文檔相關端點
    app = FastAPI(
        title="WeaMind API",
        description="API for WeaMind Weather LINE BOT",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )


def verify_line_signature(body: bytes, signature: str) -> bool:
    """
    Compare HMAC-SHA256 signature with the LINE payload

    Returns:
        bool: verification result
    """
    digest = hmac.new(settings.LINE_CHANNEL_SECRET.encode(), body, hashlib.sha256).digest()
    expected = base64.b64encode(digest).decode()
    return hmac.compare_digest(expected, signature)


@app.get("/")
async def root() -> dict:
    """
    Welcome message for the root route

    Returns:
        dict: API welcome text
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
    Receive LINE webhook and verify its signature
    """
    body = await request.body()
    if not verify_line_signature(body, x_line_signature):
        raise HTTPException(status_code=400, detail="Invalid signature")
    # TODO: handle events in the future
    return {"message": "OK"}
