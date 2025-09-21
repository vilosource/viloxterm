"""Layout management for the main window."""

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QSplitter, QWidget

from viloapp.ui.activity_bar import ActivityBar
from viloapp.ui.qt_compat import safe_splitter_collapse_setting
from viloapp.ui.sidebar import Sidebar
from viloapp.ui.status_bar import AppStatusBar
from viloapp.ui.workspace import Workspace


class MainWindowLayoutManager:
    """Manages the layout components of the main window."""

    def __init__(self, main_window):
        """Initialize the layout manager."""
        self.main_window = main_window
        self.activity_bar = None
        self.sidebar = None
        self.workspace = None
        self.status_bar = None
        self.main_splitter = None

    def setup_ui_layout(self):
        """Initialize the UI components and layout."""
        # Create central widget and main layout
        central_widget = QWidget()
        self.main_window.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Create activity bar
        self.activity_bar = ActivityBar()
        self.activity_bar.view_changed.connect(
            self.main_window.on_activity_view_changed
        )
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

        # Allow sidebar to be completely collapsed
        safe_splitter_collapse_setting(self.main_splitter, True)

        # Create status bar
        self.status_bar = AppStatusBar()
        self.main_window.setStatusBar(self.status_bar)

        # Connect signals
        self.activity_bar.toggle_sidebar.connect(self.toggle_sidebar)

        # Store references in main window
        self.main_window.activity_bar = self.activity_bar
        self.main_window.sidebar = self.sidebar
        self.main_window.workspace = self.workspace
        self.main_window.status_bar = self.status_bar
        self.main_window.main_splitter = self.main_splitter

    def on_activity_view_changed(self, view_name: str):
        """Handle activity bar view selection."""
        self.sidebar.set_current_view(view_name)
        if self.sidebar.is_collapsed:
            self.sidebar.expand()
            # Ensure splitter sizes are updated
            self.main_splitter.setSizes([250, self.main_splitter.width() - 250])
            # Update activity bar to reflect that sidebar is now visible
            self.activity_bar.set_sidebar_visible(True)

    def toggle_sidebar(self):
        """Toggle sidebar visibility."""
        self.sidebar.toggle()

        # Update splitter sizes when sidebar toggles
        if self.sidebar.is_collapsed:
            # Sidebar is now completely hidden (0 width)
            self.main_splitter.setSizes([0, self.main_splitter.width()])
            # Update activity bar to show current view as unchecked
            self.activity_bar.set_sidebar_visible(False)
        else:
            # Sidebar is now expanded
            self.main_splitter.setSizes([250, self.main_splitter.width() - 250])
            # Update activity bar to show current view as checked
            self.activity_bar.set_sidebar_visible(True)

    def toggle_activity_bar(self) -> bool:
        """Toggle activity bar visibility and adjust layout."""
        # Toggle visibility
        is_visible = not self.activity_bar.isVisible()
        self.activity_bar.setVisible(is_visible)

        # Adjust the main layout
        if is_visible:
            # Activity bar is now visible - restore normal layout
            self.activity_bar.show()
            # If sidebar was visible before, ensure it's properly sized
            if not self.sidebar.is_collapsed:
                self.main_splitter.setSizes([250, self.main_splitter.width() - 250])
        else:
            # Activity bar is now hidden - expand main content
            self.activity_bar.hide()
            # Optionally hide sidebar too when activity bar is hidden
            if not self.sidebar.is_collapsed:
                self.sidebar.collapse()
                self.main_splitter.setSizes([0, self.main_splitter.width()])

        return is_visible

    def setup_theme(self):
        """Setup theme system and apply initial theme."""
        try:
            from viloapp.services.theme_service import ThemeService

            # Get theme provider from service locator
            theme_service = self.main_window.service_locator.get(ThemeService)
            self.main_window.theme_provider = (
                theme_service.get_theme_provider() if theme_service else None
            )
            if not self.main_window.theme_provider:
                print("Warning: ThemeProvider not available")
                return

            # Connect to theme changes
            self.main_window.theme_provider.style_changed.connect(self.apply_theme)

            # Apply initial theme
            self.apply_theme()

            import logging

            logger = logging.getLogger(__name__)
            logger.info("Theme system initialized")
        except Exception as e:
            print(f"Failed to setup theme: {e}")
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"Failed to setup theme: {e}")

    def apply_theme(self):
        """Apply current theme to all components."""
        if not hasattr(self.main_window, "theme_provider"):
            return

        try:
            # Apply main window theme
            self.main_window.setStyleSheet(
                self.main_window.theme_provider.get_stylesheet("main_window")
                + self.main_window.theme_provider.get_stylesheet("menu")
            )

            # Apply splitter theme
            self.main_splitter.setStyleSheet(
                self.main_window.theme_provider.get_stylesheet("splitter")
            )

            # Let each component apply its own theme
            if self.activity_bar:
                self.activity_bar.apply_theme()
            if self.sidebar:
                self.sidebar.apply_theme()
            if self.workspace:
                self.workspace.apply_theme()
            if self.status_bar:
                self.status_bar.apply_theme()

            import logging

            logger = logging.getLogger(__name__)
            logger.debug("Theme applied to all components")
        except Exception as e:
            print(f"Failed to apply theme: {e}")
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"Failed to apply theme: {e}")
