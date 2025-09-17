#!/usr/bin/env python3
"""
View-related commands using the service layer.
"""

import logging

from core.commands.base import CommandContext, CommandResult
from core.commands.decorators import command
from services.ui_service import UIService

logger = logging.getLogger(__name__)


@command(
    id="view.toggleTheme",
    title="Toggle Theme",
    category="View",
    description="Switch between light and dark theme",
    shortcut="ctrl+t",
    icon="sun"
)
def toggle_theme_command(context: CommandContext) -> CommandResult:
    """Toggle between light and dark theme using UIService."""
    try:
        ui_service = context.get_service(UIService)
        if not ui_service:
            return CommandResult(success=False, error="UIService not available")

        new_theme = ui_service.toggle_theme()

        return CommandResult(
            success=True,
            value={'theme': new_theme}
        )
    except Exception as e:
        logger.error(f"Failed to toggle theme: {e}")
        return CommandResult(success=False, error=str(e))


@command(
    id="view.toggleSidebar",
    title="Toggle Sidebar",
    category="View",
    description="Show or hide the sidebar",
    shortcut="ctrl+b",
    icon="sidebar"
)
def toggle_sidebar_command(context: CommandContext) -> CommandResult:
    """Toggle sidebar visibility using UIService."""
    try:
        ui_service = context.get_service(UIService)
        if not ui_service:
            return CommandResult(success=False, error="UIService not available")

        visible = ui_service.toggle_sidebar()

        return CommandResult(
            success=True,
            value={'visible': visible}
        )
    except Exception as e:
        logger.error(f"Failed to toggle sidebar: {e}")
        return CommandResult(success=False, error=str(e))


@command(
    id="view.toggleActivityBar",
    title="Toggle Activity Bar",
    category="View",
    description="Show or hide the activity bar",
    shortcut="ctrl+shift+b",
    icon="menu"
)
def toggle_activity_bar_command(context: CommandContext) -> CommandResult:
    """Toggle activity bar visibility."""
    try:
        ui_service = context.get_service(UIService)
        if not ui_service:
            return CommandResult(success=False, error="UIService not available")

        visible = ui_service.toggle_activity_bar()

        return CommandResult(
            success=True,
            value={'visible': visible}
        )
    except Exception as e:
        logger.error(f"Failed to toggle activity bar: {e}")
        return CommandResult(success=False, error=str(e))


@command(
    id="view.toggleMenuBar",
    title="Toggle Menu Bar",
    category="View",
    description="Show or hide the menu bar",
    shortcut="ctrl+shift+m",
    icon="menu"
)
def toggle_menu_bar_command(context: CommandContext) -> CommandResult:
    """Toggle menu bar visibility using UIService."""
    try:
        ui_service = context.get_service(UIService)
        if not ui_service:
            return CommandResult(success=False, error="UIService not available")

        visible = ui_service.toggle_menu_bar()

        return CommandResult(
            success=True,
            value={'visible': visible}
        )
    except Exception as e:
        logger.error(f"Failed to toggle menu bar: {e}")
        return CommandResult(success=False, error=str(e))


@command(
    id="view.showExplorer",
    title="Show Explorer",
    category="View",
    description="Show the Explorer in the sidebar",
    shortcut="ctrl+shift+e",
    icon="folder"
)
def show_explorer_command(context: CommandContext) -> CommandResult:
    """Show Explorer view in sidebar using UIService."""
    try:
        ui_service = context.get_service(UIService)
        if not ui_service:
            return CommandResult(success=False, error="UIService not available")

        ui_service.set_sidebar_view("explorer")

        return CommandResult(success=True)
    except Exception as e:
        logger.error(f"Failed to show explorer: {e}")
        return CommandResult(success=False, error=str(e))


@command(
    id="view.showSearch",
    title="Show Search",
    category="View",
    description="Show the Search in the sidebar",
    shortcut="ctrl+shift+f",
    icon="search"
)
def show_search_command(context: CommandContext) -> CommandResult:
    """Show Search view in sidebar using UIService."""
    try:
        ui_service = context.get_service(UIService)
        if not ui_service:
            return CommandResult(success=False, error="UIService not available")

        ui_service.set_sidebar_view("search")

        return CommandResult(success=True)
    except Exception as e:
        logger.error(f"Failed to show search: {e}")
        return CommandResult(success=False, error=str(e))


@command(
    id="view.showGit",
    title="Show Git",
    category="View",
    description="Show the Git view in the sidebar",
    shortcut="ctrl+shift+g",
    icon="git-branch"
)
def show_git_command(context: CommandContext) -> CommandResult:
    """Show Git view in sidebar using UIService."""
    try:
        ui_service = context.get_service(UIService)
        if not ui_service:
            return CommandResult(success=False, error="UIService not available")

        ui_service.set_sidebar_view("git")

        return CommandResult(success=True)
    except Exception as e:
        logger.error(f"Failed to show git: {e}")
        return CommandResult(success=False, error=str(e))


@command(
    id="view.showSettings",
    title="Show Settings",
    category="View",
    description="Show the Settings in the sidebar",
    icon="settings"
)
def show_settings_command(context: CommandContext) -> CommandResult:
    """Show Settings view in sidebar using UIService."""
    try:
        ui_service = context.get_service(UIService)
        if not ui_service:
            return CommandResult(success=False, error="UIService not available")

        ui_service.set_sidebar_view("settings")

        return CommandResult(success=True)
    except Exception as e:
        logger.error(f"Failed to show settings: {e}")
        return CommandResult(success=False, error=str(e))


@command(
    id="view.toggleFullScreen",
    title="Toggle Full Screen",
    category="View",
    description="Enter or exit full screen mode",
    shortcut="f11",
    icon="maximize"
)
def toggle_fullscreen_command(context: CommandContext) -> CommandResult:
    """Toggle fullscreen mode using UIService."""
    try:
        ui_service = context.get_service(UIService)
        if not ui_service:
            return CommandResult(success=False, error="UIService not available")

        is_fullscreen = ui_service.toggle_fullscreen()

        return CommandResult(
            success=True,
            value={'fullscreen': is_fullscreen}
        )
    except Exception as e:
        logger.error(f"Failed to toggle fullscreen: {e}")
        return CommandResult(success=False, error=str(e))


@command(
    id="view.resetLayout",
    title="Reset Layout",
    category="View",
    description="Reset the UI layout to defaults",
    icon="layout"
)
def reset_layout_command(context: CommandContext) -> CommandResult:
    """Reset UI layout to defaults using UIService."""
    try:
        ui_service = context.get_service(UIService)
        if not ui_service:
            return CommandResult(success=False, error="UIService not available")

        ui_service.reset_layout()

        # Show status message
        if context.main_window and hasattr(context.main_window, 'status_bar'):
            context.main_window.status_bar.set_message("Layout reset to defaults", 2000)

        return CommandResult(success=True)
    except Exception as e:
        logger.error(f"Failed to reset layout: {e}")
        return CommandResult(success=False, error=str(e))


def register_view_commands():
    """Register all view commands."""
    # The @command decorator automatically registers them
    # This function ensures the module is imported
    logger.info("View commands registered")
