#!/usr/bin/env python3
"""
Commands for managing the widget registry.

These commands ensure proper architectural flow:
User Action → Command → Service → UI Update
"""

import logging

from viloapp.core.commands.base import CommandContext, CommandResult
from viloapp.core.commands.decorators import command
from viloapp.services.workspace_service import WorkspaceService

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
    widget_id = context.args.get("widget_id")
    tab_index = context.args.get("tab_index")

    if widget_id is None or tab_index is None:
        return CommandResult(
            success=False, error="widget_id and tab_index are required"
        )

    workspace_service = context.get_service(WorkspaceService)
    if not workspace_service:
        return CommandResult(success=False, error="WorkspaceService not available")

    try:
        # Register the widget using service method
        result = workspace_service.register_widget(widget_id, tab_index)
        if result:
            return CommandResult(
                success=True, value={"widget_id": widget_id, "tab_index": tab_index}
            )
        else:
            return CommandResult(success=False, error="Failed to register widget")
    except Exception as e:
        logger.error(f"Failed to register widget: {e}")
        return CommandResult(success=False, error=str(e))


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
    widget_id = context.args.get("widget_id")

    if widget_id is None:
        return CommandResult(success=False, error="widget_id is required")

    workspace_service = context.get_service(WorkspaceService)
    if not workspace_service:
        return CommandResult(success=False, error="WorkspaceService not available")

    try:
        # Unregister the widget using service method
        result = workspace_service.unregister_widget(widget_id)
        return CommandResult(
            success=True, value={"widget_id": widget_id, "unregistered": result}
        )
    except Exception as e:
        logger.error(f"Failed to unregister widget: {e}")
        return CommandResult(success=False, error=str(e))


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
    closed_index = context.args.get("closed_index")
    widget_id = context.args.get("widget_id")

    if closed_index is None:
        return CommandResult(success=False, error="closed_index is required")

    workspace_service = context.get_service(WorkspaceService)
    if not workspace_service:
        return CommandResult(success=False, error="WorkspaceService not available")

    try:
        # Update registry using service method
        updated_count = workspace_service.update_registry_after_tab_close(
            closed_index, widget_id
        )

        return CommandResult(
            success=True,
            value={"closed_index": closed_index, "updated_count": updated_count},
        )
    except Exception as e:
        logger.error(f"Failed to update registry after close: {e}")
        return CommandResult(success=False, error=str(e))


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
    widget_id = context.args.get("widget_id")

    if widget_id is None:
        return CommandResult(success=False, error="widget_id is required")

    workspace_service = context.get_service(WorkspaceService)
    if not workspace_service:
        return CommandResult(success=False, error="WorkspaceService not available")

    try:
        # Get tab index using service method
        tab_index = workspace_service.get_widget_tab_index(widget_id)
        if tab_index is not None:
            return CommandResult(
                success=True, value={"widget_id": widget_id, "tab_index": tab_index}
            )
        else:
            return CommandResult(
                success=False, error=f"Widget {widget_id} not found in registry"
            )
    except Exception as e:
        logger.error(f"Failed to get widget tab index: {e}")
        return CommandResult(success=False, error=str(e))


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
    widget_id = context.args.get("widget_id")

    if widget_id is None:
        return CommandResult(success=False, error="widget_id is required")

    workspace_service = context.get_service(WorkspaceService)
    if not workspace_service:
        return CommandResult(success=False, error="WorkspaceService not available")

    try:
        # Check registration using service method
        is_registered = workspace_service.is_widget_registered(widget_id)

        return CommandResult(
            success=True, value={"widget_id": widget_id, "registered": is_registered}
        )
    except Exception as e:
        logger.error(f"Failed to check widget registration: {e}")
        return CommandResult(success=False, error=str(e))
