#!/usr/bin/env python3
"""Bridge between plugin widgets and core UI system."""

import logging
from typing import Any, Dict

from PySide6.QtWidgets import QVBoxLayout

logger = logging.getLogger(__name__)

# Import types only when needed to avoid circular imports
try:
    from viloapp_sdk.widget import IWidget
except ImportError:
    logger.debug("IWidget not available for import")
    IWidget = None

try:
    from viloapp.ui.widgets.app_widget import AppWidget
except ImportError:
    logger.debug("AppWidget not available for import")
    AppWidget = None


class PluginWidgetBridge:
    """Bridges plugin widgets to core UI system."""

    def __init__(self, workspace_service):
        self.workspace_service = workspace_service
        self._plugin_widgets: Dict[str, Any] = {}  # IWidget instances
        logger.info("PluginWidgetBridge initialized")

    def register_plugin_widget(self, plugin_widget) -> None:
        """Register a plugin widget with core UI."""
        if not plugin_widget:
            logger.error("Cannot register null plugin widget")
            return

        try:
            widget_id = plugin_widget.get_widget_id()
            self._plugin_widgets[widget_id] = plugin_widget
            logger.info(f"Registered plugin widget: {widget_id}")

            # Register factory with workspace service
            self.workspace_service.register_widget_factory(
                widget_id, lambda instance_id: self._create_widget_adapter(widget_id, instance_id)
            )
            logger.info(f"Registered widget factory for: {widget_id}")

        except Exception as e:
            logger.error(f"Failed to register plugin widget: {e}")

    def _create_widget_adapter(self, widget_id: str, instance_id: str):
        """Create AppWidget adapter for plugin widget."""
        try:
            plugin_widget = self._plugin_widgets[widget_id]
            qt_widget = plugin_widget.create_instance(instance_id)

            if AppWidget:
                return PluginAppWidgetAdapter(plugin_widget, qt_widget, instance_id)
            else:
                logger.error("AppWidget not available - cannot create adapter")
                return qt_widget  # Return raw widget as fallback

        except Exception as e:
            logger.error(f"Failed to create widget adapter for {widget_id}: {e}")
            return None


class PluginAppWidgetAdapter(AppWidget):
    """Adapts plugin widgets to core AppWidget interface."""

    def __init__(self, plugin_widget, qt_widget, instance_id: str):
        try:
            # Use plugin's widget ID with proper namespacing
            widget_id = f"plugin.{plugin_widget.get_widget_id()}"
            super().__init__(widget_id=widget_id, instance_id=instance_id)
            self.plugin_widget = plugin_widget
            self.qt_widget = qt_widget

            # Add the Qt widget as a child
            layout = QVBoxLayout(self)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.addWidget(self.qt_widget)

            logger.info(f"Created plugin widget adapter for {plugin_widget.get_widget_id()}")

        except Exception as e:
            logger.error(f"Failed to create PluginAppWidgetAdapter: {e}")
            raise

    def get_state(self) -> Dict[str, Any]:
        """Get widget state."""
        try:
            if hasattr(self.plugin_widget, "get_state"):
                return self.plugin_widget.get_state()
            return {}
        except Exception as e:
            logger.error(f"Failed to get plugin widget state: {e}")
            return {}

    def restore_state(self, state: Dict[str, Any]) -> None:
        """Restore widget state."""
        try:
            if hasattr(self.plugin_widget, "restore_state"):
                self.plugin_widget.restore_state(state)
        except Exception as e:
            logger.error(f"Failed to restore plugin widget state: {e}")

    def cleanup(self) -> None:
        """Cleanup widget resources."""
        try:
            if hasattr(self.plugin_widget, "destroy_instance"):
                self.plugin_widget.destroy_instance(self.widget_id)
            super().cleanup()
            logger.info(f"Cleaned up plugin widget adapter: {self.widget_id}")
        except Exception as e:
            logger.error(f"Failed to cleanup plugin widget: {e}")
