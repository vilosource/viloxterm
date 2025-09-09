#!/usr/bin/env python3
"""
Terminal widget factory and registration.
Handles creation and state management of terminal widgets.
"""

from typing import Dict, Any, Optional
from PySide6.QtWidgets import QWidget

from ui.widgets.widget_registry import widget_registry, WidgetType
from ui.terminal.terminal_widget import TerminalWidget
from ui.terminal.terminal_config import terminal_config
from ui.icon_manager import get_icon_manager


def create_terminal_widget(pane_id: str) -> QWidget:
    """
    Factory function to create a terminal widget.
    
    Args:
        pane_id: Unique identifier for the pane
        
    Returns:
        TerminalWidget instance
    """
    # Create terminal with default configuration
    terminal = TerminalWidget(config=terminal_config)
    
    # Store pane_id as a property for identification
    terminal.setProperty("pane_id", pane_id)
    
    return terminal


def serialize_terminal_state(widget: QWidget) -> Dict[str, Any]:
    """
    Serialize terminal widget state.
    
    Args:
        widget: Terminal widget instance
        
    Returns:
        Dictionary containing terminal state
    """
    if isinstance(widget, TerminalWidget):
        return widget.get_state()
    return {}


def deserialize_terminal_state(widget: QWidget, state: Dict[str, Any]) -> None:
    """
    Restore terminal widget state.
    
    Args:
        widget: Terminal widget instance
        state: Saved terminal state
    """
    if isinstance(widget, TerminalWidget) and state:
        widget.restore_state(state)


def register_terminal_widget():
    """Register terminal widget with the widget registry."""
    # Get existing config and update it
    config = widget_registry.get_config(WidgetType.TERMINAL)
    if config:
        config.factory = create_terminal_widget
        config.serializer = serialize_terminal_state
        config.deserializer = deserialize_terminal_state
        config.widget_class = TerminalWidget
        
        # Terminal-specific settings
        config.min_width = 400
        config.min_height = 300
        config.preserve_context_menu = False  # Terminal handles its own context menu
        config.show_header = True
        config.allow_type_change = False
        config.can_be_closed = True
        config.can_be_split = True


def update_terminal_theme(is_dark: bool):
    """
    Update theme for all terminal widgets.
    
    Args:
        is_dark: Whether to use dark theme
    """
    # This will be called when the app theme changes
    # We'll need to find all terminal widgets and update them
    # For now, new terminals will use the correct theme
    pass