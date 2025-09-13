# Theme Editor Implementation Plan v2

## Overview
Updated implementation plan for the Theme Editor that addresses missing components and architectural gaps identified during review.

## Key Issues to Address

### 1. Preview Methods in ThemeService
**Issue**: No preview methods for temporary theme application
**Solution**: Add preview state management with backup/restore mechanism

### 2. Color Picker Components
**Issue**: No existing color picker widgets
**Solution**: Create wrapper around QColorDialog with inline preview

### 3. Theme Property Organization
**Issue**: No categorization of 60+ theme properties
**Solution**: Create hierarchical property categorization system

### 4. Import Functionality
**Issue**: No VSCode theme import support
**Solution**: Add VSCode theme format converter with mapping

## Implementation Order

### Phase 1: Core Infrastructure Updates

#### Step 1.1: Extend ThemeService with Preview Support
```python
# services/theme_service.py additions

class ThemeService(Service):
    def __init__(self):
        super().__init__("ThemeService")
        # ... existing init ...
        self._preview_mode = False
        self._preview_backup = None
        self._preview_colors = {}

    def apply_theme_preview(self, colors: Dict[str, str]) -> None:
        """
        Apply temporary theme for preview without saving.

        Args:
            colors: Dictionary of color key-value pairs to preview
        """
        if not self._preview_mode:
            # Backup current theme
            self._preview_backup = self._current_theme
            self._preview_mode = True

        # Merge preview colors with current theme
        preview_theme = Theme(
            id="__preview__",
            name="Preview",
            description="Temporary preview theme",
            version="1.0.0",
            author="Theme Editor",
            colors={**self._current_theme.colors, **colors}
        )

        # Store preview colors for reference
        self._preview_colors = colors

        # Apply without saving to settings
        self._apply_theme_internal(preview_theme, save=False)

    def end_preview(self) -> None:
        """End preview and restore previous theme."""
        if self._preview_mode and self._preview_backup:
            self._apply_theme_internal(self._preview_backup, save=False)
            self._preview_mode = False
            self._preview_backup = None
            self._preview_colors = {}

    def is_preview_mode(self) -> bool:
        """Check if in preview mode."""
        return self._preview_mode

    def get_preview_colors(self) -> Dict[str, str]:
        """Get colors being previewed."""
        return self._preview_colors.copy()

    def _apply_theme_internal(self, theme: Theme, save: bool = True) -> None:
        """
        Internal method to apply theme.

        Args:
            theme: Theme to apply
            save: Whether to save to settings
        """
        self._current_theme = theme
        if save and not self._preview_mode:
            self._save_theme_preference(theme.id)
        # Emit signal for UI updates
        self.theme_changed.emit(theme.colors)
```

#### Step 1.2: Create Theme Property Categorization
```python
# core/themes/property_categories.py

from typing import Dict, List, Tuple
from core.themes.constants import ThemeColors

class ThemePropertyCategories:
    """Organize theme properties into logical categories."""

    @staticmethod
    def get_categories() -> Dict[str, Dict[str, List[Tuple[str, str]]]]:
        """
        Get hierarchical categorization of theme properties.

        Returns:
            Dict with category -> subcategory -> [(property_key, description)]
        """
        return {
            "Editor": {
                "General": [
                    (ThemeColors.EDITOR_BACKGROUND, "Editor background color"),
                    (ThemeColors.EDITOR_FOREGROUND, "Default text color"),
                    (ThemeColors.EDITOR_LINE_HIGHLIGHT, "Current line highlight"),
                    (ThemeColors.EDITOR_SELECTION, "Selected text background"),
                ],
                "Cursor & Guides": [
                    (ThemeColors.EDITOR_CURSOR, "Cursor color"),
                    (ThemeColors.EDITOR_WHITESPACE, "Whitespace characters"),
                    (ThemeColors.EDITOR_INDENT_GUIDE, "Indentation guides"),
                    (ThemeColors.EDITOR_INDENT_GUIDE_ACTIVE, "Active indentation guide"),
                ],
            },
            "Activity Bar": {
                "Background & Borders": [
                    (ThemeColors.ACTIVITY_BAR_BACKGROUND, "Activity bar background"),
                    (ThemeColors.ACTIVITY_BAR_BORDER, "Activity bar border"),
                    (ThemeColors.ACTIVITY_BAR_ACTIVE_BORDER, "Active item border"),
                ],
                "Foreground": [
                    (ThemeColors.ACTIVITY_BAR_FOREGROUND, "Icon color"),
                    (ThemeColors.ACTIVITY_BAR_INACTIVE_FOREGROUND, "Inactive icon color"),
                ],
            },
            "Sidebar": {
                "General": [
                    (ThemeColors.SIDEBAR_BACKGROUND, "Sidebar background"),
                    (ThemeColors.SIDEBAR_FOREGROUND, "Sidebar text color"),
                    (ThemeColors.SIDEBAR_BORDER, "Sidebar border"),
                ],
                "Section Headers": [
                    (ThemeColors.SIDEBAR_SECTION_HEADER_BACKGROUND, "Section header background"),
                    (ThemeColors.SIDEBAR_SECTION_HEADER_FOREGROUND, "Section header text"),
                ],
            },
            "Terminal": {
                "General": [
                    (ThemeColors.TERMINAL_BACKGROUND, "Terminal background"),
                    (ThemeColors.TERMINAL_FOREGROUND, "Terminal text color"),
                    (ThemeColors.TERMINAL_SELECTION_BACKGROUND, "Selection background"),
                ],
                "ANSI Colors": [
                    (ThemeColors.TERMINAL_ANSI_BLACK, "Black"),
                    (ThemeColors.TERMINAL_ANSI_RED, "Red"),
                    (ThemeColors.TERMINAL_ANSI_GREEN, "Green"),
                    (ThemeColors.TERMINAL_ANSI_YELLOW, "Yellow"),
                    (ThemeColors.TERMINAL_ANSI_BLUE, "Blue"),
                    (ThemeColors.TERMINAL_ANSI_MAGENTA, "Magenta"),
                    (ThemeColors.TERMINAL_ANSI_CYAN, "Cyan"),
                    (ThemeColors.TERMINAL_ANSI_WHITE, "White"),
                ],
                "ANSI Bright Colors": [
                    (ThemeColors.TERMINAL_ANSI_BRIGHT_BLACK, "Bright Black"),
                    (ThemeColors.TERMINAL_ANSI_BRIGHT_RED, "Bright Red"),
                    (ThemeColors.TERMINAL_ANSI_BRIGHT_GREEN, "Bright Green"),
                    (ThemeColors.TERMINAL_ANSI_BRIGHT_YELLOW, "Bright Yellow"),
                    (ThemeColors.TERMINAL_ANSI_BRIGHT_BLUE, "Bright Blue"),
                    (ThemeColors.TERMINAL_ANSI_BRIGHT_MAGENTA, "Bright Magenta"),
                    (ThemeColors.TERMINAL_ANSI_BRIGHT_CYAN, "Bright Cyan"),
                    (ThemeColors.TERMINAL_ANSI_BRIGHT_WHITE, "Bright White"),
                ],
            },
            "UI Components": {
                "Status Bar": [
                    (ThemeColors.STATUS_BAR_BACKGROUND, "Status bar background"),
                    (ThemeColors.STATUS_BAR_FOREGROUND, "Status bar text"),
                    (ThemeColors.STATUS_BAR_DEBUG_BACKGROUND, "Debug mode background"),
                ],
                "Title Bar": [
                    (ThemeColors.TITLE_BAR_ACTIVE_BACKGROUND, "Active window title bar"),
                    (ThemeColors.TITLE_BAR_ACTIVE_FOREGROUND, "Active window title text"),
                    (ThemeColors.TITLE_BAR_INACTIVE_BACKGROUND, "Inactive window title bar"),
                ],
                "Tabs": [
                    (ThemeColors.TAB_ACTIVE_BACKGROUND, "Active tab background"),
                    (ThemeColors.TAB_ACTIVE_FOREGROUND, "Active tab text"),
                    (ThemeColors.TAB_INACTIVE_BACKGROUND, "Inactive tab background"),
                    (ThemeColors.TAB_INACTIVE_FOREGROUND, "Inactive tab text"),
                    (ThemeColors.TAB_BORDER, "Tab border"),
                ],
                "Buttons": [
                    (ThemeColors.BUTTON_BACKGROUND, "Button background"),
                    (ThemeColors.BUTTON_FOREGROUND, "Button text"),
                    (ThemeColors.BUTTON_HOVER_BACKGROUND, "Button hover background"),
                ],
                "Inputs": [
                    (ThemeColors.INPUT_BACKGROUND, "Input field background"),
                    (ThemeColors.INPUT_FOREGROUND, "Input field text"),
                    (ThemeColors.INPUT_BORDER, "Input field border"),
                    (ThemeColors.FOCUS_BORDER, "Focused element border"),
                ],
                "Lists": [
                    (ThemeColors.LIST_HOVER_BACKGROUND, "List item hover"),
                    (ThemeColors.LIST_ACTIVE_SELECTION_BACKGROUND, "Selected item background"),
                    (ThemeColors.LIST_ACTIVE_SELECTION_FOREGROUND, "Selected item text"),
                ],
            },
        }

    @staticmethod
    def get_all_properties() -> List[Tuple[str, str, str, str]]:
        """
        Get flat list of all properties with full categorization.

        Returns:
            List of (property_key, description, category, subcategory)
        """
        result = []
        categories = ThemePropertyCategories.get_categories()

        for category, subcategories in categories.items():
            for subcategory, properties in subcategories.items():
                for prop_key, description in properties:
                    result.append((prop_key, description, category, subcategory))

        return result
```

### Phase 2: UI Components

#### Step 2.1: Color Picker Widget
```python
# ui/widgets/color_picker_widget.py

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QLineEdit,
    QColorDialog, QLabel
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QColor, QRegularExpressionValidator

class ColorPickerWidget(QWidget):
    """Compact color picker with inline preview and popup dialog."""

    color_changed = Signal(str)  # Emits hex color string

    def __init__(self, initial_color: str = "#000000", parent=None):
        super().__init__(parent)
        self.current_color = QColor(initial_color)
        self.setup_ui()

    def setup_ui(self):
        """Initialize the UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Color preview button (click to open picker)
        self.preview_btn = QPushButton()
        self.preview_btn.setFixedSize(24, 24)
        self.preview_btn.setCursor(Qt.PointingHandCursor)
        self.preview_btn.clicked.connect(self.open_color_dialog)
        self._update_preview()

        # Hex input field
        self.hex_input = QLineEdit(self.current_color.name())
        self.hex_input.setMaximumWidth(80)
        self.hex_input.setPlaceholderText("#000000")

        # Validate hex input
        hex_validator = QRegularExpressionValidator()
        hex_validator.setRegularExpression("^#[0-9A-Fa-f]{6}$")
        self.hex_input.setValidator(hex_validator)
        self.hex_input.editingFinished.connect(self._on_hex_changed)

        # Color name label (optional)
        self.name_label = QLabel()
        self.name_label.setStyleSheet("color: #888; font-size: 11px;")

        layout.addWidget(self.preview_btn)
        layout.addWidget(self.hex_input)
        layout.addWidget(self.name_label)
        layout.addStretch()

    def _update_preview(self):
        """Update the preview button appearance."""
        self.preview_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {self.current_color.name()};
                border: 1px solid #555;
                border-radius: 3px;
            }}
            QPushButton:hover {{
                border: 2px solid #007ACC;
            }}
        """)

    def _on_hex_changed(self):
        """Handle manual hex input."""
        hex_value = self.hex_input.text()
        if QColor.isValidColor(hex_value):
            self.set_color(hex_value)

    def open_color_dialog(self):
        """Open the color picker dialog."""
        # Create custom color dialog
        dialog = QColorDialog(self.current_color, self)
        dialog.setWindowTitle("Select Color")
        dialog.setOption(QColorDialog.ShowAlphaChannel, False)

        # Add custom colors from current theme
        self._add_theme_colors_to_dialog(dialog)

        if dialog.exec() == QColorDialog.Accepted:
            new_color = dialog.selectedColor()
            self.set_color(new_color.name())

    def _add_theme_colors_to_dialog(self, dialog: QColorDialog):
        """Add current theme colors as custom colors in dialog."""
        from services.service_locator import ServiceLocator
        from services.theme_service import ThemeService

        locator = ServiceLocator.get_instance()
        theme_service = locator.get(ThemeService)

        if theme_service:
            colors = theme_service.get_colors()
            # Add first 16 unique colors as custom colors
            unique_colors = list(set(colors.values()))[:16]
            for i, color_hex in enumerate(unique_colors):
                dialog.setCustomColor(i, QColor(color_hex))

    def set_color(self, color: str):
        """Set the current color."""
        if QColor.isValidColor(color):
            self.current_color = QColor(color)
            self.hex_input.setText(color)
            self._update_preview()
            self._update_color_name()
            self.color_changed.emit(color)

    def get_color(self) -> str:
        """Get the current color as hex string."""
        return self.current_color.name()

    def _update_color_name(self):
        """Update the color name label with a friendly name."""
        # Simple color naming based on hue
        hue = self.current_color.hue()
        if hue < 0:
            name = "Gray"
        elif hue < 20:
            name = "Red"
        elif hue < 45:
            name = "Orange"
        elif hue < 65:
            name = "Yellow"
        elif hue < 150:
            name = "Green"
        elif hue < 250:
            name = "Blue"
        elif hue < 330:
            name = "Purple"
        else:
            name = "Red"

        self.name_label.setText(name)
```

#### Step 2.2: VSCode Theme Importer
```python
# core/themes/importers.py

import json
from pathlib import Path
from typing import Dict, Optional
from core.themes.theme import Theme

class VSCodeThemeImporter:
    """Import VSCode themes and convert to ViloxTerm format."""

    # Mapping from VSCode color keys to ViloxTerm keys
    VSCODE_TO_VILOX_MAP = {
        # Editor colors
        "editor.background": "editor.background",
        "editor.foreground": "editor.foreground",
        "editor.lineHighlightBackground": "editor.lineHighlightBackground",
        "editor.selectionBackground": "editor.selectionBackground",
        "editorCursor.foreground": "editorCursor.foreground",

        # Activity bar
        "activityBar.background": "activityBar.background",
        "activityBar.foreground": "activityBar.foreground",
        "activityBar.border": "activityBar.border",
        "activityBar.activeBorder": "activityBar.activeBorder",

        # Sidebar
        "sideBar.background": "sideBar.background",
        "sideBar.foreground": "sideBar.foreground",
        "sideBar.border": "sideBar.border",

        # Status bar
        "statusBar.background": "statusBar.background",
        "statusBar.foreground": "statusBar.foreground",
        "statusBar.debuggingBackground": "statusBar.debuggingBackground",

        # Terminal ANSI colors
        "terminal.ansiBlack": "terminal.ansiBlack",
        "terminal.ansiRed": "terminal.ansiRed",
        "terminal.ansiGreen": "terminal.ansiGreen",
        "terminal.ansiYellow": "terminal.ansiYellow",
        "terminal.ansiBlue": "terminal.ansiBlue",
        "terminal.ansiMagenta": "terminal.ansiMagenta",
        "terminal.ansiCyan": "terminal.ansiCyan",
        "terminal.ansiWhite": "terminal.ansiWhite",
        "terminal.ansiBrightBlack": "terminal.ansiBrightBlack",
        "terminal.ansiBrightRed": "terminal.ansiBrightRed",
        "terminal.ansiBrightGreen": "terminal.ansiBrightGreen",
        "terminal.ansiBrightYellow": "terminal.ansiBrightYellow",
        "terminal.ansiBrightBlue": "terminal.ansiBrightBlue",
        "terminal.ansiBrightMagenta": "terminal.ansiBrightMagenta",
        "terminal.ansiBrightCyan": "terminal.ansiBrightCyan",
        "terminal.ansiBrightWhite": "terminal.ansiBrightWhite",

        # Add more mappings as needed
    }

    @classmethod
    def import_from_file(cls, file_path: Path) -> Optional[Theme]:
        """
        Import a VSCode theme from JSON file.

        Args:
            file_path: Path to VSCode theme JSON file

        Returns:
            Converted Theme object or None if import failed
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                vscode_data = json.load(f)

            return cls.convert_vscode_theme(vscode_data, file_path.stem)
        except Exception as e:
            print(f"Failed to import VSCode theme: {e}")
            return None

    @classmethod
    def convert_vscode_theme(cls, vscode_data: Dict, theme_name: str) -> Theme:
        """
        Convert VSCode theme data to ViloxTerm Theme.

        Args:
            vscode_data: VSCode theme JSON data
            theme_name: Name for the imported theme

        Returns:
            Converted Theme object
        """
        # Extract colors from VSCode theme
        vscode_colors = vscode_data.get("colors", {})

        # Convert to ViloxTerm format
        vilox_colors = {}
        for vscode_key, vilox_key in cls.VSCODE_TO_VILOX_MAP.items():
            if vscode_key in vscode_colors:
                vilox_colors[vilox_key] = vscode_colors[vscode_key]

        # Handle workbench.colorCustomizations if present
        customizations = vscode_data.get("workbench.colorCustomizations", {})
        for vscode_key, vilox_key in cls.VSCODE_TO_VILOX_MAP.items():
            if vscode_key in customizations:
                vilox_colors[vilox_key] = customizations[vscode_key]

        # Create Theme object
        theme = Theme(
            id=f"imported-{theme_name}",
            name=vscode_data.get("name", theme_name),
            description=f"Imported from VSCode theme: {theme_name}",
            version="1.0.0",
            author=vscode_data.get("author", "Unknown"),
            colors=vilox_colors
        )

        # Fill in missing required colors with defaults
        cls._fill_missing_colors(theme)

        return theme

    @classmethod
    def _fill_missing_colors(cls, theme: Theme):
        """Fill in missing required colors with sensible defaults."""
        # Required colors that must be present
        required_with_defaults = {
            "editor.background": "#1e1e1e",
            "editor.foreground": "#d4d4d4",
            "activityBar.background": "#333333",
            "activityBar.foreground": "#ffffff",
            "sideBar.background": "#252526",
            "sideBar.foreground": "#cccccc",
            "statusBar.background": "#007acc",
            "statusBar.foreground": "#ffffff",
        }

        for key, default in required_with_defaults.items():
            if key not in theme.colors:
                theme.colors[key] = default
```

### Phase 3: Main Theme Editor Widget

#### Step 3.1: Theme Editor AppWidget
```python
# ui/widgets/theme_editor_app_widget.py

from PySide6.QtWidgets import (
    QVBoxLayout, QHBoxLayout, QSplitter, QTreeWidget, QTreeWidgetItem,
    QScrollArea, QWidget, QLabel, QPushButton, QLineEdit, QComboBox,
    QGroupBox, QMessageBox, QFileDialog
)
from PySide6.QtCore import Qt, Signal
from typing import Dict, Optional
import uuid

from ui.widgets.app_widget import AppWidget
from ui.widgets.widget_registry import WidgetType
from ui.widgets.color_picker_widget import ColorPickerWidget
from ui.widgets.theme_preview_widget import ThemePreviewWidget
from core.themes.property_categories import ThemePropertyCategories
from core.themes.theme import Theme
from core.themes.importers import VSCodeThemeImporter

class ThemeEditorAppWidget(AppWidget):
    """Theme editor widget for visual theme customization."""

    theme_saved = Signal(str)  # Emits theme ID when saved

    def __init__(self, widget_id: str = None, parent=None):
        if widget_id is None:
            widget_id = f"theme-editor-{uuid.uuid4()}"

        super().__init__(widget_id, WidgetType.SETTINGS, parent)

        # State
        self.current_theme: Optional[Theme] = None
        self.base_theme: Optional[Theme] = None
        self.modified_colors: Dict[str, str] = {}
        self.color_pickers: Dict[str, ColorPickerWidget] = {}

        self.setup_ui()
        self.load_current_theme()

    def setup_ui(self):
        """Initialize the UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Header toolbar
        header = self._create_header()
        layout.addWidget(header)

        # Main content area with splitter
        splitter = QSplitter(Qt.Horizontal)

        # Left: Category tree
        self.category_tree = self._create_category_tree()
        splitter.addWidget(self.category_tree)

        # Middle: Property editor
        self.property_scroll = self._create_property_panel()
        splitter.addWidget(self.property_scroll)

        # Right: Live preview
        self.preview_widget = ThemePreviewWidget()
        splitter.addWidget(self.preview_widget)

        # Set initial splitter sizes (25%, 40%, 35%)
        splitter.setSizes([250, 400, 350])

        layout.addWidget(splitter)

    def _create_header(self) -> QWidget:
        """Create header toolbar with actions."""
        header = QWidget()
        layout = QHBoxLayout(header)

        # Theme name input
        self.theme_name_input = QLineEdit()
        self.theme_name_input.setPlaceholderText("Theme Name")
        layout.addWidget(QLabel("Theme:"))
        layout.addWidget(self.theme_name_input)

        # Base theme selector
        self.base_theme_combo = QComboBox()
        self._populate_base_themes()
        self.base_theme_combo.currentTextChanged.connect(self.on_base_theme_changed)
        layout.addWidget(QLabel("Based on:"))
        layout.addWidget(self.base_theme_combo)

        layout.addStretch()

        # Action buttons
        self.import_btn = QPushButton("Import")
        self.import_btn.clicked.connect(self.import_theme)
        layout.addWidget(self.import_btn)

        self.reset_btn = QPushButton("Reset")
        self.reset_btn.clicked.connect(self.reset_changes)
        layout.addWidget(self.reset_btn)

        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.save_theme)
        layout.addWidget(self.save_btn)

        self.export_btn = QPushButton("Export")
        self.export_btn.clicked.connect(self.export_theme)
        layout.addWidget(self.export_btn)

        return header

    def _create_category_tree(self) -> QTreeWidget:
        """Create the category tree widget."""
        tree = QTreeWidget()
        tree.setHeaderLabel("Categories")
        tree.setMinimumWidth(200)

        # Populate with categories
        categories = ThemePropertyCategories.get_categories()

        for category_name, subcategories in categories.items():
            category_item = QTreeWidgetItem([category_name])

            for subcategory_name, properties in subcategories.items():
                subcat_item = QTreeWidgetItem([subcategory_name])
                subcat_item.setData(0, Qt.UserRole, (category_name, subcategory_name))
                category_item.addChild(subcat_item)

            tree.addTopLevelItem(category_item)

        # Connect selection change
        tree.itemSelectionChanged.connect(self.on_category_selected)

        # Expand all by default
        tree.expandAll()

        return tree

    def _create_property_panel(self) -> QScrollArea:
        """Create the scrollable property panel."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        self.property_widget = QWidget()
        self.property_layout = QVBoxLayout(self.property_widget)
        self.property_layout.setAlignment(Qt.AlignTop)

        scroll.setWidget(self.property_widget)
        return scroll

    def on_category_selected(self):
        """Handle category selection in tree."""
        items = self.category_tree.selectedItems()
        if not items:
            return

        item = items[0]
        data = item.data(0, Qt.UserRole)

        if data:  # This is a subcategory
            category, subcategory = data
            self.show_properties(category, subcategory)

    def show_properties(self, category: str, subcategory: str):
        """Display properties for selected category."""
        # Clear existing properties
        while self.property_layout.count():
            child = self.property_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        # Get properties for this subcategory
        categories = ThemePropertyCategories.get_categories()
        properties = categories.get(category, {}).get(subcategory, [])

        # Create property editors
        for prop_key, description in properties:
            self._add_property_editor(prop_key, description)

        # Add stretch at the end
        self.property_layout.addStretch()

    def _add_property_editor(self, prop_key: str, description: str):
        """Add a property editor row."""
        group = QGroupBox(description)
        layout = QHBoxLayout(group)

        # Get current color
        current_color = self.get_color_for_property(prop_key)

        # Create color picker
        picker = ColorPickerWidget(current_color)
        picker.color_changed.connect(lambda color: self.on_color_changed(prop_key, color))

        # Store reference
        self.color_pickers[prop_key] = picker

        # Add reset button
        reset_btn = QPushButton("↺")
        reset_btn.setFixedSize(24, 24)
        reset_btn.setToolTip("Reset to inherited value")
        reset_btn.clicked.connect(lambda: self.reset_property(prop_key))

        layout.addWidget(picker)
        layout.addWidget(reset_btn)

        self.property_layout.addWidget(group)

    def get_color_for_property(self, prop_key: str) -> str:
        """Get the current color for a property."""
        # Check modified colors first
        if prop_key in self.modified_colors:
            return self.modified_colors[prop_key]

        # Then current theme
        if self.current_theme:
            return self.current_theme.colors.get(prop_key, "#000000")

        return "#000000"

    def on_color_changed(self, prop_key: str, color: str):
        """Handle color change from picker."""
        self.modified_colors[prop_key] = color

        # Apply preview
        self.apply_preview()

        # Update save button state
        self.save_btn.setEnabled(bool(self.modified_colors))

    def apply_preview(self):
        """Apply color changes as preview."""
        from services.service_locator import ServiceLocator
        from services.theme_service import ThemeService

        locator = ServiceLocator.get_instance()
        theme_service = locator.get(ThemeService)

        if theme_service:
            # Merge current theme with modifications
            preview_colors = {}
            if self.current_theme:
                preview_colors.update(self.current_theme.colors)
            preview_colors.update(self.modified_colors)

            # Apply preview
            theme_service.apply_theme_preview(preview_colors)

            # Update preview widget
            self.preview_widget.update_colors(preview_colors)

    def reset_property(self, prop_key: str):
        """Reset a property to its base value."""
        if prop_key in self.modified_colors:
            del self.modified_colors[prop_key]

        # Update picker
        if prop_key in self.color_pickers:
            base_color = self.base_theme.colors.get(prop_key, "#000000") if self.base_theme else "#000000"
            self.color_pickers[prop_key].set_color(base_color)

        # Update preview
        self.apply_preview()

    def reset_changes(self):
        """Reset all changes."""
        reply = QMessageBox.question(
            self,
            "Reset Changes",
            "Are you sure you want to reset all changes?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.modified_colors.clear()
            self.load_current_theme()

            # End preview mode
            from services.service_locator import ServiceLocator
            from services.theme_service import ThemeService

            locator = ServiceLocator.get_instance()
            theme_service = locator.get(ThemeService)
            if theme_service:
                theme_service.end_preview()

    def save_theme(self):
        """Save the current theme."""
        if not self.theme_name_input.text():
            QMessageBox.warning(self, "Save Theme", "Please enter a theme name.")
            return

        # Create new theme with modifications
        theme = Theme(
            id=f"custom-{uuid.uuid4()}",
            name=self.theme_name_input.text(),
            description=f"Custom theme based on {self.base_theme.name if self.base_theme else 'scratch'}",
            version="1.0.0",
            author="Theme Editor",
            extends=self.base_theme.id if self.base_theme else None,
            colors={**self.current_theme.colors, **self.modified_colors}
        )

        # Save through theme service
        from services.service_locator import ServiceLocator
        from services.theme_service import ThemeService

        locator = ServiceLocator.get_instance()
        theme_service = locator.get(ThemeService)

        if theme_service:
            if theme_service.save_custom_theme(theme):
                QMessageBox.information(self, "Save Theme", f"Theme '{theme.name}' saved successfully!")
                self.theme_saved.emit(theme.id)

                # Clear modifications
                self.modified_colors.clear()
                self.current_theme = theme

                # End preview and apply saved theme
                theme_service.end_preview()
                theme_service.apply_theme(theme.id)
            else:
                QMessageBox.critical(self, "Save Theme", "Failed to save theme.")

    def import_theme(self):
        """Import a theme from file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Theme",
            "",
            "Theme Files (*.json);;All Files (*)"
        )

        if file_path:
            from pathlib import Path
            theme = VSCodeThemeImporter.import_from_file(Path(file_path))

            if theme:
                self.current_theme = theme
                self.theme_name_input.setText(theme.name)
                self.modified_colors = theme.colors.copy()
                self.apply_preview()

                QMessageBox.information(self, "Import Theme", f"Theme '{theme.name}' imported successfully!")
            else:
                QMessageBox.critical(self, "Import Theme", "Failed to import theme.")

    def export_theme(self):
        """Export current theme to file."""
        if not self.current_theme:
            QMessageBox.warning(self, "Export Theme", "No theme to export.")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Theme",
            f"{self.current_theme.name}.json",
            "JSON Files (*.json);;All Files (*)"
        )

        if file_path:
            from pathlib import Path

            # Create theme with current modifications
            export_theme = Theme(
                id=self.current_theme.id,
                name=self.theme_name_input.text() or self.current_theme.name,
                description=self.current_theme.description,
                version=self.current_theme.version,
                author=self.current_theme.author,
                extends=self.current_theme.extends,
                colors={**self.current_theme.colors, **self.modified_colors}
            )

            export_theme.to_json_file(Path(file_path))
            QMessageBox.information(self, "Export Theme", f"Theme exported to {file_path}")

    def load_current_theme(self):
        """Load the current theme for editing."""
        from services.service_locator import ServiceLocator
        from services.theme_service import ThemeService

        locator = ServiceLocator.get_instance()
        theme_service = locator.get(ThemeService)

        if theme_service:
            current_theme_id = theme_service.get_current_theme_id()
            themes = theme_service.get_available_themes()

            for theme_info in themes:
                if theme_info.id == current_theme_id:
                    # Load full theme
                    self.current_theme = theme_service._themes.get(current_theme_id)
                    self.base_theme = self.current_theme
                    self.theme_name_input.setText(f"{self.current_theme.name} (Modified)")
                    break

    def _populate_base_themes(self):
        """Populate base theme dropdown."""
        from services.service_locator import ServiceLocator
        from services.theme_service import ThemeService

        locator = ServiceLocator.get_instance()
        theme_service = locator.get(ThemeService)

        if theme_service:
            themes = theme_service.get_available_themes()
            for theme_info in themes:
                self.base_theme_combo.addItem(theme_info.name, theme_info.id)

    def on_base_theme_changed(self, theme_name: str):
        """Handle base theme selection change."""
        theme_id = self.base_theme_combo.currentData()
        if not theme_id:
            return

        from services.service_locator import ServiceLocator
        from services.theme_service import ThemeService

        locator = ServiceLocator.get_instance()
        theme_service = locator.get(ThemeService)

        if theme_service:
            self.base_theme = theme_service._themes.get(theme_id)
            if self.base_theme:
                # Reset current theme to base
                self.current_theme = self.base_theme
                self.modified_colors.clear()
                self.theme_name_input.setText(f"{self.base_theme.name} (Modified)")

                # Refresh current view
                self.on_category_selected()

    def cleanup(self):
        """Clean up resources when closing."""
        # End preview mode
        from services.service_locator import ServiceLocator
        from services.theme_service import ThemeService

        locator = ServiceLocator.get_instance()
        theme_service = locator.get(ThemeService)
        if theme_service:
            theme_service.end_preview()

        super().cleanup()
```

## Implementation Timeline

### Week 1: Core Infrastructure
- [x] Add preview methods to ThemeService
- [x] Create theme property categorization
- [x] Implement VSCode theme importer

### Week 2: UI Components
- [ ] Create ColorPickerWidget
- [ ] Create ThemePreviewWidget
- [ ] Create ThemeEditorAppWidget

### Week 3: Integration & Commands
- [ ] Add theme editor commands
- [ ] Register widget in widget registry
- [ ] Test theme editor functionality

### Week 4: Polish & Documentation
- [ ] Add undo/redo support
- [ ] Improve color picker UX
- [ ] Write user documentation
- [ ] Performance optimization

## Key Improvements in v2

1. **Preview System**: Proper temporary theme preview without affecting saved settings
2. **Property Organization**: Hierarchical categorization of all 60+ theme properties
3. **Import Support**: VSCode theme import with proper mapping
4. **Color Picker**: Custom widget wrapping QColorDialog with inline preview
5. **State Management**: Clear separation between current, base, and modified colors
6. **Export Options**: Support for multiple theme formats

This updated plan addresses all the identified issues and provides a clear implementation path.