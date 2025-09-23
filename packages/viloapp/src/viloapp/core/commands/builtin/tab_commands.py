#!/usr/bin/env python3
"""
Tab management commands.

This module contains commands for managing tabs including
duplicating, closing, and renaming tabs.
"""

import logging

from viloapp.core.commands.base import CommandContext, CommandResult, CommandStatus
from viloapp.core.commands.decorators import command

logger = logging.getLogger(__name__)


@command(
    id="workbench.action.duplicateTab",
    title="Duplicate Tab",
    category="Tabs",
    description="Duplicate the current or specified tab",
)
def duplicate_tab_command(context: CommandContext) -> CommandResult:
    """
    Duplicate a tab.

    Args:
        context: Command context with optional tab_index

    Returns:
        CommandResult indicating success or failure
    """
    try:
        # Use model directly
        if not context.model or not hasattr(context.model, "state"):
            return CommandResult(status=CommandStatus.FAILURE, message="Model not available")

        # Get tab index from context
        tab_index = context.parameters.get("tab_index")

        # Get current tabs
        if not context.model.state.tabs:
            return CommandResult(status=CommandStatus.FAILURE, message="No tabs available")

        # If no index provided, use current tab
        if tab_index is None:
            active_tab = context.model.state.get_active_tab()
            if not active_tab:
                return CommandResult(status=CommandStatus.FAILURE, message="No active tab")
            tab_index = context.model.state.tabs.index(active_tab)

        # Validate index
        if tab_index < 0 or tab_index >= len(context.model.state.tabs):
            return CommandResult(status=CommandStatus.FAILURE, message="Invalid tab index")

        # Duplicate the tab by creating a new one with same widget type
        source_tab = context.model.state.tabs[tab_index]
        # Get the root widget type from the source tab
        root_pane = source_tab.tree.root
        widget_id = root_pane.widget_id if hasattr(root_pane, "widget_id") else None

        if not widget_id:
            from viloapp.core.app_widget_manager import app_widget_manager
            widget_id = app_widget_manager.get_default_widget_id()
            if not widget_id:
                widget_id = "com.viloapp.placeholder"

        new_tab_id = context.model.create_tab(f"{source_tab.name} (Copy)", widget_id)
        new_index = len(context.model.state.tabs) - 1

        return CommandResult(
            status=CommandStatus.SUCCESS, data={"duplicated_tab": tab_index, "new_index": new_index}
        )

    except Exception as e:
        logger.error(f"Error duplicating tab: {e}", exc_info=True)
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


@command(
    id="workbench.action.closeTabsToRight",
    title="Close Tabs to the Right",
    category="Tabs",
    description="Close all tabs to the right of the current or specified tab",
)
def close_tabs_to_right_command(context: CommandContext) -> CommandResult:
    """
    Close all tabs to the right of a tab.

    Args:
        context: Command context with optional tab_index

    Returns:
        CommandResult indicating success or failure
    """
    try:
        # Use model directly
        if not context.model or not hasattr(context.model, "state"):
            return CommandResult(status=CommandStatus.FAILURE, message="Model not available")

        # Get tab index from context
        tab_index = context.parameters.get("tab_index")

        # Get current tabs
        if not context.model.state.tabs:
            return CommandResult(status=CommandStatus.FAILURE, message="No tabs available")

        # If no index provided, use current tab
        if tab_index is None:
            active_tab = context.model.state.get_active_tab()
            if not active_tab:
                return CommandResult(status=CommandStatus.FAILURE, message="No active tab")
            tab_index = context.model.state.tabs.index(active_tab)

        # Validate index
        if tab_index < 0 or tab_index >= len(context.model.state.tabs):
            return CommandResult(status=CommandStatus.FAILURE, message="Invalid tab index")

        # Close tabs to the right
        closed_count = 0
        tabs_to_close = list(context.model.state.tabs[tab_index + 1 :])

        for tab in tabs_to_close:
            if context.model.close_tab(tab.id):
                closed_count += 1

        return CommandResult(
            status=CommandStatus.SUCCESS,
            data={"closed_from_index": tab_index + 1, "closed_count": closed_count},
        )

    except Exception as e:
        logger.error(f"Error closing tabs to right: {e}", exc_info=True)
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


@command(
    id="workbench.action.renameTab",
    title="Rename Tab",
    category="Tabs",
    description="Rename the current or specified tab",
)
def rename_tab_command(context: CommandContext) -> CommandResult:
    """
    Start renaming a tab.

    Args:
        context: Command context with optional tab_index and new_name

    Returns:
        CommandResult indicating success or failure
    """
    try:
        # Use model directly
        if not context.model or not hasattr(context.model, "state"):
            return CommandResult(status=CommandStatus.FAILURE, message="Model not available")

        # Get tab index from context
        tab_index = context.parameters.get("tab_index")
        new_name = context.parameters.get("new_name")

        # Get current tabs
        if not context.model.state.tabs:
            return CommandResult(status=CommandStatus.FAILURE, message="No tabs available")

        # If no index provided, use current tab
        if tab_index is None:
            active_tab = context.model.state.get_active_tab()
            if not active_tab:
                return CommandResult(status=CommandStatus.FAILURE, message="No active tab")
            tab_index = context.model.state.tabs.index(active_tab)

        # Validate index
        if tab_index < 0 or tab_index >= len(context.model.state.tabs):
            return CommandResult(status=CommandStatus.FAILURE, message="Invalid tab index")

        tab = context.model.state.tabs[tab_index]

        # If new name provided, rename directly
        if new_name:
            success = context.model.rename_tab(tab.id, new_name)
            if success:
                return CommandResult(
                    status=CommandStatus.SUCCESS,
                    data={"tab_index": tab_index, "new_name": new_name},
                )
            else:
                return CommandResult(status=CommandStatus.FAILURE, message="Failed to rename tab")

        # Otherwise, return interactive mode indicator (UI should handle prompting)
        return CommandResult(
            status=CommandStatus.SUCCESS,
            data={"tab_index": tab_index, "mode": "interactive", "current_name": tab.name},
        )

    except Exception as e:
        logger.error(f"Error renaming tab: {e}", exc_info=True)
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


@command(
    id="workbench.action.closeOtherTabs",
    title="Close Other Tabs",
    category="Tabs",
    description="Close all tabs except the current or specified one",
)
def close_other_tabs_command(context: CommandContext) -> CommandResult:
    """
    Close all tabs except one.

    Args:
        context: Command context with optional tab_index

    Returns:
        CommandResult indicating success or failure
    """
    try:
        # Use model directly
        if not context.model or not hasattr(context.model, "state"):
            return CommandResult(status=CommandStatus.FAILURE, message="Model not available")

        # Get tab index from context
        tab_index = context.parameters.get("tab_index")

        # Get current tabs
        if not context.model.state.tabs:
            return CommandResult(status=CommandStatus.FAILURE, message="No tabs available")

        if len(context.model.state.tabs) <= 1:
            return CommandResult(status=CommandStatus.NOT_APPLICABLE, message="Only one tab open")

        # If no index provided, use current tab
        if tab_index is None:
            active_tab = context.model.state.get_active_tab()
            if not active_tab:
                return CommandResult(status=CommandStatus.FAILURE, message="No active tab")
            tab_index = context.model.state.tabs.index(active_tab)

        # Validate index
        if tab_index < 0 or tab_index >= len(context.model.state.tabs):
            return CommandResult(status=CommandStatus.FAILURE, message="Invalid tab index")

        # Close other tabs
        tab_to_keep = context.model.state.tabs[tab_index]
        closed_count = 0
        tabs_to_close = [tab for tab in context.model.state.tabs if tab.id != tab_to_keep.id]

        for tab in tabs_to_close:
            if context.model.close_tab(tab.id):
                closed_count += 1

        return CommandResult(
            status=CommandStatus.SUCCESS, data={"kept_tab": tab_index, "closed_count": closed_count}
        )

    except Exception as e:
        logger.error(f"Error closing other tabs: {e}", exc_info=True)
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


def register_tab_commands():
    """Register all tab commands."""
    # The @command decorator automatically registers them
    # This function ensures the module is imported
    logger.info("Tab commands registered")


# Command Classes for Model-View-Command Architecture
# These will replace the decorator-based commands above once migration is complete

from typing import Optional

from viloapp.core.commands.base import Command


def _get_default_editor_id() -> str:
    """Get default editor widget ID."""
    try:
        from viloapp.core.app_widget_manager import app_widget_manager
        # Try to find an editor widget
        for widget in app_widget_manager.get_all_widgets():
            if "editor" in widget.widget_id.lower():
                return widget.widget_id
        # Fall back to default
        return app_widget_manager.get_default_widget_id()
    except ImportError:
        return "com.viloapp.editor"


class CreateTabCommand(Command):
    """Command to create a new tab."""

    def __init__(self, name: str = "New Tab", widget_id: Optional[str] = None):
        """Initialize create tab command."""
        super().__init__()
        self.tab_name = name
        self.widget_id = widget_id or _get_default_editor_id()

    def execute(self, context: CommandContext) -> CommandResult:
        """Create a new tab."""
        try:
            tab_id = context.model.create_tab(self.tab_name, self.widget_id)
            return CommandResult(
                status=CommandStatus.SUCCESS,
                message=f"Created tab '{self.tab_name}'",
                data={"tab_id": tab_id, "name": self.tab_name},
            )
        except Exception as e:
            return CommandResult(
                status=CommandStatus.FAILURE,
                message=f"Failed to create tab: {str(e)}",
                error=e,
            )


class CloseTabCommand(Command):
    """Command to close a tab."""

    def __init__(self, tab_id: Optional[str] = None):
        """Initialize close tab command."""
        super().__init__()
        self.tab_id = tab_id

    def execute(self, context: CommandContext) -> CommandResult:
        """Close a tab."""
        try:
            tab_id = self.tab_id or context.active_tab_id or context.model.state.active_tab_id

            if not tab_id:
                return CommandResult(
                    status=CommandStatus.FAILURE,
                    message="No tab to close",
                )

            # Don't close last tab
            if len(context.model.state.tabs) == 1:
                return CommandResult(
                    status=CommandStatus.NOT_APPLICABLE,
                    message="Cannot close last tab",
                )

            success = context.model.close_tab(tab_id)
            if success:
                return CommandResult(
                    status=CommandStatus.SUCCESS,
                    message=f"Closed tab {tab_id}",
                    data={"tab_id": tab_id},
                )
            else:
                return CommandResult(
                    status=CommandStatus.FAILURE,
                    message=f"Failed to close tab {tab_id}",
                )
        except Exception as e:
            return CommandResult(
                status=CommandStatus.FAILURE,
                message=f"Error closing tab: {str(e)}",
                error=e,
            )


class RenameTabCommand(Command):
    """Command to rename a tab."""

    def __init__(self, new_name: str, tab_id: Optional[str] = None):
        """Initialize rename tab command."""
        super().__init__()
        self.new_name = new_name
        self.tab_id = tab_id

    def execute(self, context: CommandContext) -> CommandResult:
        """Rename a tab."""
        try:
            tab_id = self.tab_id or context.active_tab_id or context.model.state.active_tab_id

            if not tab_id:
                return CommandResult(
                    status=CommandStatus.FAILURE,
                    message="No tab to rename",
                )

            success = context.model.rename_tab(tab_id, self.new_name)
            if success:
                return CommandResult(
                    status=CommandStatus.SUCCESS,
                    message=f"Renamed tab to '{self.new_name}'",
                    data={"tab_id": tab_id, "name": self.new_name},
                )
            else:
                return CommandResult(
                    status=CommandStatus.FAILURE,
                    message=f"Failed to rename tab {tab_id}",
                )
        except Exception as e:
            return CommandResult(
                status=CommandStatus.FAILURE,
                message=f"Error renaming tab: {str(e)}",
                error=e,
            )


class SwitchTabCommand(Command):
    """Command to switch active tab."""

    def __init__(self, tab_id: str):
        """Initialize switch tab command."""
        super().__init__()
        self.tab_id = tab_id

    def execute(self, context: CommandContext) -> CommandResult:
        """Switch to a different tab."""
        try:
            success = context.model.set_active_tab(self.tab_id)
            if success:
                return CommandResult(
                    status=CommandStatus.SUCCESS,
                    message=f"Switched to tab {self.tab_id}",
                    data={"tab_id": self.tab_id},
                )
            else:
                return CommandResult(
                    status=CommandStatus.FAILURE,
                    message=f"Failed to switch to tab {self.tab_id}",
                )
        except Exception as e:
            return CommandResult(
                status=CommandStatus.FAILURE,
                message=f"Error switching tab: {str(e)}",
                error=e,
            )
