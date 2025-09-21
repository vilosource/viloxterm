#!/usr/bin/env python3
"""
Split pane view helpers - utility functions for view rendering and management.

This module provides utility functions for split pane widget view operations,
including event filtering, focus management, visual updates, and widget rendering.
"""

import logging
from typing import Optional

from PySide6.QtCore import QEvent, QObject, Qt, QTimer, Signal
from PySide6.QtWidgets import QWidget

logger = logging.getLogger(__name__)


class SplitPaneViewHelpers(QObject):
    """
    Helper class for split pane view operations.

    Provides utilities for:
    - Event filtering and focus detection
    - Visual state updates
    - Widget tree traversal
    - Pane number management
    """

    # Signals
    focus_detected = Signal(str)  # pane_id

    def __init__(self, parent=None):
        """Initialize the view helpers."""
        super().__init__(parent)
        self._pane_wrappers: dict[str, QWidget] = {}
        self._focus_restoration_timer = None
        self._restoring_focus = False

    def set_pane_wrappers(self, pane_wrappers: dict[str, QWidget]):
        """
        Set the pane wrappers dictionary for event filtering.

        Args:
            pane_wrappers: Dictionary mapping pane IDs to wrapper widgets
        """
        self._pane_wrappers = pane_wrappers

    def install_focus_event_filters(self, widget: QWidget, filter_receiver: QObject):
        """
        Install event filters on widget and its children to detect focus changes.

        Args:
            widget: The widget to install filters on
            filter_receiver: The object that will receive the filtered events
        """
        # Install filter on the widget itself
        widget.installEventFilter(filter_receiver)

        # Install filters on all child widgets recursively
        def install_on_children(parent_widget):
            for child in parent_widget.findChildren(QWidget):
                child.installEventFilter(filter_receiver)
                # Recursively install on children's children
                install_on_children(child)

        install_on_children(widget)
        logger.debug(f"Installed event filters on {widget.__class__.__name__} and children")

    def process_focus_event(self, obj: QObject, event: QEvent) -> Optional[str]:
        """
        Process a focus event and determine which pane gained focus.

        Args:
            obj: The object that received the event
            event: The focus event

        Returns:
            Pane ID that gained focus, or None if not found
        """
        if event.type() != QEvent.FocusIn:
            return None

        # Check if this widget belongs to one of our panes
        current = obj
        while current:
            for pane_id, wrapper in self._pane_wrappers.items():
                if current == wrapper or wrapper.isAncestorOf(current):
                    logger.debug(f"Focus detected on pane {pane_id} via event filter")
                    return pane_id
            current = current.parent()

        return None

    def update_pane_visual_states(self, active_pane_id: str):
        """
        Update visual indication of active pane for all tracked panes.

        Args:
            active_pane_id: ID of the currently active pane
        """
        for pane_id, wrapper in self._pane_wrappers.items():
            is_active = pane_id == active_pane_id
            self._set_wrapper_active_state(wrapper, is_active)

    def _set_wrapper_active_state(self, wrapper: QWidget, active: bool):
        """
        Set the active state of a pane wrapper.

        Args:
            wrapper: The pane wrapper widget
            active: Whether the pane should be shown as active
        """
        if hasattr(wrapper, "set_active"):
            wrapper.set_active(active)
        else:
            # Fallback visual styling
            if active:
                wrapper.setStyleSheet(
                    """
                    QWidget {
                        border: 2px solid #007ACC;
                    }
                """
                )
            else:
                wrapper.setStyleSheet(
                    """
                    QWidget {
                        border: 1px solid #3c3c3c;
                    }
                """
                )

    def update_pane_numbers_display(self, model, show_numbers: bool):
        """
        Update pane number display for all panes.

        Args:
            model: The split pane model containing pane data
            show_numbers: Whether to show pane numbers
        """
        # Ensure model indices are up to date
        if hasattr(model, "update_pane_indices"):
            model.update_pane_indices()

        # Update each pane's header
        for pane_id, wrapper in self._pane_wrappers.items():
            if hasattr(wrapper, "header_bar") and wrapper.header_bar:
                number = model.get_pane_index(pane_id) if hasattr(model, "get_pane_index") else None
                wrapper.header_bar.set_pane_number(number, show_numbers)

    def schedule_focus_restoration(self, target_pane_id: str, focus_callback, delay_ms: int = 10):
        """
        Schedule focus restoration to a specific pane after a delay.

        Args:
            target_pane_id: ID of the pane to focus
            focus_callback: Function to call to set focus
            delay_ms: Delay in milliseconds before focusing
        """
        # Prevent multiple simultaneous focus restorations
        if self._restoring_focus:
            return

        self._restoring_focus = True

        def restore_focus():
            try:
                focus_callback(target_pane_id)
                logger.debug(f"Focus restored to pane {target_pane_id}")
            except Exception as e:
                logger.warning(f"Failed to restore focus to pane {target_pane_id}: {e}")
            finally:
                self._restoring_focus = False

        # Cancel any existing timer
        if self._focus_restoration_timer:
            self._focus_restoration_timer.stop()
            self._focus_restoration_timer.deleteLater()

        self._focus_restoration_timer = QTimer()
        self._focus_restoration_timer.setSingleShot(True)
        self._focus_restoration_timer.timeout.connect(restore_focus)
        self._focus_restoration_timer.start(delay_ms)

    def find_widget_in_tree(self, root_widget: QWidget, target_class: type) -> list[QWidget]:
        """
        Find all widgets of a specific type in the widget tree.

        Args:
            root_widget: Root widget to search from
            target_class: Class type to search for

        Returns:
            List of widgets matching the target class
        """
        found_widgets = []

        def search_recursive(widget):
            if isinstance(widget, target_class):
                found_widgets.append(widget)
            for child in widget.findChildren(QWidget, "", Qt.FindDirectChildrenOnly):
                search_recursive(child)

        search_recursive(root_widget)
        return found_widgets

    def get_widget_hierarchy_info(self, widget: QWidget) -> dict:
        """
        Get hierarchy information for a widget for debugging.

        Args:
            widget: Widget to analyze

        Returns:
            Dictionary with hierarchy information
        """
        info = {
            "class": widget.__class__.__name__,
            "object_name": widget.objectName(),
            "visible": widget.isVisible(),
            "enabled": widget.isEnabled(),
            "size": f"{widget.width()}x{widget.height()}",
            "children_count": len(widget.findChildren(QWidget, "", Qt.FindDirectChildrenOnly)),
        }

        parent = widget.parent()
        if parent:
            info["parent_class"] = parent.__class__.__name__
            info["parent_object_name"] = parent.objectName()

        return info

    def log_widget_tree(self, root_widget: QWidget, max_depth: int = 3):
        """
        Log the widget tree structure for debugging.

        Args:
            root_widget: Root widget to start from
            max_depth: Maximum depth to traverse
        """

        def log_recursive(widget, depth=0, prefix=""):
            if depth > max_depth:
                return

            indent = "  " * depth
            info = self.get_widget_hierarchy_info(widget)
            logger.debug(
                f"{indent}{prefix}{info['class']} ({info['object_name']}) "
                f"- {info['size']}, visible={info['visible']}"
            )

            children = widget.findChildren(QWidget, "", Qt.FindDirectChildrenOnly)
            for i, child in enumerate(children):
                is_last = i == len(children) - 1
                child_prefix = "└── " if is_last else "├── "
                log_recursive(child, depth + 1, child_prefix)

        logger.debug("Widget tree structure:")
        log_recursive(root_widget)

    def validate_widget_integrity(self, root_widget: QWidget) -> dict[str, list[str]]:
        """
        Validate widget tree integrity and report issues.

        Args:
            root_widget: Root widget to validate

        Returns:
            Dictionary with validation results
        """
        issues = {
            "orphaned_widgets": [],
            "invisible_widgets": [],
            "large_widgets": [],
            "memory_issues": [],
        }

        def validate_recursive(widget):
            # Check for orphaned widgets (no parent when expected)
            if widget != root_widget and not widget.parent():
                issues["orphaned_widgets"].append(widget.__class__.__name__)

            # Check for invisible widgets that should be visible
            if not widget.isVisible() and widget.parent() and widget.parent().isVisible():
                issues["invisible_widgets"].append(widget.__class__.__name__)

            # Check for unusually large widgets
            if widget.width() > 5000 or widget.height() > 5000:
                issues["large_widgets"].append(
                    f"{widget.__class__.__name__} ({widget.width()}x{widget.height()})"
                )

            # Check children
            for child in widget.findChildren(QWidget, "", Qt.FindDirectChildrenOnly):
                validate_recursive(child)

        validate_recursive(root_widget)
        return issues

    def cleanup(self):
        """Clean up all resources."""
        if self._focus_restoration_timer:
            self._focus_restoration_timer.stop()
            self._focus_restoration_timer.deleteLater()
            self._focus_restoration_timer = None

        self._pane_wrappers.clear()
        self._restoring_focus = False
        logger.debug("View helpers cleanup complete")


# Global view helpers instance
_view_helpers_instance = None


def get_view_helpers() -> SplitPaneViewHelpers:
    """
    Get the global view helpers instance.

    Returns:
        Global SplitPaneViewHelpers instance
    """
    global _view_helpers_instance
    if _view_helpers_instance is None:
        _view_helpers_instance = SplitPaneViewHelpers()
    return _view_helpers_instance
