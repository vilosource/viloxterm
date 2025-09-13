#!/usr/bin/env python3
"""
Theme editor widget for creating and customizing themes.

Provides a complete interface for editing, previewing, and managing themes.
"""

from typing import Dict, Optional, List, Tuple
from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QTabWidget, QPushButton, QLabel, QComboBox,
    QScrollArea, QFrame, QGroupBox, QMessageBox,
    QFileDialog, QLineEdit, QTextEdit, QToolBar,
    QToolButton, QMenu
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QAction, QIcon
import json
import logging

from ui.widgets.app_widget import AppWidget
from ui.widgets.color_picker_widget import ColorPickerField
from ui.widgets.theme_preview_widget import ThemePreviewWidget
from core.themes.property_categories import ThemePropertyCategories
from core.themes.theme import Theme
from core.themes.importers import VSCodeThemeImporter

logger = logging.getLogger(__name__)


class ThemeEditorAppWidget(AppWidget):
    """
    Complete theme editor as an app widget.

    Features:
    - Theme selection and management
    - Property editor with categorized color pickers
    - Live preview
    - Import/export functionality
    - Save/reset capabilities
    """

    def __init__(self, widget_id: str = None, parent: Optional[QWidget] = None):
        """
        Initialize theme editor.

        Args:
            widget_id: Unique widget identifier (auto-generated if None)
            parent: Parent widget
        """
        # Generate widget ID if not provided
        if widget_id is None:
            import uuid
            widget_id = str(uuid.uuid4())[:8]

        # Import WidgetType here to avoid circular imports
        from ui.widgets.widget_registry import WidgetType

        # Initialize AppWidget with SETTINGS type
        super().__init__(widget_id, WidgetType.SETTINGS, parent)

        self._current_theme: Optional[Theme] = None
        self._modified = False
        self._preview_timer = QTimer()
        self._preview_timer.setSingleShot(True)
        self._preview_timer.timeout.connect(self._apply_preview)

        self._color_fields: Dict[str, ColorPickerField] = {}
        self._updating = False  # Flag to prevent recursive updates
        self._theme_service = None  # Will be set in _load_current_theme

        self._setup_ui()
        self._load_current_theme()
        self._connect_theme_signals()

    def get_title(self) -> str:
        """Get widget title for tab/pane."""
        return "Theme Editor"

    def get_icon(self) -> Optional[QIcon]:
        """Get widget icon."""
        # Return palette icon if available
        return None

    def can_close(self) -> bool:
        """Check if widget can be closed."""
        if self._modified:
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Do you want to save them?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
            )

            if reply == QMessageBox.Save:
                return self._save_theme()
            elif reply == QMessageBox.Cancel:
                return False

        return True

    def _setup_ui(self):
        """Set up the editor UI."""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Toolbar
        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)

        # Theme selector
        selector_layout = QHBoxLayout()
        selector_layout.setContentsMargins(8, 8, 8, 8)

        selector_layout.addWidget(QLabel("Theme:"))

        self._theme_combo = QComboBox()
        self._theme_combo.currentTextChanged.connect(self._on_theme_changed)
        selector_layout.addWidget(self._theme_combo, 1)

        self._new_button = QPushButton("New")
        self._new_button.clicked.connect(self._create_new_theme)
        selector_layout.addWidget(self._new_button)

        self._duplicate_button = QPushButton("Duplicate")
        self._duplicate_button.clicked.connect(self._duplicate_theme)
        selector_layout.addWidget(self._duplicate_button)

        layout.addLayout(selector_layout)

        # Main content splitter
        splitter = QSplitter(Qt.Horizontal)

        # Left: Property editor
        property_widget = self._create_property_editor()
        splitter.addWidget(property_widget)

        # Right: Preview
        preview_container = QFrame()
        preview_layout = QVBoxLayout()
        preview_layout.setContentsMargins(8, 8, 8, 8)

        preview_label = QLabel("Preview")
        preview_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        preview_layout.addWidget(preview_label)

        self._preview_widget = ThemePreviewWidget()
        preview_layout.addWidget(self._preview_widget, 1)

        preview_container.setLayout(preview_layout)
        splitter.addWidget(preview_container)

        # Set splitter sizes (60/40 split)
        splitter.setSizes([600, 400])

        layout.addWidget(splitter, 1)

        # Bottom buttons
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(8, 8, 8, 8)

        self._apply_button = QPushButton("Apply")
        self._apply_button.clicked.connect(self._apply_theme)
        self._apply_button.setEnabled(False)
        button_layout.addWidget(self._apply_button)

        self._save_button = QPushButton("Save")
        self._save_button.clicked.connect(self._save_theme)
        self._save_button.setEnabled(False)
        button_layout.addWidget(self._save_button)

        button_layout.addStretch()

        self._reset_button = QPushButton("Reset")
        self._reset_button.clicked.connect(self._reset_changes)
        self._reset_button.setEnabled(False)
        button_layout.addWidget(self._reset_button)

        layout.addLayout(button_layout)

        self.setLayout(layout)

    def _create_toolbar(self) -> QToolBar:
        """Create editor toolbar."""
        toolbar = QToolBar()

        # Import action
        import_action = QAction("Import", self)
        import_action.setToolTip("Import theme from file")
        import_action.triggered.connect(self._import_theme)
        toolbar.addAction(import_action)

        # Export action
        export_action = QAction("Export", self)
        export_action.setToolTip("Export current theme")
        export_action.triggered.connect(self._export_theme)
        toolbar.addAction(export_action)

        toolbar.addSeparator()

        # Import VSCode action
        vscode_action = QAction("Import VSCode", self)
        vscode_action.setToolTip("Import VSCode theme")
        vscode_action.triggered.connect(self._import_vscode_theme)
        toolbar.addAction(vscode_action)

        toolbar.addSeparator()

        # Delete action
        delete_action = QAction("Delete", self)
        delete_action.setToolTip("Delete current theme")
        delete_action.triggered.connect(self._delete_theme)
        toolbar.addAction(delete_action)

        return toolbar

    def _create_property_editor(self) -> QWidget:
        """Create property editor with categorized color pickers."""
        container = QFrame()
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)

        # Search/filter
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))

        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Filter properties...")
        self._search_input.textChanged.connect(self._filter_properties)
        search_layout.addWidget(self._search_input)

        layout.addLayout(search_layout)

        # Scrollable property area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Property container
        property_container = QWidget()
        self._property_layout = QVBoxLayout()
        self._property_layout.setSpacing(8)

        # Create categorized property editors
        categories = ThemePropertyCategories.get_categories()

        for category_name, subcategories in categories.items():
            # Category group box
            category_box = QGroupBox(category_name)
            category_layout = QVBoxLayout()

            for subcategory_name, properties in subcategories.items():
                # Subcategory label
                if len(subcategories) > 1:  # Only show subcategory if multiple
                    subcat_label = QLabel(subcategory_name)
                    subcat_label.setStyleSheet("font-weight: bold; margin-top: 8px;")
                    category_layout.addWidget(subcat_label)

                # Property fields
                for prop_key, description in properties:
                    field = ColorPickerField(
                        key=prop_key,
                        label=description,
                        initial_color="#000000",
                        description=prop_key  # Show key as tooltip
                    )
                    field.color_changed.connect(self._on_color_changed)

                    self._color_fields[prop_key] = field
                    category_layout.addWidget(field)

            category_box.setLayout(category_layout)
            self._property_layout.addWidget(category_box)

        self._property_layout.addStretch()
        property_container.setLayout(self._property_layout)

        scroll_area.setWidget(property_container)
        layout.addWidget(scroll_area, 1)

        container.setLayout(layout)
        return container

    def _load_current_theme(self):
        """Load current theme and available themes."""
        try:
            from services.service_locator import ServiceLocator
            from services.theme_service import ThemeService

            locator = ServiceLocator()
            self._theme_service = locator.get(ThemeService)

            if self._theme_service:
                # Load available themes
                themes = self._theme_service.get_available_themes()
                self._theme_combo.clear()

                for theme_info in themes:
                    self._theme_combo.addItem(theme_info.name, theme_info.id)

                # Select current theme
                current_theme = self._theme_service.get_current_theme()
                if current_theme:
                    index = self._theme_combo.findData(current_theme.id)
                    if index >= 0:
                        self._theme_combo.setCurrentIndex(index)
                    self._load_theme(current_theme)

        except Exception as e:
            logger.error(f"Failed to load themes: {e}")

    def _load_theme(self, theme: Theme):
        """Load theme into editor."""
        if self._updating:
            return  # Prevent recursive updates

        self._updating = True
        try:
            self._current_theme = theme

            # Update color fields
            for prop_key, field in self._color_fields.items():
                color = theme.get_color(prop_key, "#000000")
                field.set_color(color)

            # Update preview
            self._preview_widget.apply_theme_colors(theme.colors)

            # Reset modified state
            self._modified = False
            self._update_button_states()
        finally:
            self._updating = False

    def _on_theme_changed(self, theme_name: str):
        """Handle theme selection change."""
        if self._modified:
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Do you want to discard them?",
                QMessageBox.Discard | QMessageBox.Cancel
            )

            if reply == QMessageBox.Cancel:
                # Restore previous selection
                if self._current_theme:
                    index = self._theme_combo.findData(self._current_theme.id)
                    if index >= 0:
                        self._theme_combo.setCurrentIndex(index)
                return

        # Load selected theme
        theme_id = self._theme_combo.currentData()
        if theme_id and self._theme_service:
            theme = self._theme_service.get_theme(theme_id)
            if theme:
                self._load_theme(theme)

    def _on_color_changed(self, key: str, value: str, is_preview: bool):
        """Handle color change from picker."""
        if self._updating:
            return  # Prevent recursive updates

        self._modified = True
        self._update_button_states()

        # Schedule preview update for the widget's preview pane
        self._preview_timer.stop()
        self._preview_timer.start(100)  # Debounce preview updates

        # Don't apply theme preview to the whole app during editing
        # The preview widget will be updated by the timer

    def _apply_preview(self):
        """Apply preview colors."""
        colors = self._get_current_colors()
        self._preview_widget.apply_theme_colors(colors)

    def _get_current_colors(self) -> Dict[str, str]:
        """Get current colors from all fields."""
        colors = {}
        for prop_key, field in self._color_fields.items():
            colors[prop_key] = field.get_color()
        return colors

    def _apply_theme(self) -> bool:
        """Apply current theme changes."""
        if not self._current_theme or not self._theme_service:
            return False

        self._updating = True
        try:
            # Update theme colors
            colors = self._get_current_colors()
            self._current_theme.colors = colors

            # Apply theme
            self._theme_service.apply_theme(self._current_theme.id)

            self._modified = False
            self._update_button_states()

            QMessageBox.information(self, "Success", "Theme applied successfully!")
            return True

        except Exception as e:
            logger.error(f"Failed to apply theme: {e}")
            QMessageBox.critical(self, "Error", f"Failed to apply theme: {e}")
            return False
        finally:
            self._updating = False

    def _save_theme(self) -> bool:
        """Save current theme changes."""
        if not self._current_theme or not self._theme_service:
            return False

        try:
            # Update theme colors
            colors = self._get_current_colors()
            self._current_theme.colors = colors

            # Save theme
            if self._theme_service.save_custom_theme(self._current_theme):
                self._modified = False
                self._update_button_states()

                QMessageBox.information(self, "Success", "Theme saved successfully!")
                return True
            else:
                QMessageBox.warning(self, "Warning", "Failed to save theme")
                return False

        except Exception as e:
            logger.error(f"Failed to save theme: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save theme: {e}")
            return False

    def _reset_changes(self):
        """Reset all changes to original theme."""
        if self._current_theme:
            self._load_theme(self._current_theme)

    def _create_new_theme(self):
        """Create a new theme."""
        # Get name from user
        from PySide6.QtWidgets import QInputDialog

        name, ok = QInputDialog.getText(
            self,
            "New Theme",
            "Enter theme name:"
        )

        if ok and name and self._theme_service:
            # Create based on current theme
            base_id = self._current_theme.id if self._current_theme else "vscode-dark"
            new_theme = self._theme_service.create_custom_theme(
                base_id,
                name,
                f"Custom theme created from {base_id}"
            )

            if new_theme:
                # Save and reload themes
                self._theme_service.save_custom_theme(new_theme)
                self._load_current_theme()

                # Select new theme
                index = self._theme_combo.findData(new_theme.id)
                if index >= 0:
                    self._theme_combo.setCurrentIndex(index)

    def _duplicate_theme(self):
        """Duplicate current theme."""
        if not self._current_theme:
            return

        # Get name from user
        from PySide6.QtWidgets import QInputDialog

        name, ok = QInputDialog.getText(
            self,
            "Duplicate Theme",
            "Enter theme name:",
            text=f"{self._current_theme.name} Copy"
        )

        if ok and name and self._theme_service:
            new_theme = self._theme_service.create_custom_theme(
                self._current_theme.id,
                name,
                f"Duplicate of {self._current_theme.name}"
            )

            if new_theme:
                # Copy current colors
                new_theme.colors = self._get_current_colors()

                # Save and reload
                self._theme_service.save_custom_theme(new_theme)
                self._load_current_theme()

                # Select new theme
                index = self._theme_combo.findData(new_theme.id)
                if index >= 0:
                    self._theme_combo.setCurrentIndex(index)

    def _delete_theme(self):
        """Delete current theme."""
        if not self._current_theme or not self._theme_service:
            return

        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Delete Theme",
            f"Are you sure you want to delete '{self._current_theme.name}'?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            if self._theme_service.delete_custom_theme(self._current_theme.id):
                QMessageBox.information(self, "Success", "Theme deleted successfully!")
                self._load_current_theme()
            else:
                QMessageBox.warning(self, "Warning", "Cannot delete built-in theme")

    def _import_theme(self):
        """Import theme from file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Theme",
            "",
            "JSON Files (*.json);;All Files (*)"
        )

        if file_path and self._theme_service:
            theme_id = self._theme_service.import_theme(Path(file_path))
            if theme_id:
                QMessageBox.information(self, "Success", "Theme imported successfully!")
                self._load_current_theme()

                # Select imported theme
                index = self._theme_combo.findData(theme_id)
                if index >= 0:
                    self._theme_combo.setCurrentIndex(index)
            else:
                QMessageBox.critical(self, "Error", "Failed to import theme")

    def _export_theme(self):
        """Export current theme."""
        if not self._current_theme:
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Theme",
            f"{self._current_theme.id}.json",
            "JSON Files (*.json)"
        )

        if file_path and self._theme_service:
            # Update theme with current colors before export
            self._current_theme.colors = self._get_current_colors()

            if self._theme_service.export_theme(self._current_theme.id, Path(file_path)):
                QMessageBox.information(self, "Success", "Theme exported successfully!")
            else:
                QMessageBox.critical(self, "Error", "Failed to export theme")

    def _import_vscode_theme(self):
        """Import VSCode theme."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import VSCode Theme",
            "",
            "JSON Files (*.json);;All Files (*)"
        )

        if file_path:
            theme = VSCodeThemeImporter.import_from_file(Path(file_path))
            if theme and self._theme_service:
                # Save imported theme
                self._theme_service._themes[theme.id] = theme
                self._theme_service.save_custom_theme(theme)

                QMessageBox.information(self, "Success", "VSCode theme imported successfully!")
                self._load_current_theme()

                # Select imported theme
                index = self._theme_combo.findData(theme.id)
                if index >= 0:
                    self._theme_combo.setCurrentIndex(index)
            else:
                QMessageBox.critical(self, "Error", "Failed to import VSCode theme")

    def _filter_properties(self, text: str):
        """Filter visible properties based on search text."""
        search_text = text.lower()

        for prop_key, field in self._color_fields.items():
            # Check if key or label contains search text
            visible = (search_text in prop_key.lower() or
                      search_text in field._label.lower())
            field.setVisible(visible)

        # Hide empty category boxes
        for i in range(self._property_layout.count()):
            item = self._property_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if isinstance(widget, QGroupBox):
                    # Check if any child is visible
                    has_visible = False
                    layout = widget.layout()
                    if layout:
                        for j in range(layout.count()):
                            child_item = layout.itemAt(j)
                            if child_item and child_item.widget():
                                if child_item.widget().isVisible():
                                    has_visible = True
                                    break

                    widget.setVisible(has_visible or not search_text)

    def _update_button_states(self):
        """Update button enabled states."""
        self._apply_button.setEnabled(self._modified)
        self._save_button.setEnabled(self._modified)
        self._reset_button.setEnabled(self._modified)

    def _connect_theme_signals(self):
        """Connect to theme service signals."""
        if self._theme_service:
            # Listen for external theme changes
            self._theme_service.theme_changed.connect(self._on_external_theme_change)

    def _on_external_theme_change(self, colors: Dict[str, str]):
        """Handle theme changes from outside the editor."""
        if self._updating:
            return  # Ignore if we're the ones updating

        # Only reload if not modified or if it's a different theme
        if not self._modified and self._theme_service:
            current_theme = self._theme_service.get_current_theme()
            if current_theme and (not self._current_theme or current_theme.id != self._current_theme.id):
                # Theme changed externally, reload
                index = self._theme_combo.findData(current_theme.id)
                if index >= 0:
                    self._theme_combo.blockSignals(True)
                    self._theme_combo.setCurrentIndex(index)
                    self._theme_combo.blockSignals(False)
                self._load_theme(current_theme)