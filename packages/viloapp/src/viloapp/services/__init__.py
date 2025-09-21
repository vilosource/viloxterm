#!/usr/bin/env python3
"""
Service layer for ViloApp.

This module provides business logic services that are separate from UI components,
enabling better testability, reusability, and maintainability.
"""

from viloapp.services.base import Service, ServiceEvent
from viloapp.services.editor_service import EditorService
from viloapp.services.service_locator import ServiceLocator
from viloapp.services.state_service import StateService
from viloapp.services.terminal_service import TerminalService
from viloapp.services.theme_service import ThemeService
from viloapp.services.ui_service import UIService
from viloapp.services.workspace_service import WorkspaceService

__all__ = [
    "Service",
    "ServiceEvent",
    "ServiceLocator",
    "WorkspaceService",
    "UIService",
    "TerminalService",
    "StateService",
    "EditorService",
    "ThemeService",
    "initialize_plugin_system",
]


def initialize_plugin_system(services):
    """
    Initialize plugin system.

    Args:
        services: Dictionary of available services

    Returns:
        PluginManager instance or None if initialization fails
    """
    try:
        from viloapp_sdk import EventBus

        from viloapp.core.plugin_system import PluginManager

        # Create event bus
        event_bus = EventBus()

        # Create plugin manager
        plugin_manager = PluginManager(event_bus, services)

        # Add plugin manager and event bus to services
        services["plugin_manager"] = plugin_manager
        services["event_bus"] = event_bus

        # Initialize plugin system
        plugin_manager.initialize()

        import logging

        logger = logging.getLogger(__name__)
        logger.info("Plugin system initialized successfully")

        return plugin_manager

    except Exception as e:
        import logging

        logger = logging.getLogger(__name__)
        logger.error(f"Failed to initialize plugin system: {e}", exc_info=True)
        return None


def initialize_services(main_window=None, workspace=None, sidebar=None, activity_bar=None):
    """
    Initialize all services with application context.

    Args:
        main_window: MainWindow instance
        workspace: Workspace instance
        sidebar: Sidebar instance
        activity_bar: ActivityBar instance
    """
    locator = ServiceLocator.get_instance()

    # Create and register services (order matters - StateService before SettingsService)
    state_service = StateService()

    # ThemeService early in chain (before UIService)
    theme_service = ThemeService()

    # Import SettingsService here to avoid circular imports
    from viloapp.core.settings.service import SettingsService

    settings_service = SettingsService()

    # Enable new architecture - create model implementation and pass to service
    from viloapp.core.commands.router import CommandRouter
    from viloapp.models.workspace_model_impl import WorkspaceModelImpl

    workspace_model = WorkspaceModelImpl(workspace)
    workspace_service = WorkspaceService(workspace=workspace, model=workspace_model)

    # Make CommandRouter available globally (will be used by UI components)
    _ = CommandRouter()  # Instance created for future use
    ui_service = UIService(main_window)
    terminal_service = TerminalService()
    editor_service = EditorService()

    # Initialize plugin system
    plugin_manager = initialize_plugin_system(
        {
            "state_service": state_service,
            "theme_service": theme_service,
            "settings_service": settings_service,
            "workspace_service": workspace_service,
            "ui_service": ui_service,
            "terminal_service": terminal_service,
            "editor_service": editor_service,
        }
    )

    # Register in dependency order
    locator.register(StateService, state_service)
    locator.register(ThemeService, theme_service)
    locator.register(SettingsService, settings_service)
    locator.register(WorkspaceService, workspace_service)
    locator.register(UIService, ui_service)
    locator.register(TerminalService, terminal_service)
    locator.register(EditorService, editor_service)

    # Register plugin manager
    if plugin_manager:
        from viloapp.services.plugin_service import PluginService

        plugin_service = PluginService()
        plugin_service.set_plugin_manager(plugin_manager)
        locator.register(PluginService, plugin_service)

    # Create theme provider after theme service is registered
    # Note: ThemeProvider is a UI component that bridges services with UI
    # This is an acceptable dependency during initialization only
    from viloapp.ui.themes.theme_provider import ThemeProvider

    theme_provider = ThemeProvider(theme_service)
    theme_service.set_theme_provider(theme_provider)

    # Initialize all services with context
    context = {
        "main_window": main_window,
        "workspace": workspace,
        "sidebar": sidebar,
        "activity_bar": activity_bar,
    }

    for service in locator.get_all():
        service.initialize(context)

    return locator
