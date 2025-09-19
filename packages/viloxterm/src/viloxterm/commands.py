"""Terminal command definitions."""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


def register_terminal_commands(command_service):
    """Register all terminal commands."""

    commands = [
        {
            "id": "terminal.new",
            "handler": create_new_terminal,
            "title": "New Terminal",
            "category": "Terminal",
            "description": "Create a new terminal instance"
        },
        {
            "id": "terminal.clear",
            "handler": clear_terminal,
            "title": "Clear Terminal",
            "category": "Terminal",
            "description": "Clear the terminal screen"
        },
        {
            "id": "terminal.close",
            "handler": close_terminal,
            "title": "Close Terminal",
            "category": "Terminal",
            "description": "Close the current terminal"
        },
        {
            "id": "terminal.split",
            "handler": split_terminal,
            "title": "Split Terminal",
            "category": "Terminal",
            "description": "Split the terminal pane"
        },
        {
            "id": "terminal.focus",
            "handler": focus_terminal,
            "title": "Focus Terminal",
            "category": "Terminal",
            "description": "Focus on the terminal"
        },
        {
            "id": "terminal.selectDefaultShell",
            "handler": select_default_shell,
            "title": "Select Default Shell",
            "category": "Terminal",
            "description": "Choose the default shell for new terminals"
        }
    ]

    for cmd in commands:
        command_service.register_command(
            cmd["id"],
            cmd["handler"],
            title=cmd.get("title"),
            category=cmd.get("category"),
            description=cmd.get("description")
        )


def create_new_terminal(context, **kwargs) -> Dict[str, Any]:
    """Create a new terminal."""
    from .widget import TerminalWidget

    workspace_service = context.get_service("workspace")
    if not workspace_service:
        return {"success": False, "error": "Workspace service not available"}

    # Create terminal widget
    widget = TerminalWidget()

    # Get configuration
    config_service = context.get_service("configuration")
    if config_service:
        import platform
        if platform.system() == "Windows":
            shell = config_service.get("terminal.shell.windows", "powershell.exe")
        else:
            shell = config_service.get("terminal.shell.linux", "/bin/bash")
    else:
        shell = None

    # Start terminal
    cwd = kwargs.get("cwd", None)
    widget.start_terminal(command=shell, cwd=cwd)

    # Add to workspace
    workspace_service.add_widget(widget, "terminal", "main")

    return {"success": True, "widget": widget}


def clear_terminal(context, **kwargs) -> Dict[str, Any]:
    """Clear the active terminal."""
    workspace_service = context.get_service("workspace")
    if not workspace_service:
        return {"success": False, "error": "Workspace service not available"}

    # Get active widget
    widget = workspace_service.get_active_widget()
    if widget and hasattr(widget, 'clear_terminal'):
        widget.clear_terminal()
        return {"success": True}

    return {"success": False, "error": "No active terminal"}


def close_terminal(context, **kwargs) -> Dict[str, Any]:
    """Close the active terminal."""
    workspace_service = context.get_service("workspace")
    if not workspace_service:
        return {"success": False, "error": "Workspace service not available"}

    # Get active widget
    widget = workspace_service.get_active_widget()
    if widget and hasattr(widget, 'stop_terminal'):
        widget.stop_terminal()
        workspace_service.remove_widget(widget)
        return {"success": True}

    return {"success": False, "error": "No active terminal"}


def split_terminal(context, **kwargs) -> Dict[str, Any]:
    """Split the terminal pane."""
    # TODO: Implement terminal splitting
    return {"success": False, "error": "Not implemented"}


def focus_terminal(context, **kwargs) -> Dict[str, Any]:
    """Focus on the terminal."""
    workspace_service = context.get_service("workspace")
    if not workspace_service:
        return {"success": False, "error": "Workspace service not available"}

    # Get active widget
    widget = workspace_service.get_active_widget()
    if widget and hasattr(widget, 'focus_terminal'):
        widget.focus_terminal()
        return {"success": True}

    return {"success": False, "error": "No active terminal"}


def select_default_shell(context, **kwargs) -> Dict[str, Any]:
    """Select the default shell."""
    # TODO: Implement shell selection dialog
    return {"success": False, "error": "Not implemented"}