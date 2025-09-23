"""
Widget factory for creating UI widgets from widget IDs.

This factory creates actual UI widgets based on the widget ID,
using the app_widget_manager registry to look up widget classes.

ARCHITECTURE COMPLIANCE:
- Uses registry for ALL widget creation (no hardcoded logic)
- Platform has ZERO knowledge of specific widget implementations
- All widget creation delegated to registered factories
"""

import logging
from typing import Any, Dict, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QWidget

from viloapp.core.app_widget_manager import app_widget_manager
from viloapp.models.workspace_model import WorkspaceModel
from viloapp.ui.widgets.split_pane_widget import SplitPaneWidget

logger = logging.getLogger(__name__)


class WidgetFactory:
    """Factory for creating UI widgets from widget IDs using registry."""

    def __init__(self):
        """Initialize widget factory."""
        # No hardcoded creators - everything comes from registry
        pass

    def create_split_pane_widget(
        self,
        model: WorkspaceModel,
        initial_widget_id: Optional[str] = None,
        parent=None,
    ) -> SplitPaneWidget:
        """Create a split pane widget with model.

        Args:
            model: The workspace model
            initial_widget_id: Optional initial widget ID (unused, model determines state)
            parent: Parent widget

        Returns:
            SplitPaneWidget instance
        """
        return SplitPaneWidget(model=model, parent=parent)

    def create_legacy_split_pane_widget(
        self,
        model: WorkspaceModel,
        initial_widget_type=None,
        initial_widget_id: Optional[str] = None,
        parent=None,
    ) -> SplitPaneWidget:
        """Legacy method for compatibility.

        Args:
            model: The workspace model
            initial_widget_type: Ignored (for compatibility)
            initial_widget_id: Ignored (for compatibility)
            parent: Parent widget

        Returns:
            SplitPaneWidget instance
        """
        return self.create_split_pane_widget(model, initial_widget_id, parent)

    def create_widget(
        self, widget_id: str, pane_id: str, context: Optional[Dict[str, Any]] = None
    ) -> Optional[QWidget]:
        """Create a UI widget for the given widget ID using the registry.

        This method delegates ALL widget creation to the AppWidgetManager registry.
        No hardcoded widget creation logic exists here - true platform architecture.

        Args:
            widget_id: The widget type ID
            pane_id: The pane ID this widget is for
            context: Optional context for widget creation

        Returns:
            QWidget instance or None if creation failed
        """
        try:
            # Use the registry to create ALL widgets - no hardcoded logic
            instance_id = f"{widget_id}_{pane_id}"
            widget = app_widget_manager.create_widget(widget_id, instance_id)

            if widget:
                # Store metadata for later reference
                widget.setProperty("widget_id", widget_id)
                widget.setProperty("pane_id", pane_id)
                widget.setProperty("instance_id", instance_id)

                # If context has specific initialization data, apply it
                if context and hasattr(widget, "initialize_with_context"):
                    widget.initialize_with_context(context)
                elif context and hasattr(widget, "load_file") and "file_path" in context:
                    # Support for file-based widgets
                    widget.load_file(context["file_path"])

                return widget
            else:
                logger.warning(f"Registry could not create widget: {widget_id}")
                return self._create_error_widget(f"Widget not available: {widget_id}")

        except Exception as e:
            logger.error(f"Failed to create widget {widget_id}: {e}", exc_info=True)
            return self._create_error_widget(f"Failed to create {widget_id}: {str(e)}")

    def _create_error_widget(self, message: str) -> QWidget:
        """Create an error widget for display when widget creation fails.

        Args:
            message: Error message to display

        Returns:
            Error widget
        """
        widget = QLabel(f"⚠️ {message}")
        widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        widget.setObjectName("errorWidget")
        widget.setStyleSheet(
            """
            QLabel#errorWidget {
                color: #ff6b6b;
                font-size: 14px;
                padding: 20px;
                background-color: rgba(255, 107, 107, 0.1);
                border: 1px solid rgba(255, 107, 107, 0.3);
                border-radius: 4px;
            }
        """
        )
        return widget


# Global factory instance
_widget_factory: Optional[WidgetFactory] = None


def get_widget_factory() -> WidgetFactory:
    """Get the global widget factory instance.

    Returns:
        The widget factory
    """
    global _widget_factory
    if _widget_factory is None:
        _widget_factory = WidgetFactory()
    return _widget_factory


def create_widget_for_pane(
    widget_id: str, pane_id: str, context: Optional[Dict[str, Any]] = None
) -> Optional[QWidget]:
    """Convenience function to create a widget for a pane.

    This delegates to the registry-based factory.

    Args:
        widget_id: The widget type ID
        pane_id: The pane ID
        context: Optional context

    Returns:
        QWidget instance or None
    """
    factory = get_widget_factory()
    return factory.create_widget(widget_id, pane_id, context)
