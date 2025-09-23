#!/usr/bin/env python3
"""
Navigation-related commands using the service layer.
"""

import logging

from viloapp.core.commands.base import CommandContext, CommandResult, CommandStatus, FunctionCommand
from viloapp.core.commands.decorators import command
from viloapp.core.commands.registry import command_registry
from viloapp.services.service_locator import ServiceLocator

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
        # Use model directly instead of service
        if not context.model or not hasattr(context.model, "state"):
            return CommandResult(status=CommandStatus.FAILURE, message="Model not available")

        if not context.model.state.tabs:
            return CommandResult(status=CommandStatus.FAILURE, message="No tabs available")

        # Get first tab and switch to it
        first_tab = context.model.state.tabs[0]
        success = context.model.set_active_tab(first_tab.id)

        if success:
            return CommandResult(
                status=CommandStatus.SUCCESS, data={"tab_index": 0, "tab_id": first_tab.id}
            )
        else:
            return CommandResult(
                status=CommandStatus.FAILURE, message="Failed to switch to first tab"
            )

    except Exception as e:
        logger.error(f"Failed to switch to first tab: {e}")
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


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
        # Use model directly instead of service
        if not context.model or not hasattr(context.model, "state"):
            return CommandResult(status=CommandStatus.FAILURE, message="Model not available")

        if not context.model.state.tabs:
            return CommandResult(status=CommandStatus.FAILURE, message="No tabs available")

        # Get last tab and switch to it
        last_tab = context.model.state.tabs[-1]
        last_index = len(context.model.state.tabs) - 1
        success = context.model.set_active_tab(last_tab.id)

        if success:
            return CommandResult(
                status=CommandStatus.SUCCESS, data={"tab_index": last_index, "tab_id": last_tab.id}
            )
        else:
            return CommandResult(
                status=CommandStatus.FAILURE, message="Failed to switch to last tab"
            )

    except Exception as e:
        logger.error(f"Failed to switch to last tab: {e}")
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


@command(
    id="navigation.closeOtherTabs",
    title="Close Other Tabs (Navigation)",
    category="Navigation",
    description="Close all tabs except the current one",
    when="workbench.tabs.count > 1",
)
def close_other_tabs_command(context: CommandContext) -> CommandResult:
    """Close all tabs except the current one."""
    try:
        # Use model directly instead of service
        if not context.model or not hasattr(context.model, "state"):
            return CommandResult(status=CommandStatus.FAILURE, message="Model not available")

        if len(context.model.state.tabs) <= 1:
            return CommandResult(status=CommandStatus.FAILURE, message="Only one tab open")

        # Get current tab
        current_tab_id = context.model.state.active_tab_id
        if not current_tab_id:
            return CommandResult(status=CommandStatus.FAILURE, message="No active tab")

        # Close all tabs except the current one
        closed_count = 0
        tabs_to_close = [tab for tab in context.model.state.tabs if tab.id != current_tab_id]

        for tab in tabs_to_close:
            if context.model.close_tab(tab.id):
                closed_count += 1

        return CommandResult(
            status=CommandStatus.SUCCESS,
            data={"closed_count": closed_count, "message": f"Closed {closed_count} other tabs"},
        )

    except Exception as e:
        logger.error(f"Failed to close other tabs: {e}")
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


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
        # Use model directly
        if not context.model or not hasattr(context.model, "state"):
            return CommandResult(status=CommandStatus.FAILURE, message="Model not available")

        if not context.model.state.tabs:
            return CommandResult(status=CommandStatus.FAILURE, message="No tabs to close")

        # Close all tabs except the last one (can't close all)
        closed_count = 0
        tabs_to_close = list(context.model.state.tabs[:-1])  # Keep last tab

        for tab in tabs_to_close:
            if context.model.close_tab(tab.id):
                closed_count += 1

        # Create a new default tab if we closed everything
        if len(context.model.state.tabs) == 0:
            from viloapp.core.app_widget_manager import app_widget_manager

            # Get the system's default widget
            default_widget_id = app_widget_manager.get_default_widget_id()
            if default_widget_id:
                context.model.create_tab("Default", default_widget_id)

        return CommandResult(
            status=CommandStatus.SUCCESS,
            data={"closed_count": closed_count, "message": f"Closed {closed_count} tabs"},
        )

    except Exception as e:
        logger.error(f"Failed to close all tabs: {e}")
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


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
        if not context.model or not hasattr(context.model, "focus_pane_left"):
            return CommandResult(status=CommandStatus.FAILURE, message="Model not available")

        success = context.model.focus_pane_left()

        if success:
            return CommandResult(status=CommandStatus.SUCCESS, message="Focused left pane")
        else:
            return CommandResult(status=CommandStatus.NOT_APPLICABLE, message="No pane to the left")

    except Exception as e:
        logger.error(f"Failed to focus left pane: {e}")
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


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
        if not context.model or not hasattr(context.model, "focus_pane_right"):
            return CommandResult(status=CommandStatus.FAILURE, message="Model not available")

        success = context.model.focus_pane_right()

        if success:
            return CommandResult(status=CommandStatus.SUCCESS, message="Focused right pane")
        else:
            return CommandResult(
                status=CommandStatus.NOT_APPLICABLE, message="No pane to the right"
            )

    except Exception as e:
        logger.error(f"Failed to focus right pane: {e}")
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


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
        if not context.model or not hasattr(context.model, "focus_pane_up"):
            return CommandResult(status=CommandStatus.FAILURE, message="Model not available")

        success = context.model.focus_pane_up()

        if success:
            return CommandResult(status=CommandStatus.SUCCESS, message="Focused pane above")
        else:
            return CommandResult(status=CommandStatus.NOT_APPLICABLE, message="No pane above")

    except Exception as e:
        logger.error(f"Failed to focus above pane: {e}")
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


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
        if not context.model or not hasattr(context.model, "focus_pane_down"):
            return CommandResult(status=CommandStatus.FAILURE, message="Model not available")

        success = context.model.focus_pane_down()

        if success:
            return CommandResult(status=CommandStatus.SUCCESS, message="Focused pane below")
        else:
            return CommandResult(status=CommandStatus.NOT_APPLICABLE, message="No pane below")

    except Exception as e:
        logger.error(f"Failed to focus below pane: {e}")
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


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
        # Use main window directly to manage sidebar
        # This is a UI-specific operation that doesn't belong in the model
        main_window = context.parameters.get("main_window")
        if not main_window:
            # Try to get main window from service locator as fallback
            main_window = ServiceLocator.get_instance().get("main_window")
            if not main_window:
                return CommandResult(
                    status=CommandStatus.FAILURE, message="Main window not available"
                )

        # Ensure sidebar is visible and focus it
        if hasattr(main_window, "sidebar"):
            if not main_window.sidebar.isVisible():
                main_window.sidebar.setVisible(True)
            main_window.sidebar.setFocus()

        # Show status message
        if hasattr(main_window, "status_bar"):
            main_window.status_bar.set_message("Sidebar focused", 1000)

        return CommandResult(status=CommandStatus.SUCCESS)

    except Exception as e:
        logger.error(f"Failed to focus sidebar: {e}")
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


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
        # Use model directly
        if not context.model or not hasattr(context.model, "state"):
            return CommandResult(status=CommandStatus.FAILURE, message="Model not available")

        # Get active pane from model
        active_tab = context.model.state.get_active_tab()
        if not active_tab or not active_tab.active_pane_id:
            return CommandResult(status=CommandStatus.FAILURE, message="No active pane")

        active_pane_id = active_tab.active_pane_id

        # Set focus on the active pane (already active, but ensures focus)
        success = context.model.set_active_pane(active_tab.id, active_pane_id)

        if success:
            return CommandResult(status=CommandStatus.SUCCESS, data={"pane_id": active_pane_id})
        else:
            return CommandResult(
                status=CommandStatus.FAILURE, message="Failed to focus active pane"
            )

    except Exception as e:
        logger.error(f"Failed to focus active pane: {e}")
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


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
        # Use model directly
        if not context.model or not hasattr(context.model, "maximize_pane"):
            return CommandResult(status=CommandStatus.FAILURE, message="Model not available")

        # Maximize or restore the active pane
        success = context.model.maximize_pane()

        if success:
            # Show status message
            if context.main_window and hasattr(context.main_window, "status_bar"):
                context.main_window.status_bar.set_message("Pane maximized/restored", 2000)
            return CommandResult(status=CommandStatus.SUCCESS)
        else:
            return CommandResult(status=CommandStatus.FAILURE, message="Failed to maximize pane")

    except Exception as e:
        logger.error(f"Failed to maximize pane: {e}")
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


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
        # Use model directly
        if not context.model or not hasattr(context.model, "even_pane_sizes"):
            return CommandResult(status=CommandStatus.FAILURE, message="Model not available")

        # Even all pane sizes
        success = context.model.even_pane_sizes()

        if success:
            # Show status message
            if context.main_window and hasattr(context.main_window, "status_bar"):
                context.main_window.status_bar.set_message("Pane sizes evened", 2000)
            return CommandResult(status=CommandStatus.SUCCESS)
        else:
            return CommandResult(status=CommandStatus.FAILURE, message="Failed to even pane sizes")

    except Exception as e:
        logger.error(f"Failed to even pane sizes: {e}")
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


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
        # Use model directly
        if not context.model or not hasattr(context.model, "extract_pane_to_tab"):
            return CommandResult(status=CommandStatus.FAILURE, message="Model not available")

        # Extract active pane to new tab
        new_tab_id = context.model.extract_pane_to_tab()

        if new_tab_id:
            # Get tab index for display
            new_tab_index = -1
            for i, tab in enumerate(context.model.state.tabs):
                if tab.id == new_tab_id:
                    new_tab_index = i
                    break

            # Show status message
            if context.main_window and hasattr(context.main_window, "status_bar"):
                context.main_window.status_bar.set_message(
                    f"Pane moved to new tab {new_tab_index}", 2000
                )

            return CommandResult(
                status=CommandStatus.SUCCESS,
                data={"new_tab_id": new_tab_id, "new_tab_index": new_tab_index},
            )
        else:
            return CommandResult(
                status=CommandStatus.FAILURE, message="Cannot extract the only pane"
            )

    except Exception as e:
        logger.error(f"Failed to move pane to new tab: {e}")
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


def focus_next_group_handler(context: CommandContext) -> CommandResult:
    """Move focus to next UI group."""
    try:
        main_window = ServiceLocator.get_instance().get("main_window")
        if not main_window:
            return CommandResult(status=CommandStatus.FAILURE, message="Main window not available")

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

        return CommandResult(status=CommandStatus.SUCCESS)

    except Exception as e:
        logger.error(f"Failed to focus next group: {e}")
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


def focus_previous_group_handler(context: CommandContext) -> CommandResult:
    """Move focus to previous UI group."""
    try:
        main_window = ServiceLocator.get_instance().get("main_window")
        if not main_window:
            return CommandResult(status=CommandStatus.FAILURE, message="Main window not available")

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

        return CommandResult(status=CommandStatus.SUCCESS)

    except Exception as e:
        logger.error(f"Failed to focus previous group: {e}")
        return CommandResult(status=CommandStatus.FAILURE, message=str(e))


def get_focus_navigation_commands():
    """Get focus navigation commands."""
    return [
        FunctionCommand(
            id="workbench.action.focusNextGroup",
            title="Focus Next Group",
            category="Navigation",
            handler=focus_next_group_handler,
            description="Move focus to the next UI group",
            shortcut="f6",
            keywords=["focus", "next", "group", "navigation"],
        ),
        FunctionCommand(
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

    for cmd in commands:
        command_registry.register(cmd)

    # The @command decorator automatically registers other commands
    # This function ensures the module is imported
    logger.info(f"Registered {len(commands)} focus navigation commands")
