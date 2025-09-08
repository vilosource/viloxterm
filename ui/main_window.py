"""Main window implementation for the VSCode-style application."""

from PySide6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QSplitter, QMenuBar
from PySide6.QtCore import Qt, QSettings
from PySide6.QtGui import QAction, QKeySequence, QShortcut
from ui.activity_bar import ActivityBar
from ui.sidebar import Sidebar
from ui.workspace import Workspace
from ui.status_bar import AppStatusBar
from ui.icon_manager import get_icon_manager


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
        
        # Menu bar toggle action (shortcut handled by global QShortcut)
        self.menubar_action = QAction("Toggle Menu Bar", self)
        self.menubar_action.setToolTip("Toggle menu bar visibility (Ctrl+Shift+M)")
        self.menubar_action.triggered.connect(self.toggle_menu_bar)
        view_menu.addAction(self.menubar_action)
        
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
        
    def closeEvent(self, event):
        """Save state before closing."""
        self.save_state()
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