#!/usr/bin/env python3
"""
New workspace implementation using the Model-View-Command architecture.
This replaces the old workspace.py with a clean integration.
"""

import logging
from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QTabWidget, QVBoxLayout, QWidget

# Import our new architecture
from viloapp.core.commands.base import CommandContext
from viloapp.core.commands.registry import CommandRegistry
from viloapp.models.workspace_model import WidgetType, WorkspaceModel
from viloapp.ui.workspace_view import TabView

logger = logging.getLogger(__name__)


class Workspace(QWidget):
    """
    New workspace using Model-View-Command architecture.

    This is a thin integration layer that connects the new architecture
    to the existing application structure.
    """

    # Signals for compatibility with existing code
    tab_changed = Signal(int)
    tab_added = Signal(str)
    tab_removed = Signal(str)
    active_pane_changed = Signal(str, str)
    layout_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        # Initialize the new architecture
        self.model = WorkspaceModel()
        self.command_registry = CommandRegistry()

        # Subscribe to model changes
        self.model.add_observer(self._on_model_change)

        # UI components
        self.tab_widget = None
        self.tab_views = {}  # tab_id -> TabView

        self.setup_ui()
        self.create_default_tab()
        self._setup_theme_observer()

    def setup_ui(self):
        """Initialize the workspace UI."""
        self.setObjectName("workspace")

        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Create tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setMovable(True)
        self.tab_widget.setDocumentMode(False)  # Disabled to allow custom tab height
        self.tab_widget.setElideMode(Qt.ElideRight)

        # Ensure tab bar is visible and apply compact style
        tab_bar = self.tab_widget.tabBar()
        tab_bar.setVisible(True)

        # Apply a compact stylesheet directly to the tab bar
        tab_bar.setStyleSheet(
            """
            QTabBar {
                max-height: 24px;
                background-color: #252526;
            }
            QTabBar::tab {
                height: 22px;
                padding: 1px 8px;
                margin: 0;
                background-color: #2d2d30;  /* Inactive tab - darker */
                color: #969696;
            }
            QTabBar::tab:selected {
                background-color: #1e1e1e;  /* Active tab - matches editor */
                color: #ffffff;
            }
            QTabBar::tab:hover:!selected {
                background-color: #353536;
            }
        """
        )

        # Style the tab widget pane with border matching active tab
        self.tab_widget.setStyleSheet(
            """
            QTabWidget::pane {
                border: 1px solid #1e1e1e;  /* Same as active tab background */
                background-color: #1e1e1e;
            }
            """
        )

        # Connect tab widget signals
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
        self.tab_widget.tabCloseRequested.connect(self._on_tab_close_requested)

        layout.addWidget(self.tab_widget)

    def create_default_tab(self):
        """Create the default tab on startup."""
        logger.info("Creating default tab...")
        context = CommandContext(model=self.model)
        result = self.command_registry.execute(
            "tab.create",
            context,
            name="Terminal",
            widget_type=WidgetType.TERMINAL,
        )
        logger.info(f"Default tab creation result: {result}")

    def _on_model_change(self, event: str, data: Any):
        """Handle model change events."""
        logger.info(f"Model change event: {event}, data: {data}")
        if event == "tab_created":
            self._add_tab_view(data["tab_id"])
        elif event == "tab_closed":
            self._remove_tab_view(data["tab_id"])
        elif event == "tab_switched":
            self._update_active_tab()
        elif event == "pane_split":
            self._refresh_current_tab()
        elif event == "pane_closed":
            self._refresh_current_tab()
        elif event == "pane_focused":
            tab = self.model.state.get_active_tab()
            if tab:
                self.active_pane_changed.emit(tab.name, data.get("pane_id", ""))

        # Emit layout changed for any structural change
        if event in ["tab_created", "tab_closed", "pane_split", "pane_closed"]:
            self.layout_changed.emit()

    def _add_tab_view(self, tab_id: str):
        """Add a new tab view."""
        logger.info(f"Adding tab view for tab_id: {tab_id}")
        tab = self.model._find_tab(tab_id)
        if not tab:
            logger.error(f"Tab not found: {tab_id}")
            return

        logger.info(f"Creating TabView for tab: {tab.name}")

        # Create the view for this tab
        tab_view = TabView(tab, self.command_registry, self.model)
        self.tab_views[tab_id] = tab_view

        # Add to tab widget
        index = self.tab_widget.addTab(tab_view, tab.name)
        logger.info(f"Added tab to widget at index {index}, tab count: {self.tab_widget.count()}")

        # Switch to new tab
        self.tab_widget.setCurrentIndex(index)

        # Emit signal
        self.tab_added.emit(tab.name)

    def _remove_tab_view(self, tab_id: str):
        """Remove a tab view."""
        if tab_id not in self.tab_views:
            return

        tab_view = self.tab_views[tab_id]

        # Find and remove from tab widget
        for i in range(self.tab_widget.count()):
            if self.tab_widget.widget(i) == tab_view:
                self.tab_widget.removeTab(i)
                break

        # Clean up
        tab_name = "Unknown"
        tab = self.model._find_tab(tab_id)
        if tab:
            tab_name = tab.name

        del self.tab_views[tab_id]
        self.tab_removed.emit(tab_name)

    def _refresh_current_tab(self):
        """Refresh the current tab view."""
        tab = self.model.state.get_active_tab()
        if tab and tab.id in self.tab_views:
            # Force a re-render by removing and re-adding
            tab_view = self.tab_views[tab.id]

            # Find current index
            current_index = -1
            for i in range(self.tab_widget.count()):
                if self.tab_widget.widget(i) == tab_view:
                    current_index = i
                    break

            if current_index >= 0:
                # Remove old view
                self.tab_widget.removeTab(current_index)

                # Create new view with updated tree
                new_tab_view = TabView(tab, self.command_registry, self.model)
                self.tab_views[tab.id] = new_tab_view

                # Insert at same position
                self.tab_widget.insertTab(current_index, new_tab_view, tab.name)
                self.tab_widget.setCurrentIndex(current_index)

    def _update_active_tab(self):
        """Update the active tab in the UI."""
        active_tab_id = self.model.state.active_tab_id
        if active_tab_id in self.tab_views:
            tab_view = self.tab_views[active_tab_id]
            for i in range(self.tab_widget.count()):
                if self.tab_widget.widget(i) == tab_view:
                    self.tab_widget.setCurrentIndex(i)
                    break

    def _on_tab_changed(self, index: int):
        """Handle tab change in UI."""
        if index < 0:
            return

        # Get the tab view at this index
        tab_view = self.tab_widget.widget(index)

        # Find which tab this is
        for tab_id, view in self.tab_views.items():
            if view == tab_view:
                # Switch in model
                context = CommandContext(model=self.model)
                self.command_registry.execute("tab.switch", context, tab_id=tab_id)
                break

        self.tab_changed.emit(index)

    def _on_tab_close_requested(self, index: int):
        """Handle tab close request."""
        if index < 0:
            return

        # Don't close last tab
        if self.tab_widget.count() <= 1:
            return

        # Get the tab view at this index
        tab_view = self.tab_widget.widget(index)

        # Find which tab this is
        for tab_id, view in self.tab_views.items():
            if view == tab_view:
                # Close in model
                context = CommandContext(model=self.model)
                self.command_registry.execute("tab.close", context, tab_id=tab_id)
                break

    def _setup_theme_observer(self):
        """Setup theme observer for dynamic theme updates."""
        try:
            from viloapp.services import service_locator
            from viloapp.services.theme_service import ThemeProvider

            theme_service = service_locator.get(ThemeProvider)
            if theme_service:
                theme_service.theme_changed.connect(self.apply_theme)
                # Apply initial theme
                self.apply_theme()
        except ImportError:
            logger.warning("Theme service not available")
        except Exception as e:
            logger.error(f"Failed to setup theme observer: {e}")

    def apply_theme(self):
        """Apply the current theme to the workspace."""
        try:
            from viloapp.services import service_locator
            from viloapp.services.theme_service import ThemeProvider

            theme_service = service_locator.get(ThemeProvider)
            if theme_service:
                stylesheet = theme_service.get_component_style("workspace")
                if stylesheet:
                    self.setStyleSheet(stylesheet)
        except Exception as e:
            logger.error(f"Failed to apply theme: {e}")

    # Compatibility methods for existing code
    def create_new_tab(self, name: str = "New Tab", widget_type: str = "terminal"):
        """Create a new tab (compatibility method)."""
        # Map old widget types to new enum
        type_map = {
            "terminal": WidgetType.TERMINAL,
            "editor": WidgetType.EDITOR,
            "text_editor": WidgetType.EDITOR,
            "output": WidgetType.OUTPUT,
        }

        wtype = type_map.get(widget_type.lower(), WidgetType.TERMINAL)

        context = CommandContext(model=self.model)
        self.command_registry.execute(
            "tab.create",
            context,
            name=name,
            widget_type=wtype,
        )

    def split_pane(self, orientation: str = "horizontal"):
        """Split the current pane (compatibility method)."""
        context = CommandContext(model=self.model)

        # Update context with active items
        tab = self.model.state.get_active_tab()
        if tab:
            context.active_tab_id = tab.id
            pane = tab.get_active_pane()
            if pane:
                context.active_pane_id = pane.id

        self.command_registry.execute(
            "pane.split",
            context,
            orientation=orientation,
        )

    def close_current_pane(self):
        """Close the current pane (compatibility method)."""
        context = CommandContext(model=self.model)

        # Update context with active items
        tab = self.model.state.get_active_tab()
        if tab:
            context.active_tab_id = tab.id
            pane = tab.get_active_pane()
            if pane:
                context.active_pane_id = pane.id

        self.command_registry.execute("pane.close", context)

    def get_current_tab_name(self) -> str:
        """Get the name of the current tab."""
        tab = self.model.state.get_active_tab()
        return tab.name if tab else ""

    def get_tab_count(self) -> int:
        """Get the number of tabs."""
        return len(self.model.state.tabs)
