#!/usr/bin/env python3
"""
Command palette widget - the main UI component for command discovery and execution.

This widget provides a VSCode-style command palette with fuzzy search, 
keyboard navigation, and command execution.
"""

from typing import List, Optional, Dict, Any
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLineEdit, QListWidget, QListWidgetItem,
    QLabel, QWidget, QFrame, QApplication
)
from PySide6.QtCore import Qt, Signal, QSize, QTimer, QEvent
from PySide6.QtGui import QKeyEvent, QFont, QPalette, QIcon
import logging

from core.commands.base import Command
from ui.vscode_theme import *
from ui.icon_manager import get_icon_manager

logger = logging.getLogger(__name__)


class CommandListItem(QWidget):
    """Custom widget for displaying command items in the list."""
    
    def __init__(self, command: Command, parent=None):
        super().__init__(parent)
        self.command = command
        self.setup_ui()
    
    def setup_ui(self):
        """Initialize the command item UI."""
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
        title_label.setStyleSheet(f"""
            QLabel {{
                color: {EDITOR_FOREGROUND};
                font-weight: bold;
                font-size: 13px;
            }}
        """)
        details_layout.addWidget(title_label)
        
        # Command description (if available)
        if self.command.description:
            desc_label = QLabel(self.command.description)
            desc_label.setStyleSheet(f"""
                QLabel {{
                    color: {TAB_INACTIVE_FOREGROUND};
                    font-size: 11px;
                }}
            """)
            desc_label.setWordWrap(True)
            details_layout.addWidget(desc_label)
        
        layout.addLayout(details_layout, 1)  # Take remaining space
        
        # Keyboard shortcut (if available)
        if self.command.shortcut:
            shortcut_label = QLabel(self.command.shortcut.upper())
            shortcut_label.setStyleSheet(f"""
                QLabel {{
                    color: {TAB_INACTIVE_FOREGROUND};
                    font-size: 10px;
                    font-family: 'Consolas', 'Monaco', monospace;
                    background-color: {PANE_HEADER_BACKGROUND};
                    border: 1px solid {SPLITTER_BACKGROUND};
                    border-radius: 3px;
                    padding: 2px 6px;
                }}
            """)
            layout.addWidget(shortcut_label)
        
        # Category badge
        category_label = QLabel(self.command.category)
        category_label.setStyleSheet(f"""
            QLabel {{
                color: {ACTIVITY_BAR_FOREGROUND};
                font-size: 10px;
                background-color: {ACTIVITY_BAR_ACTIVE_BORDER};
                border-radius: 8px;
                padding: 2px 8px;
            }}
        """)
        layout.addWidget(category_label)


class CommandListWidget(QListWidget):
    """Custom list widget for command display with keyboard navigation."""
    
    command_activated = Signal(Command)  # Emitted when command should be executed
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.commands: List[Command] = []
        
    def setup_ui(self):
        """Initialize the list widget UI."""
        self.setStyleSheet(f"""
            QListWidget {{
                background-color: {EDITOR_BACKGROUND};
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
                background-color: {LIST_HOVER_BACKGROUND};
                border-left: 2px solid {ACTIVITY_BAR_ACTIVE_BORDER};
            }}
            
            QListWidget::item:hover {{
                background-color: {LIST_HOVER_BACKGROUND};
            }}
        """)
        
        self.setVerticalScrollMode(QListWidget.ScrollPerPixel)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Connect selection change
        self.itemActivated.connect(self.on_item_activated)
        
    def set_commands(self, commands: List[Command]):
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
        self.all_commands: List[Command] = []
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
        main_frame = QFrame()
        main_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {EDITOR_BACKGROUND};
                border: 1px solid {SPLITTER_BACKGROUND};
                border-radius: 6px;
            }}
        """)
        layout.addWidget(main_frame)
        
        frame_layout = QVBoxLayout(main_frame)
        frame_layout.setContentsMargins(0, 0, 0, 0)
        frame_layout.setSpacing(0)
        
        # Search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search commands...")
        self.search_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {PANEL_BACKGROUND};
                color: {EDITOR_FOREGROUND};
                border: none;
                border-bottom: 1px solid {SPLITTER_BACKGROUND};
                padding: 12px 16px;
                font-size: 14px;
                border-radius: 0px;
            }}
            
            QLineEdit:focus {{
                border-bottom: 2px solid {ACTIVITY_BAR_ACTIVE_BORDER};
            }}
        """)
        frame_layout.addWidget(self.search_input)
        
        # Results header
        self.results_header = QLabel()
        self.results_header.setStyleSheet(f"""
            QLabel {{
                background-color: {PANEL_BACKGROUND};
                color: {TAB_INACTIVE_FOREGROUND};
                padding: 8px 16px;
                font-size: 11px;
                border-bottom: 1px solid {SPLITTER_BACKGROUND};
            }}
        """)
        frame_layout.addWidget(self.results_header)
        
        # Command list
        self.command_list = CommandListWidget()
        frame_layout.addWidget(self.command_list)
        
        # Status bar
        self.status_label = QLabel()
        self.status_label.setStyleSheet(f"""
            QLabel {{
                background-color: {STATUS_BAR_BACKGROUND};
                color: {STATUS_BAR_FOREGROUND};
                padding: 6px 16px;
                font-size: 11px;
                border-top: 1px solid {SPLITTER_BACKGROUND};
            }}
        """)
        frame_layout.addWidget(self.status_label)
        
        # Connect signals
        self.search_input.textChanged.connect(self.on_search_changed)
        self.command_list.command_activated.connect(self.on_command_activated)
        
        # Initial status
        self.update_status("Type to search commands...")
    
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
    
    def show_palette(self, commands: List[Command]):
        """
        Show the command palette with the given commands.
        
        Args:
            commands: List of available commands
        """
        self.all_commands = commands
        self.current_query = ""
        
        # Reset UI state
        self.search_input.clear()
        self.search_input.setFocus()
        
        # Show all commands initially
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
            # Show all commands
            filtered_commands = self.all_commands
        else:
            # Filter commands (will be replaced with fuzzy search from registry)
            filtered_commands = []
            query_lower = query.lower()
            
            for command in self.all_commands:
                # Simple substring matching for now
                if (query_lower in command.title.lower() or
                    query_lower in command.category.lower() or
                    (command.description and query_lower in command.description.lower())):
                    filtered_commands.append(command)
        
        self.update_command_list(filtered_commands)
    
    def update_command_list(self, commands: List[Command]):
        """Update the command list display."""
        self.command_list.set_commands(commands)
        
        # Update header
        if commands:
            if self.current_query:
                self.results_header.setText(f"Results ({len(commands)} of {len(self.all_commands)})")
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