"""Test main application setup and configuration."""

from fastapi.testclient import TestClient


class TestMainApplication:
    """Test FastAPI application integration."""

    def test_app_basic_properties(self) -> None:
        """Test that the actual FastAPI app has expected basic properties."""
        # Import the real app instance
        from app.main import app

        # Test basic app properties
        assert "WeaMind" in app.title
        assert "Weather LINE BOT" in app.description

    def test_root_endpoint(self, client: TestClient) -> None:
        """Test the root endpoint returns welcome message."""
        response = client.get("/")

        assert response.status_code == 200
        assert response.json() == {"message": "Welcome to WeaMind API"}

    def test_app_has_registered_routers(self) -> None:
        """Test that the app has registered all expected routers."""
        from app.main import app

        # The app should have multiple routes registered from different routers
        # (root + user routes + line routes + static files)
        assert len(app.routes) > 3  # Should have more than just basic routes
