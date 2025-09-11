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
from core.services.locator import ServiceLocator

logger = logging.getLogger(__name__)


class ClearTerminalCommand(Command):
    """Clear the active terminal."""
    
    def __init__(self):
        super().__init__(
            id="terminal.clear",
            title="Clear Terminal",
            category="Terminal",
            description="Clear the terminal screen",
            shortcut="Ctrl+L",
            keywords=["clear", "cls", "reset"]
        )
    
    def execute(self, context: CommandContext) -> CommandResult:
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


class NewTerminalCommand(Command):
    """Create a new terminal tab."""
    
    def __init__(self):
        super().__init__(
            id="terminal.new",
            title="New Terminal",
            category="Terminal",
            description="Open a new terminal tab",
            shortcut="Ctrl+Shift+`",
            keywords=["new", "terminal", "console", "shell"]
        )
    
    def execute(self, context: CommandContext) -> CommandResult:
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


class CopyTerminalCommand(Command):
    """Copy selected text from terminal."""
    
    def __init__(self):
        super().__init__(
            id="terminal.copy",
            title="Copy from Terminal",
            category="Terminal",
            description="Copy selected text from the terminal",
            shortcut="Ctrl+Shift+C",
            keywords=["copy", "clipboard"]
        )
    
    def execute(self, context: CommandContext) -> CommandResult:
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


class PasteTerminalCommand(Command):
    """Paste text to terminal."""
    
    def __init__(self):
        super().__init__(
            id="terminal.paste",
            title="Paste to Terminal",
            category="Terminal",
            description="Paste text from clipboard to the terminal",
            shortcut="Ctrl+Shift+V",
            keywords=["paste", "clipboard"]
        )
    
    def execute(self, context: CommandContext) -> CommandResult:
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


class KillTerminalCommand(Command):
    """Kill the current terminal session."""
    
    def __init__(self):
        super().__init__(
            id="terminal.kill",
            title="Kill Terminal",
            category="Terminal",
            description="Terminate the current terminal session",
            keywords=["kill", "terminate", "close", "exit"]
        )
    
    def execute(self, context: CommandContext) -> CommandResult:
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


class RestartTerminalCommand(Command):
    """Restart the current terminal session."""
    
    def __init__(self):
        super().__init__(
            id="terminal.restart",
            title="Restart Terminal",
            category="Terminal",
            description="Restart the current terminal session",
            keywords=["restart", "reset", "reload"]
        )
    
    def execute(self, context: CommandContext) -> CommandResult:
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
        ClearTerminalCommand(),
        NewTerminalCommand(),
        CopyTerminalCommand(),
        PasteTerminalCommand(),
        KillTerminalCommand(),
        RestartTerminalCommand(),
    ]
    
    for command in commands:
        command_registry.register(command)
    
    logger.info(f"Registered {len(commands)} terminal commands")