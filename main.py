#!/usr/bin/env python3
"""
Main entry point for the VSCode-style PySide6 application.
"""

import sys
import logging

# Set up logging FIRST
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configure environment BEFORE any Qt imports
try:
    from core.environment_detector import EnvironmentConfigurator
    env_configurator = EnvironmentConfigurator()
    env_configurator.apply_configuration()
    
    # Log environment info
    env_info, strategy = env_configurator.get_info()
    logger.info(f"Environment: OS={env_info.os_type}, WSL={env_info.is_wsl}, "
                f"Docker={env_info.is_docker}, GPU={env_info.gpu_available}")
except ImportError:
    logger.warning("Environment detector not available, using defaults")
except Exception as e:
    logger.error(f"Failed to configure environment: {e}")

# NOW import Qt modules after environment is configured
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QCoreApplication, QSettings
from ui.main_window import MainWindow
from ui.chrome_main_window import ChromeMainWindow

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

# Register terminal widget if available
try:
    from ui.terminal.terminal_factory import register_terminal_widget
    register_terminal_widget()
except ImportError as e:
    logger.warning(f"Could not import terminal module: {e}")
    pass


def main():
    """Initialize and run the application."""
    # Initialize configurable settings system FIRST
    from core.settings.config import initialize_settings_from_cli, get_settings, get_settings_info
    settings_config = initialize_settings_from_cli()
    
    # Log settings information
    settings_info = get_settings_info()
    logger.info(f"Settings location: {settings_info['location']}")
    if settings_info['is_portable']:
        logger.info("Running in portable mode")
    elif settings_info['is_temporary']:
        logger.info("Using temporary settings (will not persist)")
    
    # Set application metadata
    QCoreApplication.setApplicationName("ViloApp")
    QCoreApplication.setOrganizationName("ViloApp")
    QCoreApplication.setOrganizationDomain("viloapp.local")
    
    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    # Create application
    app = QApplication(sys.argv)
    
    # Check if Chrome mode is enabled using the new settings system
    settings = get_settings("ViloApp", "ViloApp")
    chrome_mode = settings.value("UI/ChromeMode", False, type=bool)
    
    # Create appropriate main window based on preference
    if chrome_mode:
        window = ChromeMainWindow()
    else:
        window = MainWindow()
    
    window.show()
    
    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()