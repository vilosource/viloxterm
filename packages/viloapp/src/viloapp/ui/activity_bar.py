"""Activity bar implementation with icon buttons."""

import logging

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QToolBar, QWidget

from viloapp.core.commands.executor import execute_command
from viloapp.ui.icon_manager import get_icon_manager

logger = logging.getLogger(__name__)


class ActivityBar(QToolBar):
    """Vertical activity bar with icon buttons like VSCode."""

    view_changed = Signal(str)  # Emitted when a view is selected
    toggle_sidebar = Signal()  # Emitted when sidebar toggle is requested

    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.current_view = "explorer"
        self.is_sidebar_collapsed = False  # Track sidebar state

        # Connect to theme changes
        icon_manager = get_icon_manager()
        icon_manager.theme_changed.connect(self.update_icons)

    def setup_ui(self):
        """Initialize the activity bar UI."""
        # Configure toolbar
        self.setOrientation(Qt.Vertical)
        self.setMovable(False)
        self.setFloatable(False)
        self.setIconSize(QSize(24, 24))
        self.setFixedWidth(48)

        # Style the activity bar
        self.setObjectName("activityBar")
        self.setProperty("type", "activitybar")

        # Theme will be applied later

        # Create actions
        self.create_actions()

    def create_actions(self):
        """Create activity bar actions."""
        icon_manager = get_icon_manager()

        # Explorer action
        self.explorer_action = QAction(icon_manager.get_icon("explorer"), "Explorer", self)
        self.explorer_action.setCheckable(True)
        self.explorer_action.setChecked(True)
        self.explorer_action.setToolTip("Explorer (Ctrl+Shift+E)")
        # Use toggled signal which gives us the new state
        self.explorer_action.toggled.connect(
            lambda checked: self.on_action_toggled("explorer", checked)
        )
        self.addAction(self.explorer_action)

        # Search action
        self.search_action = QAction(icon_manager.get_icon("search"), "Search", self)
        self.search_action.setCheckable(True)
        self.search_action.setToolTip("Search (Ctrl+Shift+F)")
        self.search_action.toggled.connect(
            lambda checked: self.on_action_toggled("search", checked)
        )
        self.addAction(self.search_action)

        # Git action
        self.git_action = QAction(icon_manager.get_icon("git"), "Git", self)
        self.git_action.setCheckable(True)
        self.git_action.setToolTip("Source Control (Ctrl+Shift+G)")
        self.git_action.toggled.connect(lambda checked: self.on_action_toggled("git", checked))
        self.addAction(self.git_action)

        # Add separator
        self.addSeparator()

        # Settings action
        self.settings_action = QAction(icon_manager.get_icon("settings"), "Settings", self)
        self.settings_action.setCheckable(True)
        self.settings_action.setToolTip("Settings (Ctrl+,)")
        self.settings_action.toggled.connect(
            lambda checked: self.on_action_toggled("settings", checked)
        )
        self.addAction(self.settings_action)

        # Add spacer widget to push menu to bottom
        from PySide6.QtWidgets import QSizePolicy

        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        spacer.setStyleSheet("background-color: transparent;")
        self.addWidget(spacer)

        # Menu action at the bottom
        self.menu_action = QAction(icon_manager.get_icon("menu"), "Menu", self)
        self.menu_action.setCheckable(False)  # Not checkable - it's a menu trigger
        self.menu_action.setToolTip("Application Menu")
        self.menu_action.triggered.connect(self.on_menu_clicked)
        self.addAction(self.menu_action)

        # Group actions for easy access (excluding menu action)
        self.view_actions = [
            self.explorer_action,
            self.search_action,
            self.git_action,
            self.settings_action,
        ]

    def on_action_toggled(self, view_name: str, checked: bool):
        """Handle action toggle - properly manage state transitions.

        Using the toggled signal instead of triggered gives us better control
        because we know the exact state Qt has set.
        """
        logger.debug("=== ACTIVITY BAR TOGGLED ===")
        logger.debug(f"View: {view_name}, Checked: {checked}")
        logger.debug(f"Current view: {self.current_view}")
        logger.debug(f"Sidebar collapsed: {self.is_sidebar_collapsed}")

        # Ignore signals if we're programmatically updating states
        if hasattr(self, "_updating_states") and self._updating_states:
            logger.debug("Ignoring signal during programmatic update")
            return

        # Get the action that was toggled
        toggled_action = None
        for action in self.view_actions:
            if action.text().lower() == view_name:
                toggled_action = action
                break

        if not toggled_action:
            logger.error(f"Could not find action for view: {view_name}")
            return

        # Block further signals while we update states
        self._updating_states = True

        try:
            if view_name == self.current_view:
                # Same view toggled - this is a sidebar visibility toggle
                logger.debug("Same view toggled - toggling sidebar visibility")

                # Update sidebar collapsed state based on the new checked state
                self.is_sidebar_collapsed = not checked
                logger.debug(f"Sidebar collapsed: {self.is_sidebar_collapsed}")

                # Emit toggle sidebar signal
                self.toggle_sidebar.emit()

                # Execute toggle sidebar command
                execute_command("workbench.action.toggleSidebar")

            else:
                # Different view selected
                logger.debug(f"Different view selected: {view_name}")

                if checked:
                    # New view was checked - switch to it
                    # Uncheck all other actions
                    for action in self.view_actions:
                        if action != toggled_action:
                            action.setChecked(False)

                    # Update current view
                    old_view = self.current_view
                    self.current_view = view_name
                    self.is_sidebar_collapsed = False  # Sidebar will be shown
                    logger.debug(f"Switched from {old_view} to {view_name}")

                    # Emit view changed signal
                    self.view_changed.emit(view_name)

                    # Execute appropriate view command
                    view_commands = {
                        "explorer": "workbench.view.explorer",
                        "search": "workbench.view.search",
                        "git": "workbench.view.git",
                        "settings": "workbench.view.settings",
                    }
                    if view_name in view_commands:
                        execute_command(view_commands[view_name])
                else:
                    # A different view was unchecked - this shouldn't happen normally
                    # but if it does, just ignore it
                    logger.debug(f"Ignoring uncheck of non-current view {view_name}")

        finally:
            self._updating_states = False

        # Log final state
        logger.debug("Final action states:")
        for action in self.view_actions:
            logger.debug(f"  {action.text()}: checked={action.isChecked()}")
        logger.debug(
            f"Current view: {self.current_view}, Sidebar collapsed: {self.is_sidebar_collapsed}"
        )
        logger.debug("=== END ACTIVITY BAR TOGGLED ===")

    def set_sidebar_visible(self, visible: bool):
        """Update the current action's checked state based on sidebar visibility."""
        logger.debug(f"set_sidebar_visible called with visible={visible}")
        logger.debug(f"Current view: {self.current_view}")

        # Update our internal state
        self.is_sidebar_collapsed = not visible
        logger.debug(f"Updated is_sidebar_collapsed to {self.is_sidebar_collapsed}")

        # Set flag to prevent signal handling during programmatic update
        self._updating_states = True

        try:
            # Find the action for the current view
            for action in self.view_actions:
                if action.text().lower() == self.current_view:
                    logger.debug(f"Setting {action.text()} checked state to {visible}")
                    action.setChecked(visible)
                    break
        finally:
            self._updating_states = False

        # Log final state of all actions
        logger.debug("Action states after set_sidebar_visible:")
        for action in self.view_actions:
            logger.debug(f"  {action.text()}: checked={action.isChecked()}")

    def apply_theme(self):
        """Apply current theme to activity bar."""
        # Get theme provider from parent window
        main_window = self.window()
        if hasattr(main_window, "theme_provider"):
            self.setStyleSheet(main_window.theme_provider.get_stylesheet("activity_bar"))

    def update_icons(self):
        """Update icons when theme changes."""
        icon_manager = get_icon_manager()
        self.explorer_action.setIcon(icon_manager.get_icon("explorer"))
        self.search_action.setIcon(icon_manager.get_icon("search"))
        self.git_action.setIcon(icon_manager.get_icon("git"))
        self.settings_action.setIcon(icon_manager.get_icon("settings"))
        self.menu_action.setIcon(icon_manager.get_icon("menu"))

    def show_view(self, view_name: str):
        """Programmatically show a specific view. Called by commands."""
        logger.debug(f"show_view called for: {view_name}")

        # Find the action for this view
        action_map = {
            "explorer": self.explorer_action,
            "search": self.search_action,
            "git": self.git_action,
            "settings": self.settings_action,
        }

        if view_name in action_map:
            action = action_map[view_name]
            if not action.isChecked():
                action.setChecked(True)  # This will trigger on_action_toggled
            else:
                # Action is already checked - this means we're toggling the same view
                # Force trigger the toggle by unchecking and checking again
                action.setChecked(False)  # This will trigger on_action_toggled with False
                action.setChecked(True)  # This will trigger on_action_toggled with True

    def on_menu_clicked(self):
        """Handle menu button click - show application menu."""
        from PySide6.QtWidgets import QMenu

        # Get the main window to access its menu bar
        main_window = self.window()
        if not main_window or not hasattr(main_window, "menuBar"):
            logger.warning("Could not access main window menu bar")
            return

        # Create a popup menu that mirrors the menu bar
        menu = QMenu(self)
        menu.setStyleSheet(
            """
            QMenu {
                background-color: #252526;
                color: #cccccc;
                border: 1px solid #3e3e42;
                padding: 4px;
            }
            QMenu::item {
                padding: 6px 20px 6px 10px;
                border-radius: 2px;
            }
            QMenu::item:selected {
                background-color: #094771;
            }
            QMenu::separator {
                height: 1px;
                background: #3e3e42;
                margin: 4px 10px;
            }
        """
        )

        # Copy all menus from the menu bar
        menubar = main_window.menuBar()
        for action in menubar.actions():
            if action.menu():
                # Add submenu
                submenu = menu.addMenu(action.text())
                # Copy all actions from the original menu
                for sub_action in action.menu().actions():
                    if sub_action.isSeparator():
                        submenu.addSeparator()
                    else:
                        submenu.addAction(sub_action)
            else:
                # Add regular action
                menu.addAction(action)

        # Show the menu at the button position
        button_rect = self.actionGeometry(self.menu_action)
        # Position to the right of the activity bar
        pos = self.mapToGlobal(button_rect.topRight())
        menu.exec(pos)
