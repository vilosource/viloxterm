"""Editor command registration."""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


def register_editor_commands(command_service, plugin_instance):
    """Register editor commands with the command service."""

    # Define command handlers
    def open_file_command(args: Dict[str, Any] = None):
        return plugin_instance._open_file(args or {})

    def save_file_command(args: Dict[str, Any] = None):
        return plugin_instance._save_file(args or {})

    def save_file_as_command(args: Dict[str, Any] = None):
        return plugin_instance._save_file_as(args or {})

    def close_editor_command(args: Dict[str, Any] = None):
        return plugin_instance._close_editor(args or {})

    def new_file_command(args: Dict[str, Any] = None):
        return plugin_instance._new_file(args or {})

    # Register commands
    try:
        command_service.register_command("editor.open", open_file_command)
        command_service.register_command("editor.save", save_file_command)
        command_service.register_command("editor.saveAs", save_file_as_command)
        command_service.register_command("editor.close", close_editor_command)
        command_service.register_command("editor.new", new_file_command)

        logger.info("Editor commands registered successfully")
    except Exception as e:
        logger.error(f"Failed to register editor commands: {e}")