#!/usr/bin/env python3
"""
Command palette widget - the main UI component for command discovery and execution.

This widget provides a VSCode-style command palette with fuzzy search,
keyboard navigation, and command execution.
"""

import logging
from typing import Optional

from PySide6.QtCore import QEvent, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

from viloapp.core.commands.base import Command
from viloapp.core.commands.registry import command_registry
from viloapp.services.icon_service import get_icon_manager

logger = logging.getLogger(__name__)


class CommandListItem(QWidget):
    """Custom widget for displaying command items in the list."""

    def __init__(self, command: Command, parent=None):
        super().__init__(parent)
        self.command = command
        self.setup_ui()

    def setup_ui(self):
        """Initialize the command item UI."""
        # Set background for the entire widget
        self.setStyleSheet(
            """
            CommandListItem {
                background-color: transparent;
            }
        """
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)

        # Command icon (if available)
        icon_manager = get_icon_manager()
        if self.command.icon:
            icon = icon_manager.get_icon(self.command.icon)
            icon_label = QLabel()
            icon_label.setPixmap(icon.pixmap(QSize(16, 16)))
            icon_label.setFixedSize(16, 16)
            layout.addWidget(icon_label)

        # Command details container
        details_layout = QVBoxLayout()
        details_layout.setContentsMargins(0, 0, 0, 0)
        details_layout.setSpacing(2)

        # Command title
        title_label = QLabel(self.command.title)
        title_label.setStyleSheet(
            """
            QLabel {
                color: #cccccc;
                font-weight: bold;
                font-size: 13px;
                background-color: transparent;
            }
        """
        )
        details_layout.addWidget(title_label)

        # Command description (if available)
        if self.command.description:
            desc_label = QLabel(self.command.description)
            desc_label.setStyleSheet(
                """
                QLabel {
                    color: #969696;
                    font-size: 11px;
                    background-color: transparent;
                }
            """
            )
            desc_label.setWordWrap(True)
            details_layout.addWidget(desc_label)

        layout.addLayout(details_layout, 1)  # Take remaining space

        # Keyboard shortcut (if available)
        if self.command.shortcut:
            shortcut_label = QLabel(self.command.shortcut.upper())
            shortcut_label.setStyleSheet(
                """
                QLabel {
                    color: #969696;
                    font-size: 10px;
                    font-family: 'Consolas', 'Monaco', monospace;
                    background-color: rgba(128, 128, 128, 0.2);
                    border: 1px solid rgba(128, 128, 128, 0.3);
                    border-radius: 3px;
                    padding: 2px 6px;
                }
            """
            )
            layout.addWidget(shortcut_label)

        # Category badge
        category_label = QLabel(self.command.category)
        category_label.setStyleSheet(
            """
            QLabel {
                color: #cccccc;
                font-size: 10px;
                background-color: rgba(0, 122, 204, 0.3);
                border-radius: 8px;
                padding: 2px 8px;
            }
        """
        )
        layout.addWidget(category_label)


class CommandListWidget(QListWidget):
    """Custom list widget for command display with keyboard navigation."""

    command_activated = Signal(Command)  # Emitted when command should be executed

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.commands: list[Command] = []

    def setup_ui(self):
        """Initialize the list widget UI."""
        self.setStyleSheet(
            """
            QListWidget {
                background-color: #252526;
                border: none;
                outline: none;
            }

            QListWidget::item {
                background-color: transparent;
                border: none;
                padding: 0px;
                margin: 1px 0px;
            }

            QListWidget::item:selected {
                background-color: #2a2d2e;
                border-left: 2px solid #007ACC;
            }

            QListWidget::item:hover {
                background-color: #2a2d2e;
            }
        """
        )

        self.setVerticalScrollMode(QListWidget.ScrollPerPixel)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # Connect selection change
        self.itemActivated.connect(self.on_item_activated)

    def set_commands(self, commands: list[Command]):
        """Set the list of commands to display."""
        self.clear()
        self.commands = commands

        for command in commands:
            # Create list item
            item = QListWidgetItem()
            item.setSizeHint(QSize(0, 50))  # Set minimum height

            # Create custom widget for command
            command_widget = CommandListItem(command)

            # Add to list
            self.addItem(item)
            self.setItemWidget(item, command_widget)

        # Select first item if available
        if commands:
            self.setCurrentRow(0)

    def on_item_activated(self, item: QListWidgetItem):
        """Handle item activation (double-click or Enter)."""
        row = self.row(item)
        if 0 <= row < len(self.commands):
            command = self.commands[row]
            self.command_activated.emit(command)

    def get_selected_command(self) -> Optional[Command]:
        """Get the currently selected command."""
        current_row = self.currentRow()
        if 0 <= current_row < len(self.commands):
            return self.commands[current_row]
        return None

    def keyPressEvent(self, event: QKeyEvent):
        """Handle key press events."""
        if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
            # Execute selected command
            command = self.get_selected_command()
            if command:
                self.command_activated.emit(command)
            event.accept()
        else:
            super().keyPressEvent(event)

    def apply_theme(self):
        """Apply current theme to command list widget."""
        from viloapp.core.commands.executor import execute_command

        # Get colors using command
        result = execute_command("theme.getCurrentColors")
        colors = result.value if result and result.success else {}

        self.setStyleSheet(
            f"""
            QListWidget {{
                background-color: {colors.get("editor.background", "#252526")};
                border: none;
                outline: none;
            }}

            QListWidget::item {{
                background-color: transparent;
                border: none;
                padding: 0px;
                margin: 1px 0px;
            }}

            QListWidget::item:selected {{
                background-color: {colors.get("list.hoverBackground", "#2a2d2e")};
                border-left: 2px solid {colors.get("activityBar.activeBorder", "#007ACC")};
            }}

            QListWidget::item:hover {{
                background-color: {colors.get("list.hoverBackground", "#2a2d2e")};
            }}
        """
        )


class CommandPaletteWidget(QDialog):
    """
    Main command palette widget - VSCode-style command discovery interface.

    Provides fuzzy search, keyboard navigation, and command execution.
    """

    # Signals
    command_executed = Signal(str, dict)  # command_id, kwargs
    palette_closed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.setup_shortcuts()

        # Search debounce timer
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.on_search_timer)

        # State
        self.all_commands: list[Command] = []
        self.current_query = ""

    def setup_ui(self):
        """Initialize the palette UI."""
        # Configure dialog
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setModal(True)
        self.resize(600, 400)
        self.setWindowTitle("Command Palette")

        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Create main frame for styling
        self.main_frame = QFrame()
        self.main_frame.setStyleSheet(
            """
            QFrame {
                background-color: #252526;
                border: 1px solid #3e3e42;
                border-radius: 6px;
            }
        """
        )
        layout.addWidget(self.main_frame)

        frame_layout = QVBoxLayout(self.main_frame)
        frame_layout.setContentsMargins(0, 0, 0, 0)
        frame_layout.setSpacing(0)

        # Search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search commands...")
        self.search_input.setStyleSheet(
            """
            QLineEdit {
                background-color: #252526;
                color: #cccccc;
                border: none;
                border-bottom: 1px solid #3e3e42;
                padding: 12px 16px;
                font-size: 14px;
                border-radius: 0px;
            }

            QLineEdit:focus {
                border-bottom: 2px solid #007ACC;
            }
        """
        )
        frame_layout.addWidget(self.search_input)

        # Results header
        self.results_header = QLabel()
        self.results_header.setStyleSheet(
            """
            QLabel {
                background-color: #252526;
                color: #969696;
                padding: 8px 16px;
                font-size: 11px;
                border-bottom: 1px solid #3e3e42;
            }
        """
        )
        frame_layout.addWidget(self.results_header)

        # Command list
        self.command_list = CommandListWidget()
        frame_layout.addWidget(self.command_list)

        # Status bar
        self.status_label = QLabel()
        self.status_label.setStyleSheet(
            """
            QLabel {
                background-color: #007ACC;
                color: #ffffff;
                padding: 6px 16px;
                font-size: 11px;
                border-top: 1px solid #3e3e42;
            }
        """
        )
        frame_layout.addWidget(self.status_label)

        # Connect signals
        self.search_input.textChanged.connect(self.on_search_changed)
        self.command_list.command_activated.connect(self.on_command_activated)

        # Initial status
        self.update_status("Type to search commands...")

        # Apply theme
        self.apply_theme()

    def setup_shortcuts(self):
        """Set up keyboard shortcuts."""
        # The parent widget will handle Ctrl+Shift+P to show the palette
        # Escape to close
        self.search_input.installEventFilter(self)
        self.command_list.installEventFilter(self)

    def eventFilter(self, obj, event) -> bool:
        """Filter key events for navigation."""
        if event.type() == QEvent.KeyPress:
            key = event.key()

            if key == Qt.Key_Escape:
                self.close_palette()
                return True

            elif key == Qt.Key_Down:
                # Move focus to list or navigate down
                if obj == self.search_input:
                    self.command_list.setFocus()
                    return True

            elif key == Qt.Key_Up:
                # Move focus to search or navigate up
                if obj == self.command_list and self.command_list.currentRow() == 0:
                    self.search_input.setFocus()
                    return True

            elif key in (Qt.Key_Return, Qt.Key_Enter):
                # Execute selected command
                if obj == self.search_input:
                    command = self.command_list.get_selected_command()
                    if command:
                        self.on_command_activated(command)
                    return True

        return super().eventFilter(obj, event)

    def show_palette(self, commands: list[Command], recent_commands: list[Command] = None):
        """
        Show the command palette with the given commands.

        Args:
            commands: List of available commands
            recent_commands: Optional list of recently used commands to show at top
        """
        self.all_commands = commands
        self.recent_commands = recent_commands or []
        self.current_query = ""

        # Reset UI state
        self.search_input.clear()
        self.search_input.setFocus()

        # Show all commands initially (with recent at top)
        if self.recent_commands:
            # Combine recent and all commands, removing duplicates
            recent_ids = {cmd.id for cmd in self.recent_commands}
            other_commands = [cmd for cmd in commands if cmd.id not in recent_ids]
            combined_commands = self.recent_commands + other_commands
            self.update_command_list(combined_commands)
        else:
            self.update_command_list(commands)

        # Center on parent
        if self.parent():
            parent_rect = self.parent().geometry()
            x = parent_rect.x() + (parent_rect.width() - self.width()) // 2
            y = parent_rect.y() + (parent_rect.height() - self.height()) // 2
            self.move(x, y)

        # Show dialog
        self.show()
        self.raise_()
        self.activateWindow()

    def close_palette(self):
        """Close the command palette."""
        self.hide()
        self.palette_closed.emit()

    def on_search_changed(self, text: str):
        """Handle search text changes with debouncing."""
        self.current_query = text

        # Restart debounce timer
        self.search_timer.stop()
        self.search_timer.start(150)  # 150ms debounce

    def on_search_timer(self):
        """Handle search timer timeout (debounced search)."""
        self.perform_search(self.current_query)

    def perform_search(self, query: str):
        """
        Perform command search and update results.

        Args:
            query: Search query
        """
        if not query.strip():
            # Show all commands (with recent at top if available)
            if hasattr(self, "recent_commands") and self.recent_commands:
                # Combine recent and all commands, removing duplicates
                recent_ids = {cmd.id for cmd in self.recent_commands}
                other_commands = [cmd for cmd in self.all_commands if cmd.id not in recent_ids]
                filtered_commands = self.recent_commands + other_commands
            else:
                filtered_commands = self.all_commands
        else:
            # Use fuzzy search from registry
            # First, get all command IDs that match
            all_command_ids = {cmd.id for cmd in self.all_commands}

            # Search using the registry's fuzzy search
            search_results = command_registry.search_commands(query, use_fuzzy=True)

            # Filter to only commands that were in our original list
            filtered_commands = [cmd for cmd in search_results if cmd.id in all_command_ids]

        self.update_command_list(filtered_commands)

    def update_command_list(self, commands: list[Command]):
        """Update the command list display."""
        self.command_list.set_commands(commands)

        # Update header
        if commands:
            if self.current_query:
                self.results_header.setText(
                    f"Results ({len(commands)} of {len(self.all_commands)})"
                )
            else:
                self.results_header.setText(f"All Commands ({len(commands)})")
        else:
            if self.current_query:
                self.results_header.setText("No results found")
            else:
                self.results_header.setText("No commands available")

        # Update status
        if commands:
            self.update_status("↑↓ to navigate • Enter to execute • Esc to close")
        else:
            self.update_status("No matching commands found")

    def update_status(self, message: str):
        """Update the status bar message."""
        self.status_label.setText(message)

    def on_command_activated(self, command: Command):
        """Handle command activation."""
        logger.info(f"Executing command: {command.id}")

        # Emit signal for execution
        self.command_executed.emit(command.id, {})

        # Close palette
        self.close_palette()

    def keyPressEvent(self, event: QKeyEvent):
        """Handle key press events at dialog level."""
        if event.key() == Qt.Key_Escape:
            self.close_palette()
            event.accept()
        else:
            super().keyPressEvent(event)

    def _get_theme_colors(self):
        """Get current theme colors."""
        from viloapp.core.commands.executor import execute_command

        # Get colors using command
        result = execute_command("theme.getCurrentColors")
        if result and result.success:
            return result.value

        # Fallback colors
        return {
            "editor.background": "#252526",
            "editor.foreground": "#cccccc",
            "panel.background": "#252526",
            "statusBar.background": "#007ACC",
            "statusBar.foreground": "#ffffff",
            "list.hoverBackground": "#2a2d2e",
            "activityBar.activeBorder": "#007ACC",
            "widget.border": "#3e3e42",
            "tab.inactiveForeground": "#969696",
        }

    def apply_theme(self):
        """Apply current theme to command palette."""
        colors = self._get_theme_colors()

        # Update main container style
        if hasattr(self, "main_frame"):
            self.main_frame.setStyleSheet(
                f"""
            QFrame {{
                background-color: {colors.get("editor.background", "#252526")};
                border: 1px solid {colors.get("widget.border", "#3e3e42")};
                border-radius: 6px;
            }}
            """
            )

        # Update search input style
        self.search_input.setStyleSheet(
            f"""
            QLineEdit {{
                background-color: {colors.get("panel.background", "#252526")};
                color: {colors.get("editor.foreground", "#cccccc")};
                border: none;
                border-bottom: 1px solid {colors.get("widget.border", "#3e3e42")};
                padding: 12px 16px;
                font-size: 14px;
                font-weight: 500;
            }}
        """
        )

        # Update results header style
        self.results_header.setStyleSheet(
            f"""
            QLabel {{
                background-color: {colors.get("panel.background", "#252526")};
                color: {colors.get("tab.inactiveForeground", "#969696")};
                padding: 8px 16px;
                font-size: 11px;
                border-bottom: 1px solid {colors.get("widget.border", "#3e3e42")};
            }}
        """
        )

        # Update status label style
        self.status_label.setStyleSheet(
            f"""
            QLabel {{
                background-color: {colors.get("statusBar.background", "#007ACC")};
                color: {colors.get("statusBar.foreground", "#ffffff")};
                padding: 6px 16px;
                font-size: 11px;
                border-top: 1px solid {colors.get("widget.border", "#3e3e42")};
            }}
        """
        )

        # Update list view style
        if hasattr(self, "command_list"):
            self.command_list.apply_theme()
