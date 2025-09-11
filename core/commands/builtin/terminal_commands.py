#!/usr/bin/env python3
"""
Terminal-related commands.

Provides commands for terminal operations like clearing, creating new terminals,
copying/pasting, and managing terminal sessions.
"""

from typing import Optional, Dict, Any
import logging

from core.commands.base import Command, CommandContext, CommandResult
from core.commands.registry import command_registry
from services.service_locator import ServiceLocator

logger = logging.getLogger(__name__)


def clear_terminal_handler(context: CommandContext) -> CommandResult:
        """Clear the active terminal."""
        try:
            main_window = ServiceLocator.get_service("main_window")
            if not main_window:
                return CommandResult(
                    success=False,
                    message="Main window not available"
                )
            
            # Get the active terminal widget
            workspace = main_window.workspace
            if workspace and hasattr(workspace, 'get_current_widget'):
                current_widget = workspace.get_current_widget()
                
                # Check if it's a terminal widget
                if current_widget and hasattr(current_widget, 'clear_terminal'):
                    current_widget.clear_terminal()
                    return CommandResult(
                        success=True,
                        message="Terminal cleared"
                    )
            
            return CommandResult(
                success=False,
                message="No active terminal to clear"
            )
            
        except Exception as e:
            logger.error(f"Failed to clear terminal: {e}")
            return CommandResult(
                success=False,
                message=f"Failed to clear terminal: {str(e)}"
            )


def new_terminal_handler(context: CommandContext) -> CommandResult:
        """Create a new terminal tab."""
        try:
            main_window = ServiceLocator.get_service("main_window")
            if not main_window:
                return CommandResult(
                    success=False,
                    message="Main window not available"
                )
            
            # Use the existing new_terminal_tab method
            if hasattr(main_window, 'new_terminal_tab'):
                main_window.new_terminal_tab()
                return CommandResult(
                    success=True,
                    message="New terminal created"
                )
            
            return CommandResult(
                success=False,
                message="Terminal creation not available"
            )
            
        except Exception as e:
            logger.error(f"Failed to create new terminal: {e}")
            return CommandResult(
                success=False,
                message=f"Failed to create terminal: {str(e)}"
            )


def copy_terminal_handler(context: CommandContext) -> CommandResult:
        """Copy from terminal."""
        try:
            main_window = ServiceLocator.get_service("main_window")
            if not main_window:
                return CommandResult(
                    success=False,
                    message="Main window not available"
                )
            
            workspace = main_window.workspace
            if workspace and hasattr(workspace, 'get_current_widget'):
                current_widget = workspace.get_current_widget()
                
                # Check if it's a terminal widget and has copy method
                if current_widget and hasattr(current_widget, 'copy_selection'):
                    current_widget.copy_selection()
                    return CommandResult(
                        success=True,
                        message="Copied to clipboard"
                    )
            
            return CommandResult(
                success=False,
                message="No active terminal to copy from"
            )
            
        except Exception as e:
            logger.error(f"Failed to copy from terminal: {e}")
            return CommandResult(
                success=False,
                message=f"Failed to copy: {str(e)}"
            )


def paste_terminal_handler(context: CommandContext) -> CommandResult:
        """Paste to terminal."""
        try:
            from PySide6.QtWidgets import QApplication
            
            main_window = ServiceLocator.get_service("main_window")
            if not main_window:
                return CommandResult(
                    success=False,
                    message="Main window not available"
                )
            
            workspace = main_window.workspace
            if workspace and hasattr(workspace, 'get_current_widget'):
                current_widget = workspace.get_current_widget()
                
                # Check if it's a terminal widget
                if current_widget and hasattr(current_widget, 'paste_to_terminal'):
                    clipboard = QApplication.clipboard()
                    text = clipboard.text()
                    if text:
                        current_widget.paste_to_terminal(text)
                        return CommandResult(
                            success=True,
                            message="Pasted to terminal"
                        )
                    else:
                        return CommandResult(
                            success=False,
                            message="Clipboard is empty"
                        )
            
            return CommandResult(
                success=False,
                message="No active terminal to paste to"
            )
            
        except Exception as e:
            logger.error(f"Failed to paste to terminal: {e}")
            return CommandResult(
                success=False,
                message=f"Failed to paste: {str(e)}"
            )


def kill_terminal_handler(context: CommandContext) -> CommandResult:
        """Kill the current terminal."""
        try:
            main_window = ServiceLocator.get_service("main_window")
            if not main_window:
                return CommandResult(
                    success=False,
                    message="Main window not available"
                )
            
            workspace = main_window.workspace
            if workspace and hasattr(workspace, 'close_current_tab'):
                # Check if current tab is a terminal
                current_widget = workspace.get_current_widget()
                if current_widget and hasattr(current_widget, 'close_terminal'):
                    workspace.close_current_tab()
                    return CommandResult(
                        success=True,
                        message="Terminal closed"
                    )
            
            return CommandResult(
                success=False,
                message="No active terminal to close"
            )
            
        except Exception as e:
            logger.error(f"Failed to kill terminal: {e}")
            return CommandResult(
                success=False,
                message=f"Failed to kill terminal: {str(e)}"
            )


def restart_terminal_handler(context: CommandContext) -> CommandResult:
        """Restart the current terminal."""
        try:
            main_window = ServiceLocator.get_service("main_window")
            if not main_window:
                return CommandResult(
                    success=False,
                    message="Main window not available"
                )
            
            workspace = main_window.workspace
            if workspace and hasattr(workspace, 'get_current_widget'):
                current_widget = workspace.get_current_widget()
                
                # Check if it's a terminal widget
                if current_widget and hasattr(current_widget, 'restart_terminal'):
                    current_widget.restart_terminal()
                    return CommandResult(
                        success=True,
                        message="Terminal restarted"
                    )
            
            return CommandResult(
                success=False,
                message="No active terminal to restart"
            )
            
        except Exception as e:
            logger.error(f"Failed to restart terminal: {e}")
            return CommandResult(
                success=False,
                message=f"Failed to restart terminal: {str(e)}"
            )


def register_terminal_commands():
    """Register all terminal commands."""
    commands = [
        Command(
            id="terminal.clear",
            title="Clear Terminal",
            category="Terminal",
            handler=clear_terminal_handler,
            description="Clear the terminal screen",
            shortcut="Ctrl+L",
            keywords=["clear", "cls", "reset"]
        ),
        Command(
            id="terminal.new",
            title="New Terminal",
            category="Terminal",
            handler=new_terminal_handler,
            description="Open a new terminal tab",
            shortcut="Ctrl+Shift+`",
            keywords=["new", "terminal", "console", "shell"]
        ),
        Command(
            id="terminal.copy",
            title="Copy from Terminal",
            category="Terminal",
            handler=copy_terminal_handler,
            description="Copy selected text from the terminal",
            shortcut="Ctrl+Shift+C",
            keywords=["copy", "clipboard"]
        ),
        Command(
            id="terminal.paste",
            title="Paste to Terminal",
            category="Terminal",
            handler=paste_terminal_handler,
            description="Paste text from clipboard to the terminal",
            shortcut="Ctrl+Shift+V",
            keywords=["paste", "clipboard"]
        ),
        Command(
            id="terminal.kill",
            title="Kill Terminal",
            category="Terminal",
            handler=kill_terminal_handler,
            description="Terminate the current terminal session",
            keywords=["kill", "terminate", "close", "exit"]
        ),
        Command(
            id="terminal.restart",
            title="Restart Terminal",
            category="Terminal",
            handler=restart_terminal_handler,
            description="Restart the current terminal session",
            keywords=["restart", "reset", "reload"]
        ),
    ]
    
    for command in commands:
        command_registry.register(command)
    
    logger.info(f"Registered {len(commands)} terminal commands")