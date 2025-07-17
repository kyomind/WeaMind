"""Logging configuration for the application."""

import logging
import sys

from app.core.config import settings


def setup_logging() -> None:
    """Setup application logging configuration."""
    # Determine log level based on environment and debug settings
    if settings.DEBUG:
        log_level = logging.DEBUG
    elif settings.is_production:
        log_level = logging.WARNING
    else:
        log_level = logging.INFO

    # Using a more readable log format: tight and concise
    # eg. "2025-07-17 17:26:54 INFO [app.module:line:123] Message processed"
    log_format = "%(asctime)s %(levelname)s [%(name)s:%(lineno)d] %(message)s"

    # Ensure logs directory exists
    logs_dir = settings.logs_dir
    logs_dir.mkdir(exist_ok=True)

    # Setup handlers: console and file
    console_handler = logging.StreamHandler(sys.stdout)
    file_handler = logging.FileHandler(logs_dir / "app.log", encoding="utf-8")

    # Basic logging configuration
    logging.basicConfig(
        level=log_level,
        format=log_format,
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[console_handler, file_handler],
    )

    # Set SQLAlchemy logging level based on DEBUG setting
    if settings.DEBUG:
        logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
    else:
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

    # Set uvicorn logging level
    uvicorn_logger = logging.getLogger("uvicorn")
    uvicorn_access_logger = logging.getLogger("uvicorn.access")

    uvicorn_logger.setLevel(logging.INFO)
    uvicorn_access_logger.setLevel(logging.INFO)

    # Add file handler to uvicorn loggers so they also write to file
    uvicorn_logger.addHandler(file_handler)
    uvicorn_access_logger.addHandler(file_handler)

    # Log startup info
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured for {settings.ENV} environment")
    logger.info(f"Log level set to: {logging.getLevelName(log_level)}")
    logger.info(f"Logs directory: {logs_dir}")
