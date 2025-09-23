#!/usr/bin/env python3
"""
Sidebar view commands.

This module contains commands for managing sidebar views including
showing different tool panels like Explorer, Search, Git, etc.
"""

import logging

from viloapp.core.commands.base import CommandContext, CommandResult, CommandStatus
from viloapp.core.commands.decorators import command

logger = logging.getLogger(__name__)


@command(
    id="workbench.view.explorer",
    title="Show Explorer",
    category="View",
    description="Show the Explorer view in the sidebar",
)
def show_explorer_command(context: CommandContext) -> CommandResult:
    """
    Show the Explorer view in the sidebar.

    Args:
        context: Command context

    Returns:
        CommandResult indicating success or failure
    """
    try:
        main_window = context.main_window
        if not main_window:
            return CommandResult(status=CommandStatus.FAILURE, message="No main window available")

        # Show explorer through activity bar
        if hasattr(main_window, "activity_bar"):
            main_window.activity_bar.show_view("explorer")
            return CommandResult(status=CommandStatus.SUCCESS, value={"view": "explorer"})

        return CommandResult(status=CommandStatus.FAILURE, message="Could not show explorer")

    except Exception as e:
        logger.error(f"Error showing explorer: {e}", exc_info=True)
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


@command(
    id="workbench.view.search",
    title="Show Search",
    category="View",
    description="Show the Search view in the sidebar",
)
def show_search_command(context: CommandContext) -> CommandResult:
    """
    Show the Search view in the sidebar.

    Args:
        context: Command context

    Returns:
        CommandResult indicating success or failure
    """
    try:
        main_window = context.main_window
        if not main_window:
            return CommandResult(status=CommandStatus.FAILURE, message="No main window available")

        # Show search through activity bar
        if hasattr(main_window, "activity_bar"):
            main_window.activity_bar.show_view("search")
            return CommandResult(status=CommandStatus.SUCCESS, value={"view": "search"})

        return CommandResult(status=CommandStatus.FAILURE, message="Could not show search")

    except Exception as e:
        logger.error(f"Error showing search: {e}", exc_info=True)
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


@command(
    id="workbench.view.git",
    title="Show Source Control",
    category="View",
    description="Show the Git/Source Control view in the sidebar",
)
def show_git_command(context: CommandContext) -> CommandResult:
    """
    Show the Git/Source Control view in the sidebar.

    Args:
        context: Command context

    Returns:
        CommandResult indicating success or failure
    """
    try:
        main_window = context.main_window
        if not main_window:
            return CommandResult(status=CommandStatus.FAILURE, message="No main window available")

        # Show git through activity bar
        if hasattr(main_window, "activity_bar"):
            main_window.activity_bar.show_view("git")
            return CommandResult(status=CommandStatus.SUCCESS, value={"view": "git"})

        return CommandResult(status=CommandStatus.FAILURE, message="Could not show git")

    except Exception as e:
        logger.error(f"Error showing git: {e}", exc_info=True)
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


@command(
    id="workbench.view.settings",
    title="Show Settings",
    category="View",
    description="Show the Settings view in the sidebar",
)
def show_settings_command(context: CommandContext) -> CommandResult:
    """
    Show the Settings view in the sidebar.

    Args:
        context: Command context

    Returns:
        CommandResult indicating success or failure
    """
    try:
        main_window = context.main_window
        if not main_window:
            return CommandResult(status=CommandStatus.FAILURE, message="No main window available")

        # Show settings through activity bar
        if hasattr(main_window, "activity_bar"):
            main_window.activity_bar.show_view("settings")
            return CommandResult(status=CommandStatus.SUCCESS, value={"view": "settings"})

        return CommandResult(status=CommandStatus.FAILURE, message="Could not show settings")

    except Exception as e:
        logger.error(f"Error showing settings: {e}", exc_info=True)
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


def register_sidebar_commands():
    """Register all sidebar commands."""
    # The @command decorator automatically registers them
    # This function ensures the module is imported
    logger.info("Sidebar commands registered")
