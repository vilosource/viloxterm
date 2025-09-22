#!/usr/bin/env python3
"""
View-related commands using the service layer.
"""

import logging

from viloapp.core.commands.base import CommandContext, CommandResult, CommandStatus
from viloapp.core.commands.decorators import command

logger = logging.getLogger(__name__)


@command(
    id="view.toggleTheme",
    title="Toggle Theme",
    category="View",
    description="Switch between light and dark theme",
    shortcut="ctrl+shift+t",
    icon="sun",
)
def toggle_theme_command(context: CommandContext) -> CommandResult:
    """Toggle between light and dark theme."""
    try:
        # Toggle theme directly via QSettings and main window
        from PySide6.QtCore import QSettings

        settings = QSettings("ViloxTerm", "ViloxTerm")

        current_theme = settings.value("theme", "dark")
        new_theme = "light" if current_theme == "dark" else "dark"
        settings.setValue("theme", new_theme)
        settings.sync()

        # Apply theme if main window available
        main_window = context.parameters.get("main_window") if context.parameters else None
        if main_window and hasattr(main_window, "apply_theme"):
            main_window.apply_theme(new_theme)

        return CommandResult(status=CommandStatus.SUCCESS, data={"theme": new_theme})
    except Exception as e:
        logger.error(f"Failed to toggle theme: {e}")
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


@command(
    id="view.toggleSidebar",
    title="Toggle Sidebar",
    category="View",
    description="Show or hide the sidebar",
    shortcut="ctrl+b",
    icon="sidebar",
)
def toggle_sidebar_command(context: CommandContext) -> CommandResult:
    """Toggle sidebar visibility."""
    try:
        main_window = context.parameters.get("main_window") if context.parameters else None
        if not main_window:
            return CommandResult(status=CommandStatus.FAILURE, message="Main window not available")

        # Toggle sidebar directly on main window
        if hasattr(main_window, "toggle_sidebar"):
            visible = main_window.toggle_sidebar()
        elif hasattr(main_window, "sidebar"):
            visible = not main_window.sidebar.isVisible()
            main_window.sidebar.setVisible(visible)
        else:
            return CommandResult(
                status=CommandStatus.NOT_APPLICABLE, message="Sidebar not available"
            )

        return CommandResult(status=CommandStatus.SUCCESS, data={"visible": visible})
    except Exception as e:
        logger.error(f"Failed to toggle sidebar: {e}")
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


@command(
    id="view.toggleActivityBar",
    title="Toggle Activity Bar",
    category="View",
    description="Show or hide the activity bar",
    shortcut="ctrl+shift+b",
    icon="menu",
)
def toggle_activity_bar_command(context: CommandContext) -> CommandResult:
    """Toggle activity bar visibility."""
    try:
        main_window = context.parameters.get("main_window") if context.parameters else None
        if not main_window:
            return CommandResult(status=CommandStatus.FAILURE, message="Main window not available")

        # Toggle activity bar directly on main window
        if hasattr(main_window, "toggle_activity_bar"):
            visible = main_window.toggle_activity_bar()
        elif hasattr(main_window, "activity_bar"):
            visible = not main_window.activity_bar.isVisible()
            main_window.activity_bar.setVisible(visible)
        else:
            return CommandResult(
                status=CommandStatus.NOT_APPLICABLE, message="Activity bar not available"
            )

        return CommandResult(status=CommandStatus.SUCCESS, data={"visible": visible})
    except Exception as e:
        logger.error(f"Failed to toggle activity bar: {e}")
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


@command(
    id="view.toggleMenuBar",
    title="Toggle Menu Bar",
    category="View",
    description="Show or hide the menu bar",
    shortcut="ctrl+shift+m",
    icon="menu",
)
def toggle_menu_bar_command(context: CommandContext) -> CommandResult:
    """Toggle menu bar visibility."""
    try:
        main_window = context.parameters.get("main_window") if context.parameters else None
        if not main_window:
            return CommandResult(status=CommandStatus.FAILURE, message="Main window not available")

        # Toggle menu bar directly on main window
        if hasattr(main_window, "toggle_menu_bar"):
            visible = main_window.toggle_menu_bar()
        elif hasattr(main_window, "menuBar"):
            menu_bar = main_window.menuBar()
            visible = not menu_bar.isVisible()
            menu_bar.setVisible(visible)
        else:
            return CommandResult(
                status=CommandStatus.NOT_APPLICABLE, message="Menu bar not available"
            )

        return CommandResult(status=CommandStatus.SUCCESS, data={"visible": visible})
    except Exception as e:
        logger.error(f"Failed to toggle menu bar: {e}")
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


@command(
    id="view.showExplorer",
    title="Show Explorer",
    category="View",
    description="Show the Explorer in the sidebar",
    shortcut="ctrl+shift+e",
    icon="folder",
)
def show_explorer_command(context: CommandContext) -> CommandResult:
    """Show Explorer view in sidebar."""
    try:
        main_window = context.parameters.get("main_window") if context.parameters else None
        if not main_window:
            return CommandResult(status=CommandStatus.FAILURE, message="Main window not available")

        # Set sidebar view directly on main window
        if hasattr(main_window, "set_sidebar_view"):
            main_window.set_sidebar_view("explorer")
        elif hasattr(main_window, "sidebar") and hasattr(main_window.sidebar, "set_view"):
            main_window.sidebar.set_view("explorer")
        else:
            return CommandResult(
                status=CommandStatus.NOT_APPLICABLE, message="Sidebar view switching not available"
            )

        return CommandResult(status=CommandStatus.SUCCESS)
    except Exception as e:
        logger.error(f"Failed to show explorer: {e}")
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


@command(
    id="view.showSearch",
    title="Show Search",
    category="View",
    description="Show the Search in the sidebar",
    shortcut="ctrl+shift+f",
    icon="search",
)
def show_search_command(context: CommandContext) -> CommandResult:
    """Show Search view in sidebar."""
    try:
        main_window = context.parameters.get("main_window") if context.parameters else None
        if not main_window:
            return CommandResult(status=CommandStatus.FAILURE, message="Main window not available")

        # Set sidebar view directly on main window
        if hasattr(main_window, "set_sidebar_view"):
            main_window.set_sidebar_view("search")
        elif hasattr(main_window, "sidebar") and hasattr(main_window.sidebar, "set_view"):
            main_window.sidebar.set_view("search")
        else:
            return CommandResult(
                status=CommandStatus.NOT_APPLICABLE, message="Sidebar view switching not available"
            )

        return CommandResult(status=CommandStatus.SUCCESS)
    except Exception as e:
        logger.error(f"Failed to show search: {e}")
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


@command(
    id="view.showGit",
    title="Show Git",
    category="View",
    description="Show the Git view in the sidebar",
    shortcut="ctrl+shift+g",
    icon="git-branch",
)
def show_git_command(context: CommandContext) -> CommandResult:
    """Show Git view in sidebar."""
    try:
        main_window = context.parameters.get("main_window") if context.parameters else None
        if not main_window:
            return CommandResult(status=CommandStatus.FAILURE, message="Main window not available")

        # Set sidebar view directly on main window
        if hasattr(main_window, "set_sidebar_view"):
            main_window.set_sidebar_view("git")
        elif hasattr(main_window, "sidebar") and hasattr(main_window.sidebar, "set_view"):
            main_window.sidebar.set_view("git")
        else:
            return CommandResult(
                status=CommandStatus.NOT_APPLICABLE, message="Sidebar view switching not available"
            )

        return CommandResult(status=CommandStatus.SUCCESS)
    except Exception as e:
        logger.error(f"Failed to show git: {e}")
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


@command(
    id="view.showSettings",
    title="Show Settings",
    category="View",
    description="Show the Settings in the sidebar",
    icon="settings",
)
def show_settings_command(context: CommandContext) -> CommandResult:
    """Show Settings view in sidebar."""
    try:
        main_window = context.parameters.get("main_window") if context.parameters else None
        if not main_window:
            return CommandResult(status=CommandStatus.FAILURE, message="Main window not available")

        # Set sidebar view directly on main window
        if hasattr(main_window, "set_sidebar_view"):
            main_window.set_sidebar_view("settings")
        elif hasattr(main_window, "sidebar") and hasattr(main_window.sidebar, "set_view"):
            main_window.sidebar.set_view("settings")
        else:
            return CommandResult(
                status=CommandStatus.NOT_APPLICABLE, message="Sidebar view switching not available"
            )

        return CommandResult(status=CommandStatus.SUCCESS)
    except Exception as e:
        logger.error(f"Failed to show settings: {e}")
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


@command(
    id="view.toggleFullScreenView",
    title="Toggle Full Screen View",
    category="View",
    description="Enter or exit full screen mode",
    # Shortcut f11 is already used by window.toggleFullScreen
    icon="maximize",
)
def toggle_fullscreen_command(context: CommandContext) -> CommandResult:
    """Toggle fullscreen mode."""
    try:
        main_window = context.parameters.get("main_window") if context.parameters else None
        if not main_window:
            return CommandResult(status=CommandStatus.FAILURE, message="Main window not available")

        # Toggle fullscreen directly on main window
        if main_window.isFullScreen():
            main_window.showNormal()
            is_fullscreen = False
        else:
            main_window.showFullScreen()
            is_fullscreen = True

        return CommandResult(status=CommandStatus.SUCCESS, data={"fullscreen": is_fullscreen})
    except Exception as e:
        logger.error(f"Failed to toggle fullscreen: {e}")
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


@command(
    id="view.resetLayout",
    title="Reset Layout",
    category="View",
    description="Reset the UI layout to defaults",
    icon="layout",
)
def reset_layout_command(context: CommandContext) -> CommandResult:
    """Reset UI layout to defaults."""
    try:
        main_window = context.parameters.get("main_window") if context.parameters else None
        if not main_window:
            return CommandResult(status=CommandStatus.FAILURE, message="Main window not available")

        # Reset layout on main window
        if hasattr(main_window, "reset_layout"):
            main_window.reset_layout()
        else:
            # Basic reset - show all UI elements
            if hasattr(main_window, "sidebar"):
                main_window.sidebar.setVisible(True)
            if hasattr(main_window, "activity_bar"):
                main_window.activity_bar.setVisible(True)
            if hasattr(main_window, "menuBar"):
                main_window.menuBar().setVisible(True)

        # Show status message
        if context.main_window and hasattr(context.main_window, "status_bar"):
            context.main_window.status_bar.set_message("Layout reset to defaults", 2000)

        return CommandResult(status=CommandStatus.SUCCESS)
    except Exception as e:
        logger.error(f"Failed to reset layout: {e}")
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


def register_view_commands():
    """Register all view commands."""
    # The @command decorator automatically registers them
    # This function ensures the module is imported
    logger.info("View commands registered")
