#!/usr/bin/env python3
"""
Application-wide configuration and runtime flags.

This module manages global application settings that affect behavior,
particularly for testing and development modes.
"""

import os
import argparse
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class AppConfig:
    """
    Singleton class for managing application-wide configuration.

    Configuration priority (highest to lowest):
    1. Command-line arguments
    2. Environment variables
    3. Default values
    """

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize configuration with defaults."""
        if not self._initialized:
            # Check if running from a built executable (production mode)
            is_production = self._is_production_build()

            self._config: Dict[str, Any] = {
                'show_confirmations': True,  # Show confirmation dialogs
                'test_mode': False,          # Running in test mode
                'debug_mode': False,         # Debug logging enabled
                'dev_mode': not is_production,  # Dev mode by default unless production build
                'production_mode': is_production,  # Explicitly track production mode
            }
            self._initialized = True
            self._load_from_environment()

    def _is_production_build(self) -> bool:
        """
        Detect if running from a production build (AppImage or packaged executable).

        Returns:
            True if running from production build, False otherwise
        """
        import sys

        # Check for AppImage environment variable
        if os.environ.get('APPIMAGE'):
            logger.info("Running from AppImage (production mode)")
            return True

        # Check for production environment variable (set by build system)
        if os.environ.get('VILOAPP_PRODUCTION', '').lower() in ('1', 'true', 'yes'):
            logger.info("Production mode set via environment variable")
            return True

        # Check if running from a frozen executable (PyInstaller/Nuitka)
        if getattr(sys, 'frozen', False):
            logger.info("Running from frozen executable (production mode)")
            return True

        # Check if running from .dist directory (Nuitka output)
        if '.dist' in sys.executable or 'ViloxTerm.dist' in sys.executable:
            logger.info("Running from Nuitka dist (production mode)")
            return True

        logger.info("Running in development mode (not a production build)")
        return False

    def _load_from_environment(self):
        """Load configuration from environment variables."""
        # Check for test mode
        if os.environ.get('VILOAPP_TEST_MODE', '').lower() in ('1', 'true', 'yes'):
            self._config['test_mode'] = True
            self._config['show_confirmations'] = False
            logger.info("Test mode enabled via environment variable")

        # Check for confirmation dialogs
        show_confirm = os.environ.get('VILOAPP_SHOW_CONFIRMATIONS', '').lower()
        if show_confirm in ('0', 'false', 'no'):
            self._config['show_confirmations'] = False
        elif show_confirm in ('1', 'true', 'yes'):
            self._config['show_confirmations'] = True

        # Check for debug mode
        if os.environ.get('VILOAPP_DEBUG', '').lower() in ('1', 'true', 'yes'):
            self._config['debug_mode'] = True

        # Check for dev mode override (environment variable overrides auto-detection)
        dev_env = os.environ.get('VILOAPP_DEV', '').lower()
        if dev_env in ('1', 'true', 'yes'):
            self._config['dev_mode'] = True
            self._config['production_mode'] = False
            logger.info("Dev mode forced via environment variable")
        elif dev_env in ('0', 'false', 'no'):
            self._config['dev_mode'] = False
            self._config['production_mode'] = True
            logger.info("Production mode forced via environment variable")

    def parse_args(self, args: Optional[list] = None):
        """
        Parse command-line arguments and update configuration.

        Args:
            args: List of command-line arguments (for testing)
        """
        parser = argparse.ArgumentParser(
            description='ViloxTerm - Modern Terminal Application',
            add_help=True
        )

        parser.add_argument(
            '--no-confirm',
            action='store_false',
            dest='show_confirmations',
            help='Disable confirmation dialogs (useful for testing)'
        )

        parser.add_argument(
            '--test-mode',
            action='store_true',
            dest='test_mode',
            help='Run in test mode (disables confirmations, enables test features)'
        )

        parser.add_argument(
            '--debug',
            action='store_true',
            dest='debug_mode',
            help='Enable debug logging'
        )

        parser.add_argument(
            '--dev',
            action='store_true',
            dest='dev_mode',
            help='Enable development mode features'
        )

        # Parse arguments
        parsed_args, unknown = parser.parse_known_args(args)

        # Update configuration from parsed arguments
        if parsed_args.test_mode:
            self._config['test_mode'] = True
            self._config['show_confirmations'] = False
            logger.info("Test mode enabled via command line")

        if not parsed_args.show_confirmations:
            self._config['show_confirmations'] = False
            logger.info("Confirmations disabled via command line")

        if parsed_args.debug_mode:
            self._config['debug_mode'] = True
            logging.getLogger().setLevel(logging.DEBUG)
            logger.info("Debug mode enabled")

        if parsed_args.dev_mode:
            self._config['dev_mode'] = True
            logger.info("Development mode enabled")

        return parsed_args

    @property
    def show_confirmations(self) -> bool:
        """Check if confirmation dialogs should be shown."""
        return self._config['show_confirmations']

    @property
    def test_mode(self) -> bool:
        """Check if running in test mode."""
        return self._config['test_mode']

    @property
    def debug_mode(self) -> bool:
        """Check if debug mode is enabled."""
        return self._config['debug_mode']

    @property
    def dev_mode(self) -> bool:
        """Check if development mode is enabled."""
        return self._config['dev_mode']

    @property
    def production_mode(self) -> bool:
        """Check if running in production mode."""
        return self._config.get('production_mode', False)

    def set_test_mode(self, enabled: bool = True):
        """
        Enable or disable test mode.

        Args:
            enabled: Whether to enable test mode
        """
        self._config['test_mode'] = enabled
        if enabled:
            self._config['show_confirmations'] = False
            logger.info("Test mode %s", "enabled" if enabled else "disabled")

    def set_show_confirmations(self, show: bool):
        """
        Enable or disable confirmation dialogs.

        Args:
            show: Whether to show confirmation dialogs
        """
        self._config['show_confirmations'] = show
        logger.info("Confirmations %s", "enabled" if show else "disabled")

    def get_config(self) -> Dict[str, Any]:
        """Get the full configuration dictionary."""
        return self._config.copy()

    def __str__(self) -> str:
        """String representation of configuration."""
        return (
            f"AppConfig(show_confirmations={self.show_confirmations}, "
            f"test_mode={self.test_mode}, debug_mode={self.debug_mode}, "
            f"dev_mode={self.dev_mode})"
        )


# Global singleton instance
app_config = AppConfig()


# Convenience functions
def is_test_mode() -> bool:
    """Check if running in test mode."""
    return app_config.test_mode


def should_show_confirmations() -> bool:
    """Check if confirmation dialogs should be shown."""
    return app_config.show_confirmations


def is_debug_mode() -> bool:
    """Check if debug mode is enabled."""
    return app_config.debug_mode


def is_dev_mode() -> bool:
    """Check if development mode is enabled."""
    return app_config.dev_mode