#!/usr/bin/env python3
"""
Workspace-related commands using the service layer.
"""

import logging

from viloapp.core.app_widget_manager import app_widget_manager
from viloapp.core.commands.base import CommandContext, CommandResult, CommandStatus
from viloapp.core.commands.decorators import command
from viloapp.core.commands.validation import (
    OneOf,
    Optional,
    ParameterSpec,
    Range,
    String,
    validate,
)

logger = logging.getLogger(__name__)


@command(
    id="workspace.newTab",
    title="New Tab",
    category="Workspace",
    description="Create a new tab with default widget type",
    shortcut="ctrl+t",
)
def new_tab_command(context: CommandContext) -> CommandResult:
    """Create a new tab using the default widget type from settings."""
    try:
        # Access model directly from context
        model = context.model
        if not model or not hasattr(model, "create_tab"):
            return CommandResult(
                status=CommandStatus.FAILURE, message="Workspace model not available"
            )

        # Get widget type from args or use default
        widget_id = context.parameters.get("widget_id") if context.parameters else None
        if not widget_id:
            # Use app_widget_manager to get the default widget
            widget_id = app_widget_manager.get_default_widget_id()
            if not widget_id:
                # Fallback to placeholder if no widgets available
                widget_id = "com.viloapp.placeholder"

        # Widget-specific setup is now handled by plugins

        # Create the tab
        name = context.parameters.get("name") if context.parameters else None
        if not name:
            # Extract simple name from widget_id for display
            # e.g., "com.viloapp.terminal" -> "Terminal"
            widget_name = widget_id.split(".")[-1] if widget_id else "Tab"
            name = f"New {widget_name.title()}"

        # Create tab using model - it expects widget_id as string
        tab_id = model.create_tab(name, widget_id)

        # Get the index of the newly added tab
        index = len(model.state.tabs) - 1

        return CommandResult(
            status=CommandStatus.SUCCESS,
            data={"index": index, "widget_id": widget_id, "name": name, "tab_id": tab_id},
        )

    except Exception as e:
        logger.error(f"Failed to create new tab: {e}")
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


@command(
    id="workspace.newTabWithType",
    title="New Tab (Choose Type)...",
    category="Workspace",
    description="Create a new tab with a specific widget type",
    shortcut="ctrl+shift+t",
)
@validate(
    name=ParameterSpec(
        "name",
        Optional(String(max_length=100, non_empty=True)),
        required=False,
        description="Optional name for the new tab",
    ),
)
def new_tab_with_type_command(context: CommandContext) -> CommandResult:
    """Create a new tab, prompting for widget type."""
    from PySide6.QtWidgets import QInputDialog

    # Check if widget_id provided in parameters (for testing/programmatic use)
    widget_id = context.parameters.get("widget_id") if context.parameters else None

    if not widget_id and context.main_window:
        # Get available widgets from registry
        from viloapp.core.app_widget_manager import app_widget_manager

        available_widgets = app_widget_manager.get_available_widgets()
        if not available_widgets:
            return CommandResult(status=CommandStatus.FAILURE, message="No widgets available")

        widget_names = [widget.display_name for widget in available_widgets]
        widget_id_map = {widget.display_name: widget.widget_id for widget in available_widgets}

        selected, ok = QInputDialog.getItem(
            context.main_window,
            "New Tab",
            "Select widget type:",
            widget_names,
            0,  # Default to first available
            False,  # Not editable
        )

        if not ok or not selected:
            return CommandResult(status=CommandStatus.FAILURE, message="User cancelled")

        widget_id = widget_id_map[selected]

    if not widget_id:
        # Get available widgets from registry
        from viloapp.core.app_widget_manager import app_widget_manager

        available_widgets = app_widget_manager.get_available_widgets()
        available_ids = [widget.widget_id for widget in available_widgets]

        return CommandResult(
            status=CommandStatus.FAILURE,
            message="Widget type must be specified",
            data={"available_types": available_ids},
        )

    # Delegate to new_tab_command with the specified widget_id
    if not context.parameters:
        context.parameters = {}
    context.parameters["widget_id"] = widget_id
    return new_tab_command(context)


@command(
    id="workbench.action.splitRight",
    title="Split Pane Right",
    category="Workspace",
    description="Split the active pane horizontally",
    shortcut="ctrl+\\",
    icon="split-horizontal",
    when="workbench.pane.canSplit",
)
@validate(
    orientation=ParameterSpec(
        "orientation",
        Optional(OneOf("horizontal", "vertical")),
        default="horizontal",
        description="Split orientation - horizontal creates side-by-side panes",
    )
)
def split_pane_right_command(context: CommandContext) -> CommandResult:
    """Split active pane horizontally using model directly."""
    try:
        # Use model directly
        if not context.model or not hasattr(context.model, "split_pane"):
            return CommandResult(status=CommandStatus.FAILURE, message="Model not available")

        # Get active pane to split
        active_tab = context.model.state.get_active_tab()
        if not active_tab or not active_tab.active_pane_id:
            return CommandResult(status=CommandStatus.FAILURE, message="No active pane to split")

        orientation = (
            context.parameters.get("orientation", "horizontal")
            if context.parameters
            else "horizontal"
        )
        new_pane_id = context.model.split_pane(active_tab.active_pane_id, orientation)

        if new_pane_id:
            return CommandResult(status=CommandStatus.SUCCESS, data={"new_pane_id": new_pane_id})
        else:
            return CommandResult(status=CommandStatus.FAILURE, message="Failed to split pane")

    except Exception as e:
        logger.error(f"Failed to split pane right: {e}")
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


@command(
    id="workbench.action.splitDown",
    title="Split Pane Down",
    category="Workspace",
    description="Split the active pane vertically",
    shortcut="ctrl+shift+\\",
    icon="split-vertical",
    when="workbench.pane.canSplit",
)
def split_pane_down_command(context: CommandContext) -> CommandResult:
    """Split active pane vertically using model directly."""
    try:
        # Use model directly
        if not context.model or not hasattr(context.model, "split_pane"):
            return CommandResult(status=CommandStatus.FAILURE, message="Model not available")

        # Get active pane to split
        active_tab = context.model.state.get_active_tab()
        if not active_tab or not active_tab.active_pane_id:
            return CommandResult(status=CommandStatus.FAILURE, message="No active pane to split")

        new_pane_id = context.model.split_pane(active_tab.active_pane_id, "vertical")

        if new_pane_id:
            return CommandResult(status=CommandStatus.SUCCESS, data={"new_pane_id": new_pane_id})
        else:
            return CommandResult(status=CommandStatus.FAILURE, message="Failed to split pane")

    except Exception as e:
        logger.error(f"Failed to split pane down: {e}")
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


@command(
    id="workbench.action.closeActivePane",
    title="Close Active Pane",
    category="Workspace",
    description="Close the active pane",
    # Shortcut is managed by keymap system (ctrl+k w)
    icon="x",
    when="workbench.pane.count > 1",
)
def close_active_pane_command(context: CommandContext) -> CommandResult:
    """Close active pane using model directly."""
    try:
        # Use model directly
        if not context.model or not hasattr(context.model, "close_pane"):
            return CommandResult(status=CommandStatus.FAILURE, message="Model not available")

        # Get active pane to close
        active_tab = context.model.state.get_active_tab()
        if not active_tab or not active_tab.active_pane_id:
            return CommandResult(status=CommandStatus.FAILURE, message="No active pane to close")

        # Check if it's the last pane in the tab
        panes = active_tab.tree.root.get_all_panes()
        if len(panes) <= 1:
            return CommandResult(
                status=CommandStatus.NOT_APPLICABLE, message="Cannot close the last pane"
            )

        success = context.model.close_pane(active_tab.active_pane_id)

        if success:
            return CommandResult(status=CommandStatus.SUCCESS)
        else:
            return CommandResult(status=CommandStatus.FAILURE, message="Failed to close pane")

    except Exception as e:
        logger.error(f"Failed to close active pane: {e}")
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


@command(
    id="workbench.action.togglePaneNumbers",
    title="Toggle Pane Numbers",
    category="View",
    description="Show or hide pane identification numbers",
    # Shortcut is handled by QAction in MainWindow to work with WebEngine
    # shortcut="alt+p",
    icon="hash",
    when=None,  # Always available
)
def toggle_pane_numbers_command(context: CommandContext) -> CommandResult:
    """Toggle pane numbers visibility."""
    try:
        # Use model directly
        if not context.model or not hasattr(context.model, "toggle_pane_numbers"):
            return CommandResult(status=CommandStatus.FAILURE, message="Model not available")

        # Toggle pane numbers display
        success = context.model.toggle_pane_numbers()

        if success:
            # Get current state for feedback
            show_numbers = context.model.state.metadata.get("show_pane_numbers", False)
            status_msg = "Pane numbers shown" if show_numbers else "Pane numbers hidden"

            # Show status message
            if context.main_window and hasattr(context.main_window, "status_bar"):
                context.main_window.status_bar.set_message(status_msg, 2000)

            return CommandResult(status=CommandStatus.SUCCESS, data={"show_numbers": show_numbers})
        else:
            return CommandResult(
                status=CommandStatus.FAILURE, message="Failed to toggle pane numbers"
            )

    except Exception as e:
        logger.error(f"Failed to toggle pane numbers: {e}")
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


@command(
    id="workbench.action.focusNextPane",
    title="Focus Next Pane",
    category="Workspace",
    description="Focus the next pane",
    shortcut="tab",
    when="workbench.pane.count > 1",
)
def focus_next_pane_command(context: CommandContext) -> CommandResult:
    """Focus next pane using model directly."""
    try:
        # Use model directly
        if not context.model or not hasattr(context.model, "focus_next_pane"):
            return CommandResult(status=CommandStatus.FAILURE, message="Model not available")

        success = context.model.focus_next_pane()

        if success:
            return CommandResult(status=CommandStatus.SUCCESS)
        else:
            return CommandResult(status=CommandStatus.FAILURE, message="No other panes available")

    except Exception as e:
        logger.error(f"Failed to focus next pane: {e}")
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


@command(
    id="workbench.action.focusPreviousPane",
    title="Focus Previous Pane",
    category="Workspace",
    description="Focus the previous pane",
    shortcut="shift+tab",
    when="workbench.pane.count > 1",
)
def focus_previous_pane_command(context: CommandContext) -> CommandResult:
    """Focus previous pane using model directly."""
    try:
        # Use model directly
        if not context.model or not hasattr(context.model, "focus_previous_pane"):
            return CommandResult(status=CommandStatus.FAILURE, message="Model not available")

        success = context.model.focus_previous_pane()

        if success:
            return CommandResult(status=CommandStatus.SUCCESS)
        else:
            return CommandResult(status=CommandStatus.FAILURE, message="No other panes available")

    except Exception as e:
        logger.error(f"Failed to focus previous pane: {e}")
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


@command(
    id="workbench.action.nextTab",
    title="Next Tab",
    category="Workspace",
    description="Switch to the next tab",
    shortcut="ctrl+pagedown",
    when="workbench.tabs.count > 1",
)
def next_tab_command(context: CommandContext) -> CommandResult:
    """Switch to next tab using model directly."""
    try:
        # Use model directly
        if not context.model or not hasattr(context.model, "state"):
            return CommandResult(status=CommandStatus.FAILURE, message="Model not available")

        tabs = context.model.state.tabs
        if len(tabs) <= 1:
            return CommandResult(status=CommandStatus.FAILURE, message="No other tabs to switch to")

        current_tab = context.model.state.get_active_tab()
        if not current_tab:
            return CommandResult(status=CommandStatus.FAILURE, message="No active tab")

        current = tabs.index(current_tab)
        next_index = (current + 1) % len(tabs)
        next_tab = tabs[next_index]

        success = context.model.set_active_tab(next_tab.id)

        if success:
            return CommandResult(status=CommandStatus.SUCCESS, data={"tab_index": next_index})
        else:
            return CommandResult(status=CommandStatus.FAILURE, message="Failed to switch tab")

    except Exception as e:
        logger.error(f"Failed to switch to next tab: {e}")
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


@command(
    id="workbench.action.selectTab",
    title="Select Tab",
    category="Workspace",
    description="Switch to a specific tab by index",
)
@validate(
    tab_index=ParameterSpec(
        "tab_index",
        Range(0, 50),
        required=True,
        description="Index of the tab to select (0-based)",
    )
)
def select_tab_command(context: CommandContext) -> CommandResult:
    """Switch to a specific tab by index."""
    try:
        # Use model directly
        if not context.model or not hasattr(context.model, "state"):
            return CommandResult(status=CommandStatus.FAILURE, message="Model not available")

        tab_index = context.parameters.get("tab_index") if context.parameters else None
        if tab_index is None:
            return CommandResult(status=CommandStatus.FAILURE, message="No tab index provided")

        tabs = context.model.state.tabs
        if 0 <= tab_index < len(tabs):
            target_tab = tabs[tab_index]
            success = context.model.set_active_tab(target_tab.id)

            if success:
                return CommandResult(status=CommandStatus.SUCCESS, data={"tab_index": tab_index})
            else:
                return CommandResult(status=CommandStatus.FAILURE, message="Failed to switch tab")

        return CommandResult(
            status=CommandStatus.FAILURE, message=f"Invalid tab index: {tab_index}"
        )

    except Exception as e:
        logger.error(f"Failed to select tab: {e}")
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


@command(
    id="workbench.action.previousTab",
    title="Previous Tab",
    category="Workspace",
    description="Switch to the previous tab",
    shortcut="ctrl+pageup",
    when="workbench.tabs.count > 1",
)
def previous_tab_command(context: CommandContext) -> CommandResult:
    """Switch to previous tab using model directly."""
    try:
        # Use model directly
        if not context.model or not hasattr(context.model, "state"):
            return CommandResult(status=CommandStatus.FAILURE, message="Model not available")

        tabs = context.model.state.tabs
        if len(tabs) <= 1:
            return CommandResult(status=CommandStatus.FAILURE, message="No other tabs to switch to")

        current_tab = context.model.state.get_active_tab()
        if not current_tab:
            return CommandResult(status=CommandStatus.FAILURE, message="No active tab")

        current = tabs.index(current_tab)
        prev_index = (current - 1) % len(tabs)
        prev_tab = tabs[prev_index]

        success = context.model.set_active_tab(prev_tab.id)

        if success:
            return CommandResult(status=CommandStatus.SUCCESS, data={"tab_index": prev_index})
        else:
            return CommandResult(status=CommandStatus.FAILURE, message="Failed to switch tab")

    except Exception as e:
        logger.error(f"Failed to switch to previous tab: {e}")
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


@command(
    id="workbench.action.saveLayout",
    title="Save Workspace Layout",
    category="Workspace",
    description="Save the current workspace layout",
    icon="save",
)
def save_layout_command(context: CommandContext) -> CommandResult:
    """Save workspace layout using model directly."""
    try:
        # Use model directly
        if not context.model or not hasattr(context.model, "save_state"):
            return CommandResult(status=CommandStatus.FAILURE, message="Model not available")

        layout = context.model.save_state()

        # Show status message
        if context.main_window and hasattr(context.main_window, "status_bar"):
            context.main_window.status_bar.set_message("Layout saved", 2000)

        return CommandResult(status=CommandStatus.SUCCESS, value={"layout": layout})

    except Exception as e:
        logger.error(f"Failed to save layout: {e}")
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


@command(
    id="workbench.action.restoreLayout",
    title="Restore Workspace Layout",
    category="Workspace",
    description="Restore the saved workspace layout",
    icon="refresh",
)
def restore_layout_command(context: CommandContext) -> CommandResult:
    """Restore workspace layout using model directly."""
    try:
        # Use model directly
        if not context.model or not hasattr(context.model, "load_state"):
            return CommandResult(status=CommandStatus.FAILURE, message="Model not available")

        # Get layout from context parameters
        layout = context.parameters.get("layout") if context.parameters else None
        if layout:
            try:
                context.model.load_state(layout)
                success = True
            except Exception:
                success = False

            if success:
                # Show status message
                if context.main_window and hasattr(context.main_window, "status_bar"):
                    context.main_window.status_bar.set_message("Layout restored", 2000)

                return CommandResult(status=CommandStatus.SUCCESS)

        return CommandResult(status=CommandStatus.FAILURE, message="No layout to restore")

    except Exception as e:
        logger.error(f"Failed to restore layout: {e}")
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


@command(
    id="workbench.action.renamePane",
    title="Rename Pane",
    category="Workspace",
    description="Rename the active pane",
    shortcut="f2",
    when="workbench.pane.focused",
)
def rename_pane_command(context: CommandContext) -> CommandResult:
    """Rename the active pane."""
    # Will be implemented with UI integration
    return CommandResult(status=CommandStatus.SUCCESS)


def register_workspace_commands():
    """Register all workspace commands."""
    # The @command decorator automatically registers them
    # This function ensures the module is imported
    logger.info("Workspace commands registered")
