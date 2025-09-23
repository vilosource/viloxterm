#!/usr/bin/env python3
"""
Placeholder implementation as an AppWidget.
Used for testing and as a fallback for unknown widget types.
"""

from typing import Any, Set

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout

from viloapp.core.capabilities import WidgetCapability
from viloapp.ui.widgets.app_widget import AppWidget


class PlaceholderAppWidget(AppWidget):
    """
    Placeholder widget that extends AppWidget.

    Shows a simple label with widget information.
    """

    # Widget ID for this widget type
    WIDGET_ID = "com.viloapp.placeholder"

    def __init__(
        self,
        widget_id: str,
        instance_id: str,
        parent=None,
    ):
        """Initialize the placeholder widget."""
        super().__init__(widget_id, instance_id, parent)
        self.label = None
        self.setup_placeholder()

    def setup_placeholder(self):
        """Set up the placeholder UI."""
        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # Create label
        self.label = QLabel()
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setWordWrap(True)

        # Set text
        self.update_label()

        # Style
        self.label.setStyleSheet(
            """
            QLabel {
                background-color: #2d2d30;
                color: #969696;
                border: 2px dashed #3c3c3c;
                border-radius: 4px;
                padding: 20px;
                font-size: 14px;
            }
        """
        )

        # Add to layout
        layout.addWidget(self.label)

    def update_label(self):
        """Update the label text."""
        self.label.setText(
            f"{self.widget_id.value.replace('_', ' ').title()}\n"
            f"Widget ID: {self.widget_id}\n\n"
            f"This is a placeholder widget.\n"
            f"Right-click for options."
        )

    def cleanup(self):
        """Clean up resources (nothing to clean for placeholder)."""
        pass

    def get_state(self) -> dict[str, Any]:
        """Get placeholder state."""
        return super().get_state()

    def set_state(self, state: dict[str, Any]):
        """Restore placeholder state."""
        super().set_state(state)

    def get_title(self) -> str:
        """Get placeholder title."""
        return self.widget_id.value.replace("_", " ").title()

    def can_close(self) -> bool:
        """Placeholder can always be closed."""
        return True

    # === Capability Implementation ===

    def get_capabilities(self) -> Set[WidgetCapability]:
        """
        Placeholder widgets have minimal capabilities.

        Returns:
            Set of supported capabilities
        """
        # Placeholder can display text and that's about it
        return {
            WidgetCapability.TEXT_VIEWING,
            WidgetCapability.FOCUS_MANAGEMENT,
        }

    def execute_capability(
        self,
        capability: WidgetCapability,
        **kwargs: Any
    ) -> Any:
        """
        Execute capability-based actions.

        Args:
            capability: The capability to execute
            **kwargs: Capability-specific arguments

        Returns:
            Capability-specific return value
        """
        if capability == WidgetCapability.TEXT_VIEWING:
            # Return the current text being displayed
            return self.label.text() if self.label else ""
        elif capability == WidgetCapability.FOCUS_MANAGEMENT:
            # Handle focus operations
            if kwargs.get('action') == 'focus':
                self.setFocus()
                return True
            return self.hasFocus()
        else:
            # Delegate to base class for unsupported capabilities
            return super().execute_capability(capability, **kwargs)
