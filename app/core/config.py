"""Application settings and environment variable management."""

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

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()  # type: ignore
