#!/usr/bin/env python3
"""
Plugin service wrapper.

Wraps PluginManager to make it a proper Service that can be registered
with the ServiceLocator.
"""

import logging
from typing import Optional, Dict, Any

from services.base import Service

logger = logging.getLogger(__name__)


class PluginService(Service):
    """Service wrapper for plugin management."""

    def __init__(self):
        super().__init__(name="PluginService")
        self._plugin_manager = None
        self._widget_bridge = None

    def initialize(self, context: Dict[str, Any]) -> None:
        """Initialize plugin service with context."""
        super().initialize(context)
        # Plugin manager will be set externally
        logger.info("PluginService initialized")

    def set_plugin_manager(self, plugin_manager) -> None:
        """Set the plugin manager instance."""
        self._plugin_manager = plugin_manager
        logger.info("Plugin manager set in PluginService")

    def cleanup(self) -> None:
        """Cleanup plugin system."""
        if self._plugin_manager:
            try:
                self._plugin_manager.shutdown()
                logger.info("Plugin manager shutdown complete")
            except Exception as e:
                logger.error(f"Error shutting down plugin manager: {e}")
        super().cleanup()

    def get_plugin_manager(self):
        """Get the underlying plugin manager."""
        return self._plugin_manager

    def register_widget(self, widget_factory) -> None:
        """Register a plugin widget factory."""
        if self._widget_bridge:
            self._widget_bridge.register_plugin_widget(widget_factory)
            logger.info(f"Registered plugin widget: {widget_factory}")
        else:
            logger.warning("Widget bridge not available for widget registration")