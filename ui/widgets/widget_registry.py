#!/usr/bin/env python3
"""
Widget registry system for configuring behavior of different widget types.
Defines how each widget type should be handled in the split pane system.
"""

from dataclasses import dataclass
from typing import Dict, Type, Optional, Callable, Any
from enum import Enum
from PySide6.QtWidgets import (
    QWidget, QTextEdit, QPlainTextEdit, QTableWidget,
    QTreeWidget, QListWidget, QLabel
)
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from ui.vscode_theme import *


class WidgetType(Enum):
    """Types of widgets that can be created in panes."""
    TEXT_EDITOR = "text_editor"
    TERMINAL = "terminal"
    OUTPUT = "output"
    EXPLORER = "explorer"
    DEBUGGER = "debugger"
    IMAGE_VIEWER = "image_viewer"
    TABLE_VIEW = "table_view"
    TREE_VIEW = "tree_view"
    WEB_VIEW = "web_view"
    CUSTOM = "custom"
    PLACEHOLDER = "placeholder"


@dataclass
class WidgetConfig:
    """Configuration for a widget type."""
    
    # Widget creation
    widget_class: Type[QWidget]
    factory: Optional[Callable[[str], QWidget]] = None  # Custom factory function
    
    # Context menu behavior
    preserve_context_menu: bool = False  # True if widget has important native menu
    
    # Header behavior
    show_header: bool = True  # Whether to show pane header
    header_compact: bool = False  # Use compact header variant
    header_auto_hide: bool = False  # Hide header until hover
    
    # Interaction options
    allow_type_change: bool = True  # Can change to different widget type
    can_be_closed: bool = True  # Can close this pane
    can_be_split: bool = True  # Can split this pane
    
    # Visual settings
    min_width: int = 150
    min_height: int = 100
    default_content: str = ""  # Default content for new widgets
    
    # Styling
    stylesheet: str = ""  # Custom stylesheet for this widget type


# Default configurations for common widget types
WIDGET_CONFIGS: Dict[WidgetType, WidgetConfig] = {
    WidgetType.TEXT_EDITOR: WidgetConfig(
        widget_class=QPlainTextEdit,
        preserve_context_menu=True,  # Keep native text editing menu
        show_header=True,
        allow_type_change=True,
        default_content="# Text Editor\n\n",
        stylesheet=get_editor_stylesheet()
    ),
    
    WidgetType.TERMINAL: WidgetConfig(
        widget_class=QTextEdit,
        preserve_context_menu=True,  # Terminal needs copy/paste
        show_header=True,
        allow_type_change=False,  # Terminals are specialized
        default_content="$ Terminal\n> ",
        stylesheet=get_terminal_stylesheet()
    ),
    
    WidgetType.OUTPUT: WidgetConfig(
        widget_class=QTextEdit,
        preserve_context_menu=True,
        show_header=True,
        allow_type_change=True,
        default_content="Output Panel\n",
        stylesheet=f"""
            QTextEdit {{
                background-color: {PANEL_BACKGROUND};
                color: {SIDEBAR_FOREGROUND};
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 12px;
                border: none;
            }}
        """
    ),
    
    WidgetType.EXPLORER: WidgetConfig(
        widget_class=QTreeWidget,
        preserve_context_menu=True,  # Tree has its own context menu
        show_header=True,
        header_compact=True,  # Use compact header for explorer
        allow_type_change=False,
        stylesheet=get_sidebar_stylesheet()
    ),
    
    WidgetType.TABLE_VIEW: WidgetConfig(
        widget_class=QTableWidget,
        preserve_context_menu=True,  # Tables have cell operations
        show_header=True,
        allow_type_change=True,
        min_width=200,
        stylesheet=f"""
            QTableWidget {{
                background-color: {EDITOR_BACKGROUND};
                color: {EDITOR_FOREGROUND};
                border: none;
                gridline-color: {SPLITTER_BACKGROUND};
            }}
            QHeaderView::section {{
                background-color: {PANE_HEADER_BACKGROUND};
                color: {SIDEBAR_FOREGROUND};
                border: 1px solid {SPLITTER_BACKGROUND};
                padding: 4px;
            }}
        """
    ),
    
    WidgetType.IMAGE_VIEWER: WidgetConfig(
        widget_class=QLabel,
        preserve_context_menu=False,  # Simple widget, can override
        show_header=True,
        header_auto_hide=True,  # Auto-hide for better viewing
        allow_type_change=True,
        default_content="[Image Viewer]",
        stylesheet=f"""
            QLabel {{
                background-color: {TAB_INACTIVE_BACKGROUND};
                color: {TAB_INACTIVE_FOREGROUND};
                qproperty-alignment: AlignCenter;
                border: none;
                padding: 20px;
            }}
        """
    ),
    
    WidgetType.PLACEHOLDER: WidgetConfig(
        widget_class=QLabel,
        preserve_context_menu=False,
        show_header=True,
        allow_type_change=True,
        default_content="Empty Pane\n\nRight-click to change type",
        stylesheet=f"""
            QLabel {{
                background-color: {TAB_INACTIVE_BACKGROUND};
                color: {TAB_INACTIVE_FOREGROUND};
                qproperty-alignment: AlignCenter;
                padding: 20px;
                border: 1px dashed {SPLITTER_BACKGROUND};
            }}
        """
    ),
}


class WidgetRegistry:
    """Registry for managing widget configurations."""
    
    def __init__(self):
        self.configs = WIDGET_CONFIGS.copy()
        self.custom_factories: Dict[WidgetType, Callable] = {}
    
    def register_widget_type(self, widget_type: WidgetType, config: WidgetConfig):
        """Register a new widget type or override existing."""
        self.configs[widget_type] = config
    
    def register_factory(self, widget_type: WidgetType, factory: Callable[[str], QWidget]):
        """Register a custom factory function for a widget type."""
        self.custom_factories[widget_type] = factory
        if widget_type in self.configs:
            self.configs[widget_type].factory = factory
    
    def get_config(self, widget_type: WidgetType) -> Optional[WidgetConfig]:
        """Get configuration for a widget type."""
        return self.configs.get(widget_type)
    
    def create_widget(self, widget_type: WidgetType, pane_id: str) -> Optional[QWidget]:
        """Create a widget instance for the given type."""
        config = self.get_config(widget_type)
        if not config:
            return None
        
        # Use custom factory if available
        if config.factory:
            widget = config.factory(pane_id)
        else:
            # Use default class
            widget = config.widget_class()
        
        # Apply default content
        if config.default_content:
            if hasattr(widget, 'setPlainText'):
                widget.setPlainText(config.default_content)
            elif hasattr(widget, 'setText'):
                widget.setText(config.default_content)
            elif hasattr(widget, 'setHtml'):
                widget.setHtml(config.default_content)
        
        # Apply stylesheet
        if config.stylesheet:
            widget.setStyleSheet(config.stylesheet)
        
        # Set minimum size
        widget.setMinimumSize(config.min_width, config.min_height)
        
        return widget
    
    def should_preserve_context_menu(self, widget_type: WidgetType) -> bool:
        """Check if widget type needs its native context menu preserved."""
        config = self.get_config(widget_type)
        return config.preserve_context_menu if config else False
    
    def should_show_header(self, widget_type: WidgetType) -> bool:
        """Check if widget type should show header bar."""
        config = self.get_config(widget_type)
        return config.show_header if config else True
    
    def get_header_style(self, widget_type: WidgetType) -> tuple[bool, bool]:
        """Get header style preferences (compact, auto_hide)."""
        config = self.get_config(widget_type)
        if config:
            return config.header_compact, config.header_auto_hide
        return False, False


# Global registry instance
widget_registry = WidgetRegistry()