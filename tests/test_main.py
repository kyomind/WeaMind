"""Test main application setup and configuration."""

import importlib
import tempfile
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient


class TestMainApplication:
    """Test FastAPI application integration."""

    def test_app_basic_properties(self) -> None:
        """Test that the actual FastAPI app has expected basic properties."""
        # Import the real app instance
        import app.main

        # Test basic app properties
        assert "WeaMind" in app.main.app.title
        assert "Weather LINE BOT" in app.main.app.description

    def test_root_endpoint(self, client: TestClient) -> None:
        """Test the root endpoint returns welcome message."""
        response = client.get("/")

        assert response.status_code == 200
        assert response.json() == {"message": "Welcome to WeaMind API"}

    def test_health_endpoint(self, client: TestClient) -> None:
        """Test the health check endpoint returns ok status."""
        response = client.get("/health")

        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_app_has_registered_routers(self) -> None:
        """Test that the app has registered all expected routers."""
        import app.main

        # The app should have multiple routes registered from different routers
        # (root + user routes + line routes + static files)
        assert len(app.main.app.routes) > 3  # Should have more than just basic routes

    def test_production_mode_configuration(self) -> None:
        """Test FastAPI app configuration in production mode."""
        # Create a temporary directory for logs
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch("app.core.config.settings") as mock_settings:
                mock_settings.is_development = False
                mock_settings.APP_NAME = "WeaMind Test"
                mock_settings.logs_dir = Path(temp_dir)

                # Import the main module to trigger app creation in production mode
                import app.main

                importlib.reload(app.main)

                # Check that docs are disabled in production
                prod_app = app.main.app
                assert prod_app.docs_url is None
                assert prod_app.redoc_url is None
                assert prod_app.openapi_url is None
