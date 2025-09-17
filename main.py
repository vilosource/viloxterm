#!/usr/bin/env python3
"""
Main entry point for the VSCode-style PySide6 application.
"""

import sys

# Import app config FIRST to detect production mode
from core.app_config import app_config

# Set up centralized logging configuration
from logging_config import setup_logging

setup_logging()  # Will auto-detect production mode from app_config

import logging

logger = logging.getLogger(__name__)

# Configure environment BEFORE any Qt imports
try:
    from core.environment_detector import EnvironmentConfigurator

    env_configurator = EnvironmentConfigurator()
    env_configurator.apply_configuration()

    # Log environment info
    env_info, strategy = env_configurator.get_info()
    logger.info(
        f"Environment: OS={env_info.os_type}, WSL={env_info.is_wsl}, "
        f"Docker={env_info.is_docker}, GPU={env_info.gpu_available}"
    )
except ImportError:
    logger.warning("Environment detector not available, using defaults")
except Exception as e:
    logger.error(f"Failed to configure environment: {e}")

# NOW import Qt modules after environment is configured
from PySide6.QtCore import QCoreApplication, Qt
from PySide6.QtWidgets import QApplication

from ui.frameless_window import FramelessWindow
from ui.main_window import MainWindow

# Start terminal server early to ensure it's ready before any widgets are created
from ui.terminal.terminal_server import terminal_server

logger.info("Starting terminal server...")
terminal_server.start_server()
logger.info("Terminal server initialization complete")

# Import compiled resources
try:
    import resources.resources_rc
except ImportError:
    logger.warning("Resources not compiled. Run 'make resources' to compile icons.")
    pass

# Register built-in widgets with AppWidgetManager
try:
    from core.app_widget_registry import register_builtin_widgets

    register_builtin_widgets()
    logger.info("Registered built-in widgets with AppWidgetManager")
except ImportError as e:
    logger.warning(f"Could not register widgets with AppWidgetManager: {e}")

# Terminal widget is now registered through AppWidgetManager in app_widget_registry.py
# Legacy registration removed - no longer needed


def main():
    """Initialize and run the application."""
    # Parse command line args (app_config already imported at top)
    app_config.parse_args()
    logger.info(f"App configuration: {app_config}")

    # Initialize configurable settings system FIRST
    from core.settings.config import (
        get_settings,
        get_settings_info,
        initialize_settings_from_cli,
    )

    initialize_settings_from_cli()

    # Log settings information
    settings_info = get_settings_info()
    logger.info(f"Settings location: {settings_info['location']}")
    if settings_info["is_portable"]:
        logger.info("Running in portable mode")
    elif settings_info["is_temporary"]:
        logger.info("Using temporary settings (will not persist)")

    # Set application metadata
    QCoreApplication.setApplicationName("ViloxTerm")
    QCoreApplication.setOrganizationName("ViloxTerm")
    QCoreApplication.setOrganizationDomain("viloxterm.local")

    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    # Create application
    app = QApplication(sys.argv)

    # Handle theme reset if requested
    if app_config.reset_theme:
        logger.info("Theme reset requested via --reset-theme")
        # Theme reset will be handled by ThemeService during initialization

    # Check if frameless mode is enabled
    settings = get_settings("ViloxTerm", "ViloxTerm")
    frameless_mode = settings.value("UI/FramelessMode", False, type=bool)

    # Log the decision for debugging
    logger.info(f"Frameless mode setting: {frameless_mode}")
    logger.info(f"Settings file location: {settings.fileName()}")

    # Debug: List all keys to see what's stored
    all_keys = settings.allKeys()
    if "UI/FramelessMode" in all_keys:
        logger.info(
            f"UI/FramelessMode found in settings with value: {settings.value('UI/FramelessMode')}"
        )
    else:
        logger.info("UI/FramelessMode not found in settings, using default (False)")

    # Create appropriate window based on preference
    if frameless_mode:
        logger.info("Creating FramelessWindow")
        window = FramelessWindow()
    else:
        logger.info("Creating MainWindow")
        window = MainWindow()

    window.show()

    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
