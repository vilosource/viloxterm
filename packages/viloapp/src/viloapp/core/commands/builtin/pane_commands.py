#!/usr/bin/env python3
"""
Pane management commands.

This module contains commands for managing panes including
splitting, closing, and widget type changes.
"""

import logging
from typing import Optional

from viloapp.core.commands.base import Command, CommandContext, CommandResult, CommandStatus
from viloapp.core.commands.decorators import command
from viloapp.models.workspace_model import WidgetType

logger = logging.getLogger(__name__)


@command(
    id="workbench.action.splitPaneHorizontal",
    title="Split Pane Horizontal",
    category="Panes",
    description="Split the current pane horizontally",
)
def split_pane_horizontal_command(context: CommandContext) -> CommandResult:
    """
    Split a pane horizontally.

    Args:
        context: Command context with optional pane reference

    Returns:
        CommandResult indicating success or failure
    """
    try:
        # Use model directly
        if not context.model or not hasattr(context.model, "split_pane"):
            return CommandResult(status=CommandStatus.FAILURE, message="Model not available")

        # Get active pane to split
        active_tab = context.model.state.get_active_tab()
        if not active_tab or not active_tab.active_pane_id:
            return CommandResult(status=CommandStatus.FAILURE, message="No active pane to split")

        # Split the active pane horizontally
        new_pane_id = context.model.split_pane(active_tab.active_pane_id, "horizontal")

        if new_pane_id:
            return CommandResult(
                status=CommandStatus.SUCCESS,
                data={"action": "split_horizontal", "pane_id": new_pane_id},
            )
        else:
            return CommandResult(status=CommandStatus.FAILURE, message="Could not split pane")

    except Exception as e:
        logger.error(f"Error splitting pane horizontally: {e}", exc_info=True)
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


@command(
    id="workbench.action.splitPaneVertical",
    title="Split Pane Vertical",
    category="Panes",
    description="Split the current pane vertically",
)
def split_pane_vertical_command(context: CommandContext) -> CommandResult:
    """
    Split a pane vertically.

    Args:
        context: Command context with optional pane reference

    Returns:
        CommandResult indicating success or failure
    """
    try:
        # Use model directly
        if not context.model or not hasattr(context.model, "split_pane"):
            return CommandResult(status=CommandStatus.FAILURE, message="Model not available")

        # Get active pane to split
        active_tab = context.model.state.get_active_tab()
        if not active_tab or not active_tab.active_pane_id:
            return CommandResult(status=CommandStatus.FAILURE, message="No active pane to split")

        # Split the active pane vertically
        new_pane_id = context.model.split_pane(active_tab.active_pane_id, "vertical")

        if new_pane_id:
            return CommandResult(
                status=CommandStatus.SUCCESS,
                data={"action": "split_vertical", "pane_id": new_pane_id},
            )
        else:
            return CommandResult(status=CommandStatus.FAILURE, message="Could not split pane")

    except Exception as e:
        logger.error(f"Error splitting pane vertically: {e}", exc_info=True)
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


@command(
    id="workbench.action.closePane",
    title="Close Pane",
    category="Panes",
    description="Close the current pane",
    shortcut="ctrl+shift+w",
)
def close_pane_command(context: CommandContext) -> CommandResult:
    """
    Close a pane.

    Args:
        context: Command context with optional pane reference

    Returns:
        CommandResult indicating success or failure
    """
    try:
        # Use model directly
        if not context.model or not hasattr(context.model, "close_pane"):
            return CommandResult(status=CommandStatus.FAILURE, message="Model not available")

        # Get the pane from context if provided
        pane = context.parameters.get("pane")
        pane_id = context.parameters.get("pane_id")

        # Extract pane_id from the pane object if it has a leaf_node
        if not pane_id and pane:
            if hasattr(pane, "leaf_node") and hasattr(pane.leaf_node, "id"):
                pane_id = pane.leaf_node.id
            elif hasattr(pane, "pane_id"):
                pane_id = pane.pane_id

        # If no specific pane provided, use active pane
        if not pane_id:
            active_tab = context.model.state.get_active_tab()
            if not active_tab or not active_tab.active_pane_id:
                return CommandResult(
                    status=CommandStatus.FAILURE, message="No active pane to close"
                )
            pane_id = active_tab.active_pane_id

        # Check if it's the last pane in the tab
        active_tab = context.model.state.get_active_tab()
        if active_tab:
            panes = active_tab.tree.root.get_all_panes()
            if len(panes) <= 1:
                return CommandResult(
                    status=CommandStatus.NOT_APPLICABLE, message="Cannot close the last pane"
                )

        # Close the pane
        result = context.model.close_pane(pane_id)

        if result:
            return CommandResult(
                status=CommandStatus.SUCCESS, data={"action": "close_pane", "pane_id": pane_id}
            )
        else:
            return CommandResult(status=CommandStatus.FAILURE, message="Failed to close pane")

    except Exception as e:
        logger.error(f"Error closing pane: {e}", exc_info=True)
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


@command(
    id="panes.toggleMaximize",
    title="Toggle Maximize Pane",
    category="Panes",
    description="Maximize or restore the current pane",
)
def maximize_pane_command(context: CommandContext) -> CommandResult:
    """
    Maximize or restore a pane.

    Args:
        context: Command context with optional pane reference

    Returns:
        CommandResult indicating success or failure
    """
    try:
        # Use model directly
        if not context.model or not hasattr(context.model, "maximize_pane"):
            return CommandResult(status=CommandStatus.FAILURE, message="Model not available")

        # Maximize or restore the active pane
        success = context.model.maximize_pane()

        if success:
            logger.info("Pane maximized/restored successfully")
            return CommandResult(status=CommandStatus.SUCCESS)
        else:
            return CommandResult(status=CommandStatus.FAILURE, message="Failed to maximize pane")

    except Exception as e:
        logger.error(f"Error maximizing pane: {e}", exc_info=True)
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


@command(
    id="workbench.action.replaceWidgetInPane",
    title="Replace Widget in Pane",
    category="Panes",
    description="Replace current pane content with specified widget",
)
def replace_widget_in_pane_command(context: CommandContext) -> CommandResult:
    """
    Replace the current pane's widget with a new one from AppWidgetManager.

    Args:
        context: Command context with widget_id and pane reference

    Returns:
        CommandResult indicating success or failure
    """
    try:
        from viloapp.core.app_widget_manager import AppWidgetManager

        # Use model directly
        if not context.model or not hasattr(context.model, "change_pane_widget_type"):
            return CommandResult(status=CommandStatus.FAILURE, message="Model not available")

        widget_id = context.parameters.get("widget_id")
        pane = context.parameters.get("pane")
        pane_id = context.parameters.get("pane_id")

        if not widget_id:
            return CommandResult(status=CommandStatus.FAILURE, message="No widget_id specified")

        # Try to get pane_id from different sources
        if not pane_id:
            if pane:
                # Try from PaneContent wrapper
                if hasattr(pane, "leaf_node") and hasattr(pane.leaf_node, "id"):
                    pane_id = pane.leaf_node.id
                elif hasattr(pane, "pane_id"):
                    pane_id = pane.pane_id
            else:
                # Use active pane
                active_tab = context.model.state.get_active_tab()
                if active_tab and active_tab.active_pane_id:
                    pane_id = active_tab.active_pane_id

        if pane_id:
            # Get widget metadata
            manager = AppWidgetManager.get_instance()
            metadata = manager.get_widget_metadata(widget_id)

            if metadata and hasattr(metadata, "widget_type"):
                # Change pane widget type using model
                success = context.model.change_pane_widget_type(pane_id, metadata.widget_type)
                if success:
                    logger.info(f"Replaced pane {pane_id} with widget {widget_id}")
                    return CommandResult(
                        status=CommandStatus.SUCCESS,
                        data={"widget_id": widget_id, "pane_id": pane_id},
                    )
                else:
                    return CommandResult(
                        status=CommandStatus.FAILURE,
                        message=f"Failed to replace widget in pane {pane_id}",
                    )

            return CommandResult(
                status=CommandStatus.FAILURE, message=f"Could not find widget {widget_id}"
            )

        return CommandResult(status=CommandStatus.FAILURE, message="Could not identify pane")

    except Exception as e:
        logger.error(f"Error replacing widget in pane: {e}", exc_info=True)
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


@command(
    id="workbench.action.changePaneType",
    title="Change Pane Type",
    category="Panes",
    description="Change the widget type of a pane",
)
def change_pane_type_command(context: CommandContext) -> CommandResult:
    """
    Change the widget type of a pane.

    Args:
        context: Command context with pane reference and widget_type

    Returns:
        CommandResult indicating success or failure
    """
    try:
        # Use model directly
        if not context.model or not hasattr(context.model, "change_pane_widget_type"):
            return CommandResult(status=CommandStatus.FAILURE, message="Model not available")

        # Get widget type from context
        widget_type = context.parameters.get("widget_type")
        if not widget_type:
            return CommandResult(status=CommandStatus.FAILURE, message="No widget type specified")

        # Get pane from context or use active pane
        pane = context.parameters.get("pane")
        pane_id = context.parameters.get("pane_id")

        if not pane_id:
            if pane:
                # Extract pane_id from pane object
                if hasattr(pane, "leaf_node") and hasattr(pane.leaf_node, "id"):
                    pane_id = pane.leaf_node.id
                elif hasattr(pane, "pane_id"):
                    pane_id = pane.pane_id
            else:
                # Use active pane
                active_tab = context.model.state.get_active_tab()
                if active_tab and active_tab.active_pane_id:
                    pane_id = active_tab.active_pane_id

        if pane_id:
            # Change widget type using model
            success = context.model.change_pane_widget_type(pane_id, widget_type)
            if success:
                return CommandResult(
                    status=CommandStatus.SUCCESS,
                    data={"widget_type": widget_type, "pane_id": pane_id},
                )
            else:
                return CommandResult(
                    status=CommandStatus.FAILURE,
                    message=f"Failed to change pane type for {pane_id}",
                )

        return CommandResult(status=CommandStatus.FAILURE, message="Could not identify pane")

    except Exception as e:
        logger.error(f"Error changing pane type: {e}", exc_info=True)
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


def register_pane_commands():
    """Register all pane commands."""
    # The @command decorator automatically registers them
    # This function ensures the module is imported
    logger.info("Pane commands registered")


# Command Classes for Model-View-Command Architecture
# These will replace the decorator-based commands above once migration is complete


class SplitPaneCommand(Command):
    """Command to split a pane."""

    def __init__(
        self,
        orientation: str = "horizontal",
        pane_id: Optional[str] = None,
        widget_type: Optional[WidgetType] = None,
    ):
        """Initialize split pane command."""
        super().__init__()
        self.orientation = orientation
        self.pane_id = pane_id
        self.widget_type = widget_type

    def execute(self, context: CommandContext) -> CommandResult:
        """Split a pane."""
        try:
            # Get pane to split
            if self.pane_id:
                pane_id = self.pane_id
            else:
                pane = context.get_active_pane()
                if not pane:
                    return CommandResult(
                        status=CommandStatus.FAILURE,
                        message="No active pane to split",
                    )
                pane_id = pane.id

            # Split the pane
            new_pane_id = context.model.split_pane(pane_id, self.orientation)

            if new_pane_id:
                # Set widget type if specified
                if self.widget_type:
                    context.model.change_pane_widget(new_pane_id, self.widget_type)

                return CommandResult(
                    status=CommandStatus.SUCCESS,
                    message=f"Split pane {self.orientation}ly",
                    data={
                        "parent_pane_id": pane_id,
                        "new_pane_id": new_pane_id,
                        "orientation": self.orientation,
                    },
                )
            else:
                return CommandResult(
                    status=CommandStatus.FAILURE,
                    message=f"Failed to split pane {pane_id}",
                )
        except Exception as e:
            return CommandResult(
                status=CommandStatus.FAILURE,
                message=f"Error splitting pane: {str(e)}",
                error=e,
            )


class ClosePaneCommand(Command):
    """Command to close a pane."""

    def __init__(self, pane_id: Optional[str] = None):
        """Initialize close pane command."""
        super().__init__()
        self.pane_id = pane_id

    def execute(self, context: CommandContext) -> CommandResult:
        """Close a pane."""
        try:
            # Get pane to close
            if self.pane_id:
                pane_id = self.pane_id
            else:
                pane = context.get_active_pane()
                if not pane:
                    return CommandResult(
                        status=CommandStatus.FAILURE,
                        message="No active pane to close",
                    )
                pane_id = pane.id

            # Check if it's the last pane
            tab = context.get_active_tab()
            if tab and len(tab.tree.root.get_all_panes()) == 1:
                return CommandResult(
                    status=CommandStatus.NOT_APPLICABLE,
                    message="Cannot close last pane in tab",
                )

            # Close the pane
            success = context.model.close_pane(pane_id)

            if success:
                return CommandResult(
                    status=CommandStatus.SUCCESS,
                    message=f"Closed pane {pane_id}",
                    data={"pane_id": pane_id},
                )
            else:
                return CommandResult(
                    status=CommandStatus.FAILURE,
                    message=f"Failed to close pane {pane_id}",
                )
        except Exception as e:
            return CommandResult(
                status=CommandStatus.FAILURE,
                message=f"Error closing pane: {str(e)}",
                error=e,
            )


class FocusPaneCommand(Command):
    """Command to focus a pane."""

    def __init__(self, pane_id: str):
        """Initialize focus pane command."""
        super().__init__()
        self.pane_id = pane_id

    def execute(self, context: CommandContext) -> CommandResult:
        """Focus a pane."""
        try:
            success = context.model.focus_pane(self.pane_id)

            if success:
                return CommandResult(
                    status=CommandStatus.SUCCESS,
                    message=f"Focused pane {self.pane_id}",
                    data={"pane_id": self.pane_id},
                )
            else:
                return CommandResult(
                    status=CommandStatus.FAILURE,
                    message=f"Failed to focus pane {self.pane_id}",
                )
        except Exception as e:
            return CommandResult(
                status=CommandStatus.FAILURE,
                message=f"Error focusing pane: {str(e)}",
                error=e,
            )


class ChangeWidgetTypeCommand(Command):
    """Command to change widget type of a pane."""

    def __init__(self, widget_type: WidgetType, pane_id: Optional[str] = None):
        """Initialize change widget type command."""
        super().__init__()
        self.widget_type = widget_type
        self.pane_id = pane_id

    def execute(self, context: CommandContext) -> CommandResult:
        """Change widget type of a pane."""
        try:
            # Get pane to change
            if self.pane_id:
                pane_id = self.pane_id
            else:
                pane = context.get_active_pane()
                if not pane:
                    return CommandResult(
                        status=CommandStatus.FAILURE,
                        message="No active pane to change",
                    )
                pane_id = pane.id

            # Change widget type
            success = context.model.change_pane_widget(pane_id, self.widget_type)

            if success:
                return CommandResult(
                    status=CommandStatus.SUCCESS,
                    message=f"Changed widget to {self.widget_type.value}",
                    data={"pane_id": pane_id, "widget_type": self.widget_type.value},
                )
            else:
                return CommandResult(
                    status=CommandStatus.FAILURE,
                    message=f"Failed to change widget type for pane {pane_id}",
                )
        except Exception as e:
            return CommandResult(
                status=CommandStatus.FAILURE,
                message=f"Error changing widget type: {str(e)}",
                error=e,
            )


class NavigatePaneCommand(Command):
    """Command to navigate between panes."""

    def __init__(self, direction: str):
        """Initialize navigate pane command."""
        super().__init__()
        self.direction = direction  # up, down, left, right, next, previous

    def execute(self, context: CommandContext) -> CommandResult:
        """Navigate to adjacent pane."""
        try:
            # Get current pane
            current_pane = context.get_active_pane()
            if not current_pane:
                return CommandResult(
                    status=CommandStatus.FAILURE,
                    message="No active pane",
                )

            # Navigate based on direction
            if self.direction in ["next", "previous"]:
                success = (
                    context.model.focus_next_pane()
                    if self.direction == "next"
                    else context.model.focus_previous_pane()
                )
                if success:
                    return CommandResult(
                        status=CommandStatus.SUCCESS,
                        message=f"Navigated to {self.direction} pane",
                    )
            else:
                # Spatial navigation not yet implemented
                return CommandResult(
                    status=CommandStatus.NOT_APPLICABLE,
                    message=f"Spatial navigation in direction '{self.direction}' not yet implemented",
                )

            return CommandResult(
                status=CommandStatus.FAILURE,
                message=f"Failed to navigate {self.direction}",
            )
        except Exception as e:
            return CommandResult(
                status=CommandStatus.FAILURE,
                message=f"Error navigating pane: {str(e)}",
                error=e,
            )
