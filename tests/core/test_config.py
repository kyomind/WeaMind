"""Tests for app.core.config module."""

from pathlib import Path

from app.core.config import BASE_DIR, Settings, settings


class TestSettings:
    """Test Settings class."""

    def test_default_values(self) -> None:
        """Test default values are set correctly."""
        assert settings.APP_NAME == "WeaMind API"
        assert settings.DEBUG is False
        assert settings.ENV == "development"
        assert settings.POSTGRES_PORT == 5432

    def test_logs_dir_property(self) -> None:
        """Test logs_dir property returns correct path."""
        expected_path = BASE_DIR / "logs"
        assert settings.logs_dir == expected_path

    def test_is_development_property(self) -> None:
        """Test is_development property."""
        # Test with default environment (development)
        assert settings.is_development is True

        # Create a test settings instance with custom environment
        test_settings = Settings(
            POSTGRES_USER="test_user",
            POSTGRES_PASSWORD="test_password",
            POSTGRES_HOST="localhost",
            POSTGRES_DB="test_db",
            LINE_CHANNEL_SECRET="test_secret",
            LINE_CHANNEL_ACCESS_TOKEN="test_token",
            ENV="development",
        )
        assert test_settings.is_development is True

        # Test dev environment
        test_settings_dev = Settings(
            POSTGRES_USER="test_user",
            POSTGRES_PASSWORD="test_password",
            POSTGRES_HOST="localhost",
            POSTGRES_DB="test_db",
            LINE_CHANNEL_SECRET="test_secret",
            LINE_CHANNEL_ACCESS_TOKEN="test_token",
            ENV="dev",
        )
        assert test_settings_dev.is_development is True

        # Test production environment
        test_settings_prod = Settings(
            POSTGRES_USER="test_user",
            POSTGRES_PASSWORD="test_password",
            POSTGRES_HOST="localhost",
            POSTGRES_DB="test_db",
            LINE_CHANNEL_SECRET="test_secret",
            LINE_CHANNEL_ACCESS_TOKEN="test_token",
            ENV="production",
        )
        assert test_settings_prod.is_development is False

    def test_is_production_property(self) -> None:
        """Test is_production property."""
        # Test with default environment (should be false)
        assert settings.is_production is False

        # Test production environment
        test_settings_prod = Settings(
            POSTGRES_USER="test_user",
            POSTGRES_PASSWORD="test_password",
            POSTGRES_HOST="localhost",
            POSTGRES_DB="test_db",
            LINE_CHANNEL_SECRET="test_secret",
            LINE_CHANNEL_ACCESS_TOKEN="test_token",
            ENV="production",
        )
        assert test_settings_prod.is_production is True

        # Test prod environment
        test_settings_prod2 = Settings(
            POSTGRES_USER="test_user",
            POSTGRES_PASSWORD="test_password",
            POSTGRES_HOST="localhost",
            POSTGRES_DB="test_db",
            LINE_CHANNEL_SECRET="test_secret",
            LINE_CHANNEL_ACCESS_TOKEN="test_token",
            ENV="prod",
        )
        assert test_settings_prod2.is_production is True

        # Test development environment
        test_settings_dev = Settings(
            POSTGRES_USER="test_user",
            POSTGRES_PASSWORD="test_password",
            POSTGRES_HOST="localhost",
            POSTGRES_DB="test_db",
            LINE_CHANNEL_SECRET="test_secret",
            LINE_CHANNEL_ACCESS_TOKEN="test_token",
            ENV="development",
        )
        assert test_settings_dev.is_production is False

    def test_database_url_property_with_database_url_set(self) -> None:
        """Test database_url property when DATABASE_URL is set."""
        test_settings = Settings(
            POSTGRES_USER="test_user",
            POSTGRES_PASSWORD="test_password",
            POSTGRES_HOST="localhost",
            POSTGRES_DB="test_db",
            LINE_CHANNEL_SECRET="test_secret",
            LINE_CHANNEL_ACCESS_TOKEN="test_token",
            DATABASE_URL="postgresql://custom_url",
        )
        assert test_settings.database_url == "postgresql://custom_url"

    def test_database_url_property_without_database_url(self) -> None:
        """Test database_url property when DATABASE_URL is not set."""
        # Create a Settings instance without DATABASE_URL
        test_settings = Settings(
            POSTGRES_USER="test_user",
            POSTGRES_PASSWORD="test_password",
            POSTGRES_HOST="localhost",
            POSTGRES_DB="test_db",
            POSTGRES_PORT=5432,
            LINE_CHANNEL_SECRET="test_secret",
            LINE_CHANNEL_ACCESS_TOKEN="test_token",
            DATABASE_URL=None,  # Explicitly set to None
        )
        expected_url = "postgresql+psycopg://test_user:test_password@localhost:5432/test_db"
        assert test_settings.database_url == expected_url

    def test_database_url_property_custom_port(self) -> None:
        """Test database_url property with custom port."""
        test_settings = Settings(
            POSTGRES_USER="test_user",
            POSTGRES_PASSWORD="test_password",
            POSTGRES_HOST="localhost",
            POSTGRES_DB="test_db",
            POSTGRES_PORT=5433,
            LINE_CHANNEL_SECRET="test_secret",
            LINE_CHANNEL_ACCESS_TOKEN="test_token",
            DATABASE_URL=None,  # Explicitly set to None
        )
        expected_url = "postgresql+psycopg://test_user:test_password@localhost:5433/test_db"
        assert test_settings.database_url == expected_url


class TestBaseDir:
    """Test BASE_DIR constant."""

    def test_base_dir_is_correct(self) -> None:
        """Test BASE_DIR points to the correct directory."""
        # BASE_DIR should be the parent of parent of parent of this file
        # config.py is in app/core/, so BASE_DIR should be 3 levels up
        assert isinstance(BASE_DIR, Path)
        assert BASE_DIR.is_absolute()
        assert BASE_DIR.name == "WeaMind"
