#!/usr/bin/env python3
"""
Color picker widget for theme editor.

Provides a compact color selection widget with preview, hex input, and dialog.
"""

from typing import Optional
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QPushButton, QLineEdit,
    QColorDialog, QLabel, QVBoxLayout
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QColor, QPalette, QRegularExpressionValidator
import logging

logger = logging.getLogger(__name__)


class ColorPickerWidget(QWidget):
    """
    Compact color picker widget with preview and hex input.

    Features:
    - Color preview button that opens color dialog
    - Hex input field with validation
    - Optional label
    - Current theme colors as custom colors
    """

    # Emitted when color changes (value, is_preview)
    color_changed = Signal(str, bool)

    def __init__(self, initial_color: str = "#000000",
                 label: Optional[str] = None,
                 show_hex_input: bool = True,
                 parent: Optional[QWidget] = None):
        """
        Initialize color picker widget.

        Args:
            initial_color: Initial color value (hex string)
            label: Optional label text
            show_hex_input: Whether to show hex input field
            parent: Parent widget
        """
        super().__init__(parent)

        self._color = initial_color
        self._original_color = initial_color
        self._show_hex_input = show_hex_input
        self._label_text = label

        self._setup_ui()
        self._set_color(initial_color)

    def _setup_ui(self):
        """Set up the widget UI."""
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Optional label
        if self._label_text:
            self._label = QLabel(self._label_text)
            self._label.setMinimumWidth(120)
            layout.addWidget(self._label)

        # Color preview button
        self._color_button = QPushButton()
        self._color_button.setFixedSize(60, 24)
        self._color_button.setCursor(Qt.PointingHandCursor)
        self._color_button.clicked.connect(self._open_color_dialog)
        self._color_button.setToolTip("Click to choose color")

        # Style the button with border
        self._color_button.setStyleSheet("""
            QPushButton {
                border: 1px solid #3c3c3c;
                border-radius: 4px;
            }
            QPushButton:hover {
                border: 1px solid #007acc;
            }
        """)

        layout.addWidget(self._color_button)

        # Hex input field
        if self._show_hex_input:
            self._hex_input = QLineEdit()
            self._hex_input.setMaximumWidth(100)
            self._hex_input.setPlaceholderText("#000000")

            # Hex color validator (# + 6 hex digits)
            hex_validator = QRegularExpressionValidator(
                r"^#[0-9A-Fa-f]{6}$", self
            )
            self._hex_input.setValidator(hex_validator)

            # Connect signals
            self._hex_input.textChanged.connect(self._on_hex_input_changed)
            self._hex_input.editingFinished.connect(self._on_hex_input_finished)

            layout.addWidget(self._hex_input)

        # Add stretch to push everything to the left
        layout.addStretch()

        self.setLayout(layout)

    def _set_color(self, color_str: str):
        """
        Set the current color.

        Args:
            color_str: Color value as hex string
        """
        self._color = color_str

        # Update button background
        self._update_button_color(color_str)

        # Update hex input
        if self._show_hex_input:
            self._hex_input.setText(color_str)

    def _update_button_color(self, color_str: str):
        """Update the color button's background."""
        # Create contrasting border based on luminance
        color = QColor(color_str)
        luminance = (0.299 * color.red() +
                    0.587 * color.green() +
                    0.114 * color.blue()) / 255

        border_color = "#ffffff" if luminance < 0.5 else "#000000"

        self._color_button.setStyleSheet(f"""
            QPushButton {{
                background-color: {color_str};
                border: 1px solid {border_color};
                border-radius: 4px;
            }}
            QPushButton:hover {{
                border: 2px solid #007acc;
            }}
        """)

    def _open_color_dialog(self):
        """Open color dialog for selection."""
        dialog = QColorDialog(QColor(self._color), self)

        # Add current theme colors as custom colors
        self._add_theme_colors_to_dialog(dialog)

        # Show dialog with live preview
        dialog.currentColorChanged.connect(self._on_dialog_color_changed)

        if dialog.exec() == QColorDialog.Accepted:
            color = dialog.selectedColor()
            color_str = color.name()
            self._set_color(color_str)
            self.color_changed.emit(color_str, False)  # Not preview
        else:
            # Revert to original if cancelled
            self._set_color(self._original_color)
            self.color_changed.emit(self._original_color, False)

    def _on_dialog_color_changed(self, color: QColor):
        """Handle live preview from color dialog."""
        color_str = color.name()
        self._update_button_color(color_str)
        self.color_changed.emit(color_str, True)  # Is preview

    def _on_hex_input_changed(self, text: str):
        """Handle hex input text changes."""
        if len(text) == 7 and text.startswith("#"):
            try:
                # Validate it's a valid color
                QColor(text)
                self._color = text
                self._update_button_color(text)
                self.color_changed.emit(text, True)  # Preview while typing
            except:
                pass  # Invalid color, ignore

    def _on_hex_input_finished(self):
        """Handle hex input editing finished."""
        text = self._hex_input.text()
        if len(text) == 7 and text.startswith("#"):
            try:
                QColor(text)
                self._color = text
                self._update_button_color(text)
                self.color_changed.emit(text, False)  # Final value
            except:
                # Revert to current color
                self._hex_input.setText(self._color)
        else:
            # Revert to current color
            self._hex_input.setText(self._color)

    def _add_theme_colors_to_dialog(self, dialog: QColorDialog):
        """Add current theme colors as custom colors in dialog."""
        try:
            from services.service_locator import ServiceLocator
            from services.theme_service import ThemeService

            locator = ServiceLocator()
            theme_service = locator.get(ThemeService)

            if theme_service and theme_service.get_current_theme():
                theme = theme_service.get_current_theme()
                colors = theme.colors

                # Add up to 16 custom colors (QColorDialog limit)
                custom_index = 0
                for color_value in list(colors.values())[:16]:
                    try:
                        dialog.setCustomColor(custom_index, QColor(color_value))
                        custom_index += 1
                    except:
                        pass  # Skip invalid colors
        except Exception as e:
            logger.debug(f"Could not add theme colors to dialog: {e}")

    def get_color(self) -> str:
        """
        Get current color value.

        Returns:
            Color as hex string
        """
        return self._color

    def set_color(self, color: str):
        """
        Set color value.

        Args:
            color: Color as hex string
        """
        self._set_color(color)
        self._original_color = color

    def reset(self):
        """Reset to original color."""
        self._set_color(self._original_color)
        self.color_changed.emit(self._original_color, False)


class ColorPickerField(QWidget):
    """
    Color picker with field label for forms.

    Combines a label and color picker in a form-friendly layout.
    """

    color_changed = Signal(str, str, bool)  # key, value, is_preview

    def __init__(self, key: str, label: str, initial_color: str = "#000000",
                 description: Optional[str] = None,
                 parent: Optional[QWidget] = None):
        """
        Initialize color picker field.

        Args:
            key: Property key
            label: Display label
            initial_color: Initial color value
            description: Optional description/tooltip
            parent: Parent widget
        """
        super().__init__(parent)

        self._key = key
        self._label = label
        self._description = description

        self._setup_ui(initial_color)

    def _setup_ui(self, initial_color: str):
        """Set up the field UI."""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Label with description tooltip
        label_widget = QLabel(self._label)
        if self._description:
            label_widget.setToolTip(self._description)
        layout.addWidget(label_widget)

        # Color picker
        self._picker = ColorPickerWidget(
            initial_color=initial_color,
            show_hex_input=True
        )
        self._picker.color_changed.connect(self._on_color_changed)
        layout.addWidget(self._picker)

        self.setLayout(layout)

    def _on_color_changed(self, color: str, is_preview: bool):
        """Forward color change with key."""
        self.color_changed.emit(self._key, color, is_preview)

    def get_key(self) -> str:
        """Get property key."""
        return self._key

    def get_color(self) -> str:
        """Get current color value."""
        return self._picker.get_color()

    def set_color(self, color: str):
        """Set color value."""
        self._picker.set_color(color)

    def reset(self):
        """Reset to original color."""
        self._picker.reset()