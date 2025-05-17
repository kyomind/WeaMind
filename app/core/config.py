import os

from pydantic import BaseSettings


class Settings(BaseSettings):
    """
    這個類別用於管理應用程式的環境變數和配置設定。
    """

    # Environment variables for the application
    APP_NAME: str = "WeaMind API"
    DEBUG: bool = os.getenv("DEBUG", "False") == "True"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")

    # Database settings (to be configured based on implementation)
    DATABASE_URL: str | None = os.getenv("DATABASE_URL", None)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
