#!/usr/bin/env python3
"""
Service layer for ViloApp.

This module provides business logic services that are separate from UI components,
enabling better testability, reusability, and maintainability.
"""

from services.base import Service, ServiceEvent
from services.service_locator import ServiceLocator
from services.workspace_service import WorkspaceService
from services.ui_service import UIService
from services.terminal_service import TerminalService
from services.state_service import StateService
from services.editor_service import EditorService
from services.theme_service import ThemeService

__all__ = [
    'Service',
    'ServiceEvent',
    'ServiceLocator',
    'WorkspaceService',
    'UIService',
    'TerminalService',
    'StateService',
    'EditorService',
    'ThemeService',
]

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
    from core.settings.service import SettingsService
    settings_service = SettingsService()

    workspace_service = WorkspaceService(workspace)
    ui_service = UIService(main_window)
    terminal_service = TerminalService()
    editor_service = EditorService()

    # Create theme provider
    from ui.themes.theme_provider import ThemeProvider
    theme_provider = ThemeProvider(theme_service)

    # Register in dependency order
    locator.register(StateService, state_service)
    locator.register(ThemeService, theme_service)
    locator.register(SettingsService, settings_service)
    locator.register(WorkspaceService, workspace_service)
    locator.register(UIService, ui_service)
    locator.register(TerminalService, terminal_service)
    locator.register(EditorService, editor_service)
    locator.register(ThemeProvider, theme_provider)
    
    # Initialize all services with context
    context = {
        'main_window': main_window,
        'workspace': workspace,
        'sidebar': sidebar,
        'activity_bar': activity_bar
    }
    
    for service in locator.get_all():
        service.initialize(context)
    
    return locator