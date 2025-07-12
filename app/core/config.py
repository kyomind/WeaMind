from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    This class is used to manage environment variables and configuration
    settings for the application.
    """

    APP_NAME: str = "WeaMind API"
    DEBUG: bool = False
    ENV: str = "development"  # 改為與 Docker Compose 一致的變數名稱
    POSTGRES_USER: str = "DUMMY_USER"
    POSTGRES_PASSWORD: str = "DUMMY_PASSWORD"
    POSTGRES_HOST: str = "DUMMY_HOST"
    POSTGRES_DB: str = "DUMMY_DB"
    POSTGRES_PORT: int = 5432
    LINE_CHANNEL_SECRET: str = "CHANGE_ME"
    LINE_CHANNEL_ACCESS_TOKEN: str = "CHANGE_ME"
    DATABASE_URL: str | None = None  # New: allows specifying the full connection string directly

    # 新增環境判斷的便利屬性
    @property
    def is_development(self) -> bool:
        """檢查是否為開發環境."""
        return self.ENV.lower() in ("development", "dev")

    @property
    def is_production(self) -> bool:
        """檢查是否為生產環境."""
        return self.ENV.lower() in ("production", "prod")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
