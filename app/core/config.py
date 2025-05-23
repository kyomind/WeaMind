from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    這個類別用於管理應用程式的環境變數和配置設定
    """

    APP_NAME: str = "WeaMind API"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    DATABASE_URL: str | None = None

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
