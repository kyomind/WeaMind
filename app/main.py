"""FastAPI application entry point and router registration."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.admin_divisions import initialize_admin_divisions
from app.core.config import settings, setup_logging
from app.line.router import router as line_router
from app.user.router import router as user_router

# Setup logging
setup_logging()

# Initialize administrative divisions data
initialize_admin_divisions()

# Get logger for this module
logger = logging.getLogger(__name__)

# Create FastAPI app based on environment
if settings.is_development:
    app = FastAPI(
        title=settings.APP_NAME,
        description="API for WeaMind Weather LINE BOT",
    )
    logger.info("FastAPI app created in development mode")
else:
    # Hide API docs in production
    app = FastAPI(
        title=settings.APP_NAME,
        description="API for WeaMind Weather LINE BOT",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    logger.info("FastAPI app created in production mode")

# 🔒 安全配置：CORS 設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://liff.line.me"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/")
async def root() -> dict:
    """
    Welcome message for the root route.

    Returns:
        dict: API welcome text
    """
    return {"message": "Welcome to WeaMind API"}


@app.get("/health")
async def health() -> dict:
    """
    Health check endpoint for Kubernetes liveness and readiness probes.

    Returns:
        dict: Service health status
    """
    return {"status": "ok"}


# Register routers from modules
app.include_router(user_router, tags=["user"])  # no prefix because the domain is api.kyomind.tw
app.include_router(line_router, tags=["line"])

# Mount static files for LIFF
app.mount("/static", StaticFiles(directory="static"), name="static")

logger.info("All routers registered successfully")
