"""Plugin discovery system."""

import logging
import json
import importlib.metadata
from pathlib import Path
from typing import List, Set, Optional

from viloapp_sdk import PluginMetadata
from .plugin_registry import PluginInfo, LifecycleState

logger = logging.getLogger(__name__)

class PluginDiscovery:
    """Discovers plugins from various sources."""

    def __init__(self, registry):
        self.registry = registry
        self.discovered_paths: Set[Path] = set()

    def discover_all(self) -> List[PluginInfo]:
        """
        Discover plugins from all sources.

        Returns:
            List of discovered plugin information
        """
        plugins = []

        # Discover from entry points
        plugins.extend(self.discover_entry_points())

        # Discover from plugin directories
        plugins.extend(self.discover_from_directory(self._get_user_plugin_dir()))
        plugins.extend(self.discover_from_directory(self._get_system_plugin_dir()))

        # Discover built-in plugins
        plugins.extend(self.discover_builtin_plugins())

        logger.info(f"Discovered {len(plugins)} plugins")
        return plugins

    def discover_entry_points(self, group: str = "viloapp.plugins") -> List[PluginInfo]:
        """
        Discover plugins via Python entry points.

        Args:
            group: Entry point group name

        Returns:
            List of discovered plugins
        """
        plugins = []

        try:
            # Python 3.8+ compatible entry points discovery
            if hasattr(importlib.metadata, 'entry_points'):
                eps = importlib.metadata.entry_points()
                if hasattr(eps, 'select'):
                    # Python 3.10+
                    entry_points = eps.select(group=group)
                else:
                    # Python 3.8-3.9
                    entry_points = eps.get(group, [])
            else:
                # Fallback for older versions
                entry_points = []

            for entry_point in entry_points:
                try:
                    # Get plugin metadata without loading the plugin
                    plugin_path = self._get_entry_point_path(entry_point)

                    # Create minimal metadata from entry point
                    metadata = PluginMetadata(
                        id=entry_point.name,
                        name=entry_point.name.replace('-', ' ').title(),
                        version="0.0.0",  # Will be updated when loaded
                        description=f"Plugin from {entry_point.value}",
                        author="Unknown"
                    )

                    plugin_info = PluginInfo(
                        metadata=metadata,
                        path=plugin_path,
                        state=LifecycleState.DISCOVERED
                    )

                    plugins.append(plugin_info)
                    logger.debug(f"Discovered entry point plugin: {entry_point.name}")

                except Exception as e:
                    logger.error(f"Failed to process entry point {entry_point.name}: {e}")

        except Exception as e:
            logger.error(f"Failed to discover entry point plugins: {e}")

        return plugins

    def discover_from_directory(self, directory: Path) -> List[PluginInfo]:
        """
        Discover plugins from a directory.

        Args:
            directory: Directory to search for plugins

        Returns:
            List of discovered plugins
        """
        plugins = []

        if not directory or not directory.exists():
            return plugins

        # Look for plugin manifests
        for manifest_path in directory.glob("*/plugin.json"):
            try:
                plugin_info = self._load_plugin_manifest(manifest_path)
                if plugin_info:
                    plugins.append(plugin_info)
                    logger.debug(f"Discovered plugin from: {manifest_path}")
            except Exception as e:
                logger.error(f"Failed to load plugin manifest {manifest_path}: {e}")

        # Look for Python packages with __plugin__ marker
        for plugin_dir in directory.iterdir():
            if plugin_dir.is_dir():
                marker_file = plugin_dir / "__plugin__.py"
                if marker_file.exists():
                    try:
                        plugin_info = self._load_python_plugin(plugin_dir)
                        if plugin_info:
                            plugins.append(plugin_info)
                            logger.debug(f"Discovered Python plugin from: {plugin_dir}")
                    except Exception as e:
                        logger.error(f"Failed to load Python plugin {plugin_dir}: {e}")

        return plugins

    def discover_builtin_plugins(self) -> List[PluginInfo]:
        """
        Discover built-in plugins.

        Returns:
            List of built-in plugins
        """
        plugins = []

        # Define built-in plugins
        builtin_plugins = [
            {
                "id": "core-commands",
                "name": "Core Commands",
                "description": "Built-in command palette and shortcuts"
            },
            {
                "id": "core-themes",
                "name": "Core Themes",
                "description": "Built-in theme support"
            }
        ]

        for plugin_data in builtin_plugins:
            metadata = PluginMetadata(
                id=plugin_data["id"],
                name=plugin_data["name"],
                version="builtin",
                description=plugin_data["description"],
                author="ViloxTerm Team"
            )

            plugin_info = PluginInfo(
                metadata=metadata,
                path=Path("builtin") / plugin_data["id"],
                state=LifecycleState.DISCOVERED
            )

            plugins.append(plugin_info)

        return plugins

    def _load_plugin_manifest(self, manifest_path: Path) -> Optional[PluginInfo]:
        """Load plugin metadata from manifest file."""
        try:
            with open(manifest_path, 'r') as f:
                data = json.load(f)

            metadata = PluginMetadata(
                id=data.get("id"),
                name=data.get("name"),
                version=data.get("version"),
                description=data.get("description"),
                author=data.get("author"),
                homepage=data.get("homepage"),
                repository=data.get("repository"),
                license=data.get("license"),
                icon=data.get("icon"),
                categories=data.get("categories", []),
                keywords=data.get("keywords", []),
                engines=data.get("engines", {}),
                dependencies=data.get("dependencies", []),
                activation_events=data.get("activationEvents", []),
                contributes=data.get("contributes", {})
            )

            # Validate metadata
            errors = metadata.validate()
            if errors:
                logger.error(f"Invalid plugin manifest {manifest_path}: {errors}")
                return None

            return PluginInfo(
                metadata=metadata,
                path=manifest_path.parent,
                state=LifecycleState.DISCOVERED
            )

        except Exception as e:
            logger.error(f"Failed to load plugin manifest {manifest_path}: {e}")
            return None

    def _load_python_plugin(self, plugin_dir: Path) -> Optional[PluginInfo]:
        """Load plugin from Python package."""
        try:
            # Import the __plugin__ module to get metadata
            import importlib.util

            spec = importlib.util.spec_from_file_location(
                f"{plugin_dir.name}.__plugin__",
                plugin_dir / "__plugin__.py"
            )

            if not spec or not spec.loader:
                return None

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Get metadata from module
            if hasattr(module, 'METADATA'):
                metadata = module.METADATA
            elif hasattr(module, 'get_metadata'):
                metadata = module.get_metadata()
            else:
                return None

            return PluginInfo(
                metadata=metadata,
                path=plugin_dir,
                state=LifecycleState.DISCOVERED
            )

        except Exception as e:
            logger.error(f"Failed to load Python plugin {plugin_dir}: {e}")
            return None

    def _get_entry_point_path(self, entry_point) -> Path:
        """Get path for an entry point."""
        # Try to determine the package location
        try:
            module_name = entry_point.value.split(':')[0]
            module = importlib.import_module(module_name)
            if hasattr(module, '__file__'):
                return Path(module.__file__).parent
        except Exception:
            pass

        return Path("entry_points") / entry_point.name

    def _get_user_plugin_dir(self) -> Path:
        """Get user plugin directory."""
        import platformdirs
        return Path(platformdirs.user_data_dir("ViloxTerm")) / "plugins"

    def _get_system_plugin_dir(self) -> Path:
        """Get system plugin directory."""
        import platformdirs
        return Path(platformdirs.site_data_dir("ViloxTerm")) / "plugins"