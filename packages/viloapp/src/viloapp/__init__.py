"""ViloxTerm - VSCode-style desktop GUI application.

This is the main application package containing:
- Core infrastructure (commands, services, plugin system)
- UI components (main window, activity bar, workspace)
- Controllers and models
- Application configuration and state management
"""

__version__ = "0.1.0"
__author__ = "ViloxTerm Team"
__description__ = "VSCode-style desktop GUI application with plugin architecture"

# Re-export commonly used components for convenience
from viloapp.core.app_config import AppConfig
from viloapp.core.environment_detector import EnvironmentDetector

__all__ = [
    "AppConfig",
    "EnvironmentDetector",
    "__version__",
    "__author__",
    "__description__",
]
