"""Action handlers and menu setup for the main window."""

import logging

from PySide6.QtCore import QSettings
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMessageBox

from viloapp.services.icon_service import get_icon_manager

logger = logging.getLogger(__name__)


class MainWindowActionManager:
    """Manages actions and menu setup for the main window."""

    def __init__(self, main_window):
        """Initialize the action manager."""
        self.main_window = main_window
        self.apps_menu = None  # Store reference to refresh later

    def create_apps_menu(self):
        """Create dynamic Apps menu from registered widgets."""
        menubar = self.main_window.menuBar()

        # Create or get existing Apps menu
        if self.apps_menu is None:
            self.apps_menu = menubar.addMenu("Apps")
        else:
            # Clear existing menu items for refresh
            self.apps_menu.clear()

        apps_menu = self.apps_menu

        try:
            from viloapp.core.app_widget_manager import app_widget_manager

            # Get all widgets that should appear in menus
            menu_widgets = app_widget_manager.get_menu_widgets()
            logger.info(f"Apps menu: Found {len(menu_widgets)} widgets for menu")

            # Also log all registered widgets for debugging
            all_widgets = app_widget_manager.get_all_widgets()
            logger.info(f"Apps menu: Total registered widgets: {len(all_widgets)}")
            for w_meta in all_widgets:
                logger.debug(f"  Widget: {w_meta.widget_id}, show_in_menu: {w_meta.show_in_menu}, available: {w_meta.is_available()}")

            if not menu_widgets:
                # Add placeholder if no widgets available
                no_apps_action = QAction("No apps available", self.main_window)
                no_apps_action.setEnabled(False)
                apps_menu.addAction(no_apps_action)
                logger.warning("No widgets found for Apps menu")
                return

            # Group widgets by category for organization
            categories = {}
            for widget in menu_widgets:
                category = widget.category.value
                if category not in categories:
                    categories[category] = []
                categories[category].append(widget)

            # Define category order for consistent UX
            category_order = [
                "editor",      # Text/code editors first
                "terminal",    # Terminal emulators
                "viewer",      # File viewers
                "tools",       # Development tools
                "development", # Debug/profiling tools
                "system",      # System/settings widgets
                "plugin",      # Plugin-provided widgets
            ]

            # Sort categories by defined order
            sorted_categories = sorted(
                categories.items(),
                key=lambda x: (
                    category_order.index(x[0])
                    if x[0] in category_order
                    else 999
                )
            )

            # Add menu items organized by category
            for category_name, widgets in sorted_categories:
                if widgets:
                    # Add category section
                    display_name = category_name.replace("_", " ").title()
                    apps_menu.addSection(display_name)

                    # Sort widgets within category alphabetically
                    widgets.sort(key=lambda w: w.display_name)

                    # Add action for each widget
                    for widget_meta in widgets:
                        action = QAction(widget_meta.display_name, self.main_window)

                        # Add icon if available
                        if widget_meta.icon:
                            icon_manager = get_icon_manager()
                            if icon_manager:
                                icon = icon_manager.get_icon(widget_meta.icon)
                                if icon:
                                    action.setIcon(icon)

                        # Set tooltip with description and capabilities
                        tooltip = widget_meta.description
                        if widget_meta.provides_capabilities:
                            caps = ", ".join(widget_meta.provides_capabilities)
                            tooltip += f"\nCapabilities: {caps}"
                        action.setToolTip(tooltip)

                        # Connect to workspace.newTab command with widget_id
                        action.triggered.connect(
                            lambda checked, wid=widget_meta.widget_id:
                            self.main_window.execute_command(
                                "workspace.newTab",
                                widget_id=wid
                            )
                        )

                        apps_menu.addAction(action)

        except ImportError as e:
            logger.error(f"Failed to import app_widget_manager: {e}")
            # Add error indication
            error_action = QAction("Error loading apps", self.main_window)
            error_action.setEnabled(False)
            apps_menu.addAction(error_action)
        except Exception as e:
            logger.error(f"Failed to create apps menu: {e}")
            # Add error indication
            error_action = QAction("Error loading apps", self.main_window)
            error_action.setEnabled(False)
            apps_menu.addAction(error_action)

    def refresh_apps_menu(self):
        """Refresh the Apps menu after plugins are loaded."""
        try:
            # Check if menu still exists (Qt object might have been deleted)
            if self.apps_menu:
                try:
                    # Test if the Qt object is still valid
                    self.apps_menu.title()
                    logger.info("Refreshing Apps menu after plugin load")
                    self.create_apps_menu()
                except RuntimeError:
                    # Menu was deleted, need to recreate
                    logger.info("Apps menu was deleted, recreating...")
                    self.apps_menu = None
                    self.create_apps_menu()
            else:
                logger.warning("Cannot refresh Apps menu - menu not created yet")
        except (RuntimeError, AttributeError) as e:
            logger.warning(f"Cannot refresh Apps menu - error: {e}")
            # Reset the menu reference and try to recreate
            self.apps_menu = None
            try:
                self.create_apps_menu()
            except Exception as e2:
                logger.error(f"Failed to recreate Apps menu: {e2}")

    def create_menu_bar(self):
        """Create the menu bar."""
        menubar = self.main_window.menuBar()

        # Ensure menu bar is visible by default on first run
        # (restore_state will override this if there are saved settings)
        menubar.setVisible(True)

        # File menu
        file_menu = menubar.addMenu("File")

        # New tab actions (using new unified command)
        new_tab_action = QAction("New Tab", self.main_window)
        new_tab_action.setToolTip("Create a new tab (Ctrl+T)")
        new_tab_action.triggered.connect(
            lambda: self.main_window.execute_command("workspace.newTab")
        )
        file_menu.addAction(new_tab_action)

        new_tab_with_type_action = QAction("New Tab (Choose Type)...", self.main_window)
        new_tab_with_type_action.setToolTip("Create a new tab with specific type (Ctrl+Shift+T)")
        new_tab_with_type_action.triggered.connect(
            lambda: self.main_window.execute_command("workspace.newTabWithType")
        )
        file_menu.addAction(new_tab_with_type_action)

        file_menu.addSeparator()

        # Preferences/Settings menu
        preferences_menu = file_menu.addMenu("Preferences")

        # Settings action
        settings_action = QAction("Settings...", self.main_window)
        settings_action.setToolTip("Configure application settings and defaults (Ctrl+,)")
        settings_action.triggered.connect(
            lambda: self.main_window.execute_command("settings.openSettings")
        )
        preferences_menu.addAction(settings_action)

        # Keyboard Shortcuts action (now using commands)
        keyboard_shortcuts_action = QAction("Keyboard Shortcuts...", self.main_window)
        keyboard_shortcuts_action.setToolTip("Configure keyboard shortcuts (Ctrl+K, Ctrl+S)")
        keyboard_shortcuts_action.triggered.connect(
            lambda: self.main_window.execute_command("settings.openKeyboardShortcuts")
        )
        preferences_menu.addAction(keyboard_shortcuts_action)

        file_menu.addSeparator()

        # About action
        about_action = QAction("About ViloxTerm", self.main_window)
        about_action.setToolTip("Show information about ViloxTerm")
        about_action.triggered.connect(lambda: self.main_window.execute_command("help.about"))
        file_menu.addAction(about_action)

        # Apps menu - dynamically populated with available widgets
        self.create_apps_menu()
        # Note: Apps menu will be refreshed after plugins load

        # View menu
        view_menu = menubar.addMenu("View")

        # Theme selection action (now using new theme system)
        theme_action = QAction("Select Theme", self.main_window)
        # Shortcut handled by command system, not QAction
        theme_action.setToolTip("Select a color theme (Ctrl+K, Ctrl+T)")
        theme_action.triggered.connect(
            lambda: self.main_window.execute_command("theme.selectTheme")
        )
        view_menu.addAction(theme_action)

        # Theme Editor action
        theme_editor_action = QAction("Theme Editor...", self.main_window)
        theme_editor_action.setToolTip("Open the theme editor to customize themes (Ctrl+K, Ctrl+M)")
        theme_editor_action.triggered.connect(
            lambda: self.main_window.execute_command("theme.openEditor")
        )
        view_menu.addAction(theme_editor_action)

        view_menu.addSeparator()

        # Import VSCode Theme action
        import_vscode_theme_action = QAction("Import VSCode Theme...", self.main_window)
        import_vscode_theme_action.setToolTip("Import a theme from VSCode JSON format")
        import_vscode_theme_action.triggered.connect(
            lambda: self.main_window.execute_command("theme.importVSCode")
        )
        view_menu.addAction(import_vscode_theme_action)

        # Sidebar toggle action (now using commands)
        sidebar_action = QAction("Toggle Sidebar", self.main_window)
        # Shortcut handled by command system, not QAction
        sidebar_action.setToolTip("Toggle sidebar visibility (Ctrl+B)")
        sidebar_action.triggered.connect(
            lambda: self.main_window.execute_command("view.toggleSidebar")
        )
        view_menu.addAction(sidebar_action)

        view_menu.addSeparator()

        # Split actions (now using commands)
        split_horizontal_action = QAction("Split Pane Right", self.main_window)
        # Shortcut handled by command system, not QAction
        split_horizontal_action.setToolTip("Split the active pane horizontally (Ctrl+\\)")
        split_horizontal_action.triggered.connect(
            lambda: self.main_window.execute_command("workbench.action.splitRight")
        )
        view_menu.addAction(split_horizontal_action)

        split_vertical_action = QAction("Split Pane Down", self.main_window)
        # Shortcut handled by command system, not QAction
        split_vertical_action.setToolTip("Split the active pane vertically (Ctrl+Shift+\\)")
        split_vertical_action.triggered.connect(
            lambda: self.main_window.execute_command("workbench.action.splitDown")
        )
        view_menu.addAction(split_vertical_action)

        close_pane_action = QAction("Close Pane", self.main_window)
        # Shortcut handled by command system, not QAction
        close_pane_action.setToolTip("Close the active pane (Ctrl+W)")
        close_pane_action.triggered.connect(
            lambda: self.main_window.execute_command("workbench.action.closeActivePane")
        )
        view_menu.addAction(close_pane_action)

        view_menu.addSeparator()

        # Menu bar toggle action (shortcut handled by global QShortcut)
        self.main_window.menubar_action = QAction("Toggle Menu Bar", self.main_window)
        self.main_window.menubar_action.setToolTip("Toggle menu bar visibility (Ctrl+Shift+M)")
        self.main_window.menubar_action.triggered.connect(
            lambda: self.main_window.execute_command("view.toggleMenuBar")
        )
        view_menu.addAction(self.main_window.menubar_action)

        # Auto-hide menu bar option
        self.main_window.auto_hide_menubar_action = QAction(
            "Use Activity Bar Menu", self.main_window
        )
        self.main_window.auto_hide_menubar_action.setCheckable(True)
        self.main_window.auto_hide_menubar_action.setToolTip(
            "Hide menu bar and use activity bar menu icon instead"
        )
        self.main_window.auto_hide_menubar_action.toggled.connect(self.on_auto_hide_menubar_toggled)
        view_menu.addAction(self.main_window.auto_hide_menubar_action)

        view_menu.addSeparator()

        # Frameless mode toggle
        frameless_action = QAction("Frameless Mode", self.main_window)
        frameless_action.setCheckable(True)
        frameless_action.setToolTip(
            "Use frameless window for maximum screen space (requires restart)"
        )
        settings = QSettings("ViloxTerm", "ViloxTerm")
        frameless_action.setChecked(settings.value("UI/FramelessMode", False, type=bool))
        frameless_action.triggered.connect(
            lambda: self.main_window.execute_command("window.toggleFrameless")
        )
        view_menu.addAction(frameless_action)

        # Debug menu
        debug_menu = menubar.addMenu("Debug")

        # Reset app state action (now using commands)
        reset_state_action = QAction("Reset App State", self.main_window)
        # Shortcut handled by command system, not QAction
        reset_state_action.setToolTip(
            "Reset application to default state, clearing all saved settings (Ctrl+Shift+R)"
        )
        reset_state_action.triggered.connect(
            lambda: self.main_window.execute_command("debug.resetAppState")
        )
        debug_menu.addAction(reset_state_action)

        # Help menu
        help_menu = menubar.addMenu("Help")

        # Documentation action
        docs_action = QAction("Documentation", self.main_window)
        docs_action.setToolTip("Open ViloxTerm documentation")
        docs_action.triggered.connect(
            lambda: self.main_window.execute_command("help.documentation")
        )
        help_menu.addAction(docs_action)

        # Report issue action
        issue_action = QAction("Report Issue", self.main_window)
        issue_action.setToolTip("Report an issue on GitHub")
        issue_action.triggered.connect(lambda: self.main_window.execute_command("help.reportIssue"))
        help_menu.addAction(issue_action)

        help_menu.addSeparator()

        # Check for updates action
        updates_action = QAction("Check for Updates...", self.main_window)
        updates_action.setToolTip("Check for ViloxTerm updates")
        updates_action.triggered.connect(
            lambda: self.main_window.execute_command("help.checkForUpdates")
        )
        help_menu.addAction(updates_action)

        help_menu.addSeparator()

        # About action (also in Help menu)
        about_help_action = QAction("About ViloxTerm", self.main_window)
        about_help_action.setToolTip("Show information about ViloxTerm")
        about_help_action.triggered.connect(lambda: self.main_window.execute_command("help.about"))
        help_menu.addAction(about_help_action)

    def toggle_theme(self):
        """Toggle application theme - now routes through command system."""
        return self.main_window.execute_command("view.toggleTheme")

    def toggle_menu_bar(self):
        """Toggle menu bar visibility - now routes through command system."""
        return self.main_window.execute_command("view.toggleMenuBar")

    def on_auto_hide_menubar_toggled(self, checked: bool):
        """Handle the 'Use Activity Bar Menu' toggle."""
        if checked:
            # Hide menu bar when using activity bar menu
            self.main_window.menuBar().setVisible(False)
        else:
            # Show menu bar when not using activity bar menu
            self.main_window.menuBar().setVisible(True)

        # Save preference
        settings = QSettings()
        settings.setValue("MainWindow/useActivityBarMenu", checked)

    def reset_app_state(self):
        """Reset application to default state - now routes through command system."""
        return self.main_window.execute_command("debug.resetAppState")

    def reset_app_state_legacy(self):
        """Legacy reset method - kept for reference."""
        reply = QMessageBox.question(
            self.main_window,
            "Reset Application State",
            "This will reset the application to its default state and clear all saved settings including:\n\n"
            "• Window size and position\n"
            "• Split pane layouts\n"
            "• Menu bar visibility\n"
            "• Active pane selections\n\n"
            "The application will be restarted with default settings.\n\n"
            "Are you sure you want to continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            try:
                # Clear all saved settings
                settings = QSettings()
                settings.clear()

                # Show success message
                self.main_window.status_bar.set_message(
                    "Application state reset successfully", 3000
                )

                # Reset to default state immediately
                self._reset_to_defaults()

            except Exception as e:
                QMessageBox.critical(
                    self.main_window,
                    "Reset Failed",
                    f"Failed to reset application state:\n{str(e)}",
                )

    def _reset_to_defaults(self):
        """Reset current application state to defaults without restarting."""
        try:
            # Reset window to default size and center it
            self.main_window.resize(1200, 800)

            # Center window on screen
            screen = self.main_window.screen().geometry()
            window_geometry = self.main_window.geometry()
            x = (screen.width() - window_geometry.width()) // 2
            y = (screen.height() - window_geometry.height()) // 2
            self.main_window.move(x, y)

            # Reset splitter to default sizes (sidebar: 250px, workspace: rest)
            self.main_window.main_splitter.setSizes([250, 950])

            # Ensure menu bar is visible
            self.main_window.menuBar().setVisible(True)

            # Ensure sidebar is visible and expanded
            if self.main_window.sidebar.is_collapsed:
                self.main_window.sidebar.expand()

            # Reset workspace to default single pane layout
            self.main_window.workspace.reset_to_default_layout()

            # Reset theme to system default
            icon_manager = get_icon_manager()
            icon_manager.detect_system_theme()

            self.main_window.status_bar.set_message("Application reset to default state", 2000)

        except Exception as e:
            QMessageBox.warning(
                self.main_window,
                "Reset Warning",
                f"Some settings could not be reset:\n{str(e)}",
            )
