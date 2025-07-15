"""Application settings and environment variable management."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """應用程式設定類別."""

    # 基本應用設定
    APP_NAME: str = "WeaMind API"
    DEBUG: bool = False
    ENV: str = "development"

    # 資料庫設定
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str
    POSTGRES_DB: str
    POSTGRES_PORT: int = 5432
    DATABASE_URL: str | None = None

    # LINE Bot 設定
    LINE_CHANNEL_SECRET: str
    LINE_CHANNEL_ACCESS_TOKEN: str

    # 環境判斷的便利屬性
    @property
    def is_development(self) -> bool:
        """檢查是否為開發環境."""
        return self.ENV.lower() in ("development", "dev")

    @property
    def is_production(self) -> bool:
        """檢查是否為生產環境."""
        return self.ENV.lower() in ("production", "prod")

    @property
    def database_url(self) -> str:
        """取得資料庫連線URL."""
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return (
            f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()  # type: ignore
