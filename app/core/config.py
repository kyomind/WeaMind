"""Application settings, environment variable management, and logging configuration."""

import logging
import sys
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Base directory of the project (similar to Django's BASE_DIR)
BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """Application settings class."""

    # Basic application settings
    APP_NAME: str = "WeaMind API"
    DEBUG: bool = False
    ENV: str = "development"

    # Database settings
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str
    POSTGRES_DB: str
    POSTGRES_PORT: int = 5432
    DATABASE_URL: str | None = None

    # LINE Bot settings
    LINE_CHANNEL_SECRET: str
    LINE_CHANNEL_ACCESS_TOKEN: str
    # LINE Login settings
    LINE_CHANNEL_ID: str | None = None
    ENABLE_ID_TOKEN_SIGNATURE_VERIFICATION: bool = True

    # Application URL settings
    BASE_URL: str = "https://api.kyomind.tw"

    # Processing lock settings
    PROCESSING_LOCK_ENABLED: bool = True
    PROCESSING_LOCK_TTL_SECONDS: int = 1
    REDIS_URL: str | None = "redis://redis:6379/0"

    @property
    def logs_dir(self) -> Path:
        """Get the logs directory path."""
        return BASE_DIR / "logs"

    @property
    def is_development(self) -> bool:
        """Check if current environment is development."""
        return self.ENV.lower() in ("development", "dev")

    @property
    def is_production(self) -> bool:
        """Check if current environment is production."""
        return self.ENV.lower() in ("production", "prod")

    @property
    def database_url(self) -> str:
        """Get the database connection URL."""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return (
            f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # Ignore undefined environment variables
    )


settings = Settings()  # type: ignore


def setup_logging() -> None:
    """Setup application logging configuration."""
    # Determine log level based on environment and debug settings
    if settings.DEBUG:
        log_level = logging.DEBUG
    elif settings.is_production:
        log_level = logging.DEBUG
    else:
        log_level = logging.INFO

    # Using log format with milliseconds for precise timing analysis
    # eg. "2025-09-14 05:48:16.123 INFO [app.module:line:123] Message processed"
    log_format = "%(asctime)s.%(msecs)03d %(levelname)s [%(name)s:%(lineno)d] %(message)s"

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
