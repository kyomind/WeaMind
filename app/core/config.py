from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    這個類別用於管理應用程式的環境變數和配置設定
    """

    APP_NAME: str = "WeaMind API"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    DATABASE_URL: str = "DUMMY_DATABASE_URL"
    POSTGRES_USER: str = "DUMMY_USER"
    POSTGRES_PASSWORD: str = "DUMMY_PASSWORD"
    POSTGRES_HOST: str = "DUMMY_HOST"  # 原本為 POSTGRES_SERVER，改為更直觀的名稱
    POSTGRES_DB: str = "DUMMY_DB"
    POSTGRES_PORT: int = 5432  # 新增此欄位，對應 .env.example
    LINE_CHANNEL_SECRET: str = "CHANGE_ME"  # 驗證 LINE Webhook 使用

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
