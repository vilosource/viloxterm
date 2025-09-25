#!/usr/bin/env python3
"""
Main entry point for the VSCode-style PySide6 application.
This is the reorganized version that runs from within the viloapp package.
"""

import sys

# Import app config FIRST to detect production mode
from viloapp.core.app_config import app_config

# Set up centralized logging configuration
from viloapp.logging_config import setup_logging

setup_logging()  # Will auto-detect production mode from app_config

import logging

logger = logging.getLogger(__name__)

# Configure environment BEFORE any Qt imports
try:
    from viloapp.core.environment_detector import EnvironmentConfigurator

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

# Terminal server moved to plugin - plugins handle their own services
# from viloapp.services.terminal_server import terminal_server
from viloapp.ui.frameless_window import FramelessWindow
from viloapp.ui.main_window import MainWindow

# Terminal server is now started by the terminal plugin
# logger.info("Starting terminal server...")
# terminal_server.start_server()
# logger.info("Terminal server initialization complete")

# Import compiled resources
try:
    import viloapp.resources.resources_rc
except ImportError:
    logger.warning("Resources not compiled. Run 'make resources' to compile icons.")
    pass

# Register built-in widgets with AppWidgetManager
try:
    from viloapp.core.app_widget_registry import register_builtin_widgets

    register_builtin_widgets()
    logger.info("Registered built-in widgets with AppWidgetManager")
except ImportError as e:
    logger.warning(f"Could not register widgets with AppWidgetManager: {e}")


def initialize_plugins(window):
    """Initialize plugin system after main window is ready."""
    import logging

    logger = logging.getLogger(__name__)

    try:
        service_locator = window.service_locator
        from viloapp.services.plugin_service import PluginService

        plugin_service = service_locator.get(PluginService)

        if not plugin_service:
            logger.error("PluginService not found")
            return

        plugin_manager = plugin_service.get_plugin_manager()
        if not plugin_manager:
            logger.error("PluginManager not found")
            return

        # Create widget bridge
        from viloapp_sdk import LifecycleState

        from viloapp.core.plugin_system.widget_bridge import PluginWidgetBridge
        from viloapp.services.workspace_service import WorkspaceService

        workspace_service = service_locator.get(WorkspaceService)
        if workspace_service:
            widget_bridge = PluginWidgetBridge(workspace_service)
            plugin_service._widget_bridge = widget_bridge

            # Get all discovered plugins from registry
            registry = plugin_manager.registry
            all_plugins = {}
            for plugin_info in registry.get_all_plugins():
                all_plugins[plugin_info.metadata.id] = plugin_info
                logger.debug(
                    f"Plugin in registry: {plugin_info.metadata.id} (path: {plugin_info.path})"
                )

            logger.info(f"Found {len(all_plugins)} plugins to process")

            # Load and activate each plugin
            for plugin_id, plugin_info in all_plugins.items():
                logger.info(f"Processing plugin: {plugin_id}")

                # Skip built-in plugins (they're handled differently)
                if plugin_id in ["core-commands", "core-themes"]:
                    logger.info(f"Skipping built-in plugin: {plugin_id}")
                    continue

                # Check if plugin is already loaded or activated
                if plugin_info.state in [LifecycleState.ACTIVATED, LifecycleState.LOADED]:
                    logger.info(
                        f"Plugin already loaded/activated: {plugin_id} (state: {plugin_info.state})"
                    )
                    # Just register widget if available
                    plugin = plugin_manager.get_plugin(plugin_id)
                    if plugin and hasattr(plugin, "widget_factory"):
                        widget_bridge.register_plugin_widget(plugin.widget_factory, plugin_id)
                        logger.info(
                            f"Registered widget factory for already loaded plugin: {plugin_id}"
                        )
                    continue

                # Load the plugin
                if plugin_manager.load_plugin(plugin_id):
                    logger.info(f"Loaded plugin: {plugin_id}")

                    # Activate the plugin
                    if plugin_manager.activate_plugin(plugin_id):
                        logger.info(f"Activated plugin: {plugin_id}")

                        # Get the plugin instance
                        plugin = plugin_manager.get_plugin(plugin_id)
                        if plugin:
                            # Register widget factory if available
                            if hasattr(plugin, "widget_factory"):
                                widget_bridge.register_plugin_widget(
                                    plugin.widget_factory, plugin_id
                                )
                                logger.info(f"Registered widget factory for: {plugin_id}")
                    else:
                        logger.error(f"Failed to activate plugin: {plugin_id}")
                else:
                    logger.error(f"Failed to load plugin: {plugin_id}")

            logger.info("Plugin system initialization complete")

            # Now that plugins are loaded, restore all state (window geometry + workspace)
            if hasattr(window, "restore_state"):
                window.restore_state()
                logger.info("Restored window and workspace state after plugin initialization")

            # Refresh Apps menu now that plugins are loaded
            if hasattr(window, "action_manager") and window.action_manager:
                window.action_manager.refresh_apps_menu()
                logger.info("Refreshed Apps menu with plugin widgets")
    except Exception as e:
        logger.error(f"Failed to initialize plugins: {e}", exc_info=True)


def main():
    """Initialize and run the application."""
    try:
        # Parse command line args (app_config already imported at top)
        app_config.parse_args()
        logger.info(f"App configuration: {app_config}")

        # Initialize configurable settings system FIRST
        from viloapp.core.settings.config import (
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

        # Log successful startup
        logger.info("=== APPLICATION STARTUP COMPLETE ===")
        logger.info("ViloxTerm is ready for use")

        # Initialize plugin system after window is ready
        initialize_plugins(window)

        # For validation mode, exit after successful startup
        if "--validate-startup" in sys.argv:
            logger.info("Validation mode: Exiting after successful startup")
            from PySide6.QtCore import QTimer

            QTimer.singleShot(100, lambda: app.quit())
            return 0

        # Run application
        sys.exit(app.exec())

    except ImportError as e:
        logger.critical(f"Module import failed: {e}")
        logger.critical("Failed to import required modules", exc_info=True)
        sys.exit(2)  # Exit code 2: Import error

    except AttributeError as e:
        logger.critical(f"Service registration or initialization failed: {e}")
        logger.critical("Failed during service setup", exc_info=True)
        sys.exit(3)  # Exit code 3: Service error

    except Exception as e:
        logger.critical(f"Application startup failed: {e}")
        logger.critical("Unexpected error during startup", exc_info=True)
        sys.exit(1)  # Exit code 1: General error


if __name__ == "__main__":
    main()
