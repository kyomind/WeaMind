"""FastAPI application entry point and router registration."""

from fastapi import FastAPI

from app.core.config import settings
from app.line.router import router as line_router
from app.user.router import router as user_router

# 根據環境建立 FastAPI 應用程式
if settings.is_development:
    app = FastAPI(
        title=settings.APP_NAME,
        description="API for WeaMind Weather LINE BOT",
    )
else:
    # 生產環境：隱藏 API 文檔
    app = FastAPI(
        title=settings.APP_NAME,
        description="API for WeaMind Weather LINE BOT",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )


@app.get("/")
async def root() -> dict:
    """
    Welcome message for the root route.

    Returns:
        dict: API welcome text
    """
    return {"message": "Welcome to WeaMind API"}


# Include routers from modules
app.include_router(user_router, tags=["user"])
app.include_router(line_router, tags=["line"])
