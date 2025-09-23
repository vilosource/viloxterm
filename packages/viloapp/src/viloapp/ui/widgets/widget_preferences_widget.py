"""
Widget preferences settings UI.

Allows users to configure default widgets for different contexts.
"""

import logging

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from viloapp.services.widget_service import get_widget_service

logger = logging.getLogger(__name__)


class WidgetPreferencesWidget(QWidget):
    """Widget for configuring widget preferences."""

    preferences_changed = Signal()

    def __init__(self, parent=None):
        """Initialize widget preferences UI.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)

        self.widget_service = get_widget_service()
        self._preference_combos = {}

        self._setup_ui()
        self._load_preferences()

    def _setup_ui(self):
        """Set up the UI."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Title
        title = QLabel("Widget Preferences")
        title.setObjectName("settingsTitle")
        main_layout.addWidget(title)

        # Description
        desc = QLabel(
            "Configure default widgets for different contexts.\n"
            "These preferences determine which widget type opens by default."
        )
        desc.setWordWrap(True)
        desc.setObjectName("settingsDescription")
        main_layout.addWidget(desc)

        # Scroll area for preferences
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        # General preferences
        general_group = self._create_general_group()
        scroll_layout.addWidget(general_group)

        # Context-specific preferences
        context_group = self._create_context_group()
        scroll_layout.addWidget(context_group)

        # File type preferences
        file_group = self._create_file_type_group()
        scroll_layout.addWidget(file_group)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        main_layout.addWidget(scroll)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        reset_button = QPushButton("Reset to Defaults")
        reset_button.clicked.connect(self._reset_preferences)
        button_layout.addWidget(reset_button)

        apply_button = QPushButton("Apply")
        apply_button.setObjectName("primaryButton")
        apply_button.clicked.connect(self._apply_preferences)
        button_layout.addWidget(apply_button)

        main_layout.addLayout(button_layout)

    def _create_general_group(self) -> QGroupBox:
        """Create general preferences group.

        Returns:
            QGroupBox with general settings
        """
        group = QGroupBox("General")
        layout = QFormLayout()

        # Default widget for new tabs
        new_tab_combo = self._create_widget_combo("new_tab")
        layout.addRow("New Tab:", new_tab_combo)

        # Default widget for splits
        split_combo = self._create_widget_combo("split")
        layout.addRow("Split Pane:", split_combo)

        # Default widget when no context
        general_combo = self._create_widget_combo("general")
        layout.addRow("Default Widget:", general_combo)

        group.setLayout(layout)
        return group

    def _create_context_group(self) -> QGroupBox:
        """Create context-specific preferences group.

        Returns:
            QGroupBox with context settings
        """
        group = QGroupBox("Context-Specific")
        layout = QFormLayout()

        # Command palette default
        palette_combo = self._create_widget_combo("command_palette")
        layout.addRow("Command Palette:", palette_combo)

        # Quick open default
        quick_open_combo = self._create_widget_combo("quick_open")
        layout.addRow("Quick Open:", quick_open_combo)

        # Search results default
        search_combo = self._create_widget_combo("search_results")
        layout.addRow("Search Results:", search_combo)

        group.setLayout(layout)
        return group

    def _create_file_type_group(self) -> QGroupBox:
        """Create file type preferences group.

        Returns:
            QGroupBox with file type settings
        """
        group = QGroupBox("File Types")
        layout = QFormLayout()

        # Common file types
        file_types = [
            ("Python Files", "file:python"),
            ("JavaScript Files", "file:javascript"),
            ("TypeScript Files", "file:typescript"),
            ("JSON Files", "file:json"),
            ("Markdown Files", "file:markdown"),
            ("Text Files", "file:text"),
            ("Image Files", "file:image"),
        ]

        for label, context in file_types:
            combo = self._create_widget_combo(context)
            layout.addRow(f"{label}:", combo)

        group.setLayout(layout)
        return group

    def _create_widget_combo(self, context: str) -> QComboBox:
        """Create combo box for widget selection.

        Args:
            context: The preference context

        Returns:
            QComboBox configured for widget selection
        """
        combo = QComboBox()

        # Add "Default" option
        combo.addItem("(System Default)", None)

        # Get available widgets
        if self.widget_service:
            widgets = self.widget_service.get_available_widgets()

            # Group by category if needed
            for widget in widgets:
                # Only show widgets that can be defaults
                if widget.get("can_be_default", True):
                    combo.addItem(widget["name"], widget["id"])

        # Store reference
        self._preference_combos[context] = combo

        return combo

    def _load_preferences(self):
        """Load current preferences into UI."""
        if not self.widget_service:
            return

        preferences = self.widget_service.get_all_preferences()

        for context, combo in self._preference_combos.items():
            widget_id = preferences.get(context)
            if widget_id:
                # Find and select the item
                index = combo.findData(widget_id)
                if index >= 0:
                    combo.setCurrentIndex(index)
            else:
                # Select default
                combo.setCurrentIndex(0)

    def _apply_preferences(self):
        """Apply preference changes."""
        if not self.widget_service:
            return

        # Collect all preferences
        for context, combo in self._preference_combos.items():
            widget_id = combo.currentData()

            if widget_id:
                # Set preference
                self.widget_service.set_default_widget(context, widget_id)
            else:
                # Clear preference (use system default)
                self.widget_service.clear_default_widget(context)

        # Emit change signal
        self.preferences_changed.emit()

        logger.info("Widget preferences applied")

    def _reset_preferences(self):
        """Reset all preferences to defaults."""
        if not self.widget_service:
            return

        # Clear all preferences
        for context in self._preference_combos.keys():
            self.widget_service.clear_default_widget(context)

        # Reload UI
        self._load_preferences()

        # Emit change signal
        self.preferences_changed.emit()

        logger.info("Widget preferences reset to defaults")


class WidgetPreferencesDialog(QWidget):
    """Standalone dialog/widget for widget preferences."""

    def __init__(self, parent=None):
        """Initialize preferences dialog.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)

        self.setWindowTitle("Widget Preferences")
        self.resize(600, 500)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Add preferences widget
        self.prefs_widget = WidgetPreferencesWidget(self)
        layout.addWidget(self.prefs_widget)

        # Connect changes
        self.prefs_widget.preferences_changed.connect(self._on_preferences_changed)

    def _on_preferences_changed(self):
        """Handle preference changes."""
        # Could show a notification or update status
        logger.debug("Preferences changed in dialog")
