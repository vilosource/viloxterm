#!/usr/bin/env python3
"""
Terminal-related commands.

Provides commands for terminal operations like clearing, creating new terminals,
copying/pasting, and managing terminal sessions.
"""

import logging

from viloapp.core.commands.base import CommandContext, CommandResult, CommandStatus, FunctionCommand
from viloapp.core.commands.registry import command_registry

logger = logging.getLogger(__name__)


def clear_terminal_handler(context: CommandContext) -> CommandResult:
    """Clear the active terminal."""
    try:
        # Get active pane widget directly from model
        if not context.model:
            return CommandResult(status=CommandStatus.FAILURE, message="Model not available")

        active_tab = context.model.state.get_active_tab()
        if not active_tab or not active_tab.active_pane_id:
            return CommandResult(status=CommandStatus.FAILURE, message="No active pane")

        active_pane = active_tab.tree.root.find_pane(active_tab.active_pane_id)
        if not active_pane:
            return CommandResult(status=CommandStatus.FAILURE, message="Active pane not found")

        # Get widget from pane
        current_widget = active_pane.widget

        # Check if it's a terminal widget
        if current_widget and hasattr(current_widget, "clear_terminal"):
            current_widget.clear_terminal()
            return CommandResult(status=CommandStatus.SUCCESS, data="Terminal cleared")

        return CommandResult(status=CommandStatus.FAILURE, message="No active terminal to clear")

    except Exception as e:
        logger.error(f"Failed to clear terminal: {e}")
        return CommandResult(
            status=CommandStatus.FAILURE, message=f"Failed to clear terminal: {str(e)}"
        )


def new_terminal_handler(context: CommandContext) -> CommandResult:
    """Create a new terminal tab."""
    try:
        if not context.model:
            return CommandResult(status=CommandStatus.FAILURE, message="Model not available")

        # Count existing terminal tabs for naming
        terminal_count = sum(1 for tab in context.model.state.tabs if "Terminal" in tab.name)
        name = f"Terminal {terminal_count + 1}"

        # Create new terminal tab using model directly
        from viloapp.models.workspace_model import WidgetType

        tab_id = context.model.create_tab(name, WidgetType.TERMINAL)
        index = len(context.model.state.tabs) - 1

        return CommandResult(
            status=CommandStatus.SUCCESS,
            data={"message": "New terminal created", "index": index, "tab_id": tab_id},
        )

    except Exception as e:
        logger.error(f"Failed to create new terminal: {e}")
        return CommandResult(
            status=CommandStatus.FAILURE, message=f"Failed to create terminal: {str(e)}"
        )


def copy_terminal_handler(context: CommandContext) -> CommandResult:
    """Copy from terminal."""
    try:
        # Get active pane widget directly from model
        if not context.model:
            return CommandResult(status=CommandStatus.FAILURE, message="Model not available")

        active_tab = context.model.state.get_active_tab()
        if not active_tab or not active_tab.active_pane_id:
            return CommandResult(status=CommandStatus.FAILURE, message="No active pane")

        active_pane = active_tab.tree.root.find_pane(active_tab.active_pane_id)
        if not active_pane:
            return CommandResult(status=CommandStatus.FAILURE, message="Active pane not found")

        # Get widget from pane
        current_widget = active_pane.widget

        # Check if it's a terminal widget and has copy method
        if current_widget and hasattr(current_widget, "copy_selection"):
            current_widget.copy_selection()
            return CommandResult(status=CommandStatus.SUCCESS, data="Copied to clipboard")

        return CommandResult(
            status=CommandStatus.FAILURE, message="No active terminal to copy from"
        )

    except Exception as e:
        logger.error(f"Failed to copy from terminal: {e}")
        return CommandResult(status=CommandStatus.FAILURE, message=f"Failed to copy: {str(e)}")


def paste_terminal_handler(context: CommandContext) -> CommandResult:
    """Paste to terminal."""
    try:
        from PySide6.QtWidgets import QApplication

        # Get active pane widget directly from model
        if not context.model:
            return CommandResult(status=CommandStatus.FAILURE, message="Model not available")

        active_tab = context.model.state.get_active_tab()
        if not active_tab or not active_tab.active_pane_id:
            return CommandResult(status=CommandStatus.FAILURE, message="No active pane")

        active_pane = active_tab.tree.root.find_pane(active_tab.active_pane_id)
        if not active_pane:
            return CommandResult(status=CommandStatus.FAILURE, message="Active pane not found")

        # Get widget from pane
        current_widget = active_pane.widget

        # Check if it's a terminal widget
        if current_widget and hasattr(current_widget, "paste_to_terminal"):
            clipboard = QApplication.clipboard()
            text = clipboard.text()
            if text:
                current_widget.paste_to_terminal(text)
                return CommandResult(status=CommandStatus.SUCCESS, data="Pasted to terminal")
            else:
                return CommandResult(status=CommandStatus.FAILURE, message="Clipboard is empty")

        return CommandResult(status=CommandStatus.FAILURE, message="No active terminal to paste to")

    except Exception as e:
        logger.error(f"Failed to paste to terminal: {e}")
        return CommandResult(status=CommandStatus.FAILURE, message=f"Failed to paste: {str(e)}")


def kill_terminal_handler(context: CommandContext) -> CommandResult:
    """Kill the current terminal."""
    try:
        # Get active pane widget directly from model
        if not context.model:
            return CommandResult(status=CommandStatus.FAILURE, message="Model not available")

        active_tab = context.model.state.get_active_tab()
        if not active_tab or not active_tab.active_pane_id:
            return CommandResult(status=CommandStatus.FAILURE, message="No active pane")

        active_pane = active_tab.tree.root.find_pane(active_tab.active_pane_id)
        if not active_pane:
            return CommandResult(status=CommandStatus.FAILURE, message="Active pane not found")

        # Get widget from pane
        current_widget = active_pane.widget

        # Check if current widget is a terminal
        if current_widget and hasattr(current_widget, "close_terminal"):
            # Close current tab using model
            success = context.model.close_tab(active_tab.id)
            if success:
                return CommandResult(status=CommandStatus.SUCCESS, data="Terminal closed")

        return CommandResult(status=CommandStatus.FAILURE, message="No active terminal to close")

    except Exception as e:
        logger.error(f"Failed to kill terminal: {e}")
        return CommandResult(
            status=CommandStatus.FAILURE, message=f"Failed to kill terminal: {str(e)}"
        )


def restart_terminal_handler(context: CommandContext) -> CommandResult:
    """Restart the current terminal."""
    try:
        # Get active pane widget directly from model
        if not context.model:
            return CommandResult(status=CommandStatus.FAILURE, message="Model not available")

        active_tab = context.model.state.get_active_tab()
        if not active_tab or not active_tab.active_pane_id:
            return CommandResult(status=CommandStatus.FAILURE, message="No active pane")

        active_pane = active_tab.tree.root.find_pane(active_tab.active_pane_id)
        if not active_pane:
            return CommandResult(status=CommandStatus.FAILURE, message="Active pane not found")

        # Get widget from pane
        current_widget = active_pane.widget

        # Check if it's a terminal widget
        if current_widget and hasattr(current_widget, "restart_terminal"):
            current_widget.restart_terminal()
            return CommandResult(status=CommandStatus.SUCCESS, data="Terminal restarted")

        return CommandResult(status=CommandStatus.FAILURE, message="No active terminal to restart")

    except Exception as e:
        logger.error(f"Failed to restart terminal: {e}")
        return CommandResult(
            status=CommandStatus.FAILURE, message=f"Failed to restart terminal: {str(e)}"
        )


def register_terminal_commands():
    """Register all terminal commands."""
    commands = [
        FunctionCommand(
            id="terminal.clear",
            title="Clear Terminal",
            category="Terminal",
            handler=clear_terminal_handler,
            description="Clear the terminal screen",
            shortcut="ctrl+l",
            keywords=["clear", "cls", "reset"],
        ),
        FunctionCommand(
            id="terminal.new",
            title="New Terminal",
            category="Terminal",
            handler=new_terminal_handler,
            description="Open a new terminal tab",
            shortcut="ctrl+shift+`",
            keywords=["new", "terminal", "console", "shell"],
        ),
        FunctionCommand(
            id="terminal.copy",
            title="Copy from Terminal",
            category="Terminal",
            handler=copy_terminal_handler,
            description="Copy selected text from the terminal",
            shortcut="ctrl+shift+c",
            keywords=["copy", "clipboard"],
        ),
        FunctionCommand(
            id="terminal.paste",
            title="Paste to Terminal",
            category="Terminal",
            handler=paste_terminal_handler,
            description="Paste text from clipboard to the terminal",
            shortcut="ctrl+shift+v",
            keywords=["paste", "clipboard"],
        ),
        FunctionCommand(
            id="terminal.kill",
            title="Kill Terminal",
            category="Terminal",
            handler=kill_terminal_handler,
            description="Terminate the current terminal session",
            keywords=["kill", "terminate", "close", "exit"],
        ),
        FunctionCommand(
            id="terminal.restart",
            title="Restart Terminal",
            category="Terminal",
            handler=restart_terminal_handler,
            description="Restart the current terminal session",
            keywords=["restart", "reset", "reload"],
        ),
    ]

    for command in commands:
        command_registry.register(command)

    logger.info(f"Registered {len(commands)} terminal commands")
