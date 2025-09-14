"""Tests for app.core.logging module."""

from pathlib import Path
from unittest.mock import Mock, patch

from app.core.logging import setup_logging


class TestSetupLogging:
    """Test setup_logging function by mocking all logging components."""

    @patch("app.core.logging.settings")
    @patch("app.core.logging.logging")
    def test_setup_logging_function_executes_without_errors(
        self, mock_logging: Mock, mock_settings: Mock
    ) -> None:
        """Test that setup_logging executes without errors."""
        # Mock settings
        mock_settings.DEBUG = False
        mock_settings.is_production = False
        mock_settings.ENV = "test"
        mock_logs_dir = Mock()
        mock_logs_dir.__truediv__ = Mock(return_value=Path("logs/app.log"))
        mock_settings.logs_dir = mock_logs_dir

        # Mock logging operations
        mock_logging.DEBUG = 10
        mock_logging.INFO = 20
        mock_logging.WARNING = 30
        mock_file_handler = Mock()
        mock_stream_handler = Mock()
        mock_logging.FileHandler.return_value = mock_file_handler
        mock_logging.StreamHandler.return_value = mock_stream_handler
        mock_logging.getLogger.return_value = Mock()

        # This should not raise any errors
        setup_logging()

        # Verify mkdir was called
        mock_logs_dir.mkdir.assert_called_once_with(exist_ok=True)

        # Verify basicConfig was called
        mock_logging.basicConfig.assert_called_once()

        # Verify handlers were created
        mock_logging.FileHandler.assert_called_once()
        mock_logging.StreamHandler.assert_called_once()

    @patch("app.core.logging.settings")
    @patch("app.core.logging.logging")
    def test_setup_logging_development_mode(self, mock_logging: Mock, mock_settings: Mock) -> None:
        """Test that setup_logging handles development mode correctly."""
        # Mock settings for development
        mock_settings.DEBUG = True
        mock_settings.is_production = False
        mock_settings.ENV = "development"
        mock_logs_dir = Mock()
        mock_logs_dir.__truediv__ = Mock(return_value=Path("logs/app.log"))
        mock_settings.logs_dir = mock_logs_dir

        # Mock logging operations
        mock_logging.DEBUG = 10
        mock_logging.INFO = 20
        mock_logging.WARNING = 30
        mock_file_handler = Mock()
        mock_stream_handler = Mock()
        mock_logging.FileHandler.return_value = mock_file_handler
        mock_logging.StreamHandler.return_value = mock_stream_handler
        mock_logging.getLogger.return_value = Mock()

        # This should not raise any errors
        setup_logging()

        # Verify basicConfig was called
        mock_logging.basicConfig.assert_called_once()

        # Get the call args to verify DEBUG level was used
        call_args = mock_logging.basicConfig.call_args
        assert call_args[1]["level"] == 10  # DEBUG level

    @patch("app.core.logging.settings")
    @patch("app.core.logging.logging")
    def test_setup_logging_production_mode(self, mock_logging: Mock, mock_settings: Mock) -> None:
        """Test that setup_logging handles production mode correctly."""
        # Mock settings for production
        mock_settings.DEBUG = False
        mock_settings.is_production = True
        mock_settings.ENV = "production"
        mock_logs_dir = Mock()
        mock_logs_dir.__truediv__ = Mock(return_value=Path("logs/app.log"))
        mock_settings.logs_dir = mock_logs_dir

        # Mock logging operations
        mock_logging.DEBUG = 10
        mock_logging.INFO = 20
        mock_logging.WARNING = 30
        mock_file_handler = Mock()
        mock_stream_handler = Mock()
        mock_logging.FileHandler.return_value = mock_file_handler
        mock_logging.StreamHandler.return_value = mock_stream_handler
        mock_logging.getLogger.return_value = Mock()

        # This should not raise any errors
        setup_logging()

        # Verify basicConfig was called
        mock_logging.basicConfig.assert_called_once()

        # Get the call args to verify DEBUG level was used
        call_args = mock_logging.basicConfig.call_args
        assert call_args[1]["level"] == 10  # DEBUG level
