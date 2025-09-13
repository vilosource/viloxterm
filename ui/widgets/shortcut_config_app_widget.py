#!/usr/bin/env python3
"""
Keyboard shortcut configuration widget.

This AppWidget allows users to view and customize all keyboard shortcuts
in the application through an intuitive interface.
"""

import logging
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QPushButton, QLineEdit, QLabel, QWidget, QMessageBox,
    QHeaderView, QComboBox, QGroupBox, QSplitter
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QKeySequence, QFont, QColor

from ui.widgets.app_widget import AppWidget
from ui.widgets.widget_registry import WidgetType
from core.commands.registry import command_registry
from core.commands.base import Command
from core.keyboard.service import KeyboardService
from core.settings.service import SettingsService
from services.service_locator import ServiceLocator


logger = logging.getLogger(__name__)


@dataclass
class ShortcutItem:
    """Data model for a shortcut configuration item."""
    command_id: str
    title: str
    category: str
    description: str
    default_shortcut: str
    current_shortcut: str
    new_shortcut: Optional[str] = None
    has_conflict: bool = False
    conflicting_commands: List[str] = None

    def __post_init__(self):
        if self.conflicting_commands is None:
            self.conflicting_commands = []


class ShortcutRecorder(QLineEdit):
    """Custom widget for recording keyboard shortcuts."""

    shortcut_recorded = Signal(str)  # Emits the recorded shortcut string
    recording_started = Signal()
    recording_stopped = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.recording = False
        self.recorded_keys = []
        self.setPlaceholderText("Click to record shortcut...")
        self.setReadOnly(True)

    def mousePressEvent(self, event):
        """Start recording on click."""
        if not self.recording:
            self.start_recording()
        else:
            self.stop_recording()
        super().mousePressEvent(event)

    def start_recording(self):
        """Start recording keyboard input."""
        self.recording = True
        self.recorded_keys = []
        self.setText("Press shortcut keys...")
        self.setStyleSheet("QLineEdit { background-color: #1e1e1e; border: 2px solid #007ACC; }")
        self.recording_started.emit()
        self.setFocus()

    def stop_recording(self, save=True):
        """Stop recording and emit the result."""
        self.recording = False
        self.setStyleSheet("")

        if save and self.recorded_keys:
            shortcut_str = self.format_shortcut()
            self.setText(shortcut_str)
            self.shortcut_recorded.emit(shortcut_str)
        else:
            self.clear()

        self.recording_stopped.emit()

    def keyPressEvent(self, event):
        """Capture key press events during recording."""
        if not self.recording:
            super().keyPressEvent(event)
            return

        # Stop recording on Escape
        if event.key() == Qt.Key_Escape:
            self.stop_recording(save=False)
            return

        # Build key sequence
        key_sequence = QKeySequence(event.key() | int(event.modifiers()))
        if key_sequence.toString():
            self.recorded_keys = [key_sequence.toString()]
            self.setText(key_sequence.toString())

            # Auto-stop after capturing a valid shortcut
            QTimer.singleShot(500, lambda: self.stop_recording(save=True))

    def format_shortcut(self) -> str:
        """Format the recorded shortcut for display."""
        if not self.recorded_keys:
            return ""

        # Convert to lowercase and use consistent separator
        shortcut = self.recorded_keys[0]
        # Normalize the shortcut format (e.g., "Ctrl+N" -> "ctrl+n")
        parts = shortcut.split("+")
        normalized_parts = []

        for part in parts:
            part_lower = part.lower().strip()
            # Handle special cases
            if part_lower in ["ctrl", "alt", "shift", "meta", "cmd"]:
                normalized_parts.append(part_lower)
            else:
                # Keep the key as-is but lowercase
                normalized_parts.append(part_lower)

        return "+".join(normalized_parts)

    def set_shortcut(self, shortcut: str):
        """Set the displayed shortcut."""
        self.setText(shortcut)
        self.recorded_keys = [shortcut] if shortcut else []


class ShortcutConfigAppWidget(AppWidget):
    """
    AppWidget for configuring keyboard shortcuts.

    Provides a comprehensive interface for viewing, editing, and managing
    all keyboard shortcuts in the application.
    """

    def __init__(self, widget_id: str, parent=None):
        """Initialize the shortcut configuration widget."""
        super().__init__(widget_id, WidgetType.SETTINGS, parent)

        # Get services
        self.locator = ServiceLocator.get_instance()
        self.keyboard_service = self.locator.get(KeyboardService)
        self.settings_service = self.locator.get(SettingsService)

        # Data storage
        self.shortcut_items: Dict[str, ShortcutItem] = {}
        self.tree_items: Dict[str, QTreeWidgetItem] = {}
        self.modified_shortcuts: Dict[str, str] = {}  # command_id -> new_shortcut

        # UI elements
        self.tree_widget = None
        self.search_input = None
        self.category_filter = None
        self.conflict_label = None
        self.apply_button = None
        self.cancel_button = None
        self.reset_button = None

        self.setup_ui()
        self.load_shortcuts()

    def setup_ui(self):
        """Set up the user interface."""
        # Apply the theme stylesheet to the entire widget
        self.apply_theme()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)

        # Header with search and filter
        header_layout = QHBoxLayout()

        # Search input
        search_label = QLabel("Search:")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Type to filter commands...")
        self.search_input.textChanged.connect(self.filter_shortcuts)

        # Category filter
        category_label = QLabel("Category:")
        self.category_filter = QComboBox()
        self.category_filter.addItem("All Categories")
        self.category_filter.currentTextChanged.connect(self.filter_shortcuts)

        header_layout.addWidget(search_label)
        header_layout.addWidget(self.search_input, 2)
        header_layout.addWidget(category_label)
        header_layout.addWidget(self.category_filter, 1)
        header_layout.addStretch()

        layout.addLayout(header_layout)

        # Main content area
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)

        # Tree widget for shortcuts
        self.tree_widget = QTreeWidget()
        self.tree_widget.setHeaderLabels(["Command", "Current Shortcut", "New Shortcut"])
        self.tree_widget.setRootIsDecorated(True)
        # Don't use alternating row colors - let theme handle it
        self.tree_widget.setAlternatingRowColors(False)
        self.tree_widget.setSortingEnabled(True)
        self.tree_widget.sortByColumn(0, Qt.AscendingOrder)

        # Set column widths
        header = self.tree_widget.header()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeToContents)

        content_layout.addWidget(self.tree_widget)

        # Conflict warning area
        self.conflict_label = QLabel()
        # Use warning color from theme for conflict display
        self.conflict_label.setStyleSheet(f"""
            QLabel {{
                background-color: rgba(244, 135, 113, 0.1);
                color: #f48771;
                padding: 8px;
                border: 1px solid #f48771;
                border-radius: 4px;
            }}
        """)
        self.conflict_label.setWordWrap(True)
        self.conflict_label.hide()
        content_layout.addWidget(self.conflict_label)

        layout.addWidget(content_widget)

        # Button bar
        button_layout = QHBoxLayout()

        # Reset buttons
        self.reset_all_button = QPushButton("Reset All")
        self.reset_all_button.setToolTip("Reset all shortcuts to defaults")
        self.reset_all_button.clicked.connect(self.reset_all_shortcuts)

        self.reset_selected_button = QPushButton("Reset Selected")
        self.reset_selected_button.setToolTip("Reset selected shortcuts to defaults")
        self.reset_selected_button.clicked.connect(self.reset_selected_shortcuts)

        button_layout.addWidget(self.reset_all_button)
        button_layout.addWidget(self.reset_selected_button)
        button_layout.addStretch()

        # Apply/Cancel buttons
        self.apply_button = QPushButton("Apply")
        self.apply_button.setToolTip("Apply changes and close")
        self.apply_button.clicked.connect(self.apply_changes)
        self.apply_button.setEnabled(False)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setToolTip("Discard changes and close")
        self.cancel_button.clicked.connect(self.cancel_changes)

        button_layout.addWidget(self.apply_button)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)

    def load_shortcuts(self):
        """Load all shortcuts from the command registry."""
        # Clear existing items
        self.tree_widget.clear()
        self.shortcut_items.clear()
        self.tree_items.clear()

        # Get all commands
        commands = command_registry.get_all_commands()

        # Get current custom shortcuts from settings
        custom_shortcuts = {}
        if self.settings_service:
            custom_shortcuts = self.settings_service.get_keyboard_shortcuts()

        # Group commands by category
        categories = {}
        category_set = set()

        for command in commands:
            category = command.category or "Other"
            category_set.add(category)

            if category not in categories:
                categories[category] = []

            # Create shortcut item
            item = ShortcutItem(
                command_id=command.id,
                title=command.title,
                category=category,
                description=command.description or "",
                default_shortcut=command.shortcut or "",
                current_shortcut=custom_shortcuts.get(command.id, command.shortcut or "")
            )

            categories[category].append(item)
            self.shortcut_items[command.id] = item

        # Update category filter
        self.category_filter.clear()
        self.category_filter.addItem("All Categories")
        for category in sorted(category_set):
            self.category_filter.addItem(category)

        # Create tree structure
        for category in sorted(categories.keys()):
            category_item = QTreeWidgetItem(self.tree_widget)
            category_item.setText(0, category)
            category_item.setFont(0, QFont("", -1, QFont.Bold))
            category_item.setExpanded(True)

            for shortcut_item in sorted(categories[category], key=lambda x: x.title):
                self.add_shortcut_to_tree(shortcut_item, category_item)

    def add_shortcut_to_tree(self, shortcut_item: ShortcutItem, parent_item: QTreeWidgetItem):
        """Add a shortcut item to the tree."""
        tree_item = QTreeWidgetItem(parent_item)
        tree_item.setText(0, shortcut_item.title)
        tree_item.setToolTip(0, shortcut_item.description)
        tree_item.setText(1, shortcut_item.current_shortcut)

        # Create recorder widget for the third column
        recorder = ShortcutRecorder()
        recorder.set_shortcut(shortcut_item.new_shortcut or "")
        recorder.shortcut_recorded.connect(
            lambda s, cmd_id=shortcut_item.command_id: self.on_shortcut_changed(cmd_id, s)
        )

        self.tree_widget.setItemWidget(tree_item, 2, recorder)

        # Store references
        tree_item.setData(0, Qt.UserRole, shortcut_item.command_id)
        self.tree_items[shortcut_item.command_id] = tree_item

    def on_shortcut_changed(self, command_id: str, new_shortcut: str):
        """Handle shortcut change for a command."""
        if command_id not in self.shortcut_items:
            return

        item = self.shortcut_items[command_id]

        # Check if it's different from current
        if new_shortcut == item.current_shortcut:
            # Remove from modified if it was there
            if command_id in self.modified_shortcuts:
                del self.modified_shortcuts[command_id]
            item.new_shortcut = None
        else:
            # Add to modified
            self.modified_shortcuts[command_id] = new_shortcut
            item.new_shortcut = new_shortcut

        # Check for conflicts
        self.check_conflicts()

        # Update apply button state
        self.apply_button.setEnabled(bool(self.modified_shortcuts))

    def check_conflicts(self):
        """Check for shortcut conflicts."""
        conflicts = []
        shortcut_map = {}

        # Build map of all shortcuts (current + modified)
        for cmd_id, item in self.shortcut_items.items():
            shortcut = item.new_shortcut if item.new_shortcut is not None else item.current_shortcut
            if shortcut:
                if shortcut not in shortcut_map:
                    shortcut_map[shortcut] = []
                shortcut_map[shortcut].append(cmd_id)

        # Find conflicts
        for shortcut, commands in shortcut_map.items():
            if len(commands) > 1:
                conflicts.append((shortcut, commands))
                # Mark items as having conflicts
                for cmd_id in commands:
                    self.shortcut_items[cmd_id].has_conflict = True
                    self.shortcut_items[cmd_id].conflicting_commands = [c for c in commands if c != cmd_id]

        # Update UI
        if conflicts:
            conflict_text = "⚠ Conflicts detected:\n"
            for shortcut, commands in conflicts:
                cmd_titles = [self.shortcut_items[c].title for c in commands]
                conflict_text += f"• {shortcut}: {', '.join(cmd_titles)}\n"

            self.conflict_label.setText(conflict_text.strip())
            self.conflict_label.show()
        else:
            self.conflict_label.hide()
            # Clear conflict flags
            for item in self.shortcut_items.values():
                item.has_conflict = False
                item.conflicting_commands = []

    def filter_shortcuts(self):
        """Filter displayed shortcuts based on search and category."""
        search_text = self.search_input.text().lower()
        category_filter = self.category_filter.currentText()

        for i in range(self.tree_widget.topLevelItemCount()):
            category_item = self.tree_widget.topLevelItem(i)
            category_name = category_item.text(0)

            # Check category filter
            category_visible = (category_filter == "All Categories" or
                              category_name == category_filter)

            # Check children visibility
            any_child_visible = False
            for j in range(category_item.childCount()):
                child_item = category_item.child(j)
                command_id = child_item.data(0, Qt.UserRole)

                if command_id in self.shortcut_items:
                    item = self.shortcut_items[command_id]

                    # Check search filter
                    visible = category_visible and (
                        not search_text or
                        search_text in item.title.lower() or
                        search_text in item.description.lower() or
                        search_text in item.current_shortcut.lower()
                    )

                    child_item.setHidden(not visible)
                    if visible:
                        any_child_visible = True

            # Hide category if no children are visible
            category_item.setHidden(not any_child_visible)

    def reset_all_shortcuts(self):
        """Reset all shortcuts to defaults."""
        reply = QMessageBox.question(
            self,
            "Reset All Shortcuts",
            "This will reset ALL keyboard shortcuts to their default values.\n\n"
            "Are you sure you want to continue?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            # Clear all modifications
            self.modified_shortcuts.clear()

            # Reset all items to defaults
            for item in self.shortcut_items.values():
                item.new_shortcut = item.default_shortcut
                if item.command_id in self.tree_items:
                    tree_item = self.tree_items[item.command_id]
                    recorder = self.tree_widget.itemWidget(tree_item, 2)
                    if recorder:
                        recorder.set_shortcut(item.default_shortcut)

            # Mark all as modified (to apply defaults)
            for cmd_id, item in self.shortcut_items.items():
                if item.default_shortcut != item.current_shortcut:
                    self.modified_shortcuts[cmd_id] = item.default_shortcut

            self.check_conflicts()
            self.apply_button.setEnabled(bool(self.modified_shortcuts))

    def reset_selected_shortcuts(self):
        """Reset selected shortcuts to defaults."""
        selected_items = self.tree_widget.selectedItems()
        if not selected_items:
            QMessageBox.information(self, "No Selection", "Please select shortcuts to reset.")
            return

        for tree_item in selected_items:
            command_id = tree_item.data(0, Qt.UserRole)
            if command_id and command_id in self.shortcut_items:
                item = self.shortcut_items[command_id]
                item.new_shortcut = item.default_shortcut

                # Update UI
                recorder = self.tree_widget.itemWidget(tree_item, 2)
                if recorder:
                    recorder.set_shortcut(item.default_shortcut)

                # Update modified list
                if item.default_shortcut != item.current_shortcut:
                    self.modified_shortcuts[command_id] = item.default_shortcut
                elif command_id in self.modified_shortcuts:
                    del self.modified_shortcuts[command_id]

        self.check_conflicts()
        self.apply_button.setEnabled(bool(self.modified_shortcuts))

    def apply_changes(self):
        """Apply all shortcut changes."""
        if not self.modified_shortcuts:
            return

        # Check for conflicts one more time
        has_conflicts = any(item.has_conflict for item in self.shortcut_items.values())
        if has_conflicts:
            reply = QMessageBox.warning(
                self,
                "Conflicts Detected",
                "There are conflicting keyboard shortcuts.\n\n"
                "Do you want to apply anyway? Conflicting shortcuts may not work as expected.",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply != QMessageBox.Yes:
                return

        # Apply changes to settings service
        if self.settings_service:
            for command_id, new_shortcut in self.modified_shortcuts.items():
                self.settings_service.set_keyboard_shortcut(command_id, new_shortcut)

        # Re-register shortcuts in keyboard service
        if self.keyboard_service:
            for command_id, new_shortcut in self.modified_shortcuts.items():
                # Unregister old shortcut
                self.keyboard_service.unregister_shortcut(f"command.{command_id}")

                # Register new shortcut if not empty
                if new_shortcut:
                    command = command_registry.get_command(command_id)
                    if command:
                        self.keyboard_service.register_shortcut_from_string(
                            shortcut_id=f"command.{command_id}",
                            sequence_str=new_shortcut,
                            command_id=command_id,
                            description=command.description or command.title,
                            source="user",
                            priority=100  # User shortcuts have higher priority
                        )

        # Show success message
        QMessageBox.information(
            self,
            "Shortcuts Updated",
            f"Successfully updated {len(self.modified_shortcuts)} keyboard shortcuts.\n\n"
            "Changes have been applied immediately."
        )

        # Clear modifications and reload
        self.modified_shortcuts.clear()
        self.load_shortcuts()
        self.apply_button.setEnabled(False)

        # Request to close the tab
        self.request_action("close", {"widget_id": self.widget_id})

    def cancel_changes(self):
        """Cancel changes and close."""
        if self.modified_shortcuts:
            reply = QMessageBox.question(
                self,
                "Discard Changes",
                "You have unsaved changes.\n\nDo you want to discard them?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )

            if reply != QMessageBox.Yes:
                return

        # Request to close the tab
        self.request_action("close", {"widget_id": self.widget_id})

    def get_title(self) -> str:
        """Get title for this widget."""
        return "Keyboard Shortcuts"

    def get_icon_name(self) -> Optional[str]:
        """Get icon name for this widget type."""
        return "keyboard"

    def can_close(self) -> bool:
        """Check if widget can be closed safely."""
        if self.modified_shortcuts:
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes to keyboard shortcuts.\n\n"
                "Do you want to save them before closing?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel,
                QMessageBox.Save
            )

            if reply == QMessageBox.Save:
                self.apply_changes()
                return True
            elif reply == QMessageBox.Discard:
                return True
            else:
                return False

        return True

    def apply_theme(self):
        """Apply current theme to shortcut config widget."""
        from services.service_locator import ServiceLocator
        from services.theme_service import ThemeService

        locator = ServiceLocator.get_instance()
        theme_service = locator.get(ThemeService)
        theme_provider = theme_service.get_theme_provider() if theme_service else None
        if theme_provider:
            # Get the stylesheet for this widget type
            self.setStyleSheet(theme_provider.get_stylesheet("settings_widget"))