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
from viloapp.models.workspace_model import WorkspaceModel
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
        self._state_restored = False  # Track if state has been restored
        self._deferred_init = True  # True when using deferred initialization

        self.setup_ui()
        # Don't create default tab here - wait for restore_state or explicit call
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

        # Apply compact sizing to the tab bar without hardcoding colors
        # Colors will come from the theme system via stylesheet_generator.py
        tab_bar.setStyleSheet(
            """
            QTabBar {
                max-height: 24px;
            }
            QTabBar::tab {
                height: 22px;
                padding: 1px 8px;
                margin: 0;
            }
        """
        )

        # Connect tab widget signals
        self.tab_widget.currentChanged.connect(self._on_tab_changed)
        self.tab_widget.tabCloseRequested.connect(self._on_tab_close_requested)

        layout.addWidget(self.tab_widget)

    def ensure_has_tab(self):
        """Ensure workspace has at least one tab."""
        if not self.model.state.tabs:
            self.create_default_tab()

    def ensure_initialized(self):
        """Ensure workspace is initialized with at least one tab.

        This should be called after restore_state has had a chance to run.
        """
        if not self._state_restored:
            # restore_state was never called, create default tab
            logger.info("No state restoration attempted, creating default tab")
            self.ensure_has_tab()
        elif not self.model.state.tabs:
            # State was restored but no tabs exist
            logger.info("State restored but no tabs, creating default tab")
            self.ensure_has_tab()

    def create_default_tab(self):
        """Create the default tab on startup."""
        logger.info("Creating default tab...")
        # Get default widget from registry
        from viloapp.core.app_widget_manager import app_widget_manager

        default_widget = app_widget_manager.get_default_widget_id()
        if not default_widget:
            logger.warning("No default widget available, using placeholder")
            default_widget = "com.viloapp.placeholder"

        context = CommandContext(model=self.model)
        result = self.command_registry.execute(
            "tab.create",
            context,
            name="Terminal",
            widget_id=default_widget,
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
        # Use the proper migration system - no hardcoded widget IDs!
        from viloapp.core.widget_ids import get_default_widget_id, migrate_widget_type

        # Migrate old type to new widget ID using the system
        widget_id = migrate_widget_type(widget_type)

        # If migration returns unknown, use registry default
        if widget_id.startswith("plugin.unknown."):
            widget_id = get_default_widget_id() or widget_id

        context = CommandContext(model=self.model)
        self.command_registry.execute(
            "tab.create",
            context,
            name=name,
            widget_id=widget_id,
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

    def cleanup(self):
        """Clean up all workspace resources including all AppWidgets."""
        logger.info("Cleaning up workspace...")

        # Clean up all tab views
        for tab_id, tab_view in self.tab_views.items():
            try:
                # Find all AppWidgets in the tab view and clean them up
                from viloapp.ui.widgets.app_widget import AppWidget

                app_widgets = tab_view.findChildren(AppWidget)
                for widget in app_widgets:
                    try:
                        widget.cleanup()
                        logger.debug(f"Cleaned up AppWidget: {widget.widget_id}")
                    except Exception as e:
                        logger.error(f"Error cleaning up widget {widget.widget_id}: {e}")

                logger.debug(f"Cleaned up tab view: {tab_id}")
            except Exception as e:
                logger.error(f"Error cleaning up tab {tab_id}: {e}")

        # Clear tab views
        self.tab_views.clear()

        logger.info("Workspace cleanup complete")

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

    def save_state(self) -> dict:
        """Save workspace state for persistence.

        Returns:
            Dictionary containing workspace state
        """
        # Get state from the model
        tabs_state = []
        for tab in self.model.state.tabs:
            # Get widget_id from the root pane
            widget_id = None
            if tab.tree.root.pane:
                widget_id = tab.tree.root.pane.widget_id

            tab_state = {
                "id": tab.id,  # Use 'id', not 'tab_id'
                "name": tab.name,
                "widget_id": widget_id,
                "active": tab.id == self.model.state.active_tab_id,
            }
            tabs_state.append(tab_state)

        return {
            "tabs": tabs_state,
            "active_tab_id": self.model.state.active_tab_id,
        }

    def restore_state(self, state: dict) -> None:
        """Restore workspace state from persistence.

        Args:
            state: Dictionary containing workspace state
        """
        self._state_restored = True  # Mark that restore was attempted

        if not state or "tabs" not in state:
            # No valid state, create default tab
            self.ensure_has_tab()
            return

        try:
            # Clear any existing tabs (shouldn't be any if we didn't create default)
            for tab in list(self.model.state.tabs):
                self.model.close_tab(tab.id)  # Use 'id', not 'tab_id'

            # Restore tabs
            restored_any = False
            for tab_state in state.get("tabs", []):
                widget_id = tab_state.get("widget_id")
                logger.info(f"Attempting to restore tab with widget_id: {widget_id}")
                if widget_id:
                    # Check if widget is available
                    from viloapp.core.app_widget_manager import app_widget_manager

                    available = app_widget_manager.is_widget_available(widget_id)
                    logger.info(f"Widget {widget_id} available: {available}")
                    if available:
                        tab_id = self.model.create_tab(
                            name=tab_state.get("name", "Restored Tab"), widget_id=widget_id
                        )
                        restored_any = True
                        logger.info(
                            f"Restored tab: {tab_state.get('name')} with widget {widget_id}"
                        )

                        # Set active if it was active
                        if tab_state.get("active"):
                            self.model.set_active_tab(tab_id)
                    else:
                        logger.warning(
                            f"Widget {widget_id} is not available, skipping tab restoration"
                        )

            # If no tabs were restored, create default
            if not restored_any:
                logger.info("No tabs restored from state, creating default tab")
                self.ensure_has_tab()

        except Exception as e:
            logger.error(f"Failed to restore workspace state: {e}")
            # Create default tab on error
            self.ensure_has_tab()
