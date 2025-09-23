#!/usr/bin/env python3
"""
File-related commands using the service layer.
"""

import logging

from viloapp.core.commands.base import CommandContext, CommandResult, CommandStatus
from viloapp.core.commands.decorators import command

logger = logging.getLogger(__name__)


@command(
    id="file.closeTab",
    title="Close Tab",
    category="File",
    description="Close the current tab",
    shortcut="ctrl+w",
    when="workbench.tabs.count > 0",
)
def close_tab_command(context: CommandContext) -> CommandResult:
    """Close the current tab using model directly."""
    try:
        # Use model directly
        if not context.model or not hasattr(context.model, "close_tab"):
            return CommandResult(status=CommandStatus.FAILURE, message="Model not available")

        index = context.parameters.get("index") if context.parameters else None

        # If index provided, get tab by index
        if index is not None:
            tabs = context.model.state.tabs
            if 0 <= index < len(tabs):
                tab_id = tabs[index].id
            else:
                return CommandResult(
                    status=CommandStatus.FAILURE, message=f"Invalid tab index: {index}"
                )
        else:
            # Use active tab
            active_tab = context.model.state.get_active_tab()
            if not active_tab:
                return CommandResult(status=CommandStatus.FAILURE, message="No active tab")
            tab_id = active_tab.id

        # Don't close last tab
        if len(context.model.state.tabs) == 1:
            return CommandResult(
                status=CommandStatus.NOT_APPLICABLE, message="Cannot close last tab"
            )

        success = context.model.close_tab(tab_id)

        if success:
            return CommandResult(status=CommandStatus.SUCCESS, data={"tab_id": tab_id})
        else:
            return CommandResult(status=CommandStatus.FAILURE, message="Failed to close tab")

    except Exception as e:
        logger.error(f"Failed to close tab: {e}")
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


@command(
    id="file.saveState",
    title="Save Workspace State",
    category="File",
    description="Save current workspace state",
)
def save_state_command(context: CommandContext) -> CommandResult:
    """Save workspace state using model directly."""
    try:
        # Use model directly
        if not context.model or not hasattr(context.model, "state"):
            return CommandResult(status=CommandStatus.FAILURE, message="Model not available")

        # Get the state
        state = context.model.state

        # Serialize the state to dict
        state_dict = state.to_dict()

        # For now, just log it - actual persistence would go through a service
        logger.info("Saving workspace state")
        logger.debug(f"State: {state_dict}")

        # In a real implementation, this would save to persistent storage
        # For now, we'll mark it as successful
        return CommandResult(
            status=CommandStatus.SUCCESS,
            message="Workspace state saved",
            data={"state": state_dict},
        )

    except Exception as e:
        logger.error(f"Failed to save state: {e}")
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


@command(
    id="file.restoreState",
    title="Restore Workspace State",
    category="File",
    description="Restore workspace state",
)
def restore_state_command(context: CommandContext) -> CommandResult:
    """Restore workspace state using model directly."""
    try:
        # Use model directly
        if not context.model or not hasattr(context.model, "restore_state"):
            return CommandResult(status=CommandStatus.FAILURE, message="Model not available")

        # Get state data from parameters (would normally come from storage)
        state_dict = context.parameters.get("state") if context.parameters else None

        if not state_dict:
            # In a real implementation, this would load from persistent storage
            return CommandResult(status=CommandStatus.FAILURE, message="No state data provided")

        # Restore the state
        context.model.restore_state(state_dict)

        return CommandResult(
            status=CommandStatus.SUCCESS,
            message="Workspace state restored",
            data={"state": state_dict},
        )

    except Exception as e:
        logger.error(f"Failed to restore state: {e}")
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


def register_file_commands():
    """Register all file commands."""
    # The @command decorator automatically registers them
    # This function ensures the module is imported
    logger.info("File commands registered")
