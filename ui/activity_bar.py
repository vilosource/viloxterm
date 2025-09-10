"""Activity bar implementation with icon buttons."""

from PySide6.QtWidgets import QToolBar, QWidget
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QAction, QIcon
from ui.icon_manager import get_icon_manager
from ui.vscode_theme import *


class ActivityBar(QToolBar):
    """Vertical activity bar with icon buttons like VSCode."""
    
    view_changed = Signal(str)  # Emitted when a view is selected
    toggle_sidebar = Signal()   # Emitted when sidebar toggle is requested
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        self.current_view = "explorer"
        
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
        
        # Style the activity bar with VSCode theme
        self.setObjectName("activityBar")
        self.setProperty("type", "activitybar")  # For QtVSCodeStyle
        
        # Apply activity bar styling with light icons
        self.setStyleSheet(f"""
            QToolBar#activityBar {{
                background-color: {ACTIVITY_BAR_BACKGROUND};
                border: none;
                padding: 5px 0;
            }}
            QToolBar#activityBar QToolButton {{
                background-color: transparent;
                border: none;
                padding: 8px;
                margin: 2px 0;
            }}
            QToolBar#activityBar QToolButton:hover {{
                background-color: rgba(255, 255, 255, 0.1);
            }}
            QToolBar#activityBar QToolButton:checked {{
                background-color: rgba(255, 255, 255, 0.15);
                border-left: 2px solid {ACTIVITY_BAR_ACTIVE_BORDER};
            }}
            QToolBar#activityBar QToolButton:pressed {{
                background-color: rgba(255, 255, 255, 0.2);
            }}
        """)
        
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
        self.explorer_action.triggered.connect(lambda: self.on_action_clicked("explorer"))
        self.addAction(self.explorer_action)
        
        # Search action
        self.search_action = QAction(icon_manager.get_icon("search"), "Search", self)
        self.search_action.setCheckable(True)
        self.search_action.setToolTip("Search (Ctrl+Shift+F)")
        self.search_action.triggered.connect(lambda: self.on_action_clicked("search"))
        self.addAction(self.search_action)
        
        # Git action
        self.git_action = QAction(icon_manager.get_icon("git"), "Git", self)
        self.git_action.setCheckable(True)
        self.git_action.setToolTip("Source Control (Ctrl+Shift+G)")
        self.git_action.triggered.connect(lambda: self.on_action_clicked("git"))
        self.addAction(self.git_action)
        
        # Add separator
        self.addSeparator()
        
        # Settings action
        self.settings_action = QAction(icon_manager.get_icon("settings"), "Settings", self)
        self.settings_action.setCheckable(True)
        self.settings_action.setToolTip("Settings (Ctrl+,)")
        self.settings_action.triggered.connect(lambda: self.on_action_clicked("settings"))
        self.addAction(self.settings_action)
        
        # Group actions for easy access
        self.view_actions = [
            self.explorer_action,
            self.search_action,
            self.git_action,
            self.settings_action
        ]
        
    def on_action_clicked(self, view_name: str):
        """Handle action click - manually manage checked states.
        
        This method completely controls the checked state of actions
        to avoid Qt's automatic toggling behavior that causes the triple-click bug.
        """
        # Get the clicked action
        clicked_action = None
        for action in self.view_actions:
            if action.text().lower() == view_name:
                clicked_action = action
                break
        
        if not clicked_action:
            return
        
        # Get current checked state (Qt has already toggled it)
        is_now_checked = clicked_action.isChecked()
        
        if view_name == self.current_view:
            # Same view clicked - this is a toggle request
            # The checked state has already been toggled by Qt
            # Just emit the toggle signal
            self.toggle_sidebar.emit()
        else:
            # Different view clicked - switch views
            # First, uncheck all actions
            for action in self.view_actions:
                action.blockSignals(True)
                action.setChecked(False)
                action.blockSignals(False)
            
            # Check the clicked action
            clicked_action.blockSignals(True)
            clicked_action.setChecked(True)
            clicked_action.blockSignals(False)
            
            # Update current view
            self.current_view = view_name
            
            # Emit view change signal
            self.view_changed.emit(view_name)
            
    def set_sidebar_visible(self, visible: bool):
        """Update the current action's checked state based on sidebar visibility."""
        # Find the action for the current view
        for action in self.view_actions:
            if action.text().lower() == self.current_view:
                # Block signals to prevent triggering on_view_selected
                action.blockSignals(True)
                action.setChecked(visible)
                action.blockSignals(False)
                break
    
    def update_icons(self):
        """Update icons when theme changes."""
        icon_manager = get_icon_manager()
        self.explorer_action.setIcon(icon_manager.get_icon("explorer"))
        self.search_action.setIcon(icon_manager.get_icon("search"))
        self.git_action.setIcon(icon_manager.get_icon("git"))
        self.settings_action.setIcon(icon_manager.get_icon("settings"))