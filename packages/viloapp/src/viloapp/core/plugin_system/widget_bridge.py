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

try:
    from viloapp.core.app_widget_manager import app_widget_manager
    from viloapp.core.app_widget_metadata import AppWidgetMetadata, WidgetCategory
except ImportError as e:
    logger.debug(f"AppWidgetMetadata or app_widget_manager not available for import: {e}")
    AppWidgetMetadata = None
    app_widget_manager = None
    WidgetCategory = None


class PluginWidgetBridge:
    """Bridges plugin widgets to core UI system."""

    def __init__(self, workspace_service):
        self.workspace_service = workspace_service
        self._plugin_widgets: Dict[str, Any] = {}  # IWidget instances
        self._widget_to_plugin: Dict[str, str] = {}  # widget_id -> plugin_id mapping
        logger.info("PluginWidgetBridge initialized")

    def register_plugin_widget(self, plugin_widget, plugin_id: str = None) -> None:
        """Register a plugin widget with core UI.

        Args:
            plugin_widget: The widget instance from the plugin
            plugin_id: The ID of the plugin registering this widget
        """
        if not plugin_widget:
            logger.error("Cannot register null plugin widget")
            return

        try:
            # Get base widget ID from plugin (e.g., "terminal", "editor")
            base_widget_id = plugin_widget.get_widget_id()

            # Construct full widget ID with plugin namespace if plugin_id provided
            if plugin_id:
                widget_id = f"plugin.{plugin_id}.{base_widget_id}"
                self._widget_to_plugin[widget_id] = plugin_id
            else:
                # Fallback for widgets without plugin_id
                widget_id = base_widget_id

            self._plugin_widgets[widget_id] = plugin_widget
            logger.info(f"Registered plugin widget: {widget_id} (base: {base_widget_id})")

            # Register factory with workspace service
            self.workspace_service.register_widget_factory(
                widget_id, lambda instance_id: self._create_widget_adapter(widget_id, instance_id)
            )
            logger.info(f"Registered widget factory for: {widget_id}")

            # Register metadata with AppWidgetManager for UI display
            try:
                # Try lazy import if not already imported
                global AppWidgetMetadata, app_widget_manager, WidgetCategory
                if AppWidgetMetadata is None:
                    from viloapp.core.app_widget_manager import app_widget_manager
                    from viloapp.core.app_widget_metadata import AppWidgetMetadata, WidgetCategory
                    logger.debug("Successfully imported AppWidgetMetadata and app_widget_manager")

                metadata = self._create_app_widget_metadata(plugin_widget, widget_id)
                if metadata:
                    app_widget_manager.register_widget(metadata)
                    logger.info(f"Registered widget metadata for: {widget_id}")
            except ImportError as e:
                logger.debug(f"Could not import AppWidgetMetadata - skipping metadata registration: {e}")
            except Exception as e:
                logger.error(f"Failed to register widget metadata: {e}")

        except Exception as e:
            logger.error(f"Failed to register plugin widget: {e}")

    def _create_app_widget_metadata(self, plugin_widget, full_widget_id: str):
        """Create AppWidgetMetadata from plugin widget.

        Args:
            plugin_widget: The plugin widget instance
            full_widget_id: The full widget ID including plugin namespace
        """
        try:
            # Use the full widget ID (with plugin namespace)
            widget_id = full_widget_id
            title = plugin_widget.get_title() if hasattr(plugin_widget, 'get_title') else widget_id
            icon = plugin_widget.get_icon() if hasattr(plugin_widget, 'get_icon') else None

            # Determine category based on widget ID or capabilities
            category = WidgetCategory.PLUGIN  # Default for plugins
            if "terminal" in widget_id.lower():
                category = WidgetCategory.TERMINAL
            elif "editor" in widget_id.lower():
                category = WidgetCategory.EDITOR

            # Extract capabilities if available
            provides_capabilities = []
            if hasattr(plugin_widget, 'get_capabilities'):
                capabilities = plugin_widget.get_capabilities()
                if capabilities:
                    provides_capabilities = [cap.value for cap in capabilities]

            # For plugin widgets, we don't have a direct widget_class,
            # but we can use the factory function
            factory_func = lambda instance_id: self._create_widget_adapter(widget_id, instance_id)

            # Create metadata object
            # Import AppWidget here to use as placeholder class
            from viloapp.ui.widgets.app_widget import AppWidget

            metadata = AppWidgetMetadata(
                widget_id=widget_id,
                display_name=title,
                description=f"Plugin-provided {title} widget",
                icon=icon or "mdi.puzzle",  # Default icon for plugins
                category=category,
                widget_class=AppWidget,  # Placeholder, actual widget created by factory
                factory=factory_func,  # Factory that creates the actual widget
                show_in_menu=True,  # Show plugin widgets in menus
                show_in_palette=True,  # Show in command palette
                can_split=True,
                singleton=False,
                source="plugin",  # Mark as plugin-provided
                provides_capabilities=provides_capabilities,  # Capabilities list
                can_be_default=True,  # Can be used as default widget
                supports_new_tab=True,  # Can open in new tab
                supports_replacement=True  # Can replace existing pane
            )

            return metadata

        except Exception as e:
            logger.error(f"Failed to create metadata for plugin widget: {e}")
            return None

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
