"""
Widget service for managing widget operations.

This service acts as the business logic layer between commands and the model/UI.
It coordinates widget lifecycle, preferences, and factory operations.
"""

import logging
from typing import Any, Dict, List, Optional

from viloapp.core.app_widget_manager import app_widget_manager
from viloapp.models.workspace_model import WorkspaceModel

logger = logging.getLogger(__name__)


class WidgetService:
    """Service for managing widget operations."""

    def __init__(self, model: WorkspaceModel):
        """Initialize widget service.

        Args:
            model: The workspace model
        """
        self.name = "WidgetService"  # Required for service locator registration
        self.model = model

    def initialize(self, context: Any) -> None:
        """Initialize the widget service.

        Args:
            context: Service initialization context
        """
        logger.debug("WidgetService initialized")

    # Widget Discovery and Information
    def get_available_widgets(self) -> List[Dict[str, Any]]:
        """Get all available widgets with metadata.

        Returns:
            List of widget metadata dictionaries
        """
        widget_ids = app_widget_manager.get_available_widget_ids()
        widgets = []

        for widget_id in widget_ids:
            metadata = app_widget_manager.get_widget_metadata(widget_id)
            if metadata:
                widgets.append({
                    "id": widget_id,
                    "name": metadata.display_name,
                    "description": metadata.description,
                    "icon": metadata.icon,
                    "can_be_default": metadata.can_be_default,
                    "categories": metadata.categories,
                })

        return widgets

    def get_widget_info(self, widget_id: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific widget.

        Args:
            widget_id: The widget ID

        Returns:
            Widget information or None if not found
        """
        metadata = app_widget_manager.get_widget_metadata(widget_id)
        if not metadata:
            return None

        return {
            "id": widget_id,
            "name": metadata.display_name,
            "description": metadata.description,
            "icon": metadata.icon,
            "can_be_default": metadata.can_be_default,
            "categories": metadata.categories,
            "shortcuts": metadata.shortcuts,
        }

    # Widget Preferences
    def set_default_widget(self, context: str, widget_id: str) -> bool:
        """Set the default widget for a context.

        Args:
            context: The context (e.g., "general", "file:python")
            widget_id: The widget ID to set as default

        Returns:
            True if successful
        """
        if not app_widget_manager.is_widget_available(widget_id):
            logger.error(f"Widget {widget_id} is not available")
            return False

        return self.model.set_widget_preference(context, widget_id)

    def get_default_widget(self, context: Optional[str] = None) -> str:
        """Get the default widget for a context.

        Args:
            context: Optional context to get default for

        Returns:
            The default widget ID
        """
        return self.model.get_default_widget_for_context(context)

    def clear_default_widget(self, context: str) -> bool:
        """Clear the default widget preference for a context.

        Args:
            context: The context to clear

        Returns:
            True if a preference was cleared
        """
        return self.model.clear_widget_preference(context)

    def get_all_preferences(self) -> Dict[str, str]:
        """Get all widget preferences.

        Returns:
            Dictionary of context to widget ID mappings
        """
        return self.model.get_all_widget_preferences()

    # Widget Lifecycle
    def create_widget(self, widget_id: str, pane_id: str) -> bool:
        """Create a widget in a pane.

        Args:
            widget_id: The widget ID to create
            pane_id: The pane to create it in

        Returns:
            True if successful
        """
        if not app_widget_manager.is_widget_available(widget_id):
            logger.error(f"Widget {widget_id} is not available")
            return False

        # Change the pane's widget
        return self.model.change_pane_widget(pane_id, widget_id)

    def change_pane_widget(self, pane_id: str, widget_id: str) -> bool:
        """Change the widget in a pane.

        Args:
            pane_id: The pane ID
            widget_id: The new widget ID

        Returns:
            True if successful
        """
        return self.create_widget(widget_id, pane_id)

    def get_pane_widget(self, pane_id: str) -> Optional[str]:
        """Get the widget ID for a pane.

        Args:
            pane_id: The pane ID

        Returns:
            Widget ID or None if pane not found
        """
        return self.model.get_pane_widget_id(pane_id)

    # Widget Categories
    def get_widgets_by_category(self, category: str) -> List[str]:
        """Get widgets in a specific category.

        Args:
            category: The category to filter by

        Returns:
            List of widget IDs in the category
        """
        widget_ids = []
        for widget_id in app_widget_manager.get_available_widget_ids():
            metadata = app_widget_manager.get_widget_metadata(widget_id)
            if metadata and str(metadata.category.value) == category:
                widget_ids.append(widget_id)
        return widget_ids

    def get_default_for_category(self, category: str) -> Optional[str]:
        """Get the default widget for a category.

        Args:
            category: The category

        Returns:
            Default widget ID or None
        """
        # First check user preference for this category
        user_pref = self.model.get_widget_preference(f"category:{category}")
        if user_pref and app_widget_manager.is_widget_available(user_pref):
            return user_pref

        # Find widgets in this category that can be defaults
        candidates = []
        for widget_id in self.get_widgets_by_category(category):
            metadata = app_widget_manager.get_widget_metadata(widget_id)
            if metadata and metadata.can_be_default:
                candidates.append((widget_id, metadata.default_priority))

        # Sort by priority and return the highest
        if candidates:
            candidates.sort(key=lambda x: x[1], reverse=True)
            return candidates[0][0]

        return None

    # Plugin Support
    def register_plugin_widget(self, plugin_id: str, widget_metadata: Dict[str, Any]) -> bool:
        """Register a widget from a plugin.

        Args:
            plugin_id: The plugin ID
            widget_metadata: The widget metadata

        Returns:
            True if successful
        """
        # Ensure widget ID follows plugin convention
        widget_id = widget_metadata.get("id", "")
        if not widget_id.startswith(f"plugin.{plugin_id}."):
            logger.error(f"Plugin widget ID must start with 'plugin.{plugin_id}.'")
            return False

        # Register with the app widget manager
        # This would need to be enhanced in app_widget_manager to accept raw metadata
        logger.info(f"Would register plugin widget: {widget_id}")
        return True

    def unregister_plugin_widget(self, widget_id: str) -> bool:
        """Unregister a plugin widget.

        Args:
            widget_id: The widget ID to unregister

        Returns:
            True if successful
        """
        if not widget_id.startswith("plugin."):
            logger.error("Can only unregister plugin widgets")
            return False

        # This would need app_widget_manager.unregister() method
        logger.info(f"Would unregister plugin widget: {widget_id}")
        return True


# Global widget service instance
widget_service: Optional[WidgetService] = None


def initialize_widget_service(model: WorkspaceModel):
    """Initialize the global widget service.

    Args:
        model: The workspace model
    """
    global widget_service
    widget_service = WidgetService(model)
    logger.info("Widget service initialized")


def get_widget_service() -> Optional[WidgetService]:
    """Get the global widget service instance.

    Returns:
        The widget service or None if not initialized
    """
    return widget_service
