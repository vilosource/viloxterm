"""Action handlers and menu setup for the main window."""

from PySide6.QtCore import QSettings
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMessageBox

from ui.icon_manager import get_icon_manager


class MainWindowActionManager:
    """Manages actions and menu setup for the main window."""

    def __init__(self, main_window):
        """Initialize the action manager."""
        self.main_window = main_window

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
        new_tab_action.triggered.connect(lambda: self.main_window.execute_command("workspace.newTab"))
        file_menu.addAction(new_tab_action)

        new_tab_with_type_action = QAction("New Tab (Choose Type)...", self.main_window)
        new_tab_with_type_action.setToolTip("Create a new tab with specific type (Ctrl+Shift+T)")
        new_tab_with_type_action.triggered.connect(lambda: self.main_window.execute_command("workspace.newTabWithType"))
        file_menu.addAction(new_tab_with_type_action)

        file_menu.addSeparator()

        # Preferences/Settings menu
        preferences_menu = file_menu.addMenu("Preferences")

        # Settings action
        settings_action = QAction("Settings...", self.main_window)
        settings_action.setToolTip("Configure application settings and defaults (Ctrl+,)")
        settings_action.triggered.connect(lambda: self.main_window.execute_command("settings.openSettings"))
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

        # View menu
        view_menu = menubar.addMenu("View")

        # Theme selection action (now using new theme system)
        theme_action = QAction("Select Theme", self.main_window)
        # Shortcut handled by command system, not QAction
        theme_action.setToolTip("Select a color theme (Ctrl+K, Ctrl+T)")
        theme_action.triggered.connect(lambda: self.main_window.execute_command("theme.selectTheme"))
        view_menu.addAction(theme_action)

        # Theme Editor action
        theme_editor_action = QAction("Theme Editor...", self.main_window)
        theme_editor_action.setToolTip("Open the theme editor to customize themes (Ctrl+K, Ctrl+M)")
        theme_editor_action.triggered.connect(lambda: self.main_window.execute_command("theme.openEditor"))
        view_menu.addAction(theme_editor_action)

        view_menu.addSeparator()

        # Import VSCode Theme action
        import_vscode_theme_action = QAction("Import VSCode Theme...", self.main_window)
        import_vscode_theme_action.setToolTip("Import a theme from VSCode JSON format")
        import_vscode_theme_action.triggered.connect(lambda: self.main_window.execute_command("theme.importVSCode"))
        view_menu.addAction(import_vscode_theme_action)

        # Sidebar toggle action (now using commands)
        sidebar_action = QAction("Toggle Sidebar", self.main_window)
        # Shortcut handled by command system, not QAction
        sidebar_action.setToolTip("Toggle sidebar visibility (Ctrl+B)")
        sidebar_action.triggered.connect(lambda: self.main_window.execute_command("view.toggleSidebar"))
        view_menu.addAction(sidebar_action)

        view_menu.addSeparator()

        # Split actions (now using commands)
        split_horizontal_action = QAction("Split Pane Right", self.main_window)
        # Shortcut handled by command system, not QAction
        split_horizontal_action.setToolTip("Split the active pane horizontally (Ctrl+\\)")
        split_horizontal_action.triggered.connect(lambda: self.main_window.execute_command("workbench.action.splitRight"))
        view_menu.addAction(split_horizontal_action)

        split_vertical_action = QAction("Split Pane Down", self.main_window)
        # Shortcut handled by command system, not QAction
        split_vertical_action.setToolTip("Split the active pane vertically (Ctrl+Shift+\\)")
        split_vertical_action.triggered.connect(lambda: self.main_window.execute_command("workbench.action.splitDown"))
        view_menu.addAction(split_vertical_action)

        close_pane_action = QAction("Close Pane", self.main_window)
        # Shortcut handled by command system, not QAction
        close_pane_action.setToolTip("Close the active pane (Ctrl+W)")
        close_pane_action.triggered.connect(lambda: self.main_window.execute_command("workbench.action.closeActivePane"))
        view_menu.addAction(close_pane_action)

        view_menu.addSeparator()

        # Menu bar toggle action (shortcut handled by global QShortcut)
        self.main_window.menubar_action = QAction("Toggle Menu Bar", self.main_window)
        self.main_window.menubar_action.setToolTip("Toggle menu bar visibility (Ctrl+Shift+M)")
        self.main_window.menubar_action.triggered.connect(lambda: self.main_window.execute_command("view.toggleMenuBar"))
        view_menu.addAction(self.main_window.menubar_action)

        # Auto-hide menu bar option
        self.main_window.auto_hide_menubar_action = QAction("Use Activity Bar Menu", self.main_window)
        self.main_window.auto_hide_menubar_action.setCheckable(True)
        self.main_window.auto_hide_menubar_action.setToolTip("Hide menu bar and use activity bar menu icon instead")
        self.main_window.auto_hide_menubar_action.toggled.connect(self.on_auto_hide_menubar_toggled)
        view_menu.addAction(self.main_window.auto_hide_menubar_action)

        view_menu.addSeparator()

        # Frameless mode toggle
        frameless_action = QAction("Frameless Mode", self.main_window)
        frameless_action.setCheckable(True)
        frameless_action.setToolTip("Use frameless window for maximum screen space (requires restart)")
        settings = QSettings("ViloxTerm", "ViloxTerm")
        frameless_action.setChecked(settings.value("UI/FramelessMode", False, type=bool))
        frameless_action.triggered.connect(lambda: self.main_window.execute_command("window.toggleFrameless"))
        view_menu.addAction(frameless_action)

        # Debug menu
        debug_menu = menubar.addMenu("Debug")

        # Reset app state action (now using commands)
        reset_state_action = QAction("Reset App State", self.main_window)
        # Shortcut handled by command system, not QAction
        reset_state_action.setToolTip("Reset application to default state, clearing all saved settings (Ctrl+Shift+R)")
        reset_state_action.triggered.connect(lambda: self.main_window.execute_command("debug.resetAppState"))
        debug_menu.addAction(reset_state_action)

        # Help menu
        help_menu = menubar.addMenu("Help")

        # Documentation action
        docs_action = QAction("Documentation", self.main_window)
        docs_action.setToolTip("Open ViloxTerm documentation")
        docs_action.triggered.connect(lambda: self.main_window.execute_command("help.documentation"))
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
        updates_action.triggered.connect(lambda: self.main_window.execute_command("help.checkForUpdates"))
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
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                # Clear all saved settings
                settings = QSettings()
                settings.clear()

                # Show success message
                self.main_window.status_bar.set_message("Application state reset successfully", 3000)

                # Reset to default state immediately
                self._reset_to_defaults()

            except Exception as e:
                QMessageBox.critical(
                    self.main_window,
                    "Reset Failed",
                    f"Failed to reset application state:\n{str(e)}"
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
                f"Some settings could not be reset:\n{str(e)}"
            )
