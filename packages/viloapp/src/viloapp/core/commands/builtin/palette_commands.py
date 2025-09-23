#!/usr/bin/env python3
"""
Command palette related commands.
"""

import logging

from viloapp.core.commands.base import CommandContext, CommandResult, CommandStatus
from viloapp.core.commands.decorators import command

logger = logging.getLogger(__name__)


@command(
    id="commandPalette.show",
    title="Show Command Palette",
    category="View",
    description="Show all commands",
    shortcut="ctrl+shift+p",
    icon="command",
    when="!commandPaletteVisible",
)
def show_command_palette_command(context: CommandContext) -> CommandResult:
    """Show the command palette."""
    try:
        # Check if main window has a command palette controller
        if not context.main_window or not hasattr(
            context.main_window, "command_palette_controller"
        ):
            return CommandResult(status=CommandStatus.FAILURE, message="Command palette not available")

        controller = context.main_window.command_palette_controller

        # Show the palette
        controller.show_palette()

        return CommandResult(status=CommandStatus.SUCCESS, value="Command palette shown")

    except Exception as e:
        logger.error(f"Failed to show command palette: {e}")
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


@command(
    id="commandPalette.hide",
    title="Hide Command Palette",
    category="View",
    description="Hide the command palette",
    shortcut="escape",
    when="commandPaletteVisible",
)
def hide_command_palette_command(context: CommandContext) -> CommandResult:
    """Hide the command palette."""
    try:
        # Check if main window has a command palette controller
        if not context.main_window or not hasattr(
            context.main_window, "command_palette_controller"
        ):
            return CommandResult(status=CommandStatus.FAILURE, message="Command palette not available")

        controller = context.main_window.command_palette_controller

        # Hide the palette
        controller.hide_palette()

        return CommandResult(status=CommandStatus.SUCCESS, value="Command palette hidden")

    except Exception as e:
        logger.error(f"Failed to hide command palette: {e}")
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


@command(
    id="commandPalette.refresh",
    title="Refresh Command Palette",
    category="Debug",
    description="Refresh the command palette command list",
    icon="refresh",
)
def refresh_command_palette_command(context: CommandContext) -> CommandResult:
    """Refresh the command palette."""
    try:
        # Check if main window has a command palette controller
        if not context.main_window or not hasattr(
            context.main_window, "command_palette_controller"
        ):
            return CommandResult(status=CommandStatus.FAILURE, message="Command palette not available")

        controller = context.main_window.command_palette_controller

        # Refresh commands
        controller.refresh_commands()

        return CommandResult(status=CommandStatus.SUCCESS, value="Command palette refreshed")

    except Exception as e:
        logger.error(f"Failed to refresh command palette: {e}")
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


def register_palette_commands():
    """Register all palette commands."""
    # The @command decorator automatically registers them
    # This function ensures the module is imported
    logger.info("Palette commands registered")
