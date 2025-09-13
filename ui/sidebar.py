"""Collapsible sidebar implementation."""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget, QLabel
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, Signal


class Sidebar(QWidget):
    """Collapsible sidebar with multiple views."""
    
    def __init__(self):
        super().__init__()
        self.is_collapsed = False
        self.expanded_width = 250
        self.setup_ui()
        self.setup_animation()
        
    def setup_ui(self):
        """Initialize the sidebar UI."""
        self.setObjectName("sidebar")
        self.setMinimumWidth(0)
        self.setMaximumWidth(self.expanded_width)

        # Apply theme
        self.apply_theme()

        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create stacked widget for different views
        self.stack = QStackedWidget()
        layout.addWidget(self.stack)
        
        # Create view panels
        self.create_views()
        
    def create_views(self):
        """Create the different sidebar views."""
        # Explorer view
        self.explorer_view = QWidget()
        explorer_layout = QVBoxLayout(self.explorer_view)
        explorer_layout.addWidget(QLabel("Explorer"))
        explorer_layout.addStretch()
        self.stack.addWidget(self.explorer_view)
        
        # Search view
        self.search_view = QWidget()
        search_layout = QVBoxLayout(self.search_view)
        search_layout.addWidget(QLabel("Search"))
        search_layout.addStretch()
        self.stack.addWidget(self.search_view)
        
        # Git view
        self.git_view = QWidget()
        git_layout = QVBoxLayout(self.git_view)
        git_layout.addWidget(QLabel("Source Control"))
        git_layout.addStretch()
        self.stack.addWidget(self.git_view)
        
        # Settings view
        self.settings_view = QWidget()
        settings_layout = QVBoxLayout(self.settings_view)
        settings_layout.addWidget(QLabel("Settings"))
        settings_layout.addStretch()
        self.stack.addWidget(self.settings_view)
        
        # Map view names to indices
        self.view_indices = {
            "explorer": 0,
            "search": 1,
            "git": 2,
            "settings": 3
        }
        
    def setup_animation(self):
        """Setup collapse/expand animation."""
        self.animation = QPropertyAnimation(self, b"maximumWidth")
        self.animation.setDuration(200)
        self.animation.setEasingCurve(QEasingCurve.InOutCubic)
        
    def set_current_view(self, view_name: str):
        """Switch to a specific view."""
        if view_name in self.view_indices:
            self.stack.setCurrentIndex(self.view_indices[view_name])
            
    def toggle(self):
        """Toggle between collapsed and expanded state."""
        if self.is_collapsed:
            self.expand()
        else:
            self.collapse()
            
    def collapse(self):
        """Collapse the sidebar."""
        if not self.is_collapsed:
            self.animation.setStartValue(self.width())
            self.animation.setEndValue(0)
            self.animation.start()
            self.is_collapsed = True
            
    def expand(self):
        """Expand the sidebar."""
        if self.is_collapsed:
            self.animation.setStartValue(0)
            self.animation.setEndValue(self.expanded_width)
            self.animation.start()
            self.is_collapsed = False

    def apply_theme(self):
        """Apply current theme to sidebar."""
        from services.service_locator import ServiceLocator
        from services.theme_service import ThemeService

        locator = ServiceLocator.get_instance()
        theme_service = locator.get(ThemeService)
        theme_provider = theme_service.get_theme_provider() if theme_service else None
        if theme_provider:
            self.setStyleSheet(theme_provider.get_stylesheet("sidebar"))