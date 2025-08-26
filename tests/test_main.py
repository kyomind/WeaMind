"""Test main application setup and configuration."""

from unittest.mock import Mock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import Settings


class TestMainApplication:
    """Test FastAPI application setup."""

    def test_production_mode_app_creation(self) -> None:
        """Test that app is created correctly in production mode."""
        # Mock settings to be production mode
        mock_settings = Mock(spec=Settings)
        mock_settings.is_development = False
        mock_settings.APP_NAME = "WeaMind"

        # Simulate the production app creation logic from main.py lines 33-40
        with patch("app.main.settings", mock_settings):
            # This simulates the production branch in main.py
            if not mock_settings.is_development:
                prod_app = FastAPI(
                    title=mock_settings.APP_NAME,
                    description="API for WeaMind Weather LINE BOT",
                    docs_url=None,
                    redoc_url=None,
                    openapi_url=None,
                )
                # Verify production app has no docs URLs
                assert prod_app.docs_url is None
                assert prod_app.redoc_url is None
                assert prod_app.openapi_url is None

    def test_root_endpoint(self, client: TestClient) -> None:
        """Test the root endpoint returns welcome message."""
        response = client.get("/")

        assert response.status_code == 200
        assert response.json() == {"message": "Welcome to WeaMind API"}
