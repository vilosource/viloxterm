#!/usr/bin/env python3
"""
Example capability-based commands for ViloxTerm.

This module demonstrates how to write commands that interact with widgets
based on their capabilities rather than their types.

ARCHITECTURE COMPLIANCE:
- Commands don't know widget types
- All interactions through capabilities
- Dynamic widget discovery
"""

import logging

from viloapp.core.capabilities import WidgetCapability
from viloapp.core.commands.base import CommandContext, CommandResult, CommandStatus
from viloapp.core.commands.capability_commands import (
    execute_on_capable_widget,
    find_widget_for_capability,
)
from viloapp.core.commands.decorators import command

logger = logging.getLogger(__name__)


@command(
    id="capability.clearDisplay",
    title="Clear Display",
    category="View",
    description="Clear the display of any widget that supports it",
    shortcut="ctrl+l",
)
def clear_display_command(context: CommandContext) -> CommandResult:
    """
    Clear the display of the active widget or any widget that supports it.

    This command works with ANY widget that has CLEAR_DISPLAY capability,
    not just terminals. It could work with editors, output panels, etc.
    """
    return execute_on_capable_widget(
        WidgetCapability.CLEAR_DISPLAY,
        context
    )


@command(
    id="capability.copySelection",
    title="Copy Selection",
    category="Edit",
    description="Copy selected content from any capable widget",
    shortcut="ctrl+c",
)
def copy_selection_command(context: CommandContext) -> CommandResult:
    """
    Copy selection from any widget that supports clipboard operations.

    Works with terminals, editors, viewers - anything with CLIPBOARD_COPY.
    """
    return execute_on_capable_widget(
        WidgetCapability.CLIPBOARD_COPY,
        context
    )


@command(
    id="capability.pasteContent",
    title="Paste Content",
    category="Edit",
    description="Paste content into any capable widget",
    shortcut="ctrl+v",
)
def paste_content_command(context: CommandContext) -> CommandResult:
    """
    Paste content into any widget that supports it.

    The widget determines how to handle the pasted content.
    """
    return execute_on_capable_widget(
        WidgetCapability.CLIPBOARD_PASTE,
        context
    )


@command(
    id="capability.saveContent",
    title="Save Content",
    category="File",
    description="Save content from any capable widget",
    shortcut="ctrl+s",
)
def save_content_command(context: CommandContext) -> CommandResult:
    """
    Save content from any widget that supports file saving.

    Each widget handles saving in its own way - editors save files,
    settings save configurations, etc.
    """
    # Get optional file path from context
    file_path = context.parameters.get("file_path") if context.parameters else None

    return execute_on_capable_widget(
        WidgetCapability.FILE_SAVING,
        context,
        file_path=file_path
    )


@command(
    id="capability.findText",
    title="Find Text",
    category="Edit",
    description="Search for text in any capable widget",
    shortcut="ctrl+f",
)
def find_text_command(context: CommandContext) -> CommandResult:
    """
    Open find dialog for any widget that supports text search.

    Works with any widget that has TEXT_SEARCH capability.
    """
    search_term = context.parameters.get("search_term") if context.parameters else None

    if not search_term:
        # Could open a find dialog here
        # For now, just indicate that search term is needed
        return CommandResult(
            status=CommandStatus.FAILURE,
            message="Search term required"
        )

    return execute_on_capable_widget(
        WidgetCapability.TEXT_SEARCH,
        context,
        search_term=search_term
    )


@command(
    id="capability.zoomIn",
    title="Zoom In",
    category="View",
    description="Zoom in on any capable widget",
    shortcut="ctrl+plus",
)
def zoom_in_command(context: CommandContext) -> CommandResult:
    """
    Zoom in on any widget that supports zoom operations.

    Each widget handles zoom in its own way.
    """
    return execute_on_capable_widget(
        WidgetCapability.ZOOM_CONTENT,
        context,
        action="zoom_in",
        amount=1.1  # 10% zoom
    )


@command(
    id="capability.zoomOut",
    title="Zoom Out",
    category="View",
    description="Zoom out on any capable widget",
    shortcut="ctrl+minus",
)
def zoom_out_command(context: CommandContext) -> CommandResult:
    """
    Zoom out on any widget that supports zoom operations.
    """
    return execute_on_capable_widget(
        WidgetCapability.ZOOM_CONTENT,
        context,
        action="zoom_out",
        amount=0.9  # 10% zoom out
    )


@command(
    id="capability.executeCommand",
    title="Execute Command",
    category="Terminal",
    description="Execute a command in any shell-capable widget",
)
def execute_command_in_shell(context: CommandContext) -> CommandResult:
    """
    Execute a command in any widget that supports shell execution.

    This could be a terminal, REPL, or any other shell-capable widget.
    """
    command_text = context.parameters.get("command") if context.parameters else None

    if not command_text:
        return CommandResult(
            status=CommandStatus.FAILURE,
            message="Command text required"
        )

    return execute_on_capable_widget(
        WidgetCapability.SHELL_EXECUTION,
        context,
        command=command_text
    )


@command(
    id="capability.openFile",
    title="Open File in Capable Widget",
    category="File",
    description="Open a file in any widget that can handle it",
)
def open_file_command(context: CommandContext) -> CommandResult:
    """
    Open a file in any widget that supports file operations.

    The system finds an appropriate widget based on capabilities.
    """
    file_path = context.parameters.get("file_path") if context.parameters else None

    if not file_path:
        return CommandResult(
            status=CommandStatus.FAILURE,
            message="File path required"
        )

    # First try FILE_OPENING capability
    widget_id = find_widget_for_capability(
        WidgetCapability.FILE_OPENING,
        prefer_active=True,
        context=context
    )

    # Fall back to FILE_VIEWING if no opener found
    if not widget_id:
        widget_id = find_widget_for_capability(
            WidgetCapability.FILE_VIEWING,
            prefer_active=True,
            context=context
        )

    if not widget_id:
        return CommandResult(
            status=CommandStatus.FAILURE,
            message="No widget found that can open files"
        )

    # Execute the appropriate capability
    from viloapp.core.capability_manager import capability_manager

    try:
        # Try opening first
        if capability_manager.widget_has_capability(widget_id, WidgetCapability.FILE_OPENING):
            result = capability_manager.execute_capability(
                widget_id,
                WidgetCapability.FILE_OPENING,
                file_path=file_path
            )
        else:
            # Fall back to viewing
            result = capability_manager.execute_capability(
                widget_id,
                WidgetCapability.FILE_VIEWING,
                file_path=file_path
            )

        return CommandResult(
            status=CommandStatus.SUCCESS,
            data={"widget_id": widget_id, "file_path": file_path, "result": result}
        )
    except Exception as e:
        logger.error(f"Failed to open file: {e}")
        return CommandResult(
            status=CommandStatus.FAILURE,
            message=str(e)
        )


def register_capability_example_commands():
    """Register capability-based example commands."""
    logger.info("Capability example commands registered")
