#!/usr/bin/env python3
"""
New main entry point for ViloxTerm.

This wires together the model, commands, and views into a complete application.
ALL state mutations go through commands. Views are pure renderers.
"""

import json
import os
import sys
from pathlib import Path
from typing import Optional

from PySide6.QtCore import QEvent, QObject, QTimer, Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import QApplication, QMainWindow, QMenuBar, QMessageBox

try:
    from .commands import CommandContext, CommandRegistry
    from .model import WidgetType, WorkspaceModel
    from .views import WorkspaceView
except ImportError:
    # For direct script execution
    from commands import CommandContext, CommandRegistry
    from model import WidgetType, WorkspaceModel
    from views import WorkspaceView


class ViloxTermApplication(QMainWindow):
    """
    Main application window.

    This is the integration point that:
    - Creates and owns the model
    - Sets up the command system
    - Creates the view
    - Handles keyboard shortcuts
    - Manages state persistence
    """

    def __init__(self):
        """Initialize the application."""
        super().__init__()

        # Core components
        self.model = WorkspaceModel()
        self.command_registry = CommandRegistry()

        # State file path
        self.state_file = self._get_state_file_path()

        # Set up the application
        self.setup_ui()
        self.setup_shortcuts()
        self.setup_menus()

        # Load previous state if available
        self.load_state()

        # Auto-save timer
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(self.save_state)
        self.auto_save_timer.start(30000)  # Save every 30 seconds

    def _get_state_file_path(self) -> Path:
        """Get the path to the state file."""
        # Use XDG_CONFIG_HOME or fallback to ~/.config
        config_dir = os.environ.get("XDG_CONFIG_HOME")
        if not config_dir:
            config_dir = os.path.expanduser("~/.config")

        viloapp_dir = Path(config_dir) / "viloapp"
        viloapp_dir.mkdir(parents=True, exist_ok=True)

        return viloapp_dir / "workspace_state.json"

    def setup_ui(self):
        """Set up the UI."""
        self.setWindowTitle("ViloxTerm - Model-View-Command Architecture")
        self.resize(1400, 900)

        # Create the main view
        self.workspace_view = WorkspaceView(self.model, self.command_registry)
        self.setCentralWidget(self.workspace_view)

        # Style the application
        self.setStyleSheet(
            """
            QMainWindow {
                background-color: #1e1e1e;
            }
            QMenuBar {
                background-color: #2d2d30;
                color: #cccccc;
            }
            QMenuBar::item:selected {
                background-color: #094771;
            }
            QMenu {
                background-color: #2d2d30;
                color: #cccccc;
            }
            QMenu::item:selected {
                background-color: #094771;
            }
            """
        )

    def setup_shortcuts(self):
        """Set up keyboard shortcuts mapped to commands."""
        shortcuts = [
            # Tab management
            ("Ctrl+T", "tab.create", {"name": "New Tab"}),
            ("Ctrl+W", "tab.close", {}),
            ("Ctrl+Tab", "tab.next", {}),
            ("Ctrl+Shift+Tab", "tab.previous", {}),
            # Pane management
            ("Ctrl+\\", "pane.split", {"orientation": "horizontal"}),
            ("Ctrl+Shift+\\", "pane.split", {"orientation": "vertical"}),
            ("Ctrl+Shift+W", "pane.close", {}),
            # Navigation
            ("Alt+Left", "pane.focus_left", {}),
            ("Alt+Right", "pane.focus_right", {}),
            ("Alt+Up", "pane.focus_up", {}),
            ("Alt+Down", "pane.focus_down", {}),
            # Terminal shortcuts
            ("Ctrl+Shift+T", "tab.create", {"name": "Terminal", "widget_type": WidgetType.TERMINAL}),
            # Editor shortcuts
            ("Ctrl+N", "tab.create", {"name": "Editor", "widget_type": WidgetType.EDITOR}),
        ]

        for key_seq, command, params in shortcuts:
            action = QAction(self)
            action.setShortcut(QKeySequence(key_seq))
            action.triggered.connect(lambda checked, cmd=command, p=params: self.execute_command(cmd, p))
            self.addAction(action)

    def setup_menus(self):
        """Set up the menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")

        new_tab_action = QAction("New Tab", self)
        new_tab_action.setShortcut("Ctrl+T")
        new_tab_action.triggered.connect(lambda: self.execute_command("tab.create"))
        file_menu.addAction(new_tab_action)

        new_terminal_action = QAction("New Terminal", self)
        new_terminal_action.setShortcut("Ctrl+Shift+T")
        new_terminal_action.triggered.connect(
            lambda: self.execute_command("tab.create", {"name": "Terminal", "widget_type": WidgetType.TERMINAL})
        )
        file_menu.addAction(new_terminal_action)

        file_menu.addSeparator()

        save_state_action = QAction("Save State", self)
        save_state_action.setShortcut("Ctrl+S")
        save_state_action.triggered.connect(self.save_state)
        file_menu.addAction(save_state_action)

        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # View menu
        view_menu = menubar.addMenu("View")

        split_h_action = QAction("Split Horizontal", self)
        split_h_action.setShortcut("Ctrl+\\")
        split_h_action.triggered.connect(lambda: self.execute_command("pane.split", {"orientation": "horizontal"}))
        view_menu.addAction(split_h_action)

        split_v_action = QAction("Split Vertical", self)
        split_v_action.setShortcut("Ctrl+Shift+\\")
        split_v_action.triggered.connect(lambda: self.execute_command("pane.split", {"orientation": "vertical"}))
        view_menu.addAction(split_v_action)

        view_menu.addSeparator()

        close_pane_action = QAction("Close Pane", self)
        close_pane_action.setShortcut("Ctrl+Shift+W")
        close_pane_action.triggered.connect(lambda: self.execute_command("pane.close"))
        view_menu.addAction(close_pane_action)

        # Window menu
        window_menu = menubar.addMenu("Window")

        next_tab_action = QAction("Next Tab", self)
        next_tab_action.setShortcut("Ctrl+Tab")
        next_tab_action.triggered.connect(lambda: self.execute_command("tab.next"))
        window_menu.addAction(next_tab_action)

        prev_tab_action = QAction("Previous Tab", self)
        prev_tab_action.setShortcut("Ctrl+Shift+Tab")
        prev_tab_action.triggered.connect(lambda: self.execute_command("tab.previous"))
        window_menu.addAction(prev_tab_action)

        window_menu.addSeparator()

        close_tab_action = QAction("Close Tab", self)
        close_tab_action.setShortcut("Ctrl+W")
        close_tab_action.triggered.connect(lambda: self.execute_command("tab.close"))
        window_menu.addAction(close_tab_action)

        # Help menu
        help_menu = menubar.addMenu("Help")

        about_action = QAction("About", self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

        architecture_action = QAction("Architecture Info", self)
        architecture_action.triggered.connect(self.show_architecture_info)
        help_menu.addAction(architecture_action)

    def execute_command(self, command_name: str, params: Optional[dict] = None):
        """Execute a command through the registry."""
        context = CommandContext(model=self.model)

        # Update context with current active items
        tab = self.model.state.get_active_tab()
        if tab:
            context.active_tab_id = tab.id
            pane = tab.get_active_pane()
            if pane:
                context.active_pane_id = pane.id

        # Execute the command
        params = params or {}
        result = self.command_registry.execute(command_name, context, **params)

        # Show error if command failed
        if not result.success and result.message:
            QMessageBox.warning(self, "Command Failed", result.message)

    def load_state(self):
        """Load the saved state."""
        if not self.state_file.exists():
            # Create default state
            self.execute_command("tab.create", {"name": "Terminal", "widget_type": WidgetType.TERMINAL})
            return

        try:
            with open(self.state_file, "r") as f:
                state = json.load(f)
                self.model.deserialize(state)
        except Exception as e:
            print(f"Failed to load state: {e}")
            # Create default state on error
            self.execute_command("tab.create", {"name": "Terminal", "widget_type": WidgetType.TERMINAL})

    def save_state(self):
        """Save the current state."""
        try:
            state = self.model.serialize()
            with open(self.state_file, "w") as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            print(f"Failed to save state: {e}")

    def closeEvent(self, event):
        """Handle application close."""
        # Save state before closing
        self.save_state()

        # Stop auto-save timer
        self.auto_save_timer.stop()

        event.accept()

    def show_about(self):
        """Show about dialog."""
        QMessageBox.information(
            self,
            "About ViloxTerm",
            "ViloxTerm - Terminal Emulator\n\n"
            "Model-View-Command Architecture\n"
            "Built with PySide6 and Python\n\n"
            "This is the new architecture with:\n"
            "- Single source of truth (WorkspaceModel)\n"
            "- Pure command system\n"
            "- Stateless view layer\n"
            "- Clean separation of concerns",
        )

    def show_architecture_info(self):
        """Show architecture information."""
        tab_count = len(self.model.state.tabs)
        total_panes = sum(len(tab.tree.root.get_all_panes()) for tab in self.model.state.tabs)
        commands = len(self.command_registry.commands)

        info = f"""Architecture Information:

Model State:
- Tabs: {tab_count}
- Total Panes: {total_panes}
- Active Tab: {self.model.state.active_tab_id or 'None'}

Command System:
- Registered Commands: {commands}
- Command Aliases: {len(self.command_registry.aliases)}

View Layer:
- Pure rendering from model
- Observer pattern active
- No state stored in views

State Persistence:
- Config: {self.state_file}
- Auto-save: Every 30 seconds
"""
        QMessageBox.information(self, "Architecture Info", info)


def main():
    """Main entry point."""
    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("ViloxTerm")
    app.setOrganizationName("ViloxTerm")

    # Create and show main window
    window = ViloxTermApplication()
    window.show()

    # Run the application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()