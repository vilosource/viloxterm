#!/usr/bin/env python3
"""
AppWidget base class for all application content widgets.

This is the foundation of our content widget architecture. All content widgets
(terminal, editor, browser, etc.) extend this base class.
"""

from typing import Optional, Dict, Any
from PySide6.QtWidgets import QWidget
from PySide6.QtCore import Signal
from ui.widgets.widget_registry import WidgetType


class AppWidget(QWidget):
    """
    Base class for all application content widgets.
    
    AppWidgets are the actual content (terminals, editors, etc.) that users interact with.
    They are owned by the model (stored in LeafNodes) and wrapped by the view (PaneContent).
    
    Key principles:
    - AppWidgets don't know their position in the tree
    - They communicate through signals that bubble up the tree
    - They manage their own resources and cleanup
    - They can be moved between panes without recreation
    """
    
    # Signals
    action_requested = Signal(str, dict)  # action_type, params
    state_changed = Signal(dict)  # state_data
    focus_requested = Signal()  # Request focus on this widget
    
    def __init__(self, widget_id: str, widget_type: WidgetType, parent=None):
        """
        Initialize the AppWidget.
        
        Args:
            widget_id: Unique identifier for this widget
            widget_type: Type of widget (TERMINAL, TEXT_EDITOR, etc.)
            parent: Parent QWidget
        """
        super().__init__(parent)
        self.widget_id = widget_id
        self.widget_type = widget_type
        self.leaf_node = None  # Back-reference to tree node (set by model)
        
    def cleanup(self):
        """
        Clean up resources when widget is being destroyed.
        
        Must be overridden in subclasses to clean up specific resources
        (e.g., terminal sessions, unsaved documents, etc.)
        """
        pass  # Base implementation does nothing
        
    def get_state(self) -> Dict[str, Any]:
        """
        Get widget state for persistence.
        
        Returns:
            Dictionary containing widget state that can be serialized
        """
        return {
            "type": self.widget_type.value,
            "widget_id": self.widget_id
        }
        
    def set_state(self, state: Dict[str, Any]):
        """
        Restore widget state from persisted data.
        
        Args:
            state: Dictionary containing widget state to restore
        """
        pass  # Base implementation does nothing
        
    def can_close(self) -> bool:
        """
        Check if widget can be closed safely.
        
        Returns:
            True if widget can be closed, False if there are unsaved changes, etc.
        """
        return True
        
    def request_action(self, action: str, params: Optional[Dict[str, Any]] = None):
        """
        Request an action through the tree structure.
        
        This is the primary way AppWidgets communicate with the system.
        Actions bubble up through the tree to be handled by the model/view.
        
        Args:
            action: Action type (e.g., 'split', 'close', 'focus')
            params: Optional parameters for the action
        """
        self.action_requested.emit(action, params or {})
        
    def notify_state_change(self, state_data: Optional[Dict[str, Any]] = None):
        """
        Notify that widget state has changed.
        
        Args:
            state_data: Optional data about what changed
        """
        self.state_changed.emit(state_data or {})
        
    def request_focus(self):
        """Request focus on this widget."""
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"AppWidget.request_focus() called for widget {self.widget_id}")
        self.focus_requested.emit()
        logger.debug(f"focus_requested signal emitted for widget {self.widget_id}")
        
    def get_title(self) -> str:
        """
        Get title/label for this widget.
        
        Returns:
            String to display in tabs, headers, etc.
        """
        return f"{self.widget_type.value.replace('_', ' ').title()}"
        
    def get_icon_name(self) -> Optional[str]:
        """
        Get icon name for this widget type.
        
        Returns:
            Icon name or None if no icon
        """
        # Map widget types to icons
        icon_map = {
            WidgetType.TERMINAL: "terminal",
            WidgetType.TEXT_EDITOR: "file-text",
            WidgetType.FILE_EXPLORER: "folder",
            WidgetType.SEARCH: "search",
            WidgetType.GIT: "git-branch",
            WidgetType.SETTINGS: "settings",
            WidgetType.PLACEHOLDER: "layout"
        }
        return icon_map.get(self.widget_type)