#!/usr/bin/env python3
"""
Commands for managing the widget registry.

These commands ensure proper architectural flow:
User Action → Command → Service → UI Update
"""

import logging

from viloapp.core.commands.base import CommandContext, CommandResult, CommandStatus
from viloapp.core.commands.decorators import command

logger = logging.getLogger(__name__)


@command(
    id="workspace.registerWidget",
    title="Register Widget",
    category="Workspace",
    description="Register a widget in the workspace registry",
)
def register_widget_command(context: CommandContext) -> CommandResult:
    """
    Register a widget in the workspace registry.

    Expected context.args:
        widget_id: The widget identifier
        tab_index: The tab index where the widget is located
    """
    # Get arguments from context
    widget_id = context.parameters.get("widget_id") if context.parameters else None
    tab_index = context.parameters.get("tab_index") if context.parameters else None

    if widget_id is None or tab_index is None:
        return CommandResult(
            status=CommandStatus.FAILURE, message="widget_id and tab_index are required"
        )

    if not context.model:
        return CommandResult(status=CommandStatus.FAILURE, message="Model not available")

    try:
        # Widget registration is now handled by AppWidgetManager
        # This command is kept for compatibility but doesn't actually register
        # The AppWidgetManager tracks all widget instances automatically

        return CommandResult(
            status=CommandStatus.SUCCESS, data={"widget_id": widget_id, "tab_index": tab_index}
        )
    except Exception as e:
        logger.error(f"Failed to register widget: {e}")
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


@command(
    id="workspace.unregisterWidget",
    title="Unregister Widget",
    category="Workspace",
    description="Remove a widget from the workspace registry",
)
def unregister_widget_command(context: CommandContext) -> CommandResult:
    """
    Remove a widget from the workspace registry.

    Expected context.args:
        widget_id: The widget identifier to remove
    """
    # Get arguments from context
    widget_id = context.parameters.get("widget_id") if context.parameters else None

    if widget_id is None:
        return CommandResult(status=CommandStatus.FAILURE, message="widget_id is required")

    if not context.model:
        return CommandResult(status=CommandStatus.FAILURE, message="Model not available")

    try:
        # Widget unregistration is now handled by AppWidgetManager
        # This command is kept for compatibility
        result = False

        return CommandResult(
            status=CommandStatus.SUCCESS, data={"widget_id": widget_id, "unregistered": result}
        )
    except Exception as e:
        logger.error(f"Failed to unregister widget: {e}")
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


@command(
    id="workspace.updateRegistryAfterClose",
    title="Update Registry After Tab Close",
    category="Workspace",
    description="Update widget registry indices after a tab is closed",
)
def update_registry_after_close_command(context: CommandContext) -> CommandResult:
    """
    Update the widget registry after a tab is closed.

    This command:
    1. Removes the widget at the closed index (if widget_id provided)
    2. Updates all widget indices that were after the closed tab

    Expected context.args:
        closed_index: The index of the tab that was closed
        widget_id: Optional widget ID that was closed
    """
    # Get arguments from context
    closed_index = context.parameters.get("closed_index") if context.parameters else None
    # widget_id parameter is no longer used since widget registry is handled by AppWidgetManager

    if closed_index is None:
        return CommandResult(status=CommandStatus.FAILURE, message="closed_index is required")

    if not context.model:
        return CommandResult(status=CommandStatus.FAILURE, message="Model not available")

    try:
        # Widget registry updates are now handled by AppWidgetManager
        # This command is kept for compatibility
        updated_count = 0

        return CommandResult(
            status=CommandStatus.SUCCESS,
            data={"closed_index": closed_index, "updated_count": updated_count},
        )
    except Exception as e:
        logger.error(f"Failed to update registry after close: {e}")
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


@command(
    id="workspace.getWidgetTabIndex",
    title="Get Widget Tab Index",
    category="Workspace",
    description="Get the tab index for a registered widget",
)
def get_widget_tab_index_command(context: CommandContext) -> CommandResult:
    """
    Get the tab index for a registered widget.

    Expected context.args:
        widget_id: The widget identifier
    """
    # Get arguments from context
    widget_id = context.parameters.get("widget_id") if context.parameters else None

    if widget_id is None:
        return CommandResult(status=CommandStatus.FAILURE, message="widget_id is required")

    if not context.model:
        return CommandResult(status=CommandStatus.FAILURE, message="Model not available")

    try:
        # Widget to tab mapping is handled by the model's tab structure
        # This command is kept for compatibility but always returns not found
        tab_index = None
        if False:  # Disabled - widget registry no longer exists
            return CommandResult(
                status=CommandStatus.SUCCESS, data={"widget_id": widget_id, "tab_index": tab_index}
            )
        else:
            return CommandResult(
                status=CommandStatus.FAILURE, message=f"Widget {widget_id} not found in registry"
            )
    except Exception as e:
        logger.error(f"Failed to get widget tab index: {e}")
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


@command(
    id="workspace.isWidgetRegistered",
    title="Check Widget Registration",
    category="Workspace",
    description="Check if a widget is registered",
)
def is_widget_registered_command(context: CommandContext) -> CommandResult:
    """
    Check if a widget is registered in the workspace.

    Expected context.args:
        widget_id: The widget identifier
    """
    # Get arguments from context
    widget_id = context.parameters.get("widget_id") if context.parameters else None

    if widget_id is None:
        return CommandResult(status=CommandStatus.FAILURE, message="widget_id is required")

    if not context.model:
        return CommandResult(status=CommandStatus.FAILURE, message="Model not available")

    try:
        # Widget registration check is handled by AppWidgetManager
        from viloapp.core.app_widget_manager import app_widget_manager

        is_registered = app_widget_manager.is_widget_available(widget_id)

        return CommandResult(
            status=CommandStatus.SUCCESS, data={"widget_id": widget_id, "registered": is_registered}
        )
    except Exception as e:
        logger.error(f"Failed to check widget registration: {e}")
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))
