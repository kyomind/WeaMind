from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    This class is used to manage environment variables and configuration
    settings for the application
    """

    APP_NAME: str = "WeaMind API"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    POSTGRES_USER: str = "DUMMY_USER"
    POSTGRES_PASSWORD: str = "DUMMY_PASSWORD"
    POSTGRES_HOST: str = "DUMMY_HOST"
    POSTGRES_DB: str = "DUMMY_DB"
    POSTGRES_PORT: int = 5432
    LINE_CHANNEL_SECRET: str = "CHANGE_ME"
    DATABASE_URL: str | None = None  # New: allows specifying the full connection string directly

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
