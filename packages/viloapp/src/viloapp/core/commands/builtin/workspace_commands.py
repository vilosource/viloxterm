#!/usr/bin/env python3
"""
Workspace-related commands using the service layer.
"""

import logging
import uuid

from viloapp.core.commands.base import CommandContext, CommandResult
from viloapp.core.commands.decorators import command
from viloapp.core.commands.validation import (
    OneOf,
    Optional,
    ParameterSpec,
    Range,
    String,
    validate,
)
from viloapp.core.settings.app_defaults import get_default_widget_type
from viloapp.services.terminal_service import TerminalService
from viloapp.services.workspace_service import WorkspaceService
from viloapp.ui.widgets.widget_registry import WidgetType

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
        workspace_service = context.get_service(WorkspaceService)
        if not workspace_service:
            return CommandResult(success=False, error="WorkspaceService not available")

        # Get widget type from args or settings
        widget_type = context.args.get("widget_type")
        if not widget_type:
            widget_type = get_default_widget_type()

        # Special handling for terminal
        if widget_type == "terminal":
            terminal_service = context.get_service(TerminalService)
            if terminal_service and not terminal_service.is_server_running():
                terminal_service.start_server()

        # Create the tab
        name = context.args.get("name")

        # Map string widget type to WidgetType enum and widget ID
        # Note: shortcuts uses WidgetType.SETTINGS, theme_editor uses CUSTOM
        widget_type_map = {
            "terminal": (WidgetType.TERMINAL, None),
            "editor": (WidgetType.TEXT_EDITOR, None),
            "theme_editor": (WidgetType.CUSTOM, "com.viloapp.theme_editor"),
            "explorer": (WidgetType.EXPLORER, None),
            "output": (WidgetType.OUTPUT, None),
            "settings": (WidgetType.SETTINGS, "com.viloapp.settings"),
            "shortcuts": (WidgetType.SETTINGS, "com.viloapp.shortcuts"),
            "placeholder": (WidgetType.PLACEHOLDER, None),
        }

        # Use appropriate method based on widget type
        if widget_type == "terminal":
            index = workspace_service.add_terminal_tab(name)
        elif widget_type == "editor":
            index = workspace_service.add_editor_tab(name)
        elif widget_type in widget_type_map:
            # Use the generic app widget method for other types
            widget_enum, specific_widget_id = widget_type_map[widget_type]

            # Use specific widget ID if provided, otherwise generate one
            if specific_widget_id:
                widget_id = specific_widget_id
            else:
                widget_id = str(uuid.uuid4())[:8]  # Generate unique widget ID

            success = workspace_service.add_app_widget(widget_enum, widget_id, name)
            if success:
                # Get the index of the newly added tab
                index = workspace_service.get_tab_count() - 1
            else:
                return CommandResult(success=False, error=f"Failed to create {widget_type} tab")
        else:
            # Unknown widget type, fall back to terminal
            logger.warning(f"Unknown widget type '{widget_type}', using terminal")
            index = workspace_service.add_terminal_tab(name)

        return CommandResult(
            success=True,
            value={"index": index, "widget_type": widget_type, "name": name},
        )

    except Exception as e:
        logger.error(f"Failed to create new tab: {e}")
        return CommandResult(success=False, error=str(e))


@command(
    id="workspace.newTabWithType",
    title="New Tab (Choose Type)...",
    category="Workspace",
    description="Create a new tab with a specific widget type",
    shortcut="ctrl+shift+t",
)
@validate(
    widget_type=ParameterSpec(
        "widget_type",
        OneOf(
            "terminal",
            "editor",
            "theme_editor",
            "explorer",
            "settings",
            "shortcuts",
            "output",
            "placeholder",
        ),
        required=False,
        description="Type of widget to create in the new tab",
    ),
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

    # Check if widget_type provided in args (for testing/programmatic use)
    widget_type = context.args.get("widget_type") if context.args else None

    if not widget_type and context.main_window:
        # Show selection dialog
        widget_types = ["Terminal", "Editor", "Theme Editor", "Explorer", "Settings"]
        widget_type_map = {
            "Terminal": "terminal",
            "Editor": "editor",
            "Theme Editor": "theme_editor",
            "Explorer": "explorer",
            "Settings": "settings",
        }

        selected, ok = QInputDialog.getItem(
            context.main_window,
            "New Tab",
            "Select widget type:",
            widget_types,
            0,  # Default to Terminal
            False,  # Not editable
        )

        if not ok or not selected:
            return CommandResult(success=False, error="User cancelled")

        widget_type = widget_type_map[selected]

    if not widget_type:
        return CommandResult(
            success=False,
            error="Widget type must be specified",
            value={
                "available_types": [
                    "terminal",
                    "editor",
                    "theme_editor",
                    "explorer",
                    "settings",
                ]
            },
        )

    # Delegate to new_tab_command with the specified type
    if not context.args:
        context.args = {}
    context.args["widget_type"] = widget_type
    return new_tab_command._original_func(context)


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
    """Split active pane horizontally using WorkspaceService."""
    try:
        workspace_service = context.get_service(WorkspaceService)
        if not workspace_service:
            return CommandResult(success=False, error="WorkspaceService not available")

        orientation = context.args.get("orientation", "horizontal")
        new_pane_id = workspace_service.split_active_pane(orientation)

        if new_pane_id:
            return CommandResult(success=True, value={"new_pane_id": new_pane_id})
        else:
            return CommandResult(success=False, error="Failed to split pane")

    except Exception as e:
        logger.error(f"Failed to split pane right: {e}")
        return CommandResult(success=False, error=str(e))


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
    """Split active pane vertically using WorkspaceService."""
    try:
        workspace_service = context.get_service(WorkspaceService)
        if not workspace_service:
            return CommandResult(success=False, error="WorkspaceService not available")

        new_pane_id = workspace_service.split_active_pane("vertical")

        if new_pane_id:
            return CommandResult(success=True, value={"new_pane_id": new_pane_id})
        else:
            return CommandResult(success=False, error="Failed to split pane")

    except Exception as e:
        logger.error(f"Failed to split pane down: {e}")
        return CommandResult(success=False, error=str(e))


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
    """Close active pane using WorkspaceService."""
    try:
        workspace_service = context.get_service(WorkspaceService)
        if not workspace_service:
            return CommandResult(success=False, error="WorkspaceService not available")

        success = workspace_service.close_active_pane()

        if success:
            return CommandResult(success=True)
        else:
            return CommandResult(success=False, error="Cannot close the last pane")

    except Exception as e:
        logger.error(f"Failed to close active pane: {e}")
        return CommandResult(success=False, error=str(e))


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
    """Enter command mode for pane navigation with visible numbers."""
    try:
        workspace_service = context.get_service(WorkspaceService)
        if not workspace_service:
            return CommandResult(success=False, error="WorkspaceService not available")

        # Enter command mode which shows pane numbers and activates focus sink
        success = workspace_service.enter_pane_command_mode()

        if success:
            return CommandResult(success=True, value={"command_mode": True})
        else:
            return CommandResult(
                success=False,
                error="Could not enter pane command mode (no panes available)",
            )

    except Exception as e:
        logger.error(f"Failed to enter pane command mode: {e}")
        return CommandResult(success=False, error=str(e))


@command(
    id="workbench.action.focusNextPane",
    title="Focus Next Pane",
    category="Workspace",
    description="Focus the next pane",
    shortcut="tab",
    when="workbench.pane.count > 1",
)
def focus_next_pane_command(context: CommandContext) -> CommandResult:
    """Focus next pane using WorkspaceService."""
    try:
        workspace_service = context.get_service(WorkspaceService)
        if not workspace_service:
            return CommandResult(success=False, error="WorkspaceService not available")

        success = workspace_service.navigate_to_next_pane()

        if success:
            return CommandResult(success=True)
        else:
            return CommandResult(success=False, error="Failed to navigate to next pane")

    except Exception as e:
        logger.error(f"Failed to focus next pane: {e}")
        return CommandResult(success=False, error=str(e))


@command(
    id="workbench.action.focusPreviousPane",
    title="Focus Previous Pane",
    category="Workspace",
    description="Focus the previous pane",
    shortcut="shift+tab",
    when="workbench.pane.count > 1",
)
def focus_previous_pane_command(context: CommandContext) -> CommandResult:
    """Focus previous pane using WorkspaceService."""
    try:
        workspace_service = context.get_service(WorkspaceService)
        if not workspace_service:
            return CommandResult(success=False, error="WorkspaceService not available")

        success = workspace_service.navigate_to_previous_pane()

        if success:
            return CommandResult(success=True)
        else:
            return CommandResult(success=False, error="Failed to navigate to previous pane")

    except Exception as e:
        logger.error(f"Failed to focus previous pane: {e}")
        return CommandResult(success=False, error=str(e))


@command(
    id="workbench.action.nextTab",
    title="Next Tab",
    category="Workspace",
    description="Switch to the next tab",
    shortcut="ctrl+pagedown",
    when="workbench.tabs.count > 1",
)
def next_tab_command(context: CommandContext) -> CommandResult:
    """Switch to next tab using WorkspaceService."""
    try:
        workspace_service = context.get_service(WorkspaceService)
        if not workspace_service:
            return CommandResult(success=False, error="WorkspaceService not available")

        current = workspace_service.get_current_tab_index()
        count = workspace_service.get_tab_count()

        if count > 1:
            next_index = (current + 1) % count
            success = workspace_service.switch_to_tab(next_index)

            if success:
                return CommandResult(success=True, value={"tab_index": next_index})

        return CommandResult(success=False, error="No other tabs to switch to")

    except Exception as e:
        logger.error(f"Failed to switch to next tab: {e}")
        return CommandResult(success=False, error=str(e))


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
        workspace_service = context.get_service(WorkspaceService)
        if not workspace_service:
            return CommandResult(success=False, error="WorkspaceService not available")

        tab_index = context.args.get("tab_index")
        if tab_index is None:
            return CommandResult(success=False, error="No tab index provided")

        count = workspace_service.get_tab_count()
        if 0 <= tab_index < count:
            success = workspace_service.switch_to_tab(tab_index)

            if success:
                return CommandResult(success=True, value={"tab_index": tab_index})

        return CommandResult(success=False, error=f"Invalid tab index: {tab_index}")

    except Exception as e:
        logger.error(f"Failed to select tab: {e}")
        return CommandResult(success=False, error=str(e))


@command(
    id="workbench.action.previousTab",
    title="Previous Tab",
    category="Workspace",
    description="Switch to the previous tab",
    shortcut="ctrl+pageup",
    when="workbench.tabs.count > 1",
)
def previous_tab_command(context: CommandContext) -> CommandResult:
    """Switch to previous tab using WorkspaceService."""
    try:
        workspace_service = context.get_service(WorkspaceService)
        if not workspace_service:
            return CommandResult(success=False, error="WorkspaceService not available")

        current = workspace_service.get_current_tab_index()
        count = workspace_service.get_tab_count()

        if count > 1:
            prev_index = (current - 1) % count
            success = workspace_service.switch_to_tab(prev_index)

            if success:
                return CommandResult(success=True, value={"tab_index": prev_index})

        return CommandResult(success=False, error="No other tabs to switch to")

    except Exception as e:
        logger.error(f"Failed to switch to previous tab: {e}")
        return CommandResult(success=False, error=str(e))


@command(
    id="workbench.action.saveLayout",
    title="Save Workspace Layout",
    category="Workspace",
    description="Save the current workspace layout",
    icon="save",
)
def save_layout_command(context: CommandContext) -> CommandResult:
    """Save workspace layout using WorkspaceService."""
    try:
        workspace_service = context.get_service(WorkspaceService)
        if not workspace_service:
            return CommandResult(success=False, error="WorkspaceService not available")

        layout = workspace_service.save_layout()

        # Show status message
        if context.main_window and hasattr(context.main_window, "status_bar"):
            context.main_window.status_bar.set_message("Layout saved", 2000)

        return CommandResult(success=True, value={"layout": layout})

    except Exception as e:
        logger.error(f"Failed to save layout: {e}")
        return CommandResult(success=False, error=str(e))


@command(
    id="workbench.action.restoreLayout",
    title="Restore Workspace Layout",
    category="Workspace",
    description="Restore the saved workspace layout",
    icon="refresh",
)
def restore_layout_command(context: CommandContext) -> CommandResult:
    """Restore workspace layout using WorkspaceService."""
    try:
        workspace_service = context.get_service(WorkspaceService)
        if not workspace_service:
            return CommandResult(success=False, error="WorkspaceService not available")

        # Get layout from context args or use saved one
        layout = context.args.get("layout")
        if layout:
            success = workspace_service.restore_layout(layout)

            if success:
                # Show status message
                if context.main_window and hasattr(context.main_window, "status_bar"):
                    context.main_window.status_bar.set_message("Layout restored", 2000)

                return CommandResult(success=True)

        return CommandResult(success=False, error="No layout to restore")

    except Exception as e:
        logger.error(f"Failed to restore layout: {e}")
        return CommandResult(success=False, error=str(e))


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
    return CommandResult(success=True)


def register_workspace_commands():
    """Register all workspace commands."""
    # The @command decorator automatically registers them
    # This function ensures the module is imported
    logger.info("Workspace commands registered")
