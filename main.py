#!/usr/bin/env python3
"""
Main entry point for the VSCode-style PySide6 application.
"""

import sys
import logging

# Set up logging FIRST
logging.basicConfig(
    level=logging.INFO,
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
from PySide6.QtCore import Qt, QCoreApplication
from ui.main_window import MainWindow

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
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()