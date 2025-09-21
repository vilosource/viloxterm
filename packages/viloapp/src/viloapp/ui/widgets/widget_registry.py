#!/usr/bin/env python3
"""
Widget registry system for configuring behavior of different widget types.
Defines how each widget type should be handled in the split pane system.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Optional

from PySide6.QtWidgets import (
    QLabel,
    QPlainTextEdit,
    QTableWidget,
    QTextEdit,
    QTreeWidget,
    QWidget,
)

# Widget state serialization functions


def serialize_text_editor(widget: QWidget) -> dict[str, Any]:
    """Serialize text editor state (QPlainTextEdit)."""
    if isinstance(widget, QPlainTextEdit):
        cursor = widget.textCursor()
        return {
            "content": widget.toPlainText(),
            "cursor_position": cursor.position(),
            "selection_start": cursor.selectionStart(),
            "selection_end": cursor.selectionEnd(),
            "scroll_value": widget.verticalScrollBar().value(),
        }
    return {}


def deserialize_text_editor(widget: QWidget, state: dict[str, Any]) -> None:
    """Restore text editor state."""
    if isinstance(widget, QPlainTextEdit):
        # Restore content
        if "content" in state:
            widget.setPlainText(state["content"])

        # Restore cursor and selection
        if "cursor_position" in state:
            cursor = widget.textCursor()
            cursor.setPosition(state.get("selection_start", state["cursor_position"]))
            if "selection_end" in state and state["selection_end"] != state.get(
                "selection_start", state["cursor_position"]
            ):
                cursor.setPosition(state["selection_end"], cursor.KeepAnchor)
            else:
                cursor.setPosition(state["cursor_position"])
            widget.setTextCursor(cursor)

        # Restore scroll position
        if "scroll_value" in state:
            widget.verticalScrollBar().setValue(state["scroll_value"])


def serialize_terminal(widget: QWidget) -> dict[str, Any]:
    """Serialize terminal state (QTextEdit)."""
    if isinstance(widget, QTextEdit):
        cursor = widget.textCursor()
        return {
            "content": widget.toPlainText(),
            "cursor_position": cursor.position(),
            "scroll_value": widget.verticalScrollBar().value(),
            "is_read_only": widget.isReadOnly(),
        }
    return {}


def deserialize_terminal(widget: QWidget, state: dict[str, Any]) -> None:
    """Restore terminal state."""
    if isinstance(widget, QTextEdit):
        # Restore content
        if "content" in state:
            widget.setPlainText(state["content"])

        # Restore cursor position
        if "cursor_position" in state:
            cursor = widget.textCursor()
            cursor.setPosition(state["cursor_position"])
            widget.setTextCursor(cursor)

        # Restore scroll position
        if "scroll_value" in state:
            widget.verticalScrollBar().setValue(state["scroll_value"])

        # Restore read-only state
        if "is_read_only" in state:
            widget.setReadOnly(state["is_read_only"])


def serialize_table_view(widget: QWidget) -> dict[str, Any]:
    """Serialize table view state."""
    if isinstance(widget, QTableWidget):
        # Get column widths
        column_widths = []
        for i in range(widget.columnCount()):
            column_widths.append(widget.columnWidth(i))

        # Get selected items
        selected_items = []
        for item in widget.selectedItems():
            selected_items.append((item.row(), item.column()))

        return {
            "column_count": widget.columnCount(),
            "row_count": widget.rowCount(),
            "column_widths": column_widths,
            "selected_items": selected_items,
            "current_row": widget.currentRow(),
            "current_column": widget.currentColumn(),
        }
    return {}


def deserialize_table_view(widget: QWidget, state: dict[str, Any]) -> None:
    """Restore table view state."""
    if isinstance(widget, QTableWidget):
        # Restore column widths
        if "column_widths" in state:
            for i, width in enumerate(state["column_widths"]):
                if i < widget.columnCount():
                    widget.setColumnWidth(i, width)

        # Restore selection
        if "selected_items" in state:
            widget.clearSelection()
            for row, col in state["selected_items"]:
                if row < widget.rowCount() and col < widget.columnCount():
                    widget.item(row, col).setSelected(True)

        # Restore current item
        current_row = state.get("current_row", -1)
        current_col = state.get("current_column", -1)
        if current_row >= 0 and current_col >= 0:
            widget.setCurrentCell(current_row, current_col)


def serialize_label(widget: QWidget) -> dict[str, Any]:
    """Serialize label state."""
    if isinstance(widget, QLabel):
        return {"text": widget.text(), "alignment": int(widget.alignment())}
    return {}


def deserialize_label(widget: QWidget, state: dict[str, Any]) -> None:
    """Restore label state."""
    if isinstance(widget, QLabel):
        if "text" in state:
            widget.setText(state["text"])
        if "alignment" in state:
            widget.setAlignment(state["alignment"])


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
    SETTINGS = "settings"
    CUSTOM = "custom"
    PLACEHOLDER = "placeholder"


@dataclass
class WidgetConfig:
    """Configuration for a widget type."""

    # Widget creation
    widget_class: type[QWidget]
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

    # State serialization
    serializer: Optional[Callable[[QWidget], dict[str, Any]]] = (
        None  # Custom state serializer
    )
    deserializer: Optional[Callable[[QWidget, dict[str, Any]], None]] = (
        None  # Custom state deserializer
    )


# Default configurations for common widget types
WIDGET_CONFIGS: dict[WidgetType, WidgetConfig] = {
    WidgetType.TEXT_EDITOR: WidgetConfig(
        widget_class=QPlainTextEdit,
        preserve_context_menu=True,  # Keep native text editing menu
        show_header=True,
        allow_type_change=True,
        default_content="# Text Editor\n\n",
        stylesheet="",  # Theme will be applied dynamically
        serializer=serialize_text_editor,
        deserializer=deserialize_text_editor,
    ),
    WidgetType.TERMINAL: WidgetConfig(
        widget_class=QTextEdit,  # Will be overridden by factory
        factory=None,  # Will be set when terminal is imported
        preserve_context_menu=True,  # Terminal needs copy/paste
        show_header=True,
        allow_type_change=True,  # Allow changing terminal to other widget types
        default_content="",  # Terminal creates its own content
        stylesheet="",  # Terminal has its own styling
        serializer=None,  # Will be set when terminal is imported
        deserializer=None,  # Will be set when terminal is imported
    ),
    WidgetType.OUTPUT: WidgetConfig(
        widget_class=QTextEdit,
        preserve_context_menu=True,
        show_header=True,
        allow_type_change=True,
        default_content="Output Panel\n",
        stylesheet="",  # Theme will be applied dynamically
        serializer=serialize_terminal,  # Same as terminal
        deserializer=deserialize_terminal,
    ),
    WidgetType.EXPLORER: WidgetConfig(
        widget_class=QTreeWidget,
        preserve_context_menu=True,  # Tree has its own context menu
        show_header=True,
        header_compact=True,  # Use compact header for explorer
        allow_type_change=False,
        stylesheet="",  # Theme will be applied dynamically
    ),
    WidgetType.TABLE_VIEW: WidgetConfig(
        widget_class=QTableWidget,
        preserve_context_menu=True,  # Tables have cell operations
        show_header=True,
        allow_type_change=True,
        min_width=200,
        stylesheet="",  # Theme will be applied dynamically
        serializer=serialize_table_view,
        deserializer=deserialize_table_view,
    ),
    WidgetType.TREE_VIEW: WidgetConfig(
        widget_class=QTreeWidget,
        preserve_context_menu=True,  # Trees have node operations
        show_header=True,
        allow_type_change=True,
        stylesheet="",  # Theme will be applied dynamically
    ),
    WidgetType.IMAGE_VIEWER: WidgetConfig(
        widget_class=QLabel,
        preserve_context_menu=False,  # Simple widget, can override
        show_header=True,
        header_auto_hide=True,  # Auto-hide for better viewing
        allow_type_change=True,
        default_content="[Image Viewer]",
        stylesheet="",  # Theme will be applied dynamically
        serializer=serialize_label,
        deserializer=deserialize_label,
    ),
    WidgetType.SETTINGS: WidgetConfig(
        widget_class=QWidget,  # Will be overridden by factory
        factory=None,  # Will be set when creating shortcut config widget
        preserve_context_menu=False,
        show_header=True,
        allow_type_change=True,  # Allow changing to other widget types
        can_be_closed=True,
        can_be_split=False,  # Settings should not be split
        min_width=600,
        min_height=400,
        stylesheet="",  # Settings widget handles its own styling
    ),
    WidgetType.PLACEHOLDER: WidgetConfig(
        widget_class=QLabel,
        preserve_context_menu=False,
        show_header=True,
        allow_type_change=True,
        default_content="Empty Pane\n\nRight-click to change type",
        stylesheet="",  # Theme will be applied dynamically
        serializer=serialize_label,
        deserializer=deserialize_label,
    ),
}


class WidgetRegistry:
    """Registry for managing widget configurations."""

    def __init__(self):
        self.configs = WIDGET_CONFIGS.copy()
        self.custom_factories: dict[WidgetType, Callable] = {}

    def register_widget_type(self, widget_type: WidgetType, config: WidgetConfig):
        """Register a new widget type or override existing."""
        self.configs[widget_type] = config

    def register_factory(
        self, widget_type: WidgetType, factory: Callable[[str], QWidget]
    ):
        """Register a custom factory function for a widget type.

        .. deprecated:: 1.0
            Use AppWidgetManager.register_widget() with AppWidgetMetadata instead.
            This method will be removed in a future version.
        """
        import warnings

        warnings.warn(
            "WidgetRegistry.register_factory() is deprecated. "
            "Use AppWidgetManager.register_widget() with AppWidgetMetadata instead.",
            DeprecationWarning,
            stacklevel=2,
        )
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
            if hasattr(widget, "setPlainText"):
                widget.setPlainText(config.default_content)
            elif hasattr(widget, "setText"):
                widget.setText(config.default_content)
            elif hasattr(widget, "setHtml"):
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

    def serialize_widget_state(
        self, widget: QWidget, widget_type: WidgetType
    ) -> dict[str, Any]:
        """Serialize widget state using the appropriate serializer."""
        config = self.get_config(widget_type)
        if config and config.serializer:
            try:
                return config.serializer(widget)
            except Exception as e:
                print(f"Failed to serialize widget state for {widget_type}: {e}")
        return {}

    def deserialize_widget_state(
        self, widget: QWidget, widget_type: WidgetType, state: dict[str, Any]
    ) -> bool:
        """Deserialize widget state using the appropriate deserializer."""
        if not state:
            return True  # Empty state is valid

        config = self.get_config(widget_type)
        if config and config.deserializer:
            try:
                config.deserializer(widget, state)
                return True
            except Exception as e:
                print(f"Failed to deserialize widget state for {widget_type}: {e}")
                return False
        return True  # No deserializer means success (no state to restore)


# Global registry instance
widget_registry = WidgetRegistry()
