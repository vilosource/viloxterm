"""Plugin loading system."""

import logging
import importlib
import importlib.util
import sys
from pathlib import Path
from typing import Optional, Dict, Any

from viloapp_sdk import (
    IPlugin, PluginContext, EventBus, LifecycleState,
    PluginLoadError
)
from .plugin_registry import PluginInfo
from .service_proxy_impl import ServiceProxyImpl

logger = logging.getLogger(__name__)

class PluginLoader:
    """Loads and instantiates plugins."""

    def __init__(self, registry, event_bus: EventBus, services: Dict[str, Any]):
        self.registry = registry
        self.event_bus = event_bus
        self.services = services
        self.loaded_modules = {}

    def load_plugin(self, plugin_id: str) -> bool:
        """
        Load a plugin.

        Args:
            plugin_id: Plugin identifier

        Returns:
            True if loaded successfully
        """
        plugin_info = self.registry.get_plugin(plugin_id)
        if not plugin_info:
            logger.error(f"Plugin {plugin_id} not found in registry")
            return False

        if plugin_info.state not in [LifecycleState.DISCOVERED, LifecycleState.UNLOADED]:
            logger.warning(f"Plugin {plugin_id} is in state {plugin_info.state}, cannot load")
            return False

        try:
            # Load plugin module
            module = self._load_plugin_module(plugin_info)
            if not module:
                raise PluginLoadError(f"Failed to load module for {plugin_id}")

            # Find plugin class
            plugin_class = self._find_plugin_class(module)
            if not plugin_class:
                raise PluginLoadError(f"No plugin class found in {plugin_id}")

            # Instantiate plugin
            plugin_instance = plugin_class()

            # Validate plugin
            if not isinstance(plugin_instance, IPlugin):
                raise PluginLoadError(f"Plugin {plugin_id} does not implement IPlugin")

            # Update metadata from actual plugin
            actual_metadata = plugin_instance.get_metadata()
            plugin_info.metadata = actual_metadata

            # Store instance
            self.registry.set_instance(plugin_id, plugin_instance)
            self.registry.update_state(plugin_id, LifecycleState.LOADED)

            logger.info(f"Loaded plugin: {plugin_id}")
            return True

        except Exception as e:
            error_msg = f"Failed to load plugin {plugin_id}: {e}"
            logger.error(error_msg, exc_info=True)
            self.registry.set_error(plugin_id, str(e))
            return False

    def activate_plugin(self, plugin_id: str) -> bool:
        """
        Activate a loaded plugin.

        Args:
            plugin_id: Plugin identifier

        Returns:
            True if activated successfully
        """
        plugin_info = self.registry.get_plugin(plugin_id)
        if not plugin_info:
            return False

        if plugin_info.state != LifecycleState.LOADED:
            logger.warning(f"Plugin {plugin_id} is not loaded, cannot activate")
            return False

        if not plugin_info.instance:
            logger.error(f"Plugin {plugin_id} has no instance")
            return False

        try:
            # Create plugin context
            context = self._create_plugin_context(plugin_info)
            self.registry.set_context(plugin_id, context)

            # Activate plugin
            plugin_info.instance.activate(context)

            # Register plugin widgets if it has any
            if hasattr(plugin_info.instance, 'get_widgets'):
                try:
                    from viloapp.services.service_locator import ServiceLocator
                    from viloapp.services.plugin_service import PluginService

                    service_locator = ServiceLocator.get_instance()
                    plugin_service = service_locator.get(PluginService)

                    if plugin_service:
                        for widget in plugin_info.instance.get_widgets():
                            plugin_service.register_widget(widget)
                            logger.info(f"Registered widget from plugin {plugin_id}: {widget.get_widget_id()}")
                    else:
                        logger.warning(f"PluginService not available for widget registration from {plugin_id}")

                except Exception as e:
                    logger.error(f"Failed to register widgets from plugin {plugin_id}: {e}")

            # Update state
            self.registry.update_state(plugin_id, LifecycleState.ACTIVATED)

            # Emit activation event
            from viloapp_sdk import PluginEvent, EventType
            self.event_bus.emit(PluginEvent(
                type=EventType.PLUGIN_ACTIVATED,
                source="plugin_loader",
                data={"plugin_id": plugin_id}
            ))

            logger.info(f"Activated plugin: {plugin_id}")
            return True

        except Exception as e:
            error_msg = f"Failed to activate plugin {plugin_id}: {e}"
            logger.error(error_msg, exc_info=True)
            self.registry.set_error(plugin_id, str(e))
            return False

    def deactivate_plugin(self, plugin_id: str) -> bool:
        """
        Deactivate a plugin.

        Args:
            plugin_id: Plugin identifier

        Returns:
            True if deactivated successfully
        """
        plugin_info = self.registry.get_plugin(plugin_id)
        if not plugin_info:
            return False

        if plugin_info.state != LifecycleState.ACTIVATED:
            logger.warning(f"Plugin {plugin_id} is not activated")
            return False

        if not plugin_info.instance:
            return False

        try:
            # Deactivate plugin
            plugin_info.instance.deactivate()

            # Update state
            self.registry.update_state(plugin_id, LifecycleState.DEACTIVATED)

            # Emit deactivation event
            from viloapp_sdk import PluginEvent, EventType
            self.event_bus.emit(PluginEvent(
                type=EventType.PLUGIN_DEACTIVATED,
                source="plugin_loader",
                data={"plugin_id": plugin_id}
            ))

            logger.info(f"Deactivated plugin: {plugin_id}")
            return True

        except Exception as e:
            error_msg = f"Failed to deactivate plugin {plugin_id}: {e}"
            logger.error(error_msg, exc_info=True)
            return False

    def unload_plugin(self, plugin_id: str) -> bool:
        """
        Unload a plugin.

        Args:
            plugin_id: Plugin identifier

        Returns:
            True if unloaded successfully
        """
        plugin_info = self.registry.get_plugin(plugin_id)
        if not plugin_info:
            return False

        # Deactivate if necessary
        if plugin_info.state == LifecycleState.ACTIVATED:
            if not self.deactivate_plugin(plugin_id):
                return False

        if plugin_info.state not in [LifecycleState.DEACTIVATED, LifecycleState.LOADED, LifecycleState.FAILED]:
            return False

        try:
            # Clear instance and context
            self.registry.set_instance(plugin_id, None)
            self.registry.set_context(plugin_id, None)

            # Remove from loaded modules
            if plugin_id in self.loaded_modules:
                module_name = self.loaded_modules[plugin_id]
                if module_name in sys.modules:
                    del sys.modules[module_name]
                del self.loaded_modules[plugin_id]

            # Update state
            self.registry.update_state(plugin_id, LifecycleState.UNLOADED)

            # Emit unload event
            from viloapp_sdk import PluginEvent, EventType
            self.event_bus.emit(PluginEvent(
                type=EventType.PLUGIN_UNLOADED,
                source="plugin_loader",
                data={"plugin_id": plugin_id}
            ))

            logger.info(f"Unloaded plugin: {plugin_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to unload plugin {plugin_id}: {e}")
            return False

    def _load_plugin_module(self, plugin_info: PluginInfo):
        """Load plugin Python module."""
        plugin_id = plugin_info.metadata.id
        plugin_path = plugin_info.path

        # Check if it's a built-in plugin
        if str(plugin_path).startswith("builtin"):
            return self._load_builtin_plugin(plugin_id)

        # Check if it's an entry point plugin
        if str(plugin_path).startswith("entry_points"):
            return self._load_entry_point_plugin(plugin_id)

        # Load from file system
        if plugin_path.is_dir():
            # Look for plugin module
            plugin_file = plugin_path / "plugin.py"
            if not plugin_file.exists():
                plugin_file = plugin_path / "__init__.py"

            if plugin_file.exists():
                # Use the actual package name from the plugin directory
                # For viloxterm package: viloxterm.plugin
                # For viloedit package: viloedit.plugin
                package_src = plugin_path.parent  # This should be the src directory
                if package_src.exists() and package_src.name == "src":
                    # Add src directory to path if not already there
                    if str(package_src) not in sys.path:
                        sys.path.insert(0, str(package_src))

                    # Import the actual package module
                    try:
                        # Get package name from the actual directory name (not plugin_id)
                        package_name = plugin_path.name
                        logger.debug(f"Attempting to import {package_name}.plugin from path {package_src}")
                        module = importlib.import_module(f"{package_name}.plugin")
                        self.loaded_modules[plugin_id] = f"{package_name}.plugin"
                        logger.info(f"Successfully imported {package_name}.plugin")
                        return module
                    except ImportError as e:
                        logger.error(f"Failed to import {package_name}.plugin: {e}")
                        logger.debug("Falling back to standalone module loading")

                # Fallback: load as standalone module
                module_name = f"plugin_{plugin_id}"
                spec = importlib.util.spec_from_file_location(module_name, plugin_file)

                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    sys.modules[module_name] = module
                    spec.loader.exec_module(module)
                    self.loaded_modules[plugin_id] = module_name
                    return module

        return None

    def _load_builtin_plugin(self, plugin_id: str):
        """Load built-in plugin."""
        # Map builtin plugin IDs to modules
        builtin_map = {
            "core-commands": "viloapp.core.plugins.commands",
            "core-themes": "viloapp.core.plugins.themes"
        }

        module_name = builtin_map.get(plugin_id)
        if module_name:
            try:
                return importlib.import_module(module_name)
            except ImportError:
                pass

        return None

    def _load_entry_point_plugin(self, plugin_id: str):
        """Load entry point plugin."""
        try:
            # Load via entry points
            import importlib.metadata

            entry_points = importlib.metadata.entry_points()
            if hasattr(entry_points, 'select'):
                eps = entry_points.select(group='viloapp.plugins')
            else:
                eps = entry_points.get('viloapp.plugins', [])

            for ep in eps:
                if ep.name == plugin_id:
                    # Load the entry point
                    plugin_class = ep.load()
                    # Create a wrapper module
                    module = type('module', (), {'Plugin': plugin_class})
                    return module

        except Exception as e:
            logger.error(f"Failed to load entry point plugin {plugin_id}: {e}")

        return None

    def _find_plugin_class(self, module) -> Optional[type]:
        """Find plugin class in module."""
        # Look for class that implements IPlugin
        for attr_name in dir(module):
            if attr_name.startswith('_'):
                continue

            attr = getattr(module, attr_name)
            if isinstance(attr, type) and issubclass(attr, IPlugin) and attr != IPlugin:
                return attr

        # Fallback: look for specifically named class
        if hasattr(module, 'Plugin'):
            return module.Plugin

        # Look for class ending with 'Plugin'
        for attr_name in dir(module):
            if attr_name.endswith('Plugin'):
                attr = getattr(module, attr_name)
                if isinstance(attr, type):
                    return attr

        return None

    def _create_plugin_context(self, plugin_info: PluginInfo) -> PluginContext:
        """Create context for plugin."""
        plugin_id = plugin_info.metadata.id

        # Get data directory for plugin
        import platformdirs
        data_path = Path(platformdirs.user_data_dir("ViloxTerm")) / "plugins" / plugin_id

        # Create service proxy
        service_proxy = ServiceProxyImpl(self.services)

        # Get plugin configuration
        config_service = self.services.get('configuration')
        if config_service:
            config = config_service.get(f"plugins.{plugin_id}", {})
        else:
            config = {}

        return PluginContext(
            plugin_id=plugin_id,
            plugin_path=plugin_info.path,
            data_path=data_path,
            service_proxy=service_proxy,
            event_bus=self.event_bus,
            configuration=config
        )