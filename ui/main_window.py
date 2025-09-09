"""Main window implementation for the VSCode-style application."""

from PySide6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QSplitter, QMenuBar, QMessageBox
from PySide6.QtCore import Qt, QSettings
from PySide6.QtGui import QAction, QKeySequence, QShortcut
from ui.activity_bar import ActivityBar
from ui.sidebar import Sidebar
from ui.workspace_simple import Workspace  # Using new tab-based workspace
from ui.status_bar import AppStatusBar
from ui.icon_manager import get_icon_manager
from ui.vscode_theme import *


class MainWindow(QMainWindow):
    """Main application window with VSCode-style layout."""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.restore_state()
        
    def setup_ui(self):
        """Initialize the UI components."""
        self.setWindowTitle("ViloApp")
        self.resize(1200, 800)
        
        # Apply VSCode theme to main window
        self.setStyleSheet(get_main_window_stylesheet() + get_menu_stylesheet())
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create activity bar
        self.activity_bar = ActivityBar()
        self.activity_bar.view_changed.connect(self.on_activity_view_changed)
        main_layout.addWidget(self.activity_bar)
        
        # Create main splitter for sidebar and workspace
        self.main_splitter = QSplitter(Qt.Horizontal)
        self.main_splitter.setStyleSheet(get_splitter_stylesheet())
        main_layout.addWidget(self.main_splitter)
        
        # Create sidebar
        self.sidebar = Sidebar()
        self.main_splitter.addWidget(self.sidebar)
        
        # Create workspace
        self.workspace = Workspace()
        self.main_splitter.addWidget(self.workspace)
        
        # Set initial splitter sizes (sidebar: 250px, workspace: rest)
        self.main_splitter.setSizes([250, 950])
        
        # Create status bar
        self.status_bar = AppStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Create menu bar
        self.create_menu_bar()
        
        # Connect signals
        self.activity_bar.toggle_sidebar.connect(self.toggle_sidebar)
        
        # Create global shortcuts that work even when menu bar is hidden
        self.menu_toggle_shortcut = QShortcut(QKeySequence("Ctrl+Shift+M"), self)
        self.menu_toggle_shortcut.activated.connect(self.toggle_menu_bar)
        
    def create_menu_bar(self):
        """Create the menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        # New tab actions
        new_editor_tab_action = QAction("New Editor Tab", self)
        new_editor_tab_action.setShortcut(QKeySequence("Ctrl+N"))
        new_editor_tab_action.setToolTip("Create a new editor tab (Ctrl+N)")
        new_editor_tab_action.triggered.connect(lambda: self.workspace.add_editor_tab("New Editor"))
        file_menu.addAction(new_editor_tab_action)
        
        new_terminal_tab_action = QAction("New Terminal Tab", self)
        new_terminal_tab_action.setShortcut(QKeySequence("Ctrl+`"))
        new_terminal_tab_action.setToolTip("Create a new terminal tab (Ctrl+`)")
        new_terminal_tab_action.triggered.connect(lambda: self.workspace.add_terminal_tab("Terminal"))
        file_menu.addAction(new_terminal_tab_action)
        
        file_menu.addSeparator()
        
        # View menu
        view_menu = menubar.addMenu("View")
        
        # Theme toggle action
        icon_manager = get_icon_manager()
        theme_action = QAction("Toggle Theme", self)
        theme_action.setShortcut(QKeySequence("Ctrl+T"))
        theme_action.setToolTip("Toggle between light and dark theme (Ctrl+T)")
        theme_action.triggered.connect(self.toggle_theme)
        view_menu.addAction(theme_action)
        
        # Sidebar toggle action
        sidebar_action = QAction("Toggle Sidebar", self)
        sidebar_action.setShortcut(QKeySequence("Ctrl+B"))
        sidebar_action.setToolTip("Toggle sidebar visibility (Ctrl+B)")
        sidebar_action.triggered.connect(self.toggle_sidebar)
        view_menu.addAction(sidebar_action)
        
        view_menu.addSeparator()
        
        # Split actions
        split_horizontal_action = QAction("Split Pane Right", self)
        split_horizontal_action.setShortcut(QKeySequence("Ctrl+\\"))
        split_horizontal_action.setToolTip("Split the active pane horizontally (Ctrl+\\)")
        split_horizontal_action.triggered.connect(self.workspace.split_active_pane_horizontal)
        view_menu.addAction(split_horizontal_action)
        
        split_vertical_action = QAction("Split Pane Down", self)
        split_vertical_action.setShortcut(QKeySequence("Ctrl+Shift+\\"))
        split_vertical_action.setToolTip("Split the active pane vertically (Ctrl+Shift+\\)")
        split_vertical_action.triggered.connect(self.workspace.split_active_pane_vertical)
        view_menu.addAction(split_vertical_action)
        
        close_pane_action = QAction("Close Pane", self)
        close_pane_action.setShortcut(QKeySequence("Ctrl+W"))
        close_pane_action.setToolTip("Close the active pane (Ctrl+W)")
        close_pane_action.triggered.connect(self.workspace.close_active_pane)
        view_menu.addAction(close_pane_action)
        
        view_menu.addSeparator()
        
        # Menu bar toggle action (shortcut handled by global QShortcut)
        self.menubar_action = QAction("Toggle Menu Bar", self)
        self.menubar_action.setToolTip("Toggle menu bar visibility (Ctrl+Shift+M)")
        self.menubar_action.triggered.connect(self.toggle_menu_bar)
        view_menu.addAction(self.menubar_action)
        
        # Debug menu
        debug_menu = menubar.addMenu("Debug")
        
        # Reset app state action
        reset_state_action = QAction("Reset App State", self)
        reset_state_action.setShortcut(QKeySequence("Ctrl+Shift+R"))
        reset_state_action.setToolTip("Reset application to default state, clearing all saved settings (Ctrl+Shift+R)")
        reset_state_action.triggered.connect(self.reset_app_state)
        debug_menu.addAction(reset_state_action)
        
    def toggle_theme(self):
        """Toggle application theme."""
        icon_manager = get_icon_manager()
        icon_manager.toggle_theme()
        
        # Update status bar
        current_theme = icon_manager.theme.capitalize()
        self.status_bar.set_message(f"Switched to {current_theme} theme", 2000)
        
    def toggle_menu_bar(self):
        """Toggle menu bar visibility."""
        menubar = self.menuBar()
        if menubar.isVisible():
            menubar.hide()
            self.status_bar.set_message("Menu bar hidden. Press Ctrl+Shift+M to show", 3000)
        else:
            menubar.show()
            self.status_bar.set_message("Menu bar shown", 2000)
        
    def on_activity_view_changed(self, view_name: str):
        """Handle activity bar view selection."""
        self.sidebar.set_current_view(view_name)
        if self.sidebar.is_collapsed:
            self.sidebar.expand()
            
    def toggle_sidebar(self):
        """Toggle sidebar visibility."""
        self.sidebar.toggle()
        
        # Update splitter sizes when sidebar toggles
        if self.sidebar.is_collapsed:
            # Sidebar is now collapsed
            self.main_splitter.setSizes([0, self.main_splitter.width()])
        else:
            # Sidebar is now expanded
            self.main_splitter.setSizes([250, self.main_splitter.width() - 250])
        
    def reset_app_state(self):
        """Reset application to default state, clearing all saved settings."""
        reply = QMessageBox.question(
            self,
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
                self.status_bar.set_message("Application state reset successfully", 3000)
                
                # Reset to default state immediately
                self._reset_to_defaults()
                
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Reset Failed",
                    f"Failed to reset application state:\n{str(e)}"
                )
                
    def _reset_to_defaults(self):
        """Reset current application state to defaults without restarting."""
        try:
            # Reset window to default size and center it
            self.resize(1200, 800)
            
            # Center window on screen
            screen = self.screen().geometry()
            window_geometry = self.geometry()
            x = (screen.width() - window_geometry.width()) // 2
            y = (screen.height() - window_geometry.height()) // 2
            self.move(x, y)
            
            # Reset splitter to default sizes (sidebar: 250px, workspace: rest)
            self.main_splitter.setSizes([250, 950])
            
            # Ensure menu bar is visible
            self.menuBar().setVisible(True)
            
            # Ensure sidebar is visible and expanded
            if self.sidebar.is_collapsed:
                self.sidebar.expand()
                
            # Reset workspace to default single pane layout
            self.workspace.reset_to_default_layout()
            
            # Reset theme to system default
            icon_manager = get_icon_manager()
            icon_manager.detect_system_theme()
            
            self.status_bar.set_message("Application reset to default state", 2000)
            
        except Exception as e:
            QMessageBox.warning(
                self,
                "Reset Warning", 
                f"Some settings could not be reset:\n{str(e)}"
            )
        
    def closeEvent(self, event):
        """Save state and clean up resources before closing."""
        self.save_state()
        
        # Clean up all terminal sessions before closing
        from ui.terminal.terminal_server import terminal_server
        terminal_server.cleanup_all_sessions()
        
        event.accept()
        
    def save_state(self):
        """Save window state and geometry."""
        settings = QSettings()
        settings.beginGroup("MainWindow")
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("windowState", self.saveState())
        settings.setValue("splitterSizes", self.main_splitter.saveState())
        settings.setValue("menuBarVisible", self.menuBar().isVisible())
        settings.endGroup()
        
        # Save workspace state (new tab-based workspace)
        settings.beginGroup("Workspace")
        workspace_state = self.workspace.save_state()
        import json
        settings.setValue("state", json.dumps(workspace_state))
        settings.endGroup()
        
    def restore_state(self):
        """Restore window state and geometry."""
        settings = QSettings()
        settings.beginGroup("MainWindow")
        
        geometry = settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
            
        window_state = settings.value("windowState")
        if window_state:
            self.restoreState(window_state)
            
        splitter_state = settings.value("splitterSizes")
        if splitter_state:
            self.main_splitter.restoreState(splitter_state)
            
        # Restore menu bar visibility
        menu_visible = settings.value("menuBarVisible", True, type=bool)
        self.menuBar().setVisible(menu_visible)
            
        settings.endGroup()
        
        # Restore workspace state (new tab-based workspace)
        settings.beginGroup("Workspace")
        workspace_state_json = settings.value("state")
        if workspace_state_json:
            try:
                import json
                workspace_state = json.loads(workspace_state_json)
                self.workspace.restore_state(workspace_state)
            except (json.JSONDecodeError, Exception) as e:
                # If restoration fails, workspace will create default tab
                print(f"Failed to restore workspace state: {e}")
        settings.endGroup()