#!/usr/bin/env python3
"""
Navigation-related commands using the service layer.
"""

import logging

from viloapp.core.commands.base import Command, CommandContext, CommandResult
from viloapp.core.commands.decorators import command
from viloapp.core.commands.registry import command_registry
from viloapp.services.service_locator import ServiceLocator
from viloapp.services.ui_service import UIService
from viloapp.services.workspace_service import WorkspaceService

logger = logging.getLogger(__name__)


# ============= Tab Navigation =============


@command(
    id="workbench.action.firstTab",
    title="Go to First Tab",
    category="Navigation",
    description="Switch to the first tab",
    shortcut="ctrl+1",
    when="workbench.tabs.count > 0",
)
def first_tab_command(context: CommandContext) -> CommandResult:
    """Switch to the first tab."""
    try:
        workspace_service = context.get_service(WorkspaceService)
        if not workspace_service:
            return CommandResult(success=False, error="WorkspaceService not available")

        success = workspace_service.switch_to_tab(0)

        if success:
            return CommandResult(success=True, value={"tab_index": 0})
        else:
            return CommandResult(success=False, error="No tabs available")

    except Exception as e:
        logger.error(f"Failed to switch to first tab: {e}")
        return CommandResult(success=False, error=str(e))


@command(
    id="workbench.action.lastTab",
    title="Go to Last Tab",
    category="Navigation",
    description="Switch to the last tab",
    shortcut="ctrl+9",
    when="workbench.tabs.count > 0",
)
def last_tab_command(context: CommandContext) -> CommandResult:
    """Switch to the last tab."""
    try:
        workspace_service = context.get_service(WorkspaceService)
        if not workspace_service:
            return CommandResult(success=False, error="WorkspaceService not available")

        count = workspace_service.get_tab_count()
        if count > 0:
            success = workspace_service.switch_to_tab(count - 1)

            if success:
                return CommandResult(success=True, value={"tab_index": count - 1})

        return CommandResult(success=False, error="No tabs available")

    except Exception as e:
        logger.error(f"Failed to switch to last tab: {e}")
        return CommandResult(success=False, error=str(e))


@command(
    id="workbench.action.closeOtherTabs",
    title="Close Other Tabs",
    category="Navigation",
    description="Close all tabs except the current one",
    when="workbench.tabs.count > 1",
)
def close_other_tabs_command(context: CommandContext) -> CommandResult:
    """Close all tabs except the current one."""
    try:
        workspace_service = context.get_service(WorkspaceService)
        if not workspace_service:
            return CommandResult(success=False, error="WorkspaceService not available")

        # Get current tab info
        current_index = workspace_service.get_current_tab_index()
        total_tabs = workspace_service.get_tab_count()

        if total_tabs <= 1:
            return CommandResult(success=False, error="Only one tab open")

        # Close tabs from right to left to maintain indices
        closed_count = 0
        for i in range(total_tabs - 1, -1, -1):
            if i != current_index:
                if workspace_service.close_tab(i):
                    closed_count += 1

        # Show status message
        if context.main_window and hasattr(context.main_window, "status_bar"):
            context.main_window.status_bar.set_message(
                f"Closed {closed_count} other tabs", 2000
            )

        return CommandResult(success=True, value={"closed_count": closed_count})

    except Exception as e:
        logger.error(f"Failed to close other tabs: {e}")
        return CommandResult(success=False, error=str(e))


@command(
    id="workbench.action.closeAllTabs",
    title="Close All Tabs",
    category="Navigation",
    description="Close all tabs",
    shortcut="ctrl+alt+w",
    when="workbench.tabs.count > 0",
)
def close_all_tabs_command(context: CommandContext) -> CommandResult:
    """Close all tabs."""
    try:
        workspace_service = context.get_service(WorkspaceService)
        if not workspace_service:
            return CommandResult(success=False, error="WorkspaceService not available")

        total_tabs = workspace_service.get_tab_count()

        # Close all tabs from right to left
        closed_count = 0
        for i in range(total_tabs - 1, -1, -1):
            if workspace_service.close_tab(i):
                closed_count += 1

        # Show status message
        if context.main_window and hasattr(context.main_window, "status_bar"):
            context.main_window.status_bar.set_message(
                f"Closed {closed_count} tabs", 2000
            )

        return CommandResult(success=True, value={"closed_count": closed_count})

    except Exception as e:
        logger.error(f"Failed to close all tabs: {e}")
        return CommandResult(success=False, error=str(e))


# ============= Directional Pane Navigation =============


@command(
    id="workbench.action.focusLeftPane",
    title="Focus Left Pane",
    category="Navigation",
    description="Focus the pane to the left",
    shortcut="alt+left",
    when="workbench.pane.count > 1",
)
def focus_left_pane_command(context: CommandContext) -> CommandResult:
    """Focus the pane to the left."""
    try:
        workspace_service = context.get_service(WorkspaceService)
        if not workspace_service:
            return CommandResult(success=False, error="WorkspaceService not available")

        success = workspace_service.navigate_in_direction("left")

        if success:
            return CommandResult(success=True)
        else:
            return CommandResult(success=False, error="No pane to the left")

    except Exception as e:
        logger.error(f"Failed to focus left pane: {e}")
        return CommandResult(success=False, error=str(e))


@command(
    id="workbench.action.focusRightPane",
    title="Focus Right Pane",
    category="Navigation",
    description="Focus the pane to the right",
    shortcut="alt+right",
    when="workbench.pane.count > 1",
)
def focus_right_pane_command(context: CommandContext) -> CommandResult:
    """Focus the pane to the right."""
    try:
        workspace_service = context.get_service(WorkspaceService)
        if not workspace_service:
            return CommandResult(success=False, error="WorkspaceService not available")

        success = workspace_service.navigate_in_direction("right")

        if success:
            return CommandResult(success=True)
        else:
            return CommandResult(success=False, error="No pane to the right")

    except Exception as e:
        logger.error(f"Failed to focus right pane: {e}")
        return CommandResult(success=False, error=str(e))


@command(
    id="workbench.action.focusAbovePane",
    title="Focus Above Pane",
    category="Navigation",
    description="Focus the pane above",
    shortcut="alt+up",
    when="workbench.pane.count > 1",
)
def focus_above_pane_command(context: CommandContext) -> CommandResult:
    """Focus the pane above."""
    try:
        workspace_service = context.get_service(WorkspaceService)
        if not workspace_service:
            return CommandResult(success=False, error="WorkspaceService not available")

        success = workspace_service.navigate_in_direction("up")

        if success:
            return CommandResult(success=True)
        else:
            return CommandResult(success=False, error="No pane above")

    except Exception as e:
        logger.error(f"Failed to focus above pane: {e}")
        return CommandResult(success=False, error=str(e))


@command(
    id="workbench.action.focusBelowPane",
    title="Focus Below Pane",
    category="Navigation",
    description="Focus the pane below",
    shortcut="alt+down",
    when="workbench.pane.count > 1",
)
def focus_below_pane_command(context: CommandContext) -> CommandResult:
    """Focus the pane below."""
    try:
        workspace_service = context.get_service(WorkspaceService)
        if not workspace_service:
            return CommandResult(success=False, error="WorkspaceService not available")

        success = workspace_service.navigate_in_direction("down")

        if success:
            return CommandResult(success=True)
        else:
            return CommandResult(success=False, error="No pane below")

    except Exception as e:
        logger.error(f"Failed to focus below pane: {e}")
        return CommandResult(success=False, error=str(e))


# ============= UI Navigation =============


@command(
    id="workbench.action.focusSidebar",
    title="Focus Sidebar",
    category="Navigation",
    description="Focus the sidebar",
    shortcut="ctrl+0",
    when="sidebarVisible",
)
def focus_sidebar_command(context: CommandContext) -> CommandResult:
    """Focus the sidebar."""
    try:
        # This would focus the sidebar widget
        # For now, just ensure it's visible and show a status message

        ui_service = context.get_service(UIService)
        if not ui_service:
            return CommandResult(success=False, error="UIService not available")

        # Ensure sidebar is visible
        if not ui_service.is_sidebar_visible():
            ui_service.show_sidebar()

        # Show status message
        if context.main_window and hasattr(context.main_window, "status_bar"):
            context.main_window.status_bar.set_message("Sidebar focused", 1000)

        return CommandResult(success=True)

    except Exception as e:
        logger.error(f"Failed to focus sidebar: {e}")
        return CommandResult(success=False, error=str(e))


@command(
    id="workbench.action.focusActivePane",
    title="Focus Active Pane",
    category="Navigation",
    description="Focus the currently active pane",
    # Removed escape to avoid conflict with commandPalette.hide
    when="workbench.pane.count > 0",
)
def focus_active_pane_command(context: CommandContext) -> CommandResult:
    """Focus the active pane."""
    try:
        workspace_service = context.get_service(WorkspaceService)
        if not workspace_service:
            return CommandResult(success=False, error="WorkspaceService not available")

        active_pane_id = workspace_service.get_active_pane_id()
        if active_pane_id:
            success = workspace_service.focus_pane(active_pane_id)

            if success:
                return CommandResult(success=True, value={"pane_id": active_pane_id})

        return CommandResult(success=False, error="No active pane")

    except Exception as e:
        logger.error(f"Failed to focus active pane: {e}")
        return CommandResult(success=False, error=str(e))


# ============= Pane Management =============


@command(
    id="workbench.action.maximizePane",
    title="Maximize Pane",
    category="Navigation",
    description="Maximize the active pane",
    shortcut="ctrl+k z",
    when="workbench.pane.count > 1",
)
def maximize_pane_command(context: CommandContext) -> CommandResult:
    """Maximize the active pane."""
    try:
        # This is a placeholder for pane maximization
        # In a full implementation, this would temporarily hide other panes
        # or adjust splitter ratios to give maximum space to the active pane

        workspace_service = context.get_service(WorkspaceService)
        if not workspace_service:
            return CommandResult(success=False, error="WorkspaceService not available")

        active_pane_id = workspace_service.get_active_pane_id()
        if not active_pane_id:
            return CommandResult(success=False, error="No active pane")

        # Show status message (placeholder functionality)
        if context.main_window and hasattr(context.main_window, "status_bar"):
            context.main_window.status_bar.set_message(
                f"Pane {active_pane_id} maximized (placeholder)", 2000
            )

        return CommandResult(success=True, value={"pane_id": active_pane_id})

    except Exception as e:
        logger.error(f"Failed to maximize pane: {e}")
        return CommandResult(success=False, error=str(e))


@command(
    id="workbench.action.evenPaneSizes",
    title="Even Pane Sizes",
    category="Navigation",
    description="Make all panes the same size",
    when="workbench.pane.count > 1",
)
def even_pane_sizes_command(context: CommandContext) -> CommandResult:
    """Make all panes the same size."""
    try:
        # This is a placeholder for evening pane sizes
        # In a full implementation, this would adjust splitter ratios
        # to make all panes equal size

        workspace_service = context.get_service(WorkspaceService)
        if not workspace_service:
            return CommandResult(success=False, error="WorkspaceService not available")

        pane_count = workspace_service.get_pane_count()
        if pane_count <= 1:
            return CommandResult(success=False, error="Only one pane")

        # Show status message (placeholder functionality)
        if context.main_window and hasattr(context.main_window, "status_bar"):
            context.main_window.status_bar.set_message(
                f"Evened {pane_count} pane sizes (placeholder)", 2000
            )

        return CommandResult(success=True, value={"pane_count": pane_count})

    except Exception as e:
        logger.error(f"Failed to even pane sizes: {e}")
        return CommandResult(success=False, error=str(e))


@command(
    id="workbench.action.movePaneToNewTab",
    title="Move Pane to New Tab",
    category="Navigation",
    description="Move the active pane to a new tab",
    when="workbench.pane.count > 1",
)
def move_pane_to_new_tab_command(context: CommandContext) -> CommandResult:
    """Move the active pane to a new tab."""
    try:
        # This is a placeholder for moving panes between tabs
        # In a full implementation, this would extract the pane content
        # and create a new tab with it

        workspace_service = context.get_service(WorkspaceService)
        if not workspace_service:
            return CommandResult(success=False, error="WorkspaceService not available")

        active_pane_id = workspace_service.get_active_pane_id()
        if not active_pane_id:
            return CommandResult(success=False, error="No active pane")

        # For now, just create a new editor tab as placeholder
        new_tab_index = workspace_service.add_editor_tab("Moved Pane")

        # Show status message
        if context.main_window and hasattr(context.main_window, "status_bar"):
            context.main_window.status_bar.set_message(
                f"Pane moved to new tab {new_tab_index} (placeholder)", 2000
            )

        return CommandResult(
            success=True,
            value={"source_pane_id": active_pane_id, "new_tab_index": new_tab_index},
        )

    except Exception as e:
        logger.error(f"Failed to move pane to new tab: {e}")
        return CommandResult(success=False, error=str(e))


def focus_next_group_handler(context: CommandContext) -> CommandResult:
    """Move focus to next UI group."""
    try:
        main_window = ServiceLocator.get_instance().get("main_window")
        if not main_window:
            return CommandResult(success=False, error="Main window not available")

        # Focus cycle: Activity Bar -> Sidebar -> Editor -> Terminal -> Activity Bar
        from PySide6.QtWidgets import QApplication

        app = QApplication.instance()
        if app:
            # Simple focus cycling implementation
            if hasattr(main_window, "sidebar") and main_window.sidebar.isVisible():
                main_window.sidebar.setFocus()
            elif hasattr(main_window, "workspace"):
                main_window.workspace.setFocus()
            else:
                main_window.activity_bar.setFocus()

        return CommandResult(success=True)

    except Exception as e:
        logger.error(f"Failed to focus next group: {e}")
        return CommandResult(success=False, error=str(e))


def focus_previous_group_handler(context: CommandContext) -> CommandResult:
    """Move focus to previous UI group."""
    try:
        main_window = ServiceLocator.get_instance().get("main_window")
        if not main_window:
            return CommandResult(success=False, error="Main window not available")

        # Reverse focus cycle
        from PySide6.QtWidgets import QApplication

        app = QApplication.instance()
        if app:
            # Simple reverse focus cycling
            if hasattr(main_window, "workspace"):
                main_window.workspace.setFocus()
            elif hasattr(main_window, "sidebar") and main_window.sidebar.isVisible():
                main_window.sidebar.setFocus()
            else:
                main_window.activity_bar.setFocus()

        return CommandResult(success=True)

    except Exception as e:
        logger.error(f"Failed to focus previous group: {e}")
        return CommandResult(success=False, error=str(e))


def get_focus_navigation_commands():
    """Get focus navigation commands."""
    return [
        Command(
            id="workbench.action.focusNextGroup",
            title="Focus Next Group",
            category="Navigation",
            handler=focus_next_group_handler,
            description="Move focus to the next UI group",
            shortcut="f6",
            keywords=["focus", "next", "group", "navigation"],
        ),
        Command(
            id="workbench.action.focusPreviousGroup",
            title="Focus Previous Group",
            category="Navigation",
            handler=focus_previous_group_handler,
            description="Move focus to the previous UI group",
            shortcut="shift+f6",
            keywords=["focus", "previous", "group", "navigation"],
        ),
    ]


def register_navigation_commands():
    """Register all navigation commands."""
    # Register F6/Shift+F6 commands
    commands = get_focus_navigation_commands()

    for command in commands:
        command_registry.register(command)

    # The @command decorator automatically registers other commands
    # This function ensures the module is imported
    logger.info(f"Registered {len(commands)} focus navigation commands")
