"""Tests for app.core.config module's logging functionality."""

from unittest.mock import Mock, patch

from app.core.config import setup_logging


class TestSetupLogging:
    """Test setup_logging function by mocking all logging components."""

    def _setup_mocks(
        self,
        mock_logging: Mock,
        mock_settings: Mock,
        debug: bool = False,
        is_production: bool = False,
        env: str = "test",
    ) -> None:
        """Helper method to setup common mocks for logging tests."""
        # Configure settings
        mock_settings.DEBUG = debug
        mock_settings.is_production = is_production
        mock_settings.ENV = env

        # Mock logs_dir
        mock_logs_dir = Mock()
        mock_logs_dir.__truediv__ = Mock(return_value=Mock())
        mock_logs_dir.mkdir = Mock()
        mock_settings.logs_dir = mock_logs_dir

        # Configure logging mocks
        mock_logging.DEBUG = 10
        mock_logging.INFO = 20
        mock_logging.WARNING = 30
        mock_logging.FileHandler = Mock(return_value=Mock())
        mock_logging.StreamHandler = Mock(return_value=Mock())
        mock_logging.getLogger = Mock(return_value=Mock())
        mock_logging.basicConfig = Mock()

    @patch("app.core.config.settings")
    @patch("app.core.config.logging")
    def test_setup_logging_function_executes_without_errors(
        self, mock_logging: Mock, mock_settings: Mock
    ) -> None:
        """Test that setup_logging executes without errors."""
        self._setup_mocks(mock_logging, mock_settings)

        # This should not raise any errors
        setup_logging()

        # Verify mkdir was called
        mock_settings.logs_dir.mkdir.assert_called_once_with(exist_ok=True)

        # Verify basicConfig was called
        mock_logging.basicConfig.assert_called_once()

        # Verify handlers were created
        mock_logging.FileHandler.assert_called_once()
        mock_logging.StreamHandler.assert_called_once()

    @patch("app.core.config.settings")
    @patch("app.core.config.logging")
    def test_setup_logging_development_mode(self, mock_logging: Mock, mock_settings: Mock) -> None:
        """Test that setup_logging handles development mode correctly."""
        self._setup_mocks(mock_logging, mock_settings, debug=True, env="development")

        setup_logging()

        # Verify basicConfig was called
        mock_logging.basicConfig.assert_called_once()

        # Get the call args to verify DEBUG level was used
        call_args = mock_logging.basicConfig.call_args
        assert call_args[1]["level"] == 10  # DEBUG level

    @patch("app.core.config.settings")
    @patch("app.core.config.logging")
    def test_setup_logging_production_mode(self, mock_logging: Mock, mock_settings: Mock) -> None:
        """Test that setup_logging handles production mode correctly."""
        self._setup_mocks(mock_logging, mock_settings, is_production=True, env="production")

        setup_logging()

        # Verify basicConfig was called
        mock_logging.basicConfig.assert_called_once()

        # Get the call args to verify DEBUG level was used (production also uses DEBUG)
        call_args = mock_logging.basicConfig.call_args
        assert call_args[1]["level"] == 10  # DEBUG level
