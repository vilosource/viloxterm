#!/usr/bin/env python3
"""
Theme editor control panels for color and typography management.

Provides organized control panels for editing theme colors and typography settings
with categorized inputs, search/filter capabilities, and preset management.
"""

from typing import Dict, Optional, Tuple
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QScrollArea, QFrame, QGroupBox, QLineEdit, QTabWidget,
    QSpinBox, QSlider, QFontComboBox
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont
import logging

from ui.widgets.color_picker_widget import ColorPickerField
from core.themes.property_categories import ThemePropertyCategories

logger = logging.getLogger(__name__)


class ThemeControlsWidget(QWidget):
    """
    Complete control panel for theme editing.

    Contains tabbed interface with:
    - Color controls with categorized pickers and search
    - Typography controls with presets and sliders
    """

    # Signals
    color_changed = Signal(str, str, bool)  # key, value, is_preview
    typography_changed = Signal()
    preset_changed = Signal(str)  # preset name

    def __init__(self, parent: Optional[QWidget] = None):
        """
        Initialize theme controls widget.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)

        self._color_fields: Dict[str, ColorPickerField] = {}
        self._updating = False  # Flag to prevent recursive updates

        self._setup_ui()

    def _setup_ui(self):
        """Set up the controls UI."""
        layout = QVBoxLayout()
        layout.setContentsMargins(8, 8, 8, 8)

        # Tab widget for colors and typography
        self._property_tabs = QTabWidget()

        # Colors tab
        colors_tab = self._create_colors_tab()
        self._property_tabs.addTab(colors_tab, "Colors")

        # Typography tab
        typography_tab = self._create_typography_tab()
        self._property_tabs.addTab(typography_tab, "Typography")

        layout.addWidget(self._property_tabs)
        self.setLayout(layout)

    def _create_colors_tab(self) -> QWidget:
        """Create the colors property editor tab."""
        container = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

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
                    field.color_changed.connect(self._on_color_field_changed)

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

    def _create_typography_tab(self) -> QWidget:
        """Create the typography settings tab."""
        container = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        # Typography presets
        preset_layout = QHBoxLayout()
        preset_layout.addWidget(QLabel("Preset:"))

        self._preset_combo = QComboBox()
        self._preset_combo.addItem("Custom", "custom")
        self._preset_combo.addItem("Compact", "compact")
        self._preset_combo.addItem("Default", "default")
        self._preset_combo.addItem("Comfortable", "comfortable")
        self._preset_combo.addItem("Large", "large")
        self._preset_combo.currentIndexChanged.connect(self._on_preset_changed)
        preset_layout.addWidget(self._preset_combo, 1)

        layout.addLayout(preset_layout)

        # Scrollable typography controls
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        typography_container = QWidget()
        typography_layout = QVBoxLayout()
        typography_layout.setSpacing(8)

        # Font family
        font_group = QGroupBox("Font Settings")
        font_layout = QVBoxLayout()

        family_layout = QHBoxLayout()
        family_layout.addWidget(QLabel("Font Family:"))
        self._font_family_combo = QFontComboBox()
        self._font_family_combo.setCurrentFont("Fira Code")
        self._font_family_combo.currentFontChanged.connect(self._on_typography_field_changed)
        family_layout.addWidget(self._font_family_combo, 1)
        font_layout.addLayout(family_layout)

        # Base font size
        size_layout = QHBoxLayout()
        size_layout.addWidget(QLabel("Base Font Size:"))
        self._font_size_spin = QSpinBox()
        self._font_size_spin.setRange(8, 32)
        self._font_size_spin.setValue(14)
        self._font_size_spin.setSuffix(" px")
        self._font_size_spin.valueChanged.connect(self._on_typography_field_changed)
        size_layout.addWidget(self._font_size_spin)

        self._font_size_slider = QSlider(Qt.Horizontal)
        self._font_size_slider.setRange(8, 32)
        self._font_size_slider.setValue(14)
        self._font_size_slider.valueChanged.connect(self._font_size_spin.setValue)
        self._font_size_spin.valueChanged.connect(self._font_size_slider.setValue)
        size_layout.addWidget(self._font_size_slider, 1)
        font_layout.addLayout(size_layout)

        # Line height
        line_height_layout = QHBoxLayout()
        line_height_layout.addWidget(QLabel("Line Height:"))
        self._line_height_spin = QSpinBox()
        self._line_height_spin.setRange(100, 300)
        self._line_height_spin.setValue(150)
        self._line_height_spin.setSuffix(" %")
        self._line_height_spin.valueChanged.connect(self._on_typography_field_changed)
        line_height_layout.addWidget(self._line_height_spin)

        self._line_height_slider = QSlider(Qt.Horizontal)
        self._line_height_slider.setRange(100, 300)
        self._line_height_slider.setValue(150)
        self._line_height_slider.valueChanged.connect(self._line_height_spin.setValue)
        self._line_height_spin.valueChanged.connect(self._line_height_slider.setValue)
        line_height_layout.addWidget(self._line_height_slider, 1)
        font_layout.addLayout(line_height_layout)

        font_group.setLayout(font_layout)
        typography_layout.addWidget(font_group)

        # Size scale preview
        scale_group = QGroupBox("Size Scale Preview")
        scale_layout = QVBoxLayout()

        scale_sizes = [
            ("Extra Small (xs)", "xs"),
            ("Small (sm)", "sm"),
            ("Base", "base"),
            ("Large (lg)", "lg"),
            ("Extra Large (xl)", "xl"),
            ("2X Large (2xl)", "2xl"),
            ("3X Large (3xl)", "3xl"),
        ]

        self._scale_labels = {}
        for label, scale in scale_sizes:
            scale_row = QHBoxLayout()
            scale_label = QLabel(label)
            scale_label.setMinimumWidth(120)
            scale_row.addWidget(scale_label)

            sample_label = QLabel("Sample Text")
            self._scale_labels[scale] = sample_label
            scale_row.addWidget(sample_label, 1)

            scale_layout.addLayout(scale_row)

        scale_group.setLayout(scale_layout)
        typography_layout.addWidget(scale_group)

        typography_layout.addStretch()
        typography_container.setLayout(typography_layout)

        scroll_area.setWidget(typography_container)
        layout.addWidget(scroll_area, 1)

        container.setLayout(layout)
        return container

    def _on_color_field_changed(self, key: str, value: str, is_preview: bool):
        """Handle color field change."""
        if self._updating:
            return

        # Forward signal to parent
        self.color_changed.emit(key, value, is_preview)

    def _on_typography_field_changed(self):
        """Handle typography field change."""
        if self._updating:
            return

        # Update preset to "Custom" if user manually changed settings
        if self._preset_combo.currentData() != "custom":
            self._preset_combo.blockSignals(True)
            self._preset_combo.setCurrentIndex(0)  # Custom
            self._preset_combo.blockSignals(False)

        # Update size scale preview
        self._update_size_scale_preview()

        # Forward signal to parent
        self.typography_changed.emit()

    def _on_preset_changed(self):
        """Handle preset change."""
        if self._updating:
            return

        preset = self._preset_combo.currentData()
        if preset != "custom":
            self.preset_changed.emit(preset)

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

    def _update_size_scale_preview(self):
        """Update the size scale preview labels."""
        base_size = self._font_size_spin.value()
        font_family = self._font_family_combo.currentFont().family()

        # Scale multipliers
        scale_multipliers = {
            "xs": 0.75,
            "sm": 0.875,
            "base": 1.0,
            "lg": 1.125,
            "xl": 1.25,
            "2xl": 1.5,
            "3xl": 1.875,
        }

        for scale, label in self._scale_labels.items():
            multiplier = scale_multipliers.get(scale, 1.0)
            size = int(base_size * multiplier)

            font = QFont(font_family, size)
            font.setStyleHint(QFont.Monospace)
            label.setFont(font)

    def get_color_fields(self) -> Dict[str, ColorPickerField]:
        """Get all color picker fields."""
        return self._color_fields.copy()

    def get_current_colors(self) -> Dict[str, str]:
        """Get current colors from all fields."""
        colors = {}
        for prop_key, field in self._color_fields.items():
            colors[prop_key] = field.get_color()
        return colors

    def load_colors(self, colors: Dict[str, str]):
        """Load colors into all fields."""
        self._updating = True
        try:
            for prop_key, field in self._color_fields.items():
                color = colors.get(prop_key, "#000000")
                field.set_color(color)
        finally:
            self._updating = False

    def get_typography_settings(self) -> Dict[str, any]:
        """Get current typography settings."""
        return {
            "font_family": self._font_family_combo.currentFont().family(),
            "font_size_base": self._font_size_spin.value(),
            "line_height": self._line_height_spin.value() / 100.0,
            "preset": self._preset_combo.currentData()
        }

    def load_typography_settings(self, font_family: str, font_size_base: int, line_height: float, preset: str = "custom"):
        """Load typography settings into controls."""
        self._updating = True
        try:
            self._font_family_combo.setCurrentFont(font_family.split(',')[0].strip())
            self._font_size_spin.setValue(font_size_base)
            self._line_height_spin.setValue(int(line_height * 100))

            # Set preset
            preset_index = self._preset_combo.findData(preset)
            if preset_index >= 0:
                self._preset_combo.setCurrentIndex(preset_index)
            else:
                self._preset_combo.setCurrentIndex(0)  # Custom

            self._update_size_scale_preview()
        finally:
            self._updating = False

    def set_updating(self, updating: bool):
        """Set updating flag to prevent signal loops."""
        self._updating = updating