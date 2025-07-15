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

    # Optimized format: date, level, logger name, line number, message
    log_format = "%(asctime)s | %(levelname)-8s | %(name)-20s | L%(lineno)d | %(message)s"

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
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)

    # Log startup info
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured for {settings.ENV} environment")
