#!/usr/bin/env python3
"""
Split pane widget - Pure view implementation.

This widget renders the pane tree structure from WorkspaceModel.
It has NO state or business logic - it's purely a view that observes
and reacts to model changes.
"""

import logging
from typing import Dict, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from viloapp.models.workspace_model import Orientation, PaneNode, WorkspaceModel

logger = logging.getLogger(__name__)


class PaneContainer(QWidget):
    """Container for a single pane's widget."""

    def __init__(self, pane_id: str, parent=None):
        """Initialize pane container.

        Args:
            pane_id: ID of the pane this container represents
            parent: Parent widget
        """
        super().__init__(parent)
        self.pane_id = pane_id
        self.widget = None

        # Simple layout to hold the widget
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        # Phase 1: Comprehensive flicker prevention for containers
        self.setAutoFillBackground(True)

        # Enhanced Qt attributes for maximum flicker prevention
        self.setAttribute(Qt.WA_OpaquePaintEvent, True)
        self.setAttribute(Qt.WA_NoSystemBackground, True)
        self.setAttribute(Qt.WA_StaticContents, True)  # Content doesn't change often
        self.setAttribute(Qt.WA_DontCreateNativeAncestors, True)  # Avoid native windows

        # Styling without border to prevent overlapping
        self.setStyleSheet(
            """
            PaneContainer {
                background-color: #252526;
            }
        """
        )

    def set_widget(self, widget: QWidget):
        """Set the widget to display in this pane.

        Args:
            widget: The widget to display
        """
        # Clear old widget
        if self.widget:
            self.layout.removeWidget(self.widget)

            # Properly cleanup AppWidget if it has a cleanup method
            if hasattr(self.widget, "cleanup") and callable(self.widget.cleanup):
                try:
                    self.widget.cleanup()
                except Exception as e:
                    logger.error(f"Error cleaning up widget: {e}")

            self.widget.setParent(None)
            self.widget.deleteLater()

        # Add new widget
        self.widget = widget
        if widget:
            self.layout.addWidget(widget)


class SplitPaneWidget(QWidget):
    """
    Pure view widget that renders pane tree from WorkspaceModel.

    This widget:
    - Observes WorkspaceModel for changes
    - Renders tree structure using Qt splitters
    - Forwards UI events to commands
    - Has NO state or business logic
    """

    # Signals for UI events (will trigger commands)
    pane_focused = Signal(str)  # pane_id
    split_requested = Signal(str, str)  # pane_id, orientation
    close_requested = Signal(str)  # pane_id

    # Signals for other components
    active_pane_changed = Signal(str)
    layout_changed = Signal()

    def __init__(self, model: WorkspaceModel, parent=None):
        """Initialize split pane widget with model reference.

        Args:
            model: The WorkspaceModel to observe
            parent: Parent widget
        """
        super().__init__(parent)

        self.model = model
        self._pane_containers: Dict[str, PaneContainer] = {}
        self._current_root_widget = None

        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # Subscribe to model changes
        self._connect_model_observers()

        # Initial render
        self.refresh_view()

        logger.debug("SplitPaneWidget initialized as pure view")

    def _connect_model_observers(self):
        """Connect to model observer events."""
        # Subscribe to relevant model events
        self.model.add_observer("pane_split", self._on_model_changed)
        self.model.add_observer("pane_closed", self._on_model_changed)
        self.model.add_observer("pane_focused", self._on_pane_focused)
        self.model.add_observer("widget_changed", self._on_widget_changed)
        self.model.add_observer("tab_switched", self._on_tab_switched)

    def _on_model_changed(self, data: Dict):
        """Handle model structure changes.

        Args:
            data: Event data from model
        """
        logger.debug(f"Model changed: {data}")
        self.refresh_view()
        self.layout_changed.emit()

    def _on_pane_focused(self, data: Dict):
        """Handle pane focus change.

        Args:
            data: Event data with pane_id
        """
        pane_id = data.get("pane_id")
        if pane_id:
            self.active_pane_changed.emit(pane_id)

            # Update visual focus indicator
            for pid, container in self._pane_containers.items():
                if container:
                    container.setProperty("focused", pid == pane_id)
                    container.style().polish(container)

    def _on_widget_changed(self, data: Dict):
        """Handle widget change in a pane.

        Args:
            data: Event data with pane_id and widget_id
        """
        pane_id = data.get("pane_id")
        if pane_id and pane_id in self._pane_containers:
            # Widget creation is handled by WidgetFactory
            # We just need to refresh to pick up the change
            self.refresh_view()

    def _on_tab_switched(self, data: Dict):
        """Handle tab switch.

        Args:
            data: Event data
        """
        self.refresh_view()

    def refresh_view(self):
        """Render the current state from the model."""
        # Get active tab from model
        tab = self.model.state.get_active_tab()
        if not tab:
            logger.debug("No active tab to render")
            return

        # Phase 2: Enhanced double-buffering for flicker prevention
        # Build new tree completely OFF-SCREEN first
        new_root = self._build_tree_widget(tab.tree.root)
        if new_root:
            # Pre-calculate layout to avoid flicker
            new_root.resize(self.size())

            # Now do atomic swap with updates disabled
            self.setUpdatesEnabled(False)
            try:
                if self._current_root_widget:
                    # Hide old widget first to prevent visual artifacts
                    self._current_root_widget.hide()
                    self.main_layout.removeWidget(self._current_root_widget)
                    # Cleanup all AppWidgets in the tree before deleting
                    self._cleanup_widget_tree(self._current_root_widget)
                    self._current_root_widget.deleteLater()

                # Clear pane containers for clean state
                self._pane_containers.clear()

                # Add new widget immediately
                self._current_root_widget = new_root
                self.main_layout.addWidget(new_root)

                # Set active pane focus
                if tab.active_pane_id and tab.active_pane_id in self._pane_containers:
                    container = self._pane_containers[tab.active_pane_id]
                    container.setProperty("focused", True)
                    container.style().polish(container)
            finally:
                # Re-enable updates - triggers single repaint with complete layout
                self.setUpdatesEnabled(True)

    def _build_tree_widget(self, node: PaneNode) -> Optional[QWidget]:
        """Build Qt widget tree from model node.

        Args:
            node: The PaneNode to build from

        Returns:
            QWidget representing the node, or None
        """
        if not node:
            return None

        if node.is_leaf() and node.pane:
            # Create container for this pane
            container = PaneContainer(node.pane.id)

            # Phase 3: Store container BEFORE requesting widget (pre-styling)
            self._pane_containers[node.pane.id] = container

            # Request widget creation from factory
            self._request_widget_for_pane(node.pane.id, node.pane.widget_id)

            # Connect focus handling
            container.mousePressEvent = lambda e: self._handle_pane_click(node.pane.id, e)

            return container

        elif node.is_split() and node.first and node.second:
            # Create splitter
            if node.orientation == Orientation.HORIZONTAL:
                splitter = QSplitter(Qt.Horizontal)
            else:
                splitter = QSplitter(Qt.Vertical)

            # CRITICAL: QSplitter optimizations to prevent flicker and artifacts
            # 1. Prevent children from collapsing - major source of artifacts
            splitter.setChildrenCollapsible(False)

            # 2. Disable opaque resize to prevent intermediate redraws
            splitter.setOpaqueResize(False)

            # 3. Set handle width explicitly to prevent size calculation issues
            splitter.setHandleWidth(3)

            # 4. Qt rendering attributes for flicker prevention
            splitter.setAttribute(Qt.WA_OpaquePaintEvent, True)
            splitter.setAttribute(Qt.WA_NoSystemBackground, True)
            splitter.setAttribute(Qt.WA_StaticContents, True)  # Hint that content is static

            # 5. Complete styling with explicit dimensions
            splitter.setStyleSheet(
                """
                QSplitter {
                    background-color: #252526;
                }
                QSplitter::handle {
                    background-color: #3c3c3c;
                    border: none;
                    margin: 0px;
                }
                QSplitter::handle:horizontal {
                    width: 3px;
                    min-width: 3px;
                    max-width: 3px;
                }
                QSplitter::handle:vertical {
                    height: 3px;
                    min-height: 3px;
                    max-height: 3px;
                }
            """
            )

            # Build child widgets
            first_widget = self._build_tree_widget(node.first)
            second_widget = self._build_tree_widget(node.second)

            if first_widget and second_widget:
                splitter.addWidget(first_widget)
                splitter.addWidget(second_widget)

                # Set split ratio - ensure minimum sizes to prevent collapse
                sizes = splitter.sizes()
                total = sum(sizes)
                if total > 0:
                    ratio = node.ratio
                    first_size = max(50, int(total * ratio))  # Minimum 50px
                    second_size = max(50, total - first_size)
                    splitter.setSizes([first_size, second_size])
                else:
                    # Fallback sizes if initial size is 0
                    splitter.setSizes([400, 400])

                # Update model ratio when user drags splitter
                splitter.splitterMoved.connect(lambda: self._update_split_ratio(node, splitter))

                return splitter

        return None

    def _request_widget_for_pane(self, pane_id: str, widget_id: str):
        """Request widget creation from factory.

        Args:
            pane_id: ID of the pane
            widget_id: ID of the widget type to create
        """
        # Get the container we just created
        container = self._pane_containers.get(pane_id)
        if not container:
            logger.error(f"Container not found for pane {pane_id}")
            return

        # Create the actual widget using AppWidgetManager
        from viloapp.core.app_widget_manager import app_widget_manager

        widget = app_widget_manager.get_or_create_widget(widget_id, pane_id)

        if widget:
            container.set_widget(widget)
            logger.debug(f"Created widget {widget_id} for pane {pane_id}")
        else:
            # Fallback to placeholder if widget creation fails
            from PySide6.QtWidgets import QLabel

            placeholder = QLabel("Widget unavailable")
            placeholder.setStyleSheet(
                """
                QLabel {
                    background-color: #252526;
                    color: #999999;
                    text-align: center;
                    padding: 20px;
                }
            """
            )
            placeholder.setAlignment(Qt.AlignCenter)
            container.set_widget(placeholder)
            logger.warning(f"Failed to create widget {widget_id} for pane {pane_id}")

    def _cleanup_widget_tree(self, widget: QWidget):
        """Recursively cleanup all AppWidgets in a widget tree.

        Args:
            widget: Root widget of the tree to cleanup
        """
        if not widget:
            return

        # Check if this widget is a PaneContainer with an AppWidget
        if isinstance(widget, PaneContainer) and widget.widget:
            if hasattr(widget.widget, "cleanup") and callable(widget.widget.cleanup):
                try:
                    widget.widget.cleanup()
                    logger.debug(f"Cleaned up AppWidget in pane {widget.pane_id}")
                except Exception as e:
                    logger.error(f"Error cleaning up widget in pane {widget.pane_id}: {e}")

        # Recursively cleanup children
        for child in widget.findChildren(QWidget):
            if isinstance(child, PaneContainer) and child.widget:
                if hasattr(child.widget, "cleanup") and callable(child.widget.cleanup):
                    try:
                        child.widget.cleanup()
                        logger.debug(f"Cleaned up AppWidget in pane {child.pane_id}")
                    except Exception as e:
                        logger.error(f"Error cleaning up widget in pane {child.pane_id}: {e}")

    def _handle_pane_click(self, pane_id: str, event):
        """Handle click on a pane.

        Args:
            pane_id: ID of clicked pane
            event: Mouse event
        """
        # Emit signal to trigger focus command
        self.pane_focused.emit(pane_id)

        # Continue with normal event processing
        if pane_id in self._pane_containers:
            QWidget.mousePressEvent(self._pane_containers[pane_id], event)

    def _update_split_ratio(self, node: PaneNode, splitter: QSplitter):
        """Update model when splitter is moved.

        Args:
            node: The split node
            splitter: The QSplitter widget
        """
        sizes = splitter.sizes()
        total = sum(sizes)
        if total > 0 and len(sizes) >= 2:
            ratio = sizes[0] / total
            node.ratio = ratio
            # Could emit a model update event here if needed

    # Public API for compatibility (delegate to model)

    def get_active_pane_id(self) -> Optional[str]:
        """Get active pane ID from model.

        Returns:
            Active pane ID or None
        """
        tab = self.model.state.get_active_tab()
        return tab.active_pane_id if tab else None

    def set_active_pane(self, pane_id: str):
        """Request pane focus through model.

        Args:
            pane_id: ID of pane to focus
        """
        self.pane_focused.emit(pane_id)

    def get_pane_widget(self, pane_id: str) -> Optional[QWidget]:
        """Get widget for a pane.

        Args:
            pane_id: ID of the pane

        Returns:
            The widget or None
        """
        container = self._pane_containers.get(pane_id)
        return container.widget if container else None

    def set_pane_widget(self, pane_id: str, widget: QWidget):
        """Set widget for a pane container.

        Args:
            pane_id: ID of the pane
            widget: Widget to set
        """
        container = self._pane_containers.get(pane_id)
        if container:
            container.set_widget(widget)

    def cleanup(self):
        """Clean up observers when done."""
        # Remove model observers
        self.model.remove_observer("pane_split", self._on_model_changed)
        self.model.remove_observer("pane_closed", self._on_model_changed)
        self.model.remove_observer("pane_focused", self._on_pane_focused)
        self.model.remove_observer("widget_changed", self._on_widget_changed)
        self.model.remove_observer("tab_switched", self._on_tab_switched)

        # Clear containers
        self._pane_containers.clear()
