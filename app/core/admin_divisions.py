"""
Taiwan administrative divisions management.

This module provides a singleton to load and validate Taiwan administrative divisions
from the static JSON data file during application startup.
"""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class AdminDivisionsManager:
    """Singleton manager for Taiwan administrative divisions validation."""

    _instance = None
    _valid_divisions: set[str] | None = None

    def __new__(cls) -> "AdminDivisionsManager":
        """Ensure singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self) -> None:
        """Initialize the manager (only once due to singleton)."""
        if self._valid_divisions is None:
            self._load_admin_divisions()

    def _load_admin_divisions(self) -> None:
        """
        Load Taiwan administrative divisions from JSON file and build validation set.

        The JSON file contains county/city -> districts mapping.
        We build a set of all valid full_name combinations (e.g., "臺北市信義區").
        """
        try:
            # Path to the static data file
            json_path = (
                Path(__file__).parent.parent.parent / "static" / "data" / "tw_admin_divisions.json"
            )

            if not json_path.exists():
                logger.error(f"Admin divisions JSON file not found: {json_path}")
                self._valid_divisions = set()
                return

            with open(json_path, encoding="utf-8") as f:
                admin_data = json.load(f)

            # Build set of valid full names
            valid_divisions = set()
            for county_city, districts in admin_data.items():
                for district in districts:
                    full_name = f"{county_city}{district}"
                    valid_divisions.add(full_name)

            self._valid_divisions = valid_divisions
            logger.info(f"Loaded {len(self._valid_divisions)} Taiwan administrative divisions")

        except Exception:
            logger.exception("Failed to load admin divisions")
            self._valid_divisions = set()

    def is_valid_division(self, full_name: str) -> bool:
        """
        Check if a full administrative division name is valid.

        Args:
            full_name: Full administrative division name (e.g., "臺北市信義區")

        Returns:
            bool: True if the division name is valid, False otherwise
        """
        if self._valid_divisions is None:
            logger.warning("Admin divisions not loaded, cannot validate")
            return False

        return full_name in self._valid_divisions

    def get_valid_divisions_count(self) -> int:
        """
        Get the number of loaded valid administrative divisions.

        Returns:
            int: Number of valid divisions loaded
        """
        return len(self._valid_divisions) if self._valid_divisions else 0


# Global singleton instance
admin_divisions_manager = AdminDivisionsManager()


def is_valid_taiwan_division(full_name: str) -> bool:
    """
    Convenience function to check if an administrative division name is valid.

    Args:
        full_name: Full administrative division name (e.g., "臺北市信義區")

    Returns:
        bool: True if valid Taiwan administrative division, False otherwise
    """
    return admin_divisions_manager.is_valid_division(full_name)


def initialize_admin_divisions() -> None:
    """
    Initialize the administrative divisions manager.

    This function should be called during application startup to ensure
    the admin divisions data is loaded early.
    """
    global admin_divisions_manager
    admin_divisions_manager = AdminDivisionsManager()
    count = admin_divisions_manager.get_valid_divisions_count()
    logger.info(f"Admin divisions manager initialized with {count} divisions")
