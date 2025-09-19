"""Main plugin manager orchestrating all plugin operations."""

import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from viloapp_sdk import EventBus, IPlugin
from .plugin_registry import PluginRegistry
from .plugin_discovery import PluginDiscovery
from .plugin_loader import PluginLoader
from .dependency_resolver import DependencyResolver
from .service_adapters import create_service_adapters

logger = logging.getLogger(__name__)

class PluginManager:
    """Central manager for all plugin operations."""

    def __init__(self, event_bus: EventBus, services: Dict[str, Any]):
        self.event_bus = event_bus
        self.services = services

        # Create service adapters for plugins
        self.service_adapters = create_service_adapters(services)

        # Initialize components
        self.registry = PluginRegistry()
        self.discovery = PluginDiscovery(self.registry)
        # Pass adapted services to loader
        self.loader = PluginLoader(self.registry, event_bus, self.service_adapters)
        self.resolver = DependencyResolver(self.registry)

        self._initialized = False

    def initialize(self) -> bool:
        """
        Initialize the plugin system.

        Returns:
            True if initialized successfully
        """
        if self._initialized:
            return True

        try:
            # Discover all plugins
            plugins = self.discovery.discover_all()

            # Register discovered plugins
            for plugin_info in plugins:
                self.registry.register(plugin_info)

            # Resolve dependencies
            load_order, unmet_deps = self.resolver.resolve_dependencies()

            # Log dependency issues
            if unmet_deps:
                for plugin_id, deps in unmet_deps.items():
                    logger.warning(f"Plugin {plugin_id} has unmet dependencies: {deps}")

            # Load and activate plugins in order
            for plugin_id in load_order:
                if plugin_id not in unmet_deps:
                    if self.load_plugin(plugin_id):
                        # Auto-activate plugins with activation events
                        plugin_info = self.registry.get_plugin(plugin_id)
                        if plugin_info and self._should_auto_activate(plugin_info):
                            self.activate_plugin(plugin_id)

            self._initialized = True
            logger.info("Plugin system initialized")
            return True

        except Exception as e:
            logger.error(f"Failed to initialize plugin system: {e}", exc_info=True)
            return False

    def discover_plugins(self) -> List[str]:
        """
        Discover available plugins.

        Returns:
            List of discovered plugin IDs
        """
        plugins = self.discovery.discover_all()
        plugin_ids = []

        for plugin_info in plugins:
            if self.registry.register(plugin_info):
                plugin_ids.append(plugin_info.metadata.id)

        return plugin_ids

    def load_plugin(self, plugin_id: str) -> bool:
        """
        Load a plugin.

        Args:
            plugin_id: Plugin identifier

        Returns:
            True if loaded successfully
        """
        return self.loader.load_plugin(plugin_id)

    def activate_plugin(self, plugin_id: str) -> bool:
        """
        Activate a plugin.

        Args:
            plugin_id: Plugin identifier

        Returns:
            True if activated successfully
        """
        return self.loader.activate_plugin(plugin_id)

    def deactivate_plugin(self, plugin_id: str) -> bool:
        """
        Deactivate a plugin.

        Args:
            plugin_id: Plugin identifier

        Returns:
            True if deactivated successfully
        """
        return self.loader.deactivate_plugin(plugin_id)

    def unload_plugin(self, plugin_id: str) -> bool:
        """
        Unload a plugin.

        Args:
            plugin_id: Plugin identifier

        Returns:
            True if unloaded successfully
        """
        return self.loader.unload_plugin(plugin_id)

    def reload_plugin(self, plugin_id: str) -> bool:
        """
        Reload a plugin.

        Args:
            plugin_id: Plugin identifier

        Returns:
            True if reloaded successfully
        """
        # Unload first
        if not self.unload_plugin(plugin_id):
            return False

        # Then load and activate
        if self.load_plugin(plugin_id):
            return self.activate_plugin(plugin_id)

        return False

    def get_plugin(self, plugin_id: str) -> Optional[IPlugin]:
        """
        Get plugin instance.

        Args:
            plugin_id: Plugin identifier

        Returns:
            Plugin instance or None
        """
        plugin_info = self.registry.get_plugin(plugin_id)
        if plugin_info:
            return plugin_info.instance
        return None

    def get_all_plugins(self) -> Dict[str, IPlugin]:
        """
        Get all plugin instances.

        Returns:
            Dictionary of plugin ID to instance
        """
        plugins = {}
        for plugin_info in self.registry.get_all_plugins():
            if plugin_info.instance:
                plugins[plugin_info.metadata.id] = plugin_info.instance
        return plugins

    def get_plugin_metadata(self, plugin_id: str) -> Optional[Dict[str, Any]]:
        """
        Get plugin metadata.

        Args:
            plugin_id: Plugin identifier

        Returns:
            Plugin metadata dictionary or None
        """
        plugin_info = self.registry.get_plugin(plugin_id)
        if plugin_info:
            return {
                "id": plugin_info.metadata.id,
                "name": plugin_info.metadata.name,
                "version": plugin_info.metadata.version,
                "description": plugin_info.metadata.description,
                "author": plugin_info.metadata.author,
                "state": plugin_info.state.name,
                "error": plugin_info.error,
                "dependencies": plugin_info.metadata.dependencies
            }
        return None

    def list_plugins(self) -> List[Dict[str, Any]]:
        """
        List all plugins with their status.

        Returns:
            List of plugin information dictionaries
        """
        plugins = []
        for plugin_info in self.registry.get_all_plugins():
            plugins.append({
                "id": plugin_info.metadata.id,
                "name": plugin_info.metadata.name,
                "version": plugin_info.metadata.version,
                "state": plugin_info.state.name,
                "error": plugin_info.error
            })
        return plugins

    def enable_plugin(self, plugin_id: str) -> bool:
        """
        Enable a plugin (load and activate).

        Args:
            plugin_id: Plugin identifier

        Returns:
            True if enabled successfully
        """
        if self.load_plugin(plugin_id):
            return self.activate_plugin(plugin_id)
        return False

    def disable_plugin(self, plugin_id: str) -> bool:
        """
        Disable a plugin (deactivate and unload).

        Args:
            plugin_id: Plugin identifier

        Returns:
            True if disabled successfully
        """
        if self.deactivate_plugin(plugin_id):
            return self.unload_plugin(plugin_id)
        return False

    def _should_auto_activate(self, plugin_info) -> bool:
        """Check if plugin should be auto-activated."""
        activation_events = plugin_info.metadata.activation_events

        # Check for startup activation
        if "onStartup" in activation_events:
            return True

        # Check for '*' (always activate)
        if "*" in activation_events:
            return True

        return False

    def save_state(self, path: Optional[Path] = None) -> bool:
        """
        Save plugin manager state.

        Args:
            path: Path to save state file

        Returns:
            True if saved successfully
        """
        if not path:
            import platformdirs
            path = Path(platformdirs.user_data_dir("ViloxTerm")) / "plugin_state.json"

        return self.registry.save_state(path)

    def load_state(self, path: Optional[Path] = None) -> bool:
        """
        Load plugin manager state.

        Args:
            path: Path to state file

        Returns:
            True if loaded successfully
        """
        if not path:
            import platformdirs
            path = Path(platformdirs.user_data_dir("ViloxTerm")) / "plugin_state.json"

        return self.registry.load_state(path)