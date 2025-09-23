"""State management for the main window."""

import json

from PySide6.QtCore import QSettings

from viloapp.ui.qt_compat import safe_splitter_collapse_setting


class MainWindowStateManager:
    """Manages saving and restoring state for the main window."""

    def __init__(self, main_window):
        """Initialize the state manager."""
        self.main_window = main_window

    def save_state(self):
        """Save window state and geometry."""
        settings = QSettings()
        settings.beginGroup("MainWindow")
        settings.setValue("geometry", self.main_window.saveGeometry())
        settings.setValue("windowState", self.main_window.saveState())
        settings.setValue("splitterSizes", self.main_window.main_splitter.saveState())
        settings.setValue("menuBarVisible", self.main_window.menuBar().isVisible())
        settings.setValue("activityBarVisible", self.main_window.activity_bar.isVisible())
        settings.endGroup()

        # Save workspace state (new tab-based workspace)
        settings.beginGroup("Workspace")
        workspace_state = self.main_window.workspace.save_state()
        settings.setValue("state", json.dumps(workspace_state))
        settings.endGroup()

    def restore_state(self):
        """Restore window state and geometry."""
        settings = QSettings()
        settings.beginGroup("MainWindow")

        geometry = settings.value("geometry")
        if geometry:
            self.main_window.restoreGeometry(geometry)

        window_state = settings.value("windowState")
        if window_state:
            self.main_window.restoreState(window_state)

        splitter_state = settings.value("splitterSizes")
        if splitter_state:
            self.main_window.main_splitter.restoreState(splitter_state)

        # Allow sidebar to be completely collapsed after restoration
        safe_splitter_collapse_setting(self.main_window.main_splitter, True)

        # Restore menu bar visibility and activity bar menu preference
        # Fix the path - it should be under MainWindow group
        use_activity_bar_menu = settings.value("MainWindow/useActivityBarMenu", False, type=bool)
        if hasattr(self.main_window, "auto_hide_menubar_action"):
            if use_activity_bar_menu:
                self.main_window.auto_hide_menubar_action.setChecked(True)
                self.main_window.menuBar().setVisible(False)
            else:
                menu_visible = settings.value("menuBarVisible", True, type=bool)
                self.main_window.menuBar().setVisible(menu_visible)
        else:
            menu_visible = settings.value("menuBarVisible", True, type=bool)
            self.main_window.menuBar().setVisible(menu_visible)

        # Restore activity bar visibility
        activity_bar_visible = settings.value("activityBarVisible", True, type=bool)
        if not activity_bar_visible:
            self.main_window.activity_bar.hide()

        settings.endGroup()

        # Restore workspace state (new tab-based workspace)
        settings.beginGroup("Workspace")
        workspace_state_json = settings.value("state")
        if workspace_state_json:
            try:
                workspace_state = json.loads(workspace_state_json)
                self.main_window.workspace.restore_state(workspace_state)
            except (json.JSONDecodeError, Exception) as e:
                # If restoration fails, workspace will create default tab
                print(f"Failed to restore workspace state: {e}")
        settings.endGroup()

    def close_event_handler(self, event):
        """Handle close event by saving state."""
        self.save_state()

        # Clean up workspace widgets first
        if hasattr(self.window, 'workspace') and self.window.workspace:
            if hasattr(self.window.workspace, 'cleanup'):
                self.window.workspace.cleanup()

        # Terminal cleanup is now handled by the terminal plugin
        # from viloapp.services.terminal_server import terminal_server
        # terminal_server.cleanup_all_sessions()

        event.accept()
